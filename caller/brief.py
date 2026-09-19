"""The evidence packet handed to the voice agent before it places the call.

Shaped like a Handshake results/<run_id>/run.json so that wiring a real run in
later is a loader change, not a redesign. FIXTURE is a contract-drift failure:
the provider's response stopped matching ProviderResult, so the run died on
validation rather than reaching an outcome.
"""
import json

FIXTURE = {
    "run_id": "e3c1a77b94d2401f8a66f0b2d5c81a90",
    "created_at": "2026-09-19T15:12:04.881000+00:00",
    "provider": "Northwind Shipping API",
    "support_line": "+44 20 7946 0102",
    "order_id": "ORDER-1042",
    "request_key": "req-a3f91c8e5b7d4266",
    "status": "error",
    "error": "ValidationError",
    "failure": {
        "kind": "contract_drift",
        "tool": "lookup_request",
        "detail": (
            "Response no longer validates against ProviderResult. The object under "
            "'shipment' is missing the required field 'tracking_number'; an unrecognised "
            "field 'tracking_ref' is present instead. Status vocabulary also returned "
            "'in_transit', which is not one of the eight documented values."
        ),
        "expected_fields": ["shipment_id", "order_id", "tracking_number", "status"],
        "observed_fields": ["shipment_id", "order_id", "tracking_ref", "status"],
        "last_known_good": "2026-09-18T22:40:11Z",
    },
    "events": [
        {"tool": "create_shipment", "arguments": {"order_id": "ORDER-1042", "request_key": "req-a3f91c8e5b7d4266"},
         "result": {"status": "timeout", "detail": "Provider response timed out. Request outcome is unknown."},
         "elapsed_ms": 0.0, "phase": "incident"},
        {"tool": "lookup_request", "arguments": {"request_key": "req-a3f91c8e5b7d4266"},
         "result": {"status": "unavailable", "detail": "Request-status service is unavailable."},
         "elapsed_ms": 812.4, "phase": "recovery"},
        {"tool": "lookup_request", "arguments": {"request_key": "req-a3f91c8e5b7d4266"},
         "result": {"status": "invalid", "detail": "Schema validation failed: 'tracking_number' missing, 'tracking_ref' unexpected."},
         "elapsed_ms": 2104.9, "phase": "recovery"},
    ],
}


def opening_facts(brief):
    """Compact, quotable facts. The agent must speak from these, not invent."""
    failure = brief["failure"]
    lines = [
        "Order: %s" % brief["order_id"],
        "Idempotency key preserved: %s" % brief["request_key"],
        "Failing call: %s" % failure["tool"],
        "Last known good: %s" % failure["last_known_good"],
        "Expected fields: %s" % ", ".join(failure["expected_fields"]),
        "Fields actually returned: %s" % ", ".join(failure["observed_fields"]),
        "Validation error: %s" % failure["detail"],
    ]
    for event in brief["events"]:
        lines.append("Tool %s returned %s at +%.1fs — %s" % (
            event["tool"], event["result"]["status"], event["elapsed_ms"] / 1000.0, event["result"]["detail"]))
    return "\n".join("- " + line for line in lines)


SYSTEM_INSTRUCTION = """You are the escalation agent for an automated shipping integration. \
You have just called the support line for %(provider)s because your integration broke and \
you cannot resolve it from their documentation. A human support representative has answered.

You are the CALLER, not the support desk. Never describe yourself as support. Speak first, \
as soon as the line opens, and keep the opening to about fifteen seconds.

Open in roughly this shape, in your own words:
"Hi, this is the automated integration agent calling about order ORDER-1042. Our lookup_request call \
started failing last night: we expect a field called tracking_number and we're getting tracking_ref \
instead. Can you tell me what changed?"

Say the order number out loud. Say both field names out loud. Then stop and listen.

The evidence from the failed run:
%(facts)s

How to conduct the call:
- Lead with the specific discrepancy: the field you expected and the field you received.
- Ask directly what changed, when it changed, and what you should send or read instead.
- Ask one question at a time, then stop and listen. Do not deliver monologues.
- If they are vague, ask one concrete follow-up. Do not interrogate them; two follow-ups is plenty.
- Never invent details. Every technical fact you state must come from the evidence above.
- You are gathering information only. You have no authority to confirm a shipment exists, to \
agree that a duplicate is acceptable, or to promise any action. If the representative asks you \
to confirm or approve something, say that you are only collecting information and that a human \
engineer will decide.
- Keep the whole call under about two minutes.
- The representative speaks in discrete turns. When they finish, reply once and then wait. \
Never ask whether they can hear you, and never fill a silence \u2014 silence means they are thinking.

Before you finish, every discrepancy in the evidence must have been raised: the renamed field \
AND the unrecognised status value the API returned. If they answer the first but you have not \
yet asked about the second, ask about it now. Also ask whether there is a way to keep the old \
behaviour while you update.

Only once each of those has been answered or explicitly refused, call the report_finding \
function exactly once, then thank them and say goodbye.""" % {
    "provider": FIXTURE["provider"],
    "facts": opening_facts(FIXTURE),
}


if __name__ == "__main__":
    print(json.dumps({"brief": FIXTURE, "system_instruction": SYSTEM_INSTRUCTION}, indent=2))
