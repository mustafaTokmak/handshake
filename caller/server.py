#!/usr/bin/env python3
"""Local-only static server for the escalation caller.

The browser holds the WebSocket to Gemini Live directly, so this process never
touches audio. It serves the page, hands over the session configuration, and
persists validated findings. Stdlib only, to match breaker-demo and to avoid
depending on the handshake toolchain.
"""
import argparse
import json
import os
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

from brief import FIXTURE, SYSTEM_INSTRUCTION
from models import FINDING_DECLARATION, CallFinding

HERE = Path(__file__).resolve().parent
CALLS = HERE / "calls"
DEFAULT_MODEL = "gemini-3.8-live"
KEY_NAMES = ("GOOGLE_API_KEY", "GEMINI_API_KEY", "GOOGLE_GENAI_API_KEY", "GOOGLE_API")
MAX_BODY = 32768


def load_key():
    for name in KEY_NAMES:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    for path in (HERE / ".env", HERE.parent / ".env"):
        try:
            text = path.read_text()
        except OSError:
            continue
        for name in KEY_NAMES:
            found = re.search(r"^%s\s*=\s*['\"]?([^'\"\s]+)" % name, text, re.M)
            if found:
                return found.group(1)
    return ""


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


def serve(port, model):
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
            if path == "/api/session":
                # The key reaches the browser because the browser owns the Gemini
                # socket. Bound to localhost; do not expose this server.
                # liveSetup is the single source of truth: the page and the smoke
                # test send this same object, so they cannot drift apart.
                return self.send_payload(200, {
                    "apiKey": key, "model": model, "hasKey": bool(key),
                    "brief": FIXTURE,
                    "liveSetup": {
                        "model": "models/" + model,
                        "generationConfig": {"responseModalities": ["AUDIO"]},
                        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
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
            record = {"recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      "run_id": FIXTURE["run_id"], "model": model,
                      "finding": finding.model_dump(mode="json"),
                      "transcript": payload.get("transcript") or []}
            name = CALLS / ("call-%d.json" % time.time())
            name.write_text(json.dumps(record, indent=2) + "\n")
            self.send_payload(200, {"saved": name.name, "finding": record["finding"]})

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("Escalation caller: http://127.0.0.1:%d" % port, flush=True)
    print("API key: %s   model: %s" % ("present" if key else "MISSING", model), flush=True)
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
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--model", default=os.environ.get("CALLER_MODEL", DEFAULT_MODEL))
    parser.add_argument("--list-models", action="store_true", help="Print Live-capable models for this key and exit")
    args = parser.parse_args()
    if args.list_models:
        key = load_key()
        if not key:
            print("No API key found", file=sys.stderr)
            raise SystemExit(1)
        print(json.dumps(list_live_models(key), indent=2))
        return
    serve(args.port, args.model)


if __name__ == "__main__":
    main()
