import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import logfire
from opentelemetry import trace
from pydantic_ai import capture_run_messages
from pydantic_ai.messages import ModelMessagesTypeAdapter

from .agent import BASE_INSTRUCTIONS, ToolClient, live_recovery, rehearsal_recovery
from .attacks import NAMES
from .provider import CONTRACT
from .transport import LocalTransport, ModalTransport


def configure_tracing():
    enabled = bool(os.getenv("LOGFIRE_TOKEN"))
    logfire.configure(service_name="handshake", send_to_logfire=enabled, console=False, inspect_arguments=False)
    if enabled:
        logfire.instrument_pydantic_ai()
    return enabled


def atomic_json(path: Path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2)+"\n")
    temporary.replace(path)


def implementation_fingerprint():
    package = Path(__file__).parent
    digest = hashlib.sha256()
    for name in ("agent.py", "attacks.py", "models.py", "provider.py", "transport.py", "worker.py", "runner.py"):
        digest.update(name.encode())
        digest.update((package/name).read_bytes())
    return digest.hexdigest()


async def run_scenario(scenario="accepted", mode="rehearsal", condition="off", backend="local", results_dir=Path("results"), request_key=None, attack=None, guardrail=True):
    if scenario not in ("accepted", "not_accepted", "pending", "unavailable") or mode not in ("rehearsal", "live") or condition not in ("off", "on") or backend not in ("local", "modal"):
        raise ValueError("Invalid run configuration")
    if attack is not None and attack not in NAMES:
        raise ValueError("Unknown attack")
    if mode == "rehearsal" and condition != "off":
        raise ValueError("Rehearsals have no Gateway condition and cannot simulate rule-on results")
    if mode == "live":
        if not os.getenv("PYDANTIC_AI_GATEWAY_API_KEY") or not os.getenv("HANDSHAKE_MODEL"):
            raise ValueError("Gateway key is missing; fill in handshake/.env")
        if condition == "on" and not os.getenv("HANDSHAKE_GATEWAY_POLICY_REFERENCE"):
            raise ValueError("Configure a real remote Gateway rule and its policy reference first")
    run_id = uuid.uuid4().hex
    request_key = request_key or f"req-{run_id}"
    order_id = "ORDER-1042"
    directory = Path(results_dir)/run_id
    directory.mkdir(parents=True)
    record = {"run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(), "scenario": scenario, "mode": mode, "condition": condition if mode == "live" else "not_applicable", "backend": backend, "attack": attack, "guardrail": guardrail if mode == "live" else "not_applicable", "order_id": order_id, "request_key": request_key, "status": "starting", "model": os.getenv("HANDSHAKE_MODEL") if mode == "live" else None, "gateway_route": os.getenv("HANDSHAKE_GATEWAY_ROUTE", "modal"), "gateway_base_url": os.getenv("PYDANTIC_AI_GATEWAY_BASE_URL"), "policy_reference": os.getenv("HANDSHAKE_GATEWAY_POLICY_REFERENCE") if mode == "live" and condition == "on" else None, "gateway_policy_verified": False, "guardrail_reference": os.getenv("HANDSHAKE_GATEWAY_GUARDRAIL_REFERENCE") or None, "gateway_guardrail_action": os.getenv("HANDSHAKE_GATEWAY_GUARDRAIL_ACTION") or None, "gateway_guardrail_verified": False, "prompt_sha256": hashlib.sha256(BASE_INSTRUCTIONS.encode()).hexdigest(), "contract_sha256": hashlib.sha256(CONTRACT.encode()).hexdigest(), "usage": None, "trace_id": None, "trace_url": None}
    # Persist the original key before any create request can happen.
    record["implementation_sha256"] = implementation_fingerprint()
    atomic_json(directory/"run.json", record)
    transport = ModalTransport() if backend == "modal" else LocalTransport()
    client = ToolClient(transport, order_id=order_id, request_key=request_key)
    start = time.perf_counter()
    with logfire.span("Handshake {scenario} {mode} {condition}", scenario=scenario, mode=mode, condition=condition, run_id=run_id):
        context = trace.get_current_span().get_span_context()
        if context.is_valid and os.getenv("LOGFIRE_TOKEN"):
            record["trace_id"] = f"{context.trace_id:032x}"
            project = os.getenv("HANDSHAKE_LOGFIRE_PROJECT_URL", "").rstrip("/")
            if project:
                query = urlencode({"q": f"trace_id='{record['trace_id']}'"})
                record["trace_url"] = f"{project}?{query}"
        outcome = None
        initialized = False
        try:
            await transport.start()
            await transport.rpc({"op": "initialize", "scenario": scenario, "attack": attack})
            initialized = True
            record["startup_ms"] = round((time.perf_counter()-start)*1000, 2)
            client.started = time.perf_counter()
            timeout = await client.call("create_shipment", {"order_id": order_id, "request_key": request_key}, initial=True)
            if mode == "rehearsal":
                outcome = await rehearsal_recovery(client, order_id, request_key)
            else:
                with capture_run_messages() as messages:
                    try:
                        outcome, record["usage"], _ = await live_recovery(client, order_id, request_key, timeout, condition, guardrail)
                    finally:
                        (directory/"messages.json").write_bytes(ModelMessagesTypeAdapter.dump_json(messages, indent=2))
                        record["usage"] = client.model_usage
            record["outcome"] = outcome.model_dump(mode="json")
            record["status"] = outcome.status
        except Exception as exc:
            record["status"] = "error"
            # SDK error bodies can include account details. Keep the persisted/UI error minimal.
            record["error"] = type(exc).__name__
            record["outcome"] = None
            logfire.error("Run failed with {error_type}", error_type=type(exc).__name__)
        finally:
            record["scenario_ms"] = round((time.perf_counter()-client.started)*1000, 2) if initialized else None
            record["events"] = client.events
            record["blocked"] = client.blocked
            record["flagged"] = client.flagged
            try:
                if initialized:
                    record["evaluation"] = await transport.rpc({"op": "evaluate", "order_id": order_id, "request_key": request_key, "outcome": outcome.model_dump(mode="json") if outcome else None})
            except Exception as exc:
                record["evaluation_error"] = type(exc).__name__
            finally:
                try:
                    await transport.close()
                except Exception as exc:
                    record["cleanup_error"] = type(exc).__name__
                record["total_ms"] = round((time.perf_counter()-start)*1000, 2)
                atomic_json(directory/"run.json", record)
    return record


async def batch(condition, experiment, trials=5, backend="local", results_dir=Path("results"), attack=None, guardrail=True):
    if not 5 <= trials <= 50:
        raise ValueError("Use 5–50 exploratory trials per condition and case")
    if condition not in ("off", "on"):
        raise ValueError("Choose the actual remote policy condition")
    runs = []
    for scenario in ("accepted", "not_accepted", "pending"):
        for trial in range(trials):
            # Identical keys for paired conditions; always a fresh provider instance.
            key = "req-" + hashlib.sha256(f"{experiment}:{scenario}:{trial}".encode()).hexdigest()[:32]
            runs.append(await run_scenario(scenario, "live", condition, backend, results_dir, key, attack, guardrail))
    result = {"experiment": experiment, "condition": condition, "attack": attack, "guardrail": guardrail, "run_ids": [r["run_id"] for r in runs]}
    atomic_json(Path(results_dir)/f"batch-{uuid.uuid4().hex}.json", result)
    return result


def compare(experiment, results_dir=Path("results")):
    runs = []
    for path in Path(results_dir).glob("batch-*.json"):
        batch_record = json.loads(path.read_text())
        if batch_record["experiment"] == experiment:
            runs.extend(json.loads((Path(results_dir)/run_id/"run.json").read_text()) for run_id in batch_record["run_ids"])
    seen = set()
    for run in runs:
        key = (run["scenario"], run["condition"], run["request_key"])
        if key in seen:
            raise ValueError("Repeated trials detected; use a new experiment name instead of mixing reruns")
        seen.add(key)
    signatures = {tuple(r.get(k) for k in ("model", "gateway_route", "gateway_base_url", "backend", "prompt_sha256", "contract_sha256", "implementation_sha256")) for r in runs}
    if len(signatures) != 1:
        raise ValueError("Comparison requires identical model, route, backend, prompt, contract and implementation")
    for scenario in ("accepted", "not_accepted", "pending"):
        keys = [{r["request_key"] for r in runs if r["scenario"] == scenario and r["condition"] == c} for c in ("off", "on")]
        if keys[0] != keys[1] or len(keys[0]) < 5:
            raise ValueError("Comparison requires at least five matched trials per condition per case")
    groups = []
    for scenario in ("accepted", "not_accepted", "pending"):
        for condition in ("off", "on"):
            selected = [r for r in runs if r["scenario"] == scenario and r["condition"] == condition]
            groups.append({"scenario": scenario, "condition": condition, "trials": len(selected), "errors": sum(r["status"] == "error" for r in selected), **{metric: sum(r.get("evaluation", {}).get(metric, 0) for r in selected) for metric in ("passed", "duplicate_count", "correct_recovery", "appropriate_retry", "appropriate_unresolved", "fresh_key_attempts", "tool_calls")}, "input_tokens": sum((r["usage"] or {}).get("input_tokens", 0) for r in selected), "output_tokens": sum((r["usage"] or {}).get("output_tokens", 0) for r in selected), "mean_scenario_ms": sum(r.get("scenario_ms") or 0 for r in selected)/len(selected)})
    result = {"experiment": experiment, "note": "Exploratory sequential batches only; order/time confounding remains. Remote rule application is unverified until inspected in actual Gateway traces. Missing usage from failed runs is not counted. No causal improvement is inferred automatically.", "groups": groups, "run_ids": [r["run_id"] for r in runs]}
    atomic_json(Path(results_dir)/f"comparison-{uuid.uuid4().hex}.json", result)
    return result
