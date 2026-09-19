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


CONDUCT = """How to conduct the call:
- Lead with the single most concrete fact you have. Name fields and identifiers out loud.
- Ask one question at a time, then stop and listen.
- If they are vague, ask one concrete follow-up. Two follow-ups is plenty.
- Never invent details. Every technical fact you state must come from the evidence above.
- When they dictate an identifier, code or field name, read it back to confirm you heard it right.
- You are gathering information only. You have no authority to confirm anything, to approve a
  change, or to promise any action. If asked to approve something, say a human engineer decides.
- The representative speaks in discrete turns. When they finish, reply once and then wait.
  Never ask whether they can hear you, and never fill a silence.
- Keep the whole call under about two minutes.

When every question below has been answered or explicitly refused, call the report_finding
function exactly once, then thank them and say goodbye.

Record what they tell you precisely:
- field_mappings: one entry per old-to-new field change, including any unit conversion.
- required_values: any value the request must now carry, exactly as dictated.
Do not tidy, summarise or correct what they say. Record it as given."""


def fixture_instruction(brief):
    return """You are the escalation agent for an automated shipping integration. You have just called \
the support line for %(provider)s because your integration broke and you cannot resolve it from \
their documentation. A human support representative has answered.

You are the CALLER, not the support desk. Never describe yourself as support. Speak first, as \
soon as the line opens, and keep the opening to about fifteen seconds.

Open in roughly this shape, in your own words:
"Hi, this is the automated integration agent calling about order %(order)s. Our %(tool)s call \
started failing last night: we expect a field called %(expected)s and we're getting %(observed)s \
instead. Can you tell me what changed?"

Say the order number out loud. Say both field names out loud. Then stop and listen.

The evidence from the failed run:
%(facts)s

Questions you must get answered:
- What changed in the response, and when did it change?
- Is there a way to keep the old behaviour while we update?
- The API returned a status value we do not recognise. Was the status vocabulary changed too?

%(conduct)s""" % {
        "provider": brief["provider"], "order": brief["order_id"],
        "tool": brief["failure"]["tool"],
        "expected": brief["failure"]["expected_fields"][2],
        "observed": brief["failure"]["observed_fields"][2],
        "facts": opening_facts(brief), "conduct": CONDUCT,
    }


def incident_instruction(brief):
    """Brief built from a live repair-lab incident handoff."""
    facts = ["Carrier: %s" % brief["provider"], "Incident: %s" % brief["incident_id"]]
    if brief.get("reason"):
        facts.append("Why we are calling: %s" % brief["reason"])
    if brief["failure"].get("detail"):
        facts.append("Failure summary: %s" % brief["failure"]["detail"])
    for attempt in brief.get("attempts", [])[:4]:
        facts.append("Repair attempt %s already tried: %s" % (
            attempt.get("number", "?"), (attempt.get("hypothesis") or "")[:300]))
    questions = brief.get("questions") or [
        "Please provide the current API request/response contract and required agreement details."]
    return """You are the escalation agent for an automated carrier integration. Our system tried to \
repair the %(provider)s quote adapter by itself and could not: the information needed is not in \
their published documentation. You have called their integration support line and a human \
representative has answered.

You are the CALLER, not the support desk. Never describe yourself as support. Speak first, as \
soon as the line opens, and keep the opening to about fifteen seconds.

Open in roughly this shape, in your own words:
"Hi, this is the automated integration agent calling about our %(provider)s quote integration. \
Our adapter started failing and we could not work it out from the public documentation. Can you \
give me the current request and response contract, and any agreement details we need to send?"

What we already know:
%(facts)s

Questions you must get answered before you finish:
%(questions)s

You are rebuilding an adapter, so you need the WHOLE contract. Work through this checklist and
do not call report_finding until each item is answered or explicitly refused. Tick them off out
loud to yourself; if one reply covers two items, move to the next:
  1. Any agreement, account or credential value the request must now carry.
  2. The REQUEST contract: every field name, where it sits in the body, and any unit conversion.
  3. The RESPONSE contract: every field you must read to get price, currency, delivery time
     and service name.
  4. Whether the old field names still work alongside the new ones, or must be dropped.

After each answer, ask for the next missing item: "Thanks, and what about the response side?"
If you have items 1 and 2 but not 3, you are not finished. Getting all four matters more than
being quick.

%(conduct)s""" % {
        "provider": brief["provider"],
        "facts": "\n".join("- " + f for f in facts),
        "questions": "\n".join("- " + q for q in questions),
        "conduct": CONDUCT,
    }


def from_incident(incident):
    """Map a repair-lab incident record onto our brief shape. Defensive: their
    record is another service's output, so every field is treated as optional."""
    handoff = incident.get("handoff") or {}
    contact = incident.get("contact") or {}
    return {
        "source": "repair-lab",
        "incident_id": incident.get("id", ""),
        "run_id": incident.get("run_id", ""),
        "carrier_id": incident.get("carrier_id", ""),
        "provider": incident.get("company") or incident.get("carrier_id") or "the carrier",
        "support_line": contact.get("phone", "unknown"),
        "contact_name": contact.get("name", ""),
        "order_id": incident.get("run_id", ""),
        "reason": incident.get("reason", ""),
        "failure": {"detail": handoff.get("failure_summary") or ""},
        "attempts": handoff.get("attempts") or [],
        "questions": handoff.get("questions") or [],
        "callback_path": handoff.get("callback_path") or ("/api/incidents/%s/context" % incident.get("id", "")),
        "events": [],
    }


def instruction_for(brief):
    return incident_instruction(brief) if brief.get("source") == "repair-lab" else fixture_instruction(brief)


FIXTURE["source"] = "fixture"
SYSTEM_INSTRUCTION = fixture_instruction(FIXTURE)


if __name__ == "__main__":
    print(SYSTEM_INSTRUCTION)
