import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .carriers import CARRIERS, public_company, contact_context, start_carriers
from .coordinator import Coordinator
from .models import StartRequest, ContactReply
from .store import Store


def serve(port=8780, state_dir=Path("state")):
    static = Path(__file__).parent/"static"
    store = Store(state_dir/"repair.sqlite")
    coordinator = Coordinator(store)
    carrier_servers = start_carriers()
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, data, mime="application/json"):
            body = json.dumps(data).encode() if mime == "application/json" else data
            self.send_response(status); self.send_header("Content-Type", mime); self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store"); self.send_header("X-Content-Type-Options", "nosniff"); self.end_headers(); self.wfile.write(body)
        def local(self):
            allowed = {f"localhost:{port}", f"127.0.0.1:{port}"}
            return self.headers.get("Host") in allowed and self.headers.get("Origin") in (None, *["http://"+s for s in allowed])
        def do_GET(self):
            if not self.local(): return self.send(403, {"error": "Local requests only"})
            path = urlsplit(self.path).path
            if path in ("/", "/app.js", "/style.css"):
                name, mime = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript"), "/style.css": ("style.css", "text/css")}[path]
                return self.send(200, (static/name).read_bytes(), mime)
            if path == "/api/config": return self.send(200, {"carriers": [public_company(c) for c in CARRIERS], "gateway_configured": bool(os.getenv("PYDANTIC_AI_GATEWAY_API_KEY")), "route": os.getenv("REPAIR_GATEWAY_ROUTE", "repair-lab"), "model": os.getenv("HANDSHAKE_MODEL"), "contact_mode": "stub_no_call_placed"})
            if path == "/api/runs": return self.send(200, [{k:r[k] for k in ("id", "created_at", "condition", "order", "carriers")} for r in store.runs()])
            if path == "/api/latest": return self.send(200, store.latest())
            if path.startswith("/api/runs/"):
                r = store.get_run(path.rsplit("/", 1)[-1]); return self.send(200 if r else 404, r or {"error": "Run not found"})
            if path.startswith("/api/incidents/"):
                r = store.incident(path.rsplit("/", 1)[-1]); return self.send(200 if r else 404, r or {"error": "Incident not found"})
            return self.send(404, {"error": "Not found"})
        def do_POST(self):
            if not self.local() or self.headers.get("Content-Type") != "application/json": return self.send(403, {"error": "Local JSON requests only"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 20000: raise ValueError("Invalid payload size")
                data = json.loads(self.rfile.read(size))
                if self.path == "/api/runs":
                    if coordinator.active: return self.send(409, {"error": "A repair is running. Wait for it to finish before starting a fresh comparison."})
                    return self.send(202, coordinator.start(StartRequest.model_validate(data)))
                parts = self.path.strip("/").split("/")
                if len(parts) == 4 and parts[:2] == ["api", "incidents"] and parts[3] in ("context", "simulate-reply"):
                    incident_id = parts[2]
                    if parts[3] == "simulate-reply":
                        incident = store.incident(incident_id)
                        if not incident or incident["carrier_id"] != "harbor": raise ValueError("Only Harbor has a simulated contact reply")
                        reply = ContactReply(message_id=f"simulated-harbor-reply-{len(incident['messages'])+1}", source="simulated-carrier-representative", context=contact_context())
                    else:
                        token = os.getenv("CONTACT_CALLBACK_TOKEN")
                        if token and not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer "+token): return self.send(401, {"error": "Callback authentication required"})
                        reply = ContactReply.model_validate(data)
                    return self.send(202, coordinator.callback(incident_id, reply))
                return self.send(404, {"error": "Not found"})
            except (ValueError, TypeError) as exc: return self.send(400, {"error": str(exc)[:1200]})
        def log_message(self, *_): pass
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Repair lab: http://127.0.0.1:{port}", flush=True)
    try: server.serve_forever()
    finally:
        server.server_close()
        for carrier in carrier_servers: carrier.shutdown(); carrier.server_close()
