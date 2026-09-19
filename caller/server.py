#!/usr/bin/env python3
"""Local-only static server for the escalation caller.

The browser holds the WebSocket to Gemini Live directly, so this process never
touches audio. It serves the page, hands over the session configuration, and
persists validated findings. Stdlib only, to match breaker-demo and to avoid
depending on the handshake toolchain.
"""
import argparse
import errno
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from urllib.request import urlopen

import env
import lab
from brief import FIXTURE, from_incident, instruction_for
from models import FINDING_DECLARATION, CallFinding, to_context

HERE = Path(__file__).resolve().parent
CALLS = HERE / "calls"
DEFAULT_MODEL = "gemini-3.8-live"
# 8770 is claimed by macOS sharingd on a stock machine, which made the caller
# die on startup with nothing but an EADDRINUSE. Start above it and, when the
# port was not asked for by name, walk forward rather than refusing to run.
DEFAULT_PORT = 8771
PORT_SCAN = 8
KEY_NAMES = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_API_KEY", "GOOGLE_API")
# Generous: the page posts the finding plus the whole call transcript, and a
# finding's list entries carry no length limit of their own. to_context() is
# what guarantees the lab's size contract, so this only has to stop abuse.
MAX_BODY = 262144


def pick_incident(wanted=""):
    """The incident to brief the caller for: the requested one if it is still
    waiting, otherwise the most recent one the lab is blocked on."""
    queue = lab.waiting_incidents()
    if wanted:
        for incident in queue:
            if incident.get("id") == wanted:
                return incident, queue
    return (queue[0] if queue else None), queue


def load_key():
    """The Gemini key, under whichever of its several names it was written."""
    return env.first(KEY_NAMES)


def list_live_models(key):
    """Ask the key which models it can actually reach. Beats guessing an ID."""
    url = "https://generativelanguage.googleapis.com/v1beta/models?key=%s&pageSize=200" % key
    with urlopen(url, timeout=15) as response:
        payload = json.loads(response.read().decode())
    names = []
    for model in payload.get("models", []):
        methods = model.get("supportedGenerationMethods", []) or model.get("supportedActions", [])
        if any("bidi" in method.lower() for method in methods):
            names.append(model["name"].replace("models/", ""))
    return sorted(names)


def bind(handler, port, scan=1):
    """First free port at or after `port`. scan=1 means: this one or nothing."""
    last = None
    for candidate in range(port, port + max(scan, 1)):
        try:
            return ThreadingHTTPServer(("127.0.0.1", candidate), handler)
        except OSError as exc:
            if exc.errno not in (errno.EADDRINUSE, errno.EACCES):
                raise
            last = exc
    raise last


