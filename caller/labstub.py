#!/usr/bin/env python3
"""Stand-in for repair-lab's contact endpoints, for testing and rehearsal.

repair-lab needs Python 3.12 and uv. This mirrors the routes the caller
touches, with the same record shapes and the same ContactReply constraints, so
the integration can be exercised on the system Python. It is a test double, not
a reimplementation: it validates and records, it does not repair anything.
"""
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

INCIDENT_ID = "inc-harbor-001"
AGREEMENT = "HARBOR-DEMO-AGREEMENT-7F29"

INCIDENT = {
    "id": INCIDENT_ID, "run_id": "run-demo-1", "carrier_id": "harbor",
    "company": "Harbor Freightline",
    "contact": {"name": "Sam Arden", "email": "integrations@harbor-freightline.example",
                "phone": "+44 7700 900204"},
    "status": "waiting", "created_at": "2026-09-19T16:40:00Z",
    "reason": "Adapter repair exhausted without contact context",
    "messages": [],
    "handoff": {
        "type": "carrier_contact_requested",
        "failure_summary": "POST /quote returned 422 unavailable agreement on every attempt.",
        "attempts": [
            {"number": 1, "hypothesis": "Response renamed price_minor to rate.pence; remapped the parser.",
             "checks": {"schema": "pass", "quote_matches_expected": "fail"}},
            {"number": 2, "hypothesis": "Request needs metric units; converted weight and distance.",
             "checks": {"schema": "pass", "quote_matches_expected": "fail"}},
        ],
        "callback_path": "/api/incidents/%s/context" % INCIDENT_ID,
        "questions": ["Please provide the current API request/response contract and required agreement details."],
    },
    "transport": "stub_no_call_placed",
}
# Carriers keyed by id, as the lab stores them.
LATEST = {"id": "run-demo-1", "created_at": "2026-09-19T16:39:00Z", "condition": "baseline",
          "carriers": {
              "parcelnest": {"status": "available", "incident_id": None},
              "harbor": {"status": "waiting_contact", "incident_id": INCIDENT_ID},
          }}
RUNS = [LATEST]
received = []


def serve(port):
    class Handler(BaseHTTPRequestHandler):
        def send_json(self, status, data):
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def local(self):
            return self.headers.get("Host") in {"127.0.0.1:%d" % port, "localhost:%d" % port}

        def do_GET(self):
            if not self.local():
                return self.send_json(403, {"error": "Local requests only"})
            path = urlsplit(self.path).path
            if path == "/api/latest":
                return self.send_json(200, LATEST)
            if path == "/api/runs":
                return self.send_json(200, RUNS)
            if path.startswith("/api/incidents/"):
                wanted = path.rsplit("/", 1)[-1]
                if wanted == INCIDENT_ID:
                    return self.send_json(200, INCIDENT)
                return self.send_json(404, {"error": "Incident not found"})
            self.send_json(404, {"error": "Not found"})

        def do_POST(self):
            if not self.local() or self.headers.get("Content-Type") != "application/json":
                return self.send_json(403, {"error": "Local JSON requests only"})
            parts = self.path.strip("/").split("/")
            if len(parts) != 4 or parts[:2] != ["api", "incidents"] or parts[3] != "context":
                return self.send_json(404, {"error": "Not found"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 20000:
                    raise ValueError("Invalid payload size")
                data = json.loads(self.rfile.read(size))
                # Same constraints as repair_lab.models.ContactReply.
                for field, low, high in (("message_id", 1, 100), ("context", 10, 12000), ("source", 1, 100)):
                    value = data.get(field, "carrier-contact-agent" if field == "source" else None)
                    if not isinstance(value, str) or not low <= len(value) <= high:
                        raise ValueError("%s must be a string of %d..%d chars" % (field, low, high))
                if set(data) - {"message_id", "context", "source"}:
                    raise ValueError("Extra inputs are not permitted")
            except (ValueError, TypeError) as exc:
                return self.send_json(400, {"error": str(exc)[:1200]})
            if parts[2] != INCIDENT_ID:
                return self.send_json(400, {"error": "Unknown incident"})
            if any(m["message_id"] == data["message_id"] for m in INCIDENT["messages"]):
                return self.send_json(202, {"accepted": True, "duplicate": True, "incident_id": parts[2]})
            INCIDENT["messages"].append({**data, "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            INCIDENT["status"] = "resuming"
            received.append(data)
            print("\n=== ContactReply received (%d chars) ===" % len(data["context"]), flush=True)
            print(data["context"], flush=True)
            print("=== agreement code present: %s ===\n" % (AGREEMENT in data["context"]), flush=True)
            return self.send_json(202, {"accepted": True, "incident_id": parts[2], "status": "resuming"})

        def log_message(self, *_):
            pass

    print("Repair-lab stub: http://127.0.0.1:%d  (incident %s waiting)" % (port, INCIDENT_ID), flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Test double for repair-lab contact endpoints")
    ap.add_argument("--port", type=int, default=8780)
    serve(ap.parse_args().port)
