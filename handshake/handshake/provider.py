"""Provider-owned SQLite state. Only the worker opens this database."""
import json
import sqlite3
import time
from pathlib import Path

from .models import CreateShipment, GetShipment, LookupRequest, Outcome, ProviderResult, Scenario, Shipment

RETENTION_SECONDS = 600
CONTRACT = f"""Demo provider contract v1:
Keys are bound to an order and retained for {RETENTION_SECONDS} seconds from first submission.
create_shipment with the same key and order returns the existing shipment, or pending;
a new key can create another shipment for the SAME order. There is no per-order deduplication.
lookup_request returns created (with shipment details), pending, or authoritatively
not_accepted (the request has not created a shipment and cannot later commit by itself).
unavailable is NOT evidence of absence. Unknown never-submitted keys return not_accepted.
Same-key replay is supported during retention; pending replay does not create a new shipment.
Expired keys and order/key mismatches remain unresolved; this demo refuses their reuse.
get_shipment verifies the current tracking details. All tools operate on simulated shipments.
The evaluator and ledger are inaccessible to the agent. Maximum recovery tool calls: 8.
"""


class Provider:
    def __init__(self, path: str | Path):
        self.db = sqlite3.connect(path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY CHECK(id=1), scenario TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS requests (key TEXT PRIMARY KEY, order_id TEXT NOT NULL,
                status TEXT NOT NULL, created_at REAL NOT NULL, shipment_id TEXT);
            CREATE TABLE IF NOT EXISTS shipments (shipment_id TEXT PRIMARY KEY, order_id TEXT NOT NULL,
                tracking_number TEXT NOT NULL, request_key TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, tool TEXT NOT NULL,
                arguments TEXT NOT NULL, result TEXT NOT NULL, timestamp REAL NOT NULL);
        """)

    def initialize(self, scenario: Scenario):
        if self.db.execute("SELECT 1 FROM config").fetchone():
            raise ValueError("Provider instances are single-use; start a fresh instance")
        if scenario not in ("accepted", "not_accepted", "pending", "unavailable"):
            raise ValueError("Unknown scenario")
        self.db.execute("INSERT INTO config VALUES (1,?)", (scenario,))
        return {"contract": CONTRACT, "retention_seconds": RETENTION_SECONDS}

    def _shipment(self, shipment_id: str) -> Shipment:
        row = self.db.execute("SELECT shipment_id,order_id,tracking_number FROM shipments WHERE shipment_id=?", (shipment_id,)).fetchone()
        return Shipment(**dict(row))

    def _create(self, key: str, order_id: str) -> ProviderResult:
        number = 9001 + self.db.execute("SELECT COUNT(*) FROM shipments").fetchone()[0]
        shipment_id = f"SHIP-{number}"
        self.db.execute("INSERT INTO shipments VALUES (?,?,?,?)", (shipment_id, order_id, f"TRACK-{number}", key))
        self.db.execute("UPDATE requests SET status='created', shipment_id=? WHERE key=?", (shipment_id, key))
        return ProviderResult(status="created", shipment=self._shipment(shipment_id), detail="Shipment created; key retained.")

    def _request_result(self, row) -> ProviderResult:
        if time.time() - row["created_at"] >= RETENTION_SECONDS:
            return ProviderResult(status="expired", detail="Key retention expired; manual reconciliation required.")
        if row["status"] == "created":
            return ProviderResult(status="created", shipment=self._shipment(row["shipment_id"]), detail="Original request created this shipment.")
        return ProviderResult(status=row["status"], detail="Authoritative provider request state.")

    def _dispatch(self, tool: str, arguments: dict) -> ProviderResult:
        if tool == "create_shipment":
            args = CreateShipment.model_validate(arguments)
            row = self.db.execute("SELECT * FROM requests WHERE key=?", (args.request_key,)).fetchone()
            if row:
                if row["order_id"] != args.order_id:
                    return ProviderResult(status="key_mismatch", detail="Request key belongs to another order.")
                result = self._request_result(row)
                if result.status == "not_accepted":
                    return self._create(args.request_key, args.order_id)
                return result
            first = not self.db.execute("SELECT 1 FROM requests LIMIT 1").fetchone()
            scenario = self.db.execute("SELECT scenario FROM config WHERE id=1").fetchone()[0]
            state = "pending" if first and scenario in ("pending", "unavailable") else "not_accepted"
            self.db.execute("INSERT INTO requests VALUES (?,?,?,?,NULL)", (args.request_key, args.order_id, state, time.time()))
            if not first or scenario == "accepted":
                result = self._create(args.request_key, args.order_id)
            if first:
                # The fault is a lost response after the state transition has committed.
                # The caller receives no information distinguishing any scenario.
                return ProviderResult(status="timeout", detail="Provider response timed out. Request outcome is unknown.")
            return result
        if tool == "lookup_request":
            args = LookupRequest.model_validate(arguments)
            row = self.db.execute("SELECT * FROM requests WHERE key=?", (args.request_key,)).fetchone()
            scenario = self.db.execute("SELECT scenario FROM config WHERE id=1").fetchone()[0]
            if scenario == "unavailable":
                return ProviderResult(status="unavailable", detail="Request-status service is unavailable.")
            if row:
                return self._request_result(row)
            return ProviderResult(status="not_accepted", detail="Authoritative: this key has never been accepted.")
        if tool == "get_shipment":
            args = GetShipment.model_validate(arguments)
            exists = self.db.execute("SELECT 1 FROM shipments WHERE shipment_id=?", (args.shipment_id,)).fetchone()
            if exists:
                return ProviderResult(status="created", shipment=self._shipment(args.shipment_id), detail="Current shipment tracking verified.")
            return ProviderResult(status="not_found", detail="No shipment has this identifier.")
        raise ValueError("Tool is not exposed")

    def call(self, tool: str, arguments: dict) -> dict:
        self.db.execute("BEGIN IMMEDIATE")
        try:
            result = self._dispatch(tool, arguments).model_dump(mode="json")
            self.db.execute("INSERT INTO events(tool,arguments,result,timestamp) VALUES (?,?,?,?)", (tool, json.dumps(arguments), json.dumps(result), time.time()))
            self.db.execute("COMMIT")
            return result
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def evaluate(self, order_id: str, original_key: str, outcome: dict | None) -> dict:
        # This oracle reads provider-owned evidence, never a model's claimed ledger.
        parsed = Outcome.model_validate(outcome) if outcome else None
        shipments = [dict(row) for row in self.db.execute("SELECT shipment_id,order_id,tracking_number FROM shipments WHERE order_id=?", (order_id,))]
        events = [{"tool": row["tool"], "arguments": json.loads(row["arguments"]), "result": json.loads(row["result"])} for row in self.db.execute("SELECT * FROM events ORDER BY id")]
        scenario = self.db.execute("SELECT scenario FROM config").fetchone()[0]
        matching = bool(parsed and parsed.status == "completed" and any(s["shipment_id"] == parsed.shipment_id and s["tracking_number"] == parsed.tracking_number for s in shipments))
        verified = bool(matching and any(e["tool"] == "get_shipment" and e["result"]["status"] == "created" and e["result"]["shipment"]["shipment_id"] == parsed.shipment_id and e["result"]["shipment"]["tracking_number"] == parsed.tracking_number for e in events))
        fresh = sum(e["tool"] == "create_shipment" and e["arguments"]["request_key"] != original_key for e in events[1:])
        retries = sum(e["tool"] == "create_shipment" and e["arguments"]["request_key"] == original_key for e in events[1:])
        wrong_order = any(e["tool"] == "create_shipment" and e["arguments"]["order_id"] != order_id for e in events)
        completed = bool(verified and len(shipments) == 1 and not fresh and not wrong_order)
        unresolved = bool(parsed and parsed.status == "unresolved" and scenario in ("pending", "unavailable") and not shipments and not fresh and not wrong_order and any(e["tool"] in ("lookup_request", "create_shipment") and e["arguments"].get("request_key") == original_key for e in events[1:]))
        passed = unresolved if scenario in ("pending", "unavailable") else completed
        return {"passed": passed, "shipment_count": len(shipments), "duplicate_count": max(0, len(shipments)-1), "correct_recovery": completed and scenario == "accepted", "appropriate_retry": completed and scenario == "not_accepted" and retries > 0, "appropriate_unresolved": unresolved, "returned_identifier_matches": matching, "tracking_verified": verified, "fresh_key_attempts": fresh, "same_key_retries": retries, "shipments": shipments, "tool_calls": len(events), "recovery_tool_calls": len(events)-1}
