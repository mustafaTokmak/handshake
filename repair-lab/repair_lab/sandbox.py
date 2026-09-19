import asyncio
import json
import time
from pathlib import Path
import httpx
import modal
from .carriers import BY_ID, expected_quote
from .models import Quote

TEST_ORDERS = [
    {"reference": "ORDER-CHECK-A", "weight_kg": 1.1, "distance_km": 127, "destination_country": "GB"},
    {"reference": "ORDER-CHECK-B", "weight_kg": 7.3, "distance_km": 811, "destination_country": "GB"},
]


def invalid_responses(carrier_id):
    malformed = [{}, {"price_minor": -1, "currency": "GBP", "delivery_days": 1, "service": "standard"}, {"error": "provider unavailable"}]
    current = {
        "cedar": {"api_version": "2", "quote": {"amount": {"minor": -100, "iso": "GBP"}, "transit": {"business_days": 2}, "service_code": "standard"}},
        "harbor": {"version": "3", "rate": {"pence": -100, "currency_code": "GBP", "days": 4, "product": "standard"}},
        "copper": {"version": "2", "offer": {"total_gbp": "-1.00", "currency": "GBP", "eta_days": 1, "product": "standard"}},
    }
    if carrier_id in current:
        malformed.extend([current[carrier_id], {"version": "2", {"cedar": "quote", "harbor": "rate", "copper": "offer"}[carrier_id]: {}}])
    return malformed


class PatchSandbox:
    async def __aenter__(self):
        image = modal.Image.debian_slim(python_version="3.12").add_local_file(str(Path(__file__).with_name("adapter_runner.py")), "/app/adapter_runner.py")
        app = await modal.App.lookup.aio("handshake-repair-validation", create_if_missing=True)
        self.sandbox = await modal.Sandbox.create.aio(image=image, app=app, timeout=300, idle_timeout=90, block_network=True, cpu=1, memory=256)
        self.id = self.sandbox.object_id
        return self

    async def call(self, source, function, argument):
        process = await self.sandbox.exec.aio("python", "-I", "/app/adapter_runner.py", timeout=10)
        raw = json.dumps({"source": source, "function": function, "argument": argument}) + "\n"
        process.stdin.write(raw.encode()); await process.stdin.drain.aio(); process.stdin.write_eof()
        async def read_bounded():
            chunks = []; size = 0
            async for chunk in process.stdout:
                size += len(chunk)
                if size > 64000:
                    await self.sandbox.terminate.aio()
                    raise ValueError("Sandbox output exceeded 64 KB")
                chunks.append(chunk)
            return "".join(chunks)
        output = await asyncio.wait_for(read_bounded(), timeout=20)
        lines = [line.removeprefix("REPAIR_RESULT:") for line in output.splitlines() if line.startswith("REPAIR_RESULT:")]
        if len(lines) != 1: return {"ok": False, "error": "SandboxProtocolError", "detail": "Adapter did not return one result"}
        try:
            answer = json.loads(lines[0])
            if not isinstance(answer, dict) or not isinstance(answer.get("ok"), bool): raise ValueError()
            return answer
        except (ValueError, TypeError): return {"ok": False, "error": "SandboxProtocolError", "detail": "Invalid adapter output"}

    async def __aexit__(self, *_):
        try: await self.sandbox.terminate.aio()
        finally: await self.sandbox.detach.aio()


async def validate_patch(carrier_id, source, order, event):
    """Execute candidates remotely; compare results against an independent host oracle."""
    start = time.perf_counter(); checks = []; current_quote = None; failure_response = None
    async with PatchSandbox() as sandbox:
        event("sandbox_started", {"sandbox_id": sandbox.id, "network": "blocked"})
        async with httpx.AsyncClient(timeout=10, trust_env=False) as http:
            for fixture_order, legacy in [(order, False), (TEST_ORDERS[0], False), (TEST_ORDERS[1], False), (order, True)]:
                request = await sandbox.call(source, "build_request", fixture_order)
                if not request.get("ok") or not isinstance(request.get("result"), dict):
                    checks.append({"case": "request", "passed": False, "error": request.get("error", "InvalidRequest")}); break
                suffix = "?version=legacy" if legacy else ""
                response = await http.post(f'http://127.0.0.1:{BY_ID[carrier_id]["port"]}/quote{suffix}', json=request["result"])
                payload = response.json()
                parsed = await sandbox.call(source, "parse_quote", payload)
                if not parsed.get("ok"):
                    failure_response = payload
                    checks.append({"case": "legacy" if legacy else "current", "passed": False, "http_status": response.status_code, "error": parsed.get("error"), "detail": parsed.get("detail")}); break
                try:
                    quote = Quote.model_validate(parsed["result"]).model_dump()
                    passed = response.status_code == 200 and quote == expected_quote(carrier_id, fixture_order)
                    check = {"case": "legacy" if legacy else "current", "passed": passed, "http_status": response.status_code}
                    if not passed: check["error"] = "Quote disagrees with independent carrier pricing truth"
                    checks.append(check)
                    if current_quote is None and not legacy: current_quote = quote
                except (ValueError, KeyError, TypeError) as exc:
                    checks.append({"case": "quote_validation", "passed": False, "error": type(exc).__name__})
                if not checks[-1]["passed"]: break
            if checks and all(c["passed"] for c in checks):
                for malformed in invalid_responses(carrier_id):
                    parsed = await sandbox.call(source, "parse_quote", malformed)
                    rejected = not parsed.get("ok")
                    if not rejected:
                        try: Quote.model_validate(parsed.get("result"))
                        except (ValueError, TypeError): rejected = True
                    checks.append({"case": "invalid_input", "passed": rejected, "error": None if rejected else "Adapter invented a quote for invalid provider data"})
        result = {"passed": len(checks) == 4 + len(invalid_responses(carrier_id)) and all(c["passed"] for c in checks), "checks": checks, "sandbox_id": sandbox.id, "duration_ms": round((time.perf_counter()-start)*1000), "quote": current_quote, "failure_response": failure_response}
        event("sandbox_finished", result)
        return result
