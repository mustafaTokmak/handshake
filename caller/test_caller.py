"""Tests for the caller's side of the repair-lab handoff.

Stdlib unittest so this runs on the same interpreter as server.py, which is
deliberately dependency-light. The lab itself is never started: its HTTP
surface is faked, because what is under test is how we read its records and
how we behave when it rejects or stalls.
"""
import importlib.util
import json
import unittest
from urllib.error import HTTPError, URLError

import lab
from models import MAX_CONTEXT, CallFinding, to_context
from server import pick_incident

LAB_MODELS = importlib.util.spec_from_file_location("lab_models", "../repair_lab/models.py")
ContactReply = None
if LAB_MODELS:
    _module = importlib.util.module_from_spec(LAB_MODELS)
    LAB_MODELS.loader.exec_module(_module)
    ContactReply = _module.ContactReply


def incident(incident_id, status="waiting", carrier="harbor", company="Harbor Freightline"):
    return {"id": incident_id, "run_id": "run-" + incident_id, "carrier_id": carrier,
            "company": company, "status": status,
            "contact": {"name": "Sam Arden", "phone": "+44 7700 900204"},
            "reason": "Five distinct candidates failed",
            "created_at": "2026-09-19T17:00:00+00:00",
            "handoff": {"failure_summary": "422 unavailable agreement", "attempts": [],
                        "callback_path": "/api/incidents/%s/context" % incident_id,
                        "questions": ["What is the current contract?"]}}


def run(run_id, states):
    return {"id": run_id, "created_at": "2026-09-19T17:00:00+00:00", "carriers": states}


class FakeLab:
    """Stands in for lab.get. Records what was asked for."""

    def __init__(self, runs, incidents):
        self.runs, self.incidents, self.asked = runs, incidents, []

    def get(self, path):
        self.asked.append(path)
        if path == "/api/runs?include_children=1":
            return self.runs
        if path.startswith("/api/incidents/"):
            found = self.incidents.get(path.rsplit("/", 1)[-1])
            if found is None:
                raise HTTPError(path, 404, "Not found", {}, None)
            return found
        raise HTTPError(path, 404, "Not found", {}, None)


class WaitingIncidents(unittest.TestCase):
    def setUp(self):
        self._get = lab.get

    def tearDown(self):
        lab.get = self._get

    def install(self, runs, incidents):
        fake = FakeLab(runs, incidents)
        lab.get = fake.get
        return fake

    def test_finds_incident_on_a_run_that_is_no_longer_the_latest(self):
        # Arrange: a fresh shared session has displaced the run that escalated.
        runs = [run("newest", {"harbor": {"status": "ready", "incident_id": None}}),
                run("older", {"harbor": {"status": "waiting_contact", "incident_id": "INC-1"}})]
        self.install(runs, {"INC-1": incident("INC-1")})

        found = lab.waiting_incidents()

        self.assertEqual([i["id"] for i in found], ["INC-1"])

    def test_returns_every_waiting_carrier_not_just_the_first(self):
        runs = [run("r1", {"harbor": {"status": "waiting_contact", "incident_id": "INC-1"},
                           "copper": {"status": "waiting_contact", "incident_id": "INC-2"}})]
        self.install(runs, {"INC-1": incident("INC-1"),
                            "INC-2": incident("INC-2", carrier="copper", company="Copper Courier")})

        found = lab.waiting_incidents()

        self.assertEqual(sorted(i["id"] for i in found), ["INC-1", "INC-2"])

    def test_skips_incidents_that_are_no_longer_waiting(self):
        runs = [run("r1", {"harbor": {"status": "waiting_contact", "incident_id": "INC-1"}})]
        self.install(runs, {"INC-1": incident("INC-1", status="resuming")})

        self.assertEqual(lab.waiting_incidents(), [])

    def test_the_same_incident_on_two_runs_is_fetched_once(self):
        runs = [run("r1", {"harbor": {"status": "waiting_contact", "incident_id": "INC-1"}}),
                run("r2", {"harbor": {"status": "waiting_contact", "incident_id": "INC-1"}})]
        fake = self.install(runs, {"INC-1": incident("INC-1")})

        found = lab.waiting_incidents()

        self.assertEqual(len(found), 1)
        self.assertEqual(fake.asked.count("/api/incidents/INC-1"), 1)

    def test_unreachable_lab_yields_an_empty_queue(self):
        def unreachable(path):
            raise URLError("connection refused")
        lab.get = unreachable

        self.assertEqual(lab.waiting_incidents(), [])

    def test_a_malformed_run_record_does_not_break_the_scan(self):
        runs = ["not a run", {"carriers": "unexpected"},
                run("r1", {"harbor": {"status": "waiting_contact", "incident_id": "INC-1"}})]
        self.install(runs, {"INC-1": incident("INC-1")})

        self.assertEqual([i["id"] for i in lab.waiting_incidents()], ["INC-1"])


