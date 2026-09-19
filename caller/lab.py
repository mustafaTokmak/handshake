"""Client for the repair lab's incident endpoints.

Everything this module reads is another service's output, so no field shape is
assumed and every parse is defensive. Nothing here decides anything: it finds
the incidents the lab is blocked on and delivers a reply it was handed.
"""
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

LAB_URL = os.environ.get("REPAIR_LAB_URL", "http://127.0.0.1:8780").rstrip("/")
TIMEOUT = 8
MAX_QUEUE = 10
# The lab rejects a second reply while the previous repair worker is still
# winding down. That is a wait, not a refusal, so it is worth retrying.
DELIVERY_ATTEMPTS = 4
RETRY_DELAY = 1.5
TRANSIENT_MARKERS = ("retry", "already running", "finishing")
NETWORK_ERRORS = (URLError, OSError, ValueError)


def get(path):
    with urlopen(LAB_URL + path, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode())


def post(path, payload):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("CONTACT_CALLBACK_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(LAB_URL + path, data=body, headers=headers, method="POST")
    with urlopen(request, timeout=TIMEOUT) as response:
        return response.status, json.loads(response.read().decode() or "{}")


def _carrier_states(run):
    """The lab keys carriers by id; older records used a list. Accept both."""
    carriers = run.get("carriers") if isinstance(run, dict) else None
    if isinstance(carriers, dict):
        return [s for s in carriers.values() if isinstance(s, dict)]
    if isinstance(carriers, list):
        return [s for s in carriers if isinstance(s, dict)]
    return []


def _incident_ids(runs):
    """Incident ids the lab says it is blocked on, newest run first."""
    ids = []
    for run in runs if isinstance(runs, list) else []:
        for state in _carrier_states(run):
            incident_id = state.get("incident_id")
            if state.get("status") == "waiting_contact" and incident_id and str(incident_id) not in ids:
                ids.append(str(incident_id))
    return ids


def waiting_incidents():
    """Every incident still waiting for contact context, across all runs.

    Scanning every run rather than only the latest one matters since the lab
    gained shared sessions: starting a new session makes an earlier run stop
    being the latest, and an incident waiting on it would otherwise vanish.
    Include the six comparison children so earlier case incidents remain visible.
    """
    try:
        runs = get("/api/runs?include_children=1")
    except (HTTPError,) + NETWORK_ERRORS:
        return []
    found = []
    for incident_id in _incident_ids(runs)[:MAX_QUEUE]:
        try:
            incident = get("/api/incidents/" + incident_id)
        except (HTTPError,) + NETWORK_ERRORS:
            continue
        if isinstance(incident, dict) and incident.get("status") == "waiting":
            found.append(incident)
    return found


def summarize(incident):
    """One queue row. Display fields only; nothing here is acted on."""
    contact = incident.get("contact") if isinstance(incident.get("contact"), dict) else {}
    return {
        "incident_id": incident.get("id", ""),
        "carrier_id": incident.get("carrier_id", ""),
        "provider": incident.get("company") or incident.get("carrier_id") or "the carrier",
        "phone": contact.get("phone", ""),
        "reason": incident.get("reason", ""),
        "created_at": incident.get("created_at", ""),
    }


def _is_transient(status, detail):
    if status in (409, 429, 503):
        return True
    return status == 400 and any(marker in detail.lower() for marker in TRANSIENT_MARKERS)


def deliver(incident_id, reply, sleep=time.sleep):
    """Send a ContactReply, retrying only failures the lab calls temporary.

    A validation rejection is final and is reported as-is; a busy worker or an
    unreachable lab is retried, because the finding is the product of a phone
    call that cannot be placed again.
    """
    path = "/api/incidents/%s/context" % incident_id
    attempts = 0
    result = {"ok": False, "attempts": 0}
    while attempts < DELIVERY_ATTEMPTS:
        attempts += 1
        try:
            status, body = post(path, reply)
            return {"ok": True, "status": status, "response": body, "attempts": attempts}
        except HTTPError as exc:
            try:
                detail = exc.read().decode()[:400]
            except OSError:
                detail = ""
            result = {"ok": False, "status": exc.code, "error": detail or str(exc.reason), "attempts": attempts}
            if not _is_transient(exc.code, detail):
                return result
        except NETWORK_ERRORS as exc:
            result = {"ok": False, "error": type(exc).__name__, "attempts": attempts}
        if attempts < DELIVERY_ATTEMPTS:
            sleep(RETRY_DELAY)
    return result
