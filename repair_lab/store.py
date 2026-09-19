import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path


def now(): return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, created_at TEXT, data TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS incidents(id TEXT PRIMARY KEY, data TEXT)")
        self.db.commit()

    def save_run(self, run):
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO runs VALUES(?,?,?)", (run["id"], run["created_at"], json.dumps(run))); self.db.commit()

    def get_run(self, run_id):
        with self.lock:
            row = self.db.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def latest(self):
        with self.lock:
            row = self.db.execute("SELECT data FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()
            return json.loads(row[0]) if row else None

    def runs(self, *, limit=30):
        query = "SELECT data FROM runs ORDER BY created_at DESC"
        parameters = () if limit is None else (limit,)
        if limit is not None: query += " LIMIT ?"
        with self.lock: return [json.loads(r[0]) for r in self.db.execute(query, parameters)]

    def update_carrier(self, run_id, carrier_id, **changes):
        with self.lock:
            run = self.get_run(run_id); run["carriers"][carrier_id].update(changes); self.save_run(run)

    def event(self, run_id, carrier_id, kind, data):
        with self.lock:
            run = self.get_run(run_id)
            run["events"].append({"sequence": len(run["events"])+1, "at": now(), "carrier_id": carrier_id, "kind": kind, "data": data})
            self.save_run(run)

    def save_incident(self, incident):
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO incidents VALUES(?,?)", (incident["id"], json.dumps(incident))); self.db.commit()

    def incident(self, incident_id):
        with self.lock:
            row = self.db.execute("SELECT data FROM incidents WHERE id=?", (incident_id,)).fetchone()
            return json.loads(row[0]) if row else None