class PickIncident(unittest.TestCase):
    def setUp(self):
        self._waiting = lab.waiting_incidents

    def tearDown(self):
        lab.waiting_incidents = self._waiting

    def install(self, queue):
        lab.waiting_incidents = lambda: queue

    def test_returns_the_operators_choice_when_it_is_still_waiting(self):
        self.install([incident("INC-1"), incident("INC-2")])

        chosen, queue = pick_incident("INC-2")

        self.assertEqual(chosen["id"], "INC-2")
        self.assertEqual(len(queue), 2)

    def test_falls_back_to_the_newest_when_the_choice_is_gone(self):
        self.install([incident("INC-1")])

        chosen, _ = pick_incident("INC-STALE")

        self.assertEqual(chosen["id"], "INC-1")

    def test_returns_nothing_when_the_lab_is_not_blocked(self):
        self.install([])

        chosen, queue = pick_incident("")

        self.assertIsNone(chosen)
        self.assertEqual(queue, [])


class Delivery(unittest.TestCase):
    def setUp(self):
        self._post = lab.post

    def tearDown(self):
        lab.post = self._post

    def http_error(self, code, body):
        return HTTPError("http://lab/api", code, "error", {}, _Body(json.dumps({"error": body}).encode()))

    def test_retries_while_the_previous_repair_worker_is_finishing(self):
        calls = []

        def flaky(path, payload):
            calls.append(path)
            if len(calls) < 3:
                raise self.http_error(400, "Previous repair worker is finishing; retry this message shortly")
            return 202, {"accepted": True}

        lab.post = flaky

        result = lab.deliver("INC-1", {"context": "x"}, sleep=lambda _s: None)

        self.assertTrue(result["ok"])
        self.assertEqual(result["attempts"], 3)

    def test_does_not_retry_a_schema_rejection(self):
        calls = []

        def rejecting(path, payload):
            calls.append(path)
            raise self.http_error(400, "context: String should have at most 12000 characters")

        lab.post = rejecting

        result = lab.deliver("INC-1", {"context": "x"}, sleep=lambda _s: None)

        self.assertFalse(result["ok"])
        self.assertEqual(len(calls), 1)

    def test_gives_up_after_the_attempt_budget(self):
        def always_busy(path, payload):
            raise URLError("connection refused")

        lab.post = always_busy

        result = lab.deliver("INC-1", {"context": "x"}, sleep=lambda _s: None)

        self.assertFalse(result["ok"])
        self.assertEqual(result["attempts"], lab.DELIVERY_ATTEMPTS)
        self.assertEqual(result["error"], "URLError")


class _Body:
    """Minimal stand-in for HTTPError's file object."""

    def __init__(self, raw):
        self.raw = raw

    def read(self):
        return self.raw

    def close(self):
        pass


class ContextRendering(unittest.TestCase):
    def realistic(self):
        return CallFinding(status="informative", summary="Harbor moved to v3.",
                           change={"described_behaviour": "v3 nests metric units and needs an agreement.",
                                   "field_mappings": ["weight_kg -> quote_request.mass_grams (x1000)"],
                                   "required_values": ["service_agreement=DEMO-AGREEMENT-0000"]})

    def test_a_verbose_finding_still_fits_what_the_lab_accepts(self):
        # Arrange: schema-valid but enormous — list entries carry no length cap.
        huge = CallFinding(status="informative", summary="s" * 600,
                           change={"described_behaviour": "d" * 600,
                                   "field_mappings": ["X" * 5000] * 12,
                                   "required_values": ["Y" * 5000] * 6,
                                   "changed_fields": ["Z" * 5000] * 12,
                                   "affected_parameters": ["W" * 5000] * 12})

        context = to_context(huge, "Harbor Freightline")

        self.assertLessEqual(len(context), MAX_CONTEXT)

    def test_the_untrusted_header_and_scope_survive_truncation(self):
        huge = CallFinding(status="informative", summary="s",
                           change={"described_behaviour": "d", "field_mappings": ["X" * 9000] * 12})

        context = to_context(huge, "Harbor Freightline")

        self.assertIn("UNTRUSTED", context)
        self.assertIn("Harbor Freightline adapter only", context)

    def test_a_refusal_never_implies_a_change(self):
        context = to_context(CallFinding(status="refused", summary="Would not say."), "Harbor Freightline")

        self.assertIn("Do not infer any change", context)

    @unittest.skipIf(ContactReply is None, "repair_lab models not importable")
    def test_rendered_context_is_accepted_by_the_labs_own_schema(self):
        for finding in (self.realistic(),
                        CallFinding(status="refused", summary="Would not say."),
                        CallFinding(status="informative", summary="s",
                                    change={"described_behaviour": "d",
                                            "field_mappings": ["X" * 5000] * 12})):
            with self.subTest(status=finding.status):
                ContactReply(message_id="escalation-call-1", source="escalation-voice-caller",
                             context=to_context(finding, "Harbor Freightline"))


if __name__ == "__main__":
    unittest.main()
