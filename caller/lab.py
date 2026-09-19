"""Client for the repair lab's incident endpoints.

Everything this module reads is another service's output, so no field shape is
assumed and every parse is defensive. Nothing here decides anything: it finds
the incidents the lab is blocked on and delivers a reply it was handed.
"""
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import env

DEFAULT_LAB_URL = "http://127.0.0.1:8780"
TIMEOUT = 8
MAX_QUEUE = 10
# The lab rejects a second reply while the previous repair worker is still
# winding down. That is a wait, not a refusal, so it is worth retrying.
DELIVERY_ATTEMPTS = 4
RETRY_DELAY = 1.5
TRANSIENT_MARKERS = ("retry", "already running", "finishing")
NETWORK_ERRORS = (URLError, OSError, ValueError)


def lab_url():
    """Read at call time, not import time, so a reload() is visible here."""
    return env.get("REPAIR_LAB_URL", DEFAULT_LAB_URL).rstrip("/")


def callback_token():
    """The bearer the lab expects on /context. Shared with it through .env."""
    return env.get("CONTACT_CALLBACK_TOKEN")


def get(path):
    with urlopen(lab_url() + path, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode())


def post(path, payload):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    token = callback_token()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(lab_url() + path, data=body, headers=headers, method="POST")
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
    """
    try:
        runs = get("/api/runs")
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
    call that cannot be placed again. A 401 is neither: the lab wants a
    callback token we did not send, so the .env is re-read once in case the
    operator supplied it after this process started. Only once — repeating a
    rejected credential is not a retry, it is a loop.
    """
    path = "/api/incidents/%s/context" % incident_id
    attempts = 0
    reread = False
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
            if exc.code == 401 and not reread:
                reread = True
                before = callback_token()
                env.reload()
                if callback_token() and callback_token() != before:
                    continue
                result["hint"] = ("The lab requires CONTACT_CALLBACK_TOKEN. Set it in .env "
                                  "beside the lab's own value and relay this call again.")
                return result
            if not _is_transient(exc.code, detail):
                return result
        except NETWORK_ERRORS as exc:
            result = {"ok": False, "error": type(exc).__name__, "attempts": attempts}
        if attempts < DELIVERY_ATTEMPTS:
            sleep(RETRY_DELAY)
    return result
