import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from handshake.agent import ToolClient, incident_history, make_agent
from handshake.runner import configure_tracing, run_scenario
from handshake.transport import LocalTransport


class RunnerTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        configure_tracing()

    async def test_all_rehearsals_and_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            for scenario in ("accepted","not_accepted","pending","unavailable"):
                r=await run_scenario(scenario,results_dir=Path(d))
                self.assertTrue(r["evaluation"]["passed"],r)
                self.assertEqual(r["evaluation"]["duplicate_count"],0)
                self.assertEqual(r["condition"],"not_applicable")
                self.assertIsNone(r["usage"])
                saved=json.loads((Path(d)/r["run_id"]/"run.json").read_text())
                self.assertEqual(saved["request_key"],r["events"][0]["arguments"]["request_key"])

    async def test_live_configuration_fails_before_side_effects(self):
        with tempfile.TemporaryDirectory() as d, patch.dict("os.environ", {},clear=True):
            with self.assertRaises(ValueError): await run_scenario(mode="live",results_dir=Path(d))
            self.assertEqual(list(Path(d).iterdir()),[])
            with self.assertRaises(ValueError): await run_scenario(condition="on",results_dir=Path(d))

    async def test_cancelled_rpc_cannot_be_reused_for_evaluation(self):
        started=asyncio.Event()
        class DelayedPipe:
            def write(self, data): pass
            async def drain(self): pass
            async def readline(self):
                started.set()
                await asyncio.Future()
        transport=LocalTransport()
        transport.lock=asyncio.Lock()
        transport.broken=False
        pipe=DelayedPipe()
        transport.process=SimpleNamespace(stdin=pipe,stdout=pipe)
        task=asyncio.create_task(transport.rpc({"op":"tool"}))
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        with self.assertRaisesRegex(RuntimeError,"channel interrupted"):
            await transport.rpc({"op":"evaluate"})

    async def test_real_agent_tool_roundtrip_with_function_model(self):
        """Exercise Pydantic AI tool serialization without claiming an LLM test."""
        transport=LocalTransport()
        await transport.start()
        try:
            await transport.rpc({"op":"initialize","scenario":"accepted"})
            client=ToolClient(transport)
            initial=await client.call("create_shipment",{"order_id":"ORDER-1042","request_key":"original"},initial=True)
            step=0
            def respond(messages, info):
                nonlocal step
                step+=1
                if step==1:
                    return ModelResponse(parts=[ToolCallPart("lookup_request",{"request_key":"original"})])
                if step==2:
                    return ModelResponse(parts=[ToolCallPart("get_shipment",{"shipment_id":"SHIP-9001"})])
                return ModelResponse(parts=[ToolCallPart(info.output_tools[0].name,{"status":"completed","shipment_id":"SHIP-9001","tracking_number":"TRACK-9001","explanation":"Verified"})])
            agent=make_agent(FunctionModel(respond))
            result=await agent.run(deps=client,message_history=incident_history("ORDER-1042","original",initial))
            self.assertEqual(result.output.shipment_id,"SHIP-9001")
            e=await transport.rpc({"op":"evaluate","order_id":"ORDER-1042","request_key":"original","outcome":result.output.model_dump()})
            self.assertTrue(e["passed"])
            self.assertEqual([e["tool"] for e in client.events],["create_shipment","lookup_request","get_shipment"])
        finally:
            await transport.close()


if __name__ == "__main__":
    unittest.main()
