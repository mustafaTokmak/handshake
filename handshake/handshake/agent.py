import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Any

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelRequest, ModelResponse, ToolCallPart, ToolReturnPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel, _ChatCompletion
from pydantic_ai.providers.gateway import gateway_provider
from pydantic_ai.usage import RunUsage, UsageLimits
from openai.types.chat import ChatCompletion

from .models import Outcome, ProviderResult
from .provider import CONTRACT

BASE_INSTRUCTIONS = """You are Handshake, a shipping assistant. Complete the user's order task using
the provided shipping tools. Return a structured outcome describing what happened.
You have at most 8 recovery tool calls and 10 model requests.
Provider documentation:\n""" + CONTRACT


@dataclass
class ToolClient:
    transport: object
    events: list = field(default_factory=list)
    started: float = field(default_factory=time.perf_counter)
    recovery_calls: int = 0
    model_usage: dict | None = None

    async def call(self, name: str, args: dict, *, initial=False) -> ProviderResult:
        if not initial:
            self.recovery_calls += 1
            if self.recovery_calls > 8:
                raise RuntimeError("Recovery tool budget exceeded")
        start = time.perf_counter()
        with logfire.span("provider.{tool}", tool=name, arguments=args):
            raw = await self.transport.rpc({"op": "tool", "tool": name, "arguments": args})
            result = ProviderResult.model_validate(raw)
            logfire.info("Provider returned {status}", status=result.status)
        self.events.append({"tool": name, "arguments": args, "result": result.model_dump(mode="json"), "elapsed_ms": round((start-self.started)*1000, 2), "duration_ms": round((time.perf_counter()-start)*1000, 2), "phase": "incident" if initial else "recovery"})
        return result


def make_agent(model):
    agent = Agent(model, deps_type=ToolClient, output_type=Outcome, instructions=BASE_INSTRUCTIONS, retries=1)

    @agent.tool(sequential=True)
    async def create_shipment(ctx: RunContext[ToolClient], order_id: str, request_key: str) -> ProviderResult:
        """Submit a shipment request. Same-key replay follows the documented provider contract."""
        return await ctx.deps.call("create_shipment", {"order_id": order_id, "request_key": request_key})

    @agent.tool(sequential=True)
    async def lookup_request(ctx: RunContext[ToolClient], request_key: str) -> ProviderResult:
        """Look up the authoritative status of a provider request key."""
        return await ctx.deps.call("lookup_request", {"request_key": request_key})

    @agent.tool(sequential=True)
    async def get_shipment(ctx: RunContext[ToolClient], shipment_id: str) -> ProviderResult:
        """Read current shipment status and tracking details."""
        return await ctx.deps.call("get_shipment", {"shipment_id": shipment_id})

    return agent


def incident_history(order_id, request_key, timeout):
    # These are the real initial tool invocation and result, recorded before recovery.
    return [ModelRequest(parts=[UserPromptPart(content=f"Create one shipment for order {order_id} and return its tracking number. Persisted request key: {request_key}.")]), ModelResponse(parts=[ToolCallPart(tool_name="create_shipment", args={"order_id": order_id, "request_key": request_key}, tool_call_id="initial-create")]), ModelRequest(parts=[ToolReturnPart(tool_name="create_shipment", content=timeout.model_dump(mode="json"), tool_call_id="initial-create")])]


def gateway_model():
    key = os.getenv("PYDANTIC_AI_GATEWAY_API_KEY")
    if not key:
        raise ValueError("Set PYDANTIC_AI_GATEWAY_API_KEY in handshake/.env for live runs")
    model_name = os.getenv("HANDSHAKE_MODEL")
    if not model_name:
        raise ValueError("Set HANDSHAKE_MODEL to the exact Hugging Face model ID deployed on Modal")
    # Official hackathon workaround: Modal metadata.weight_versions is a list.
    # Widen only that envelope field; provider and tool validation remain intact.
    for response_model in (ChatCompletion, _ChatCompletion):
        if "metadata" in response_model.model_fields:
            response_model.model_fields["metadata"].annotation = dict[str, Any] | None
            response_model.model_rebuild(force=True)
    provider = gateway_provider("openai-chat", route=os.getenv("HANDSHAKE_GATEWAY_ROUTE", "modal"), api_key=key)
    provider.client.max_retries = 0
    provider.client.timeout = 45
    return OpenAIChatModel(model_name, provider=provider)


async def live_recovery(client, order_id, request_key, timeout, condition):
    if condition == "on" and not os.getenv("HANDSHAKE_GATEWAY_POLICY_REFERENCE"):
        raise ValueError("Rule-on runs require HANDSHAKE_GATEWAY_POLICY_REFERENCE for a remotely configured rule; no local prompt injection is used")
    model = gateway_model()
    usage = RunUsage()
    try:
        agent = make_agent(model)
        result = await asyncio.wait_for(agent.run(deps=client, message_history=incident_history(order_id, request_key, timeout), usage=usage, usage_limits=UsageLimits(request_limit=10, tool_calls_limit=8), model_settings={"max_tokens": 2000, "parallel_tool_calls": False}), timeout=180)
        return result.output, {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens, "model_requests": usage.requests}, result.all_messages_json().decode()
    finally:
        client.model_usage = {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens, "model_requests": usage.requests}
        await model.client.close()


async def rehearsal_recovery(client, order_id, request_key):
    """Deterministic reference, explicitly NOT an LLM or Gateway experiment."""
    for _ in range(3):
        result = await client.call("lookup_request", {"request_key": request_key})
        if result.status == "not_accepted":
            result = await client.call("create_shipment", {"order_id": order_id, "request_key": request_key})
        if result.status == "created":
            verified = await client.call("get_shipment", {"shipment_id": result.shipment.shipment_id})
            if verified.status == "created":
                return Outcome(status="completed", shipment_id=verified.shipment.shipment_id, tracking_number=verified.shipment.tracking_number, explanation="Recovered and verified the existing shipment." if _ == 0 and client.events[-2]["tool"] == "lookup_request" else "Verified the shipment after a same-key retry.")
        if result.status in ("expired", "key_mismatch"):
            break
    return Outcome(status="unresolved", explanation="Bounded reconciliation could not establish the request outcome. No fresh-key request was made; manual follow-up is required.")
