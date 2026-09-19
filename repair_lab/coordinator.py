import ast
import asyncio
import difflib
import hashlib
import json
import os
import threading
import uuid
from pathlib import Path
from urllib.parse import urlencode
import httpx
import logfire
from opentelemetry import trace
from pydantic import BaseModel, Field, ValidationError
from .agent import propose, INSTRUCTIONS
from .carriers import CARRIERS, BY_ID, LEGACY_SOURCE, contact_context
from .models import Quote
from .sandbox import validate_patch
from .store import now


class LegacyResponse(BaseModel):
    price_minor: int = Field(strict=True, gt=0)
    currency: str
    delivery_days: int = Field(strict=True, gt=0)
    service: str


def code_hash(source):
    try: normalized = ast.dump(ast.parse(source), include_attributes=False)
    except SyntaxError: normalized = source.strip()
    return hashlib.sha256(normalized.encode()).hexdigest()


def fingerprint():
    h = hashlib.sha256()
    for name in ("agent.py", "coordinator.py", "models.py", "carriers.py", "sandbox.py", "adapter_runner.py"):
        h.update((Path(__file__).parent/name).read_bytes())
    return h.hexdigest()


class Coordinator:
    def __init__(self, store):
        self.store = store; self.active = set(); self.lock = threading.RLock()
        # A crashed process cannot leave a run silently marked as actively repairing.
        for run in store.runs(limit=None):
            for cid, state in run["carriers"].items():
                if state["status"] in ("loading", "repairing", "resuming"):
                    status = "interrupted"
                    if state.get("incident_id"):
                        incident = store.incident(state["incident_id"])
                        if incident:
                            incident.update(status="waiting", last_error="Process restarted during repair")
                            store.save_incident(incident)
                            status = "waiting_contact"
                    attempts = state["attempts"]
                    for attempt in attempts:
                        if attempt["status"] == "sandbox_running":
                            attempt["status"] = "interrupted"
                    store.update_carrier(run["id"], cid, status=status, attempts=attempts, error="Process restarted; start a fresh comparison or resend contact context with a new message ID")

    def new_session(self):
        from .models import StartRequest
        with self.lock:
            if self.active: raise ValueError("Wait for the active repair to finish before resetting the demo")
            return self._start(StartRequest(condition="protected"), ready=True)

    def start(self, request, session_id=None):
        with self.lock:
            if self.active:
                raise ValueError("A repair is already running")
            if session_id:
                run = self.store.get_run(session_id)
                if not run or any(s["status"] != "ready" for s in run["carriers"].values()):
                    raise ValueError("This session has already started; create a new test session")
                if self.store.latest()["id"] != session_id:
                    raise ValueError("A newer shared session exists; refresh before starting")
                run.update(order=request.order.model_dump(), condition=request.condition, attack=request.attack)
                for state in run["carriers"].values(): state["status"] = "loading"
                self.store.save_run(run)
                self._launch(session_id, "all", self._initial(session_id))
                return run
            return self._start(request)

    def _start(self, request, ready=False):
        run_id = uuid.uuid4().hex
        run = {"id": run_id, "created_at": now(), "order": request.order.model_dump(), "condition": request.condition, "attack": request.attack, "implementation_sha256": fingerprint(), "agent_prompt_sha256": hashlib.sha256(INSTRUCTIONS.encode()).hexdigest(), "route": os.getenv("REPAIR_GATEWAY_ROUTE", "repair-lab"), "model": os.getenv("HANDSHAKE_MODEL"), "remote_state_verified": False, "events": [], "carriers": {c["id"]: {"status": "loading", "quote": None, "attempts": [], "source": LEGACY_SOURCE, "incident_id": None} for c in CARRIERS}}
        if ready:
            for state in run["carriers"].values(): state["status"] = "ready"
        self.store.save_run(run)
        if not ready: self._launch(run_id, "all", self._initial(run_id))
        return run

    def _launch(self, run_id, key, coroutine):
        with self.lock:
            if (run_id, key) in self.active:
                coroutine.close(); raise ValueError("Work already running")
            self.active.add((run_id, key))
        def worker():
            try: asyncio.run(coroutine)
            except Exception as exc:
                self.store.event(run_id, key, "worker_error", {"error": type(exc).__name__})
                for cid, state in self.store.get_run(run_id)["carriers"].items():
                    if (key == "all" or cid == key) and state["status"] in ("loading", "repairing", "resuming"):
                        self.store.update_carrier(run_id, cid, status="error", error=type(exc).__name__)
            finally:
                with self.lock: self.active.discard((run_id, key))
                logfire.force_flush()
        threading.Thread(target=worker, daemon=True).start()

    async def _initial(self, run_id):
        run = self.store.get_run(run_id); order = run["order"]
        async with httpx.AsyncClient(timeout=10, trust_env=False) as http:
            async def fetch(c):
                cid = c["id"]
                body = {"order_ref": order["reference"], "weight_kg": order["weight_kg"], "distance_km": order["distance_km"], "destination_country": order["destination_country"]}
                try:
                    r = await http.post(f'http://127.0.0.1:{c["port"]}/quote', json=body); payload = r.json()
                    self.store.event(run_id, cid, "quote_response", {"http_status": r.status_code, "response": payload})
                    # Actual Pydantic wire validation triggers failures on changed schemas.
                    wire = LegacyResponse.model_validate(payload)
                    r.raise_for_status()
                    quote = Quote(amount_minor=wire.price_minor, currency=wire.currency, eta_days=wire.delivery_days, service=wire.service)
                    self.store.update_carrier(run_id, cid, status="available", quote=quote.model_dump())
                    return None
                except (ValidationError, httpx.HTTPStatusError) as exc:
                    error = str(exc)[:1500]
                    self.store.update_carrier(run_id, cid, status="repairing", response=payload, error=error)
                    self.store.event(run_id, cid, "validation_failed", {"error": error})
                    return cid
                except httpx.HTTPError as exc:
                    self.store.update_carrier(run_id, cid, status="infrastructure_error", error=type(exc).__name__)
                    return None
            broken = [cid for cid in await asyncio.gather(*(fetch(c) for c in CARRIERS)) if cid]
        await asyncio.gather(*(self._repair(run_id, cid, None, "initial") for cid in broken))

    async def _repair(self, run_id, cid, context, phase):
        event = lambda kind, data: self.store.event(run_id, cid, kind, {"phase": phase, **data})
        with logfire.span("Carrier repair {carrier} {phase}", carrier=cid, phase=phase, run_id=run_id):
            span = trace.get_current_span().get_span_context()
            project = os.getenv("HANDSHAKE_LOGFIRE_PROJECT_URL", "").rstrip("/")
            if span.is_valid and project:
                self.store.update_carrier(run_id, cid, trace_url=project+"?"+urlencode({"q": f"trace_id='{span.trace_id:032x}'"}))
            proposals = 0; phase_attempts = 0; seen = set()
            try:
                while phase_attempts < 5 and proposals < 10:
                    run = self.store.get_run(run_id); state = run["carriers"][cid]
                    prior = [{k:a[k] for k in ("hypothesis", "source", "validation") if k in a} for a in state["attempts"][-5:]]
                    event("investigating", {"attempt": phase_attempts+1, "context_available": bool(context)})
                    candidate, usage = await propose(cid, run["order"], state.get("response"), state.get("error"), state["source"], prior, context, run["attack"], event)
                    proposals += 1; digest = code_hash(candidate.source)
                    if digest in seen:
                        event("duplicate_proposal", {"code_sha256": digest})
                        self.store.update_carrier(run_id, cid, error="The candidate repeats a previous patch. Make a materially different code change based on the failing feedback; whitespace and comments do not count.")
                        continue
                    seen.add(digest); phase_attempts += 1
                    attempt = {"number": len(state["attempts"])+1, "phase": phase, "phase_attempt": phase_attempts, "created_at": now(), **candidate.model_dump(), "code_sha256": digest, "usage": usage, "diff": "".join(difflib.unified_diff(state["source"].splitlines(True), candidate.source.splitlines(True), fromfile="current_adapter.py", tofile="candidate_adapter.py")), "status": "sandbox_running"}
                    attempts = state["attempts"]+[attempt]
                    self.store.update_carrier(run_id, cid, attempts=attempts, status="repairing")
                    event("candidate_proposed", {"number": attempt["number"], "hypothesis": candidate.hypothesis, "code_sha256": digest})
                    validation = await validate_patch(cid, candidate.source, run["order"], event)
                    attempt["validation"] = validation; attempt["status"] = "passed" if validation["passed"] else "failed"
                    self.store.update_carrier(run_id, cid, attempts=attempts)
                    if validation["passed"]:
                        # Promotion stores a version; no generated code executes on the host.
                        self.store.update_carrier(run_id, cid, status="restored", quote=validation["quote"], source=candidate.source, adapter_version=digest, error=None)
                        event("quote_restored", {"quote": validation["quote"], "adapter_version": digest})
                        incident_id = state.get("incident_id")
                        if incident_id:
                            incident = self.store.incident(incident_id); incident["status"] = "resolved"; self.store.save_incident(incident)
                        return
                    self.store.update_carrier(run_id, cid, error=json.dumps(validation["checks"]), response=validation.get("failure_response") or state.get("response"))
                self._escalate(run_id, cid, phase, "Five distinct candidates failed" if phase_attempts == 5 else "Proposal budget reached before five distinct candidates", event)
            except Exception as exc:
                # SDK bodies may contain account information. Persist a safe error class.
                error = type(exc).__name__
                status = "infrastructure_error"
                attempts = self.store.get_run(run_id)["carriers"][cid]["attempts"]
                for attempt in attempts:
                    if attempt["status"] == "sandbox_running":
                        attempt.update(status="interrupted", validation={"passed": False, "checks": [], "error": error})
                self.store.update_carrier(run_id, cid, status=status, error=error, attempts=attempts)
                incident_id = self.store.get_run(run_id)["carriers"][cid].get("incident_id")
                if incident_id:
                    incident = self.store.incident(incident_id)
                    incident.update(status="waiting", last_error=error)
                    self.store.save_incident(incident)
                    self.store.update_carrier(run_id, cid, status="waiting_contact")
                event("repair_error", {"error": error, "candidate_attempts": phase_attempts})

    def _escalate(self, run_id, cid, phase, reason, event):
        run = self.store.get_run(run_id); state = run["carriers"][cid]
        if phase != "initial":
            self.store.update_carrier(run_id, cid, status="needs_review", error=reason)
            incident = self.store.incident(state["incident_id"]); incident["status"] = "needs_review"; self.store.save_incident(incident)
            event("operator_review_required", {"reason": reason}); return
        incident_id = "INC-"+uuid.uuid4().hex[:12].upper(); c = BY_ID[cid]
        incident = {"id": incident_id, "run_id": run_id, "carrier_id": cid, "company": c["name"], "contact": c["contact"], "status": "waiting", "created_at": now(), "reason": reason, "messages": [], "handoff": {"type": "carrier_contact_requested", "failure_summary": state.get("error"), "attempts": [{"number": a["number"], "hypothesis": a["hypothesis"], "checks": a.get("validation", {}).get("checks")} for a in state["attempts"]], "callback_path": f"/api/incidents/{incident_id}/context", "questions": ["Please provide the current API request/response contract and required agreement details."]}, "transport": "stub_no_call_placed"}
        self.store.save_incident(incident)
        self.store.update_carrier(run_id, cid, status="waiting_contact", incident_id=incident_id)
        event("contact_requested", {"incident_id": incident_id, "contact": c["contact"], "reason": reason, "transport": "stub_no_call_placed"})

    def callback(self, incident_id, reply):
        with self.lock, self.store.lock:
            incident = self.store.incident(incident_id)
            if not incident: raise ValueError("Unknown incident")
            if any(m["message_id"] == reply.message_id for m in incident["messages"]): return {"accepted": True, "duplicate": True, "incident_id": incident_id}
            if incident["status"] != "waiting": raise ValueError("Incident is not waiting for context")
            if (incident["run_id"], incident["carrier_id"]) in self.active:
                raise ValueError("Previous repair worker is finishing; retry this message shortly")
            incident["messages"].append({**reply.model_dump(), "received_at": now()}); incident["status"] = "resuming"; self.store.save_incident(incident)
            self.store.update_carrier(incident["run_id"], incident["carrier_id"], status="resuming")
            self.store.event(incident["run_id"], incident["carrier_id"], "contact_context_received", {"incident_id": incident_id, **reply.model_dump()})
            self._launch(incident["run_id"], incident["carrier_id"], self._repair(incident["run_id"], incident["carrier_id"], reply.context, "contact-1"))
        return {"accepted": True, "duplicate": False, "incident_id": incident_id}
