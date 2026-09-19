import argparse
import asyncio
import json
import os
import uuid
from pathlib import Path

import logfire
from dotenv import dotenv_values
from pydantic_ai import Agent

from .agent import gateway_model
from .runner import atomic_json, batch, compare, configure_tracing, run_scenario

PROJECT = Path(__file__).resolve().parent.parent


def settings_status():
    return {"gateway_key": bool(os.getenv("PYDANTIC_AI_GATEWAY_API_KEY")), "model": os.getenv("HANDSHAKE_MODEL") or None, "route": os.getenv("HANDSHAKE_GATEWAY_ROUTE", "modal"), "logfire_token": bool(os.getenv("LOGFIRE_TOKEN")), "policy_reference": os.getenv("HANDSHAKE_GATEWAY_POLICY_REFERENCE") or None, "modal_auth": bool((os.getenv("MODAL_TOKEN_ID") and os.getenv("MODAL_TOKEN_SECRET")) or (Path.home()/".modal.toml").exists())}


async def warmup(condition, results_dir):
    """Same code/model/prompt in each run. Toggle the warm-up rule in Logfire."""
    from opentelemetry import trace
    model = gateway_model()
    try:
        with logfire.span("Gateway warmup {condition}", condition=condition):
            result = await asyncio.wait_for(Agent(model).run("Explain how HTTPS certificate validation works.", model_settings={"max_tokens": 2000}), timeout=180)
            context = trace.get_current_span().get_span_context()
            record = {"kind": "warmup", "condition": condition, "model": model.model_name, "output": result.output, "words": len(result.output.split()), "input_tokens": result.usage.input_tokens, "output_tokens": result.usage.output_tokens, "trace_id": f"{context.trace_id:032x}" if context.is_valid and os.getenv("LOGFIRE_TOKEN") else None}
        results_dir.mkdir(exist_ok=True, parents=True)
        atomic_json(results_dir/f"warmup-{condition}-{uuid.uuid4().hex}.json", record)
        return record
    finally:
        await model.client.close()


def main():
    # Empty template fields must not override Modal's authenticated CLI profile.
    for key, value in dotenv_values(PROJECT/".env").items():
        if value:
            os.environ.setdefault(key, value)
    parser = argparse.ArgumentParser(description="Handshake: reconcile before retry")
    parser.add_argument("--results-dir", type=Path, default=PROJECT/"results")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Show configuration presence, never credentials")
    serve = commands.add_parser("serve", help="Local demo dashboard")
    serve.add_argument("--port", type=int, default=8765)
    run = commands.add_parser("run")
    run.add_argument("--scenario", choices=["accepted", "not_accepted", "pending", "unavailable"], default="accepted")
    run.add_argument("--mode", choices=["rehearsal", "live"], default="rehearsal")
    for item in (run, commands.add_parser("batch"), commands.add_parser("warmup")):
        item.add_argument("--condition", choices=["off", "on"], default="off", help="Record the actual rule state already set in Gateway; does not toggle it")
        if item.prog.endswith("batch"):
            item.add_argument("--experiment", required=True)
            item.add_argument("--trials", type=int, default=5)
        if not item.prog.endswith("warmup"):
            item.add_argument("--backend", choices=["local", "modal"], default="local")
    compare_parser = commands.add_parser("compare")
    compare_parser.add_argument("--experiment", required=True)
    args = parser.parse_args()
    if args.command == "doctor":
        print(json.dumps(settings_status(), indent=2))
        return
    configure_tracing()
    try:
        if args.command == "serve":
            from .server import serve
            serve(args.port, args.results_dir)
            return
        if args.command == "run":
            result = asyncio.run(run_scenario(args.scenario, args.mode, args.condition, args.backend, args.results_dir))
        elif args.command == "batch":
            result = asyncio.run(batch(args.condition, args.experiment, args.trials, args.backend, args.results_dir))
        elif args.command == "warmup":
            result = asyncio.run(warmup(args.condition, args.results_dir))
        else:
            result = compare(args.experiment, args.results_dir)
        print(json.dumps(result, indent=2))
        if result.get("status") == "error":
            raise SystemExit(1)
    except ValueError as exc:
        parser.error(str(exc))
    finally:
        logfire.force_flush()


if __name__ == "__main__":
    main()
