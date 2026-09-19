import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .cli import settings_status
from .models import Scenario, StrictModel
from .runner import run_scenario
from typing import Literal


class RunRequest(StrictModel):
    scenario: Scenario = "accepted"
    mode: Literal["rehearsal", "live"] = "rehearsal"
    condition: Literal["off", "on"] = "off"
    backend: Literal["local", "modal"] = "local"
    # run_scenario validates the attack name and raises ValueError, which the handler
    # already turns into a 400; no second copy of the catalogue to drift out of sync.
    attack: str | None = None
    guardrail: bool = True


def serve(port: int, results_dir: Path):
    static = Path(__file__).parent/"static"
    run_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def send(self, status, content, content_type="application/json"):
            body = json.dumps(content).encode() if content_type == "application/json" else content
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def local_request(self):
            allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
            origin = self.headers.get("Origin")
            return self.headers.get("Host") in allowed and (not origin or origin in {f"http://{host}" for host in allowed})

        def do_GET(self):
            if not self.local_request():
                return self.send(403, {"error": "Local requests only"})
            path = urlsplit(self.path).path
            if path in ("/", "/app.js", "/style.css"):
                filename, mime = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}[path]
                return self.send(200, (static/filename).read_bytes(), mime)
            if path == "/api/config":
                return self.send(200, settings_status())
            if path == "/api/runs":
                records = [json.loads(p.read_text()) for p in results_dir.glob("*/run.json")]
                return self.send(200, sorted(records, key=lambda x:x["created_at"], reverse=True)[:50])
            if path == "/api/policy":
                return self.send(200, json.loads((Path(__file__).parent/"policy.json").read_text()))
            if path == "/api/guardrail-policy":
                return self.send(200, json.loads((Path(__file__).parent/"guardrail-policy.json").read_text()))
            if path == "/api/comparisons":
                paths = sorted(results_dir.glob("comparison-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
                return self.send(200, [json.loads(p.read_text()) for p in paths[:10]])
            self.send(404, {"error": "Not found"})

        def do_POST(self):
            if not self.local_request() or self.headers.get("Content-Type") != "application/json":
                return self.send(403, {"error": "Local JSON requests only"})
            if self.path != "/api/run":
                return self.send(404, {"error": "Not found"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    return self.send(400, {"error": "Invalid request length"})
                request = RunRequest.model_validate_json(self.rfile.read(length))
            except ValueError:
                return self.send(400, {"error": "Invalid run settings"})
            if not run_lock.acquire(blocking=False):
                return self.send(409, {"error": "A run is already in progress"})
            try:
                result = asyncio.run(run_scenario(**request.model_dump(), results_dir=results_dir))
                self.send(200, result)
            except ValueError as exc:
                self.send(400, {"error": str(exc)})
            except Exception as exc:
                self.send(500, {"error": type(exc).__name__})
            finally:
                run_lock.release()

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Handshake dashboard: http://127.0.0.1:{port}", flush=True)
    server.serve_forever()