def serve(port, model, scan=1):
    key = load_key()
    CALLS.mkdir(exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        def send_payload(self, status, content, content_type="application/json"):
            body = json.dumps(content).encode() if content_type == "application/json" else content
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def is_local(self):
            allowed = {"127.0.0.1:%d" % port, "localhost:%d" % port}
            origin = self.headers.get("Origin")
            return self.headers.get("Host") in allowed and (
                not origin or origin in {"http://%s" % host for host in allowed})

        def do_GET(self):
            if not self.is_local():
                return self.send_payload(403, {"error": "Local requests only"})
            path = urlsplit(self.path).path
            files = {"/": ("index.html", "text/html; charset=utf-8"),
                     "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                     "/style.css": ("style.css", "text/css; charset=utf-8")}
            if path in files:
                name, mime = files[path]
                return self.send_payload(200, (HERE / name).read_bytes(), mime)
            if path == "/api/incidents":
                # The queue the lab is blocked on. An operator chooses which one
                # to call; nothing here places a call by itself.
                return self.send_payload(200, {
                    "incidents": [lab.summarize(i) for i in lab.waiting_incidents()]})
            if path == "/api/session":
                # The key reaches the browser because the browser owns the Gemini
                # socket. Bound to localhost; do not expose this server.
                # liveSetup is the single source of truth: the page and the smoke
                # test send this same object, so they cannot drift apart.
                wanted = (parse_qs(urlsplit(self.path).query).get("incident") or [""])[0][:100]
                incident, queue = pick_incident(wanted)
                brief = from_incident(incident) if incident else FIXTURE
                return self.send_payload(200, {
                    "apiKey": key, "model": model, "hasKey": bool(key),
                    "brief": brief,
                    "source": brief.get("source", "fixture"),
                    "incidentId": brief.get("incident_id", ""),
                    "callbackPath": brief.get("callback_path", ""),
                    "queue": [lab.summarize(i) for i in queue],
                    "liveSetup": {
                        "model": "models/" + model,
                        "generationConfig": {"responseModalities": ["AUDIO"]},
                        "systemInstruction": {"parts": [{"text": instruction_for(brief)}]},
                        "tools": [{"functionDeclarations": [FINDING_DECLARATION]}],
                        "inputAudioTranscription": {},
                        "outputAudioTranscription": {},
                        # Push-to-talk: we signal turn boundaries explicitly, so the
                        # model never guesses from silence and cannot hear itself.
                        "realtimeInputConfig": {
                            "automaticActivityDetection": {"disabled": True}},
                    }})
            if path == "/api/models":
                if not key:
                    return self.send_payload(400, {"error": "No API key configured"})
                try:
                    return self.send_payload(200, {"live_models": list_live_models(key)})
                except Exception as exc:
                    return self.send_payload(502, {"error": type(exc).__name__})
            if path == "/api/calls":
                records = []
                for item in sorted(CALLS.glob("*.json"), reverse=True)[:20]:
                    try:
                        records.append(json.loads(item.read_text()))
                    except ValueError:
                        continue
                return self.send_payload(200, records)
            self.send_payload(404, {"error": "Not found"})

        def do_POST(self):
            if not self.is_local() or self.headers.get("Content-Type") != "application/json":
                return self.send_payload(403, {"error": "Local JSON requests only"})
            if self.path != "/api/finding":
                return self.send_payload(404, {"error": "Not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= MAX_BODY:
                    return self.send_payload(400, {"error": "Invalid request length"})
                payload = json.loads(self.rfile.read(length))
                finding = CallFinding.model_validate(payload.get("finding") or {})
            except ValueError as exc:
                # A malformed finding is a real outcome: the model said something
                # the schema refuses. Record the rejection rather than hiding it.
                return self.send_payload(400, {"error": "Finding rejected by schema",
                                               "detail": str(exc)[:500]})
            incident_id = str(payload.get("incidentId") or "")[:100]
            carrier = str(payload.get("carrier") or FIXTURE["provider"])[:100]
            relay = {"attempted": False}
            if incident_id:
                # Only the typed finding crosses this boundary. The transcript
                # stays here; it is never sent to the code-generating agent.
                context = to_context(finding, carrier)
                reply = {"message_id": "escalation-call-%d" % time.time(),
                         "source": "escalation-voice-caller",
                         "context": context}
                relay = {"attempted": True, "incident_id": incident_id,
                         "context_chars": len(context)}
                # A transient rejection is retried inside deliver(): the call
                # that produced this finding cannot be placed a second time.
                relay.update(lab.deliver(incident_id, reply))
            record = {"recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      "incident_id": incident_id or None, "carrier": carrier, "model": model,
                      "finding": finding.model_dump(mode="json"),
                      "relay": relay,
                      "transcript": payload.get("transcript") or []}
            name = CALLS / ("call-%d.json" % time.time())
            name.write_text(json.dumps(record, indent=2) + "\n")
            self.send_payload(200, {"saved": name.name, "finding": record["finding"], "relay": relay})

        def log_message(self, *_):
            pass

    server = bind(Handler, port, scan)
    port = server.server_port
    print("Escalation caller: http://127.0.0.1:%d" % port, flush=True)
    print("API key: %s   model: %s" % ("present" if key else "MISSING", model), flush=True)
    # The relay target and its credential are the two things that decide
    # whether a finding reaches the lab, so say both before a call is placed
    # rather than after one has already been made.
    print("Repair lab: %s   callback token: %s" % (
        lab.lab_url(), "present" if lab.callback_token() else "MISSING"), flush=True)
    if not key:
        print("Set GOOGLE_API_KEY, or put it in caller/.env", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Local escalation caller")
    parser.add_argument("--port", type=int, default=None,
                        help="Default %d, or the next free port after it" % DEFAULT_PORT)
    parser.add_argument("--model", default=env.get("CALLER_MODEL", DEFAULT_MODEL))
    parser.add_argument("--list-models", action="store_true", help="Print Live-capable models for this key and exit")
    args = parser.parse_args()
    if args.list_models:
        key = load_key()
        if not key:
            print("No API key found", file=sys.stderr)
            raise SystemExit(1)
        print(json.dumps(list_live_models(key), indent=2))
        return
    # An explicit --port is an instruction; the default is only a preference.
    chosen = args.port or int(env.get("CALLER_PORT", DEFAULT_PORT))
    serve(chosen, args.model, scan=1 if args.port else PORT_SCAN)


if __name__ == "__main__":
    main()
