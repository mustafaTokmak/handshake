#!/usr/bin/env python3
"""Tiny local Breaker demo. Run: python3 server.py [--port 8765]."""
import argparse
import json
import os
import sys
import time
from decimal import Decimal, InvalidOperation, ROUND_CEILING
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vendor.txn_harness import Offer  # immutable seller total arithmetic

DEFAULT_LIMIT = 500
EXPECTED = ("within_request", "outside_request", "insufficient_evidence")
FIXTURES = (
    {"id": "refund-20", "label": "Small refund", "amount": 2000,
     "request": "Please refund the duplicate £20 charge."},
    {"id": "refund-4200", "label": "Large refund", "amount": 420000,
     "request": "Do not refund; please explain this charge."},
    {"id": "refund-80", "label": "Uncertain refund", "amount": 8000,
     "request": "I have a billing question, can you help?"},
)


class JevUnavailable(Exception):
    pass


class GeminiUnavailable(Exception):
    pass


def money(pence):
    return "£%d.%02d" % (pence // 100, pence % 100)


def make_offer(fixture):
    return Offer(fixture["id"], (("refund", fixture["amount"]),))


def load_api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key.strip()
    for path in (os.path.join(os.path.dirname(__file__), ".env"),
                 os.path.join(os.path.dirname(__file__), os.pardir, ".env")):
        try:
            with open(path, "r") as env_file:
                for line in env_file:
                    if line.startswith("OPENROUTER_API_KEY="):
                        return line.split("=", 1)[1].strip().strip("'\"")
        except OSError:
            continue
    return ""


def validate_fixtures():
    ids = set()
    for fixture in FIXTURES:
        offer = make_offer(fixture)
        if fixture["id"] in ids or not isinstance(offer.total, int) or offer.total <= 0:
            raise ValueError("invalid duplicate or non-positive fixture")
        ids.add(fixture["id"])


def new_state(limit=DEFAULT_LIMIT, uncertainty_guard=True):
    return {"limit": limit, "uncertainty_guard": uncertainty_guard, "cursor": 0,
            "evaluated": {}, "paid": 0, "exposure": 0,
            "notice": "Ready to evaluate the next proposal."}


validate_fixtures()
STATE = new_state()


def decimal_probability(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise JevUnavailable("invalid probability")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise JevUnavailable("invalid probability")
    if not result.is_finite() or result < 0 or result > 1:
        raise JevUnavailable("invalid probability")
    return result


def cents_for_probability(amount, probability):
    return int((Decimal(amount) * probability).quantize(Decimal("1"), rounding=ROUND_CEILING))


def ask_jev(fixture):
    key = load_api_key()
    if not key:
        raise JevUnavailable("live Jev is unavailable")
    state = ("Synthetic customer request:\n%s\n\nProposed action: issue a refund of %s. "
             "Assess only whether the proposal is within the request, outside it, or lacks evidence.") % (fixture["request"], money(make_offer(fixture).total))
    body = {"model": "typesafe/jev-1.13", "state": state,
            "questions": {"refund_intent": {
                "type": "choice",
                "instructions": "Classify the proposed refund and return probabilities for every criterion.",
                "criteria": {
                    "within_request": "The request explicitly asks to refund the duplicate charge for this amount.",
                    "outside_request": "The request explicitly says not to refund or asks for a different action or amount.",
                    "insufficient_evidence": "The request is ambiguous or lacks enough detail to decide whether this exact refund is wanted.",
                },
            }}}
    request = Request("https://openrouter.ai/api/alpha/decisions",
                      data=json.dumps(body).encode("utf-8"),
                      headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                      method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError):
        raise JevUnavailable("live Jev is unavailable")
    try:
        answer = payload["answers"]["refund_intent"]
        served_model = payload.get("model")
        choice = answer.get("choice")
        probabilities = answer.get("probabilities")
        if (not isinstance(served_model, str) or not served_model or answer.get("type") != "choice"
                or not isinstance(choice, str) or choice not in EXPECTED or not isinstance(probabilities, dict)):
            raise JevUnavailable("invalid Jev answer")
        if set(probabilities) != set(EXPECTED):
            raise JevUnavailable("invalid Jev answer")
        raw = {name: decimal_probability(probabilities[name]) for name in EXPECTED}
        total = sum(raw.values(), Decimal("0"))
        if total <= 0 or abs(total - Decimal("1")) > Decimal("0.01"):
            raise JevUnavailable("invalid Jev answer")
        confidence = answer.get("confidence")
        if confidence is not None:
            confidence = float(decimal_probability(confidence))
        return {"raw": {name: float(value) for name, value in raw.items()},
                "sum": float(total), "choice": choice, "confidence": confidence,
                "model": served_model}
    except (KeyError, TypeError, AttributeError, JevUnavailable):
        raise JevUnavailable("invalid Jev answer")


def ask_gemini(fixture, jev_result):
    key = load_api_key()
    if not key:
        raise GeminiUnavailable("Gemini explanation is unavailable")
    context = ("Synthetic Breaker review. Explain the already-computed Jev result in plain language; "
               "do not authorize or perform any action.\n\nProposal: %s for %s\nSynthetic request: %s\n"
               "Jev choice: %s\nJev probabilities: %s\nRisk limit: %s\nOutcome: %s\nReasons: %s") % (
                   fixture["label"], money(make_offer(fixture).total), fixture["request"], jev_result["choice"],
                   json.dumps(jev_result["probabilities"], sort_keys=True), money(STATE["limit"]),
                   jev_result["status"], "; ".join(jev_result.get("reasons", [])) or "none")
    body = {"model": "google/gemini-3.8-flash", "messages": [
        {"role": "system", "content": "Give a concise explanation of this synthetic risk decision. State that it is a simulated result."},
        {"role": "user", "content": context},
    ], "max_tokens": 400}
    request = Request("https://openrouter.ai/api/v1/chat/completions",
                      data=json.dumps(body).encode("utf-8"),
                      headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                      method="POST")
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text = payload["choices"][0]["message"]["content"]
        served_model = payload.get("model")
        if not isinstance(text, str) or not text.strip() or not isinstance(served_model, str) or not served_model:
            raise GeminiUnavailable("invalid Gemini explanation")
        return {"text": text.strip(), "model": served_model,
                "latency_ms": int(round((time.perf_counter() - started) * 1000))}
    except (HTTPError, URLError, OSError, TimeoutError, ValueError, json.JSONDecodeError,
            KeyError, TypeError, IndexError, AttributeError, GeminiUnavailable):
        raise GeminiUnavailable("Gemini explanation is unavailable")


def fixture_view(fixture, result=None):
    offer = make_offer(fixture)
    item = {"id": fixture["id"], "label": fixture["label"], "amount": offer.total,
            "request": fixture["request"]}
    if result:
        item.update(result)
    return item


def evaluate_next():
    if STATE["cursor"] >= len(FIXTURES):
        STATE["notice"] = "All proposals have been evaluated."
        return None
    fixture = FIXTURES[STATE["cursor"]]
    proposal_id = fixture["id"]
    if proposal_id in STATE["evaluated"]:  # hard duplicate control: no second commit
        return STATE["evaluated"][proposal_id]
    started = time.perf_counter()
    try:
        answer = ask_jev(fixture)
        latency = int(round((time.perf_counter() - started) * 1000))
        raw = answer["raw"]
        exposure = cents_for_probability(make_offer(fixture).total, Decimal(str(answer["raw"]["outside_request"])))
        reasons = []
        if exposure > STATE["limit"]:
            reasons.append("estimated outside-request exposure exceeds the per-action risk limit")
        if STATE["uncertainty_guard"] and Decimal(str(answer["raw"]["insufficient_evidence"])) >= Decimal("0.25"):
            reasons.append("uncertainty guard halts insufficient evidence at or above 25%")
        allowed = not reasons
        result = {"status": "allowed" if allowed else "paused", "reasons": reasons,
                  "probabilities": raw, "probability_sum": answer["sum"], "choice": answer["choice"],
                  "confidence": answer["confidence"], "model": answer["model"],
                  "latency_ms": latency, "calculation": "%s × %.2f%% outside-request = %s" %
                  (money(make_offer(fixture).total), raw["outside_request"] * 100, money(exposure)),
                  "committed": allowed}
    except JevUnavailable:
        result = {"status": "unavailable", "reasons": ["live Jev was unavailable; simulated commit was halted"],
                  "probabilities": {}, "latency_ms": int(round((time.perf_counter() - started) * 1000)),
                  "committed": False}
        STATE["notice"] = "%s could not be evaluated; no simulated commit." % fixture["label"]
    else:
        if allowed:
            STATE["paid"] += make_offer(fixture).total
            STATE["exposure"] += exposure
            STATE["notice"] = "%s passed the live Jev risk check and was simulated as committed." % fixture["label"]
        else:
            STATE["notice"] = "%s was paused before simulated commit." % fixture["label"]
    STATE["evaluated"][proposal_id] = result
    STATE["cursor"] += 1
    return result


def state_payload():
    return {"policy": {"limit": STATE["limit"], "uncertainty_guard": STATE["uncertainty_guard"]},
            "rows": [fixture_view(fixture, STATE["evaluated"].get(fixture["id"])) for fixture in FIXTURES],
            "paid": STATE["paid"], "exposure": STATE["exposure"],
            "next": FIXTURES[STATE["cursor"]]["id"] if STATE["cursor"] < len(FIXTURES) else None,
            "notice": STATE["notice"]}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/state":
            self._send(200, json.dumps(state_payload()))
        elif self.path in ("/", "/index.html"):
            with open(os.path.join(os.path.dirname(__file__), "index.html"), "rb") as page:
                self._send(200, page.read(), "text/html")
        else:
            self._send(404, '{"error":"not found"}')

    def _json(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 <= size <= 4096:
                return None
            return json.loads(self.rfile.read(size) or b"{}")
        except (ValueError, TypeError, json.JSONDecodeError):
            return None

    def do_POST(self):
        global STATE
        if self.path == "/explain":
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                size = 9999
            if not 0 <= size <= 512:
                self._send(413, '{"error":"explanation request too large"}')
                return
            payload = self._json()
            if not isinstance(payload, dict) or set(payload) != {"id"} or not isinstance(payload["id"], str):
                self._send(400, '{"error":"explanation requires a fixture id"}')
                return
            fixture = next((item for item in FIXTURES if item["id"] == payload["id"]), None)
            result = STATE["evaluated"].get(payload["id"])
            if fixture is None or result is None or result.get("status") == "unavailable":
                self._send(409, '{"error":"evaluate this fixture with live Jev first"}')
                return
            try:
                explanation = ask_gemini(fixture, result)
            except GeminiUnavailable:
                self._send(503, '{"error":"Gemini explanation unavailable"}')
                return
            self._send(200, json.dumps(explanation))
            return
        if self.path == "/step":
            evaluate_next()
            self._send(200, json.dumps(state_payload()))
            return
        if self.path == "/reset":
            STATE = new_state()
            self._send(200, json.dumps(state_payload()))
            return
        if self.path == "/policy":
            payload = self._json()
            limit = payload.get("limit") if isinstance(payload, dict) else None
            guard = payload.get("uncertainty_guard") if isinstance(payload, dict) else None
            if not isinstance(limit, int) or isinstance(limit, bool) or not 0 <= limit <= 25000 or not isinstance(guard, bool):
                self._send(400, '{"error":"limit must be integer pence 0..25000 and guard boolean"}')
                return
            STATE = new_state(limit, guard)
            STATE["notice"] = "Policy changed; the simulated run was reset explicitly."
            self._send(200, json.dumps(state_payload()))
            return
        self._send(404, '{"error":"not found"}')

    def log_message(self, *_args):
        pass


def main():
    parser = argparse.ArgumentParser(description="Local-only Breaker demo")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print("Breaker demo listening at http://127.0.0.1:%d" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
