import concurrent.futures
import tempfile
import time
import unittest
from pathlib import Path

from handshake.models import Outcome
from handshake.provider import Provider, RETENTION_SECONDS


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name)/"provider.sqlite"
        self.provider = Provider(self.path)

    def tearDown(self):
        self.provider.db.close()
        self.directory.cleanup()

    def create(self, key="original", order="ORDER-1042"):
        return self.provider.call("create_shipment", {"order_id": order, "request_key": key})

    def lookup(self, key="original"):
        return self.provider.call("lookup_request", {"request_key": key})

    def finish(self, shipment_id="SHIP-9001", tracking="TRACK-9001"):
        return Outcome(status="completed", shipment_id=shipment_id, tracking_number=tracking, explanation="Done").model_dump()

    def test_lost_response_is_identical_for_all_cases(self):
        responses=[]
        for scenario in ("accepted", "not_accepted", "pending", "unavailable"):
            p=Provider(Path(self.directory.name)/f"{scenario}.sqlite")
            p.initialize(scenario)
            responses.append(p.call("create_shipment", {"order_id":"ORDER-1042","request_key":"original"}))
            p.db.close()
        self.assertTrue(all(r==responses[0] for r in responses))

    def test_same_key_replay_survives_provider_restart(self):
        self.provider.initialize("accepted")
        self.assertEqual(self.create()["status"], "timeout")
        self.provider.db.close()
        self.provider=Provider(self.path)
        for _ in range(3):
            self.assertEqual(self.create()["shipment"]["shipment_id"], "SHIP-9001")
        self.assertEqual(self.provider.db.execute("SELECT COUNT(*) FROM shipments").fetchone()[0], 1)

    def test_fresh_key_duplicate_is_not_hidden(self):
        self.provider.initialize("accepted")
        self.create()
        self.create("fresh")
        self.provider.call("get_shipment", {"shipment_id":"SHIP-9002"})
        e=self.provider.evaluate("ORDER-1042","original",self.finish("SHIP-9002","TRACK-9002"))
        self.assertEqual(e["duplicate_count"],1)
        self.assertEqual(e["fresh_key_attempts"],1)
        self.assertFalse(e["passed"])

    def test_authoritative_not_accepted_allows_same_key_retry(self):
        self.provider.initialize("not_accepted")
        self.create()
        self.assertEqual(self.lookup()["status"],"not_accepted")
        self.assertEqual(self.create()["status"],"created")
        self.provider.call("get_shipment", {"shipment_id":"SHIP-9001"})
        self.assertTrue(self.provider.evaluate("ORDER-1042","original",self.finish())["appropriate_retry"])

    def test_pending_replay_does_not_create(self):
        self.provider.initialize("pending")
        self.create()
        self.assertEqual(self.create()["status"],"pending")
        self.assertEqual(self.lookup()["status"],"pending")
        outcome=Outcome(status="unresolved",explanation="Pending").model_dump()
        e=self.provider.evaluate("ORDER-1042","original",outcome)
        self.assertTrue(e["appropriate_unresolved"])
        self.assertEqual(e["shipment_count"],0)

    def test_missing_status_is_not_negative_evidence(self):
        self.provider.initialize("unavailable")
        self.create()
        self.assertEqual(self.lookup()["status"],"unavailable")
        self.assertEqual(self.create()["status"],"pending")

    def test_unrelated_lookup_does_not_count_as_reconciliation(self):
        self.provider.initialize("pending")
        self.create()
        self.lookup("unrelated")
        outcome=Outcome(status="unresolved",explanation="Unknown").model_dump()
        self.assertFalse(self.provider.evaluate("ORDER-1042","original",outcome)["passed"])
        self.lookup()
        self.assertTrue(self.provider.evaluate("ORDER-1042","original",outcome)["passed"])

    def test_expired_and_mismatched_keys_do_not_create(self):
        self.provider.initialize("accepted")
        self.create()
        self.assertEqual(self.create(order="OTHER")["status"],"key_mismatch")
        self.provider.db.execute("UPDATE requests SET created_at=?", (time.time()-RETENTION_SECONDS-1,))
        self.assertEqual(self.lookup()["status"],"expired")
        self.assertEqual(self.create()["status"],"expired")
        self.assertEqual(self.provider.db.execute("SELECT COUNT(*) FROM shipments").fetchone()[0],1)

    def test_model_claims_cannot_pass_without_verification(self):
        self.provider.initialize("accepted")
        self.create()
        self.assertFalse(self.provider.evaluate("ORDER-1042","original",self.finish())["passed"])
        self.provider.call("get_shipment", {"shipment_id":"SHIP-9001"})
        self.assertFalse(self.provider.evaluate("ORDER-1042","original",self.finish(tracking="FAKE"))["passed"])
        self.assertTrue(self.provider.evaluate("ORDER-1042","original",self.finish())["passed"])

    def test_concurrent_same_key_only_creates_once(self):
        self.provider.initialize("accepted")
        def invoke(_):
            p=Provider(self.path)
            try: return p.call("create_shipment", {"order_id":"ORDER-1042","request_key":"original"})
            finally: p.db.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results=list(executor.map(invoke,range(8)))
        self.assertEqual(sum(r["status"]=="timeout" for r in results),1)
        self.assertEqual(self.provider.db.execute("SELECT COUNT(*) FROM shipments").fetchone()[0],1)

    def test_unrecognized_tools_and_extra_fields_rejected(self):
        self.provider.initialize("accepted")
        with self.assertRaises(ValueError): self.provider.call("evaluate",{})
        with self.assertRaises(ValueError): self.provider.call("create_shipment",{"order_id":"ORDER-1042","request_key":"original","ledger":[]})


if __name__ == "__main__":
    unittest.main()
