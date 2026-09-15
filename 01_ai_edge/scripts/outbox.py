import json
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import threading
import time
import requests


class Outbox:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS events (event_id TEXT PRIMARY KEY, payload TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0, next_attempt REAL NOT NULL DEFAULT 0, error TEXT, sent_at REAL)")

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def enqueue(self, payload):
        serialized = json.dumps(payload, sort_keys=True)
        with self.connect() as db:
            existing = db.execute("SELECT payload FROM events WHERE event_id=?", (payload["event_id"],)).fetchone()
            if existing and existing["payload"] != serialized:
                raise ValueError("Cannot change an event that is already queued")
            db.execute("INSERT OR IGNORE INTO events(event_id,payload) VALUES (?,?)", (payload["event_id"], serialized))

    def counts(self):
        with self.connect() as db:
            counts = dict(db.execute("SELECT state, COUNT(*) FROM events GROUP BY state").fetchall())
        return {state: counts.get(state, 0) for state in ("pending", "sent", "invalid")}

    def delivery_states(self, event_ids):
        """Read actual delivery results for the current video's events only."""
        states = {}
        identifiers = list(event_ids)
        with self.connect() as db:
            for start in range(0, len(identifiers), 500):
                batch = identifiers[start:start + 500]
                placeholders = ",".join("?" for _ in batch)
                states.update(db.execute(f"SELECT event_id, state FROM events WHERE event_id IN ({placeholders})", batch).fetchall())
        return states

    def flush_once(self, client, limit=20, retry_now=False):
        with self.connect() as db:
            records = db.execute("SELECT * FROM events WHERE state='pending' AND next_attempt<=? ORDER BY rowid LIMIT ?", (float("inf") if retry_now else time.time(), limit)).fetchall()
        for record in records:
            payload = json.loads(record["payload"])
            state, error = "pending", None
            try:
                response = client.send_observation(payload)
                if 200 <= response.status_code < 300:
                    receipt = response.json()
                    if isinstance(receipt, dict) and receipt.get("event_id") == payload["event_id"] and isinstance(receipt.get("issue_id"), str) and receipt["issue_id"]:
                        state = "sent"
                    else:
                        error = "Backend response did not acknowledge this event"
                elif response.status_code in (408, 425, 429) or response.status_code >= 500:
                    error = f"Temporary HTTP {response.status_code}"
                else:
                    state, error = "invalid", f"HTTP {response.status_code}: {response.text[:400]}"
            except (requests.RequestException, ValueError) as exc:
                error = str(exc)[:400]
            attempts = record["attempts"] + 1
            with self.connect() as db:
                db.execute("UPDATE events SET state=?,attempts=?,next_attempt=?,error=?,sent_at=? WHERE event_id=?", (state, attempts, time.time() + min(60, 2 ** min(attempts, 6)), error, time.time() if state == "sent" else None, record["event_id"]))


class DeliveryWorker:
    def __init__(self, outbox, client, bus_id, heartbeat_seconds=10):
        self.outbox, self.client, self.bus_id = outbox, client, bus_id
        self.heartbeat_seconds = heartbeat_seconds
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.latest_telemetry = None
        self.last_heartbeat = -float("inf")
        self.last_error = None
        self.thread = threading.Thread(target=self.run, name="codyssey-delivery", daemon=True)

    def start(self):
        self.thread.start()

    def heartbeat(self, telemetry):
        with self.lock:
            self.latest_telemetry = telemetry

    def run(self):
        while not self.stop_event.is_set():
            self.last_error = None
            with self.lock:
                telemetry = dict(self.latest_telemetry) if self.latest_telemetry else None
            try:
                if telemetry and time.monotonic() - self.last_heartbeat >= self.heartbeat_seconds:
                    self.last_heartbeat = time.monotonic()
                    telemetry["timestamp"] = datetime.now(timezone.utc).isoformat()
                    response = self.client.heartbeat(self.bus_id, telemetry)
                    response.raise_for_status()
            except requests.RequestException as exc:
                self.last_error = str(exc)
            try:
                self.outbox.flush_once(self.client, limit=5)
            except (requests.RequestException, sqlite3.Error) as exc:
                self.last_error = str(exc)
            self.stop_event.wait(.3)

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=3)
