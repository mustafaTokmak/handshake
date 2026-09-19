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
            row = self.db.execute("SELECT data FROM runs WHERE json_extract(data, '$.parent_id') IS NULL ORDER BY created_at DESC LIMIT 1").fetchone()
            return json.loads(row[0]) if row else None

    def runs(self, *, limit=30, include_children=False):
        query = "SELECT data FROM runs"
        if not include_children: query += " WHERE json_extract(data, '$.parent_id') IS NULL"
        query += " ORDER BY created_at DESC"
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


class ModalStore(Store):
    """Shared demo state, persisted across container restarts by Modal Dict.

    The deployment runs exactly one writer container. Inactive demo records expire
    after Modal Dict's retention window; this is not an archival database.
    """
    def __init__(self, name, records=None):
        import modal
        self.lock = threading.RLock()
        self.records = records if records is not None else modal.Dict.from_name(name, create_if_missing=True)

    def save_run(self, run):
        with self.lock:
            self.records.put('run:'+run['id'], json.dumps(run))
            latest = self.records.get('meta:latest')
            if not run.get('parent_id') and (not latest or run['created_at'] > latest['created_at']):
                self.records.put('meta:latest', {k: run[k] for k in ('id', 'created_at')})

    def get_run(self, run_id):
        with self.lock:
            raw = self.records.get('run:'+run_id)
            return json.loads(raw) if raw else None

    def runs(self, *, limit=30, include_children=False):
        with self.lock:
            runs = [json.loads(value) for key, value in self.records.items() if key.startswith('run:')]
            return sorted((r for r in runs if include_children or not r.get('parent_id')), key=lambda r: r['created_at'], reverse=True)[:limit]

    def latest(self):
        with self.lock:
            latest = self.records.get('meta:latest')
            if latest: return self.get_run(latest['id'])
            # Bootstrap older deployments once, before the indexed live-poll path.
            runs = self.runs(limit=1)
            if runs: self.records.put('meta:latest', {k: runs[0][k] for k in ('id', 'created_at')})
            return runs[0] if runs else None

    def save_incident(self, incident):
        with self.lock: self.records.put('incident:'+incident['id'], json.dumps(incident))

    def incident(self, incident_id):
        with self.lock:
            raw = self.records.get('incident:'+incident_id)
            return json.loads(raw) if raw else None
