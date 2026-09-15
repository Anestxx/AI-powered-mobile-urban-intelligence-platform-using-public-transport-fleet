from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_backend_database"))
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app

FIXTURE = json.loads((ROOT / "contracts/fixtures/demo.json").read_text())


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.url = f"sqlite:///{Path(self.directory.name).as_posix()}/test.db"
        self.settings = Settings(database_url=self.url, operator_password="test-operator-password")
        self.app = create_app(self.settings)
        self.client = TestClient(self.app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.directory.cleanup()

    def observation(self, index=0, **changes):
        result = deepcopy(FIXTURE["observations"][index])
        result.update(event_id=str(uuid4()))
        result.update(changes)
        return result

    def post(self, payload):
        response = self.client.post("/api/alerts", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["issue_id"]

    def login(self):
        response = self.client.post("/api/auth/login", json={"password": "test-operator-password"})
        self.assertEqual(response.status_code, 200)

    def test_create_and_exact_retry(self):
        payload = self.observation()
        issue_id = self.post(payload)
        retry = self.client.post("/api/alerts", json=payload)
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json(), {"event_id": payload["event_id"], "issue_id": issue_id, "duplicate": True})
        issue = self.client.get(f"/api/alerts/{issue_id}").json()
        self.assertEqual(issue["report_count"], 1)
        self.assertEqual(issue["observations"][0]["confidence"], payload["confidence"])
        self.assertEqual(issue["severity"], "unknown")

    def test_reused_id_with_different_content_conflicts(self):
        payload = self.observation()
        issue_id = self.post(payload)
        self.assertEqual(self.client.post("/api/alerts", json=dict(payload, confidence=.5)).status_code, 409)
        self.assertEqual(self.client.get(f"/api/alerts/{issue_id}").json()["report_count"], 1)

    def test_nearby_and_distant_reports(self):
        first = self.post(self.observation(0))
        self.assertEqual(self.post(self.observation(1)), first)
        self.assertNotEqual(self.post(self.observation(2)), first)
        issue = self.client.get(f"/api/alerts/{first}").json()
        self.assertEqual((issue["report_count"], issue["distinct_bus_count"], issue["priority"]), (2, 2, "medium"))

    def test_same_bus_reports_do_not_raise_priority(self):
        first = self.post(self.observation())
        self.post(self.observation())
        issue = self.client.get(f"/api/alerts/{first}").json()
        self.assertEqual((issue["report_count"], issue["distinct_bus_count"], issue["priority"]), (2, 1, "low"))
        self.post(self.observation(bus_id="BUS_02"))
        self.post(self.observation(bus_id="BUS_03"))
        self.assertEqual(self.client.get(f"/api/alerts/{first}").json()["priority"], "high")

    def test_simulated_and_real_locations_do_not_merge(self):
        first = self.post(self.observation())
        self.assertNotEqual(self.post(self.observation(location_source="gps")), first)

    def test_status_requires_operator_and_preserves_observations(self):
        issue_id = self.post(self.observation())
        path = f"/api/alerts/{issue_id}/status"
        self.assertEqual(self.client.patch(path, json={"status": "resolved"}).status_code, 401)
        self.login()
        self.assertEqual(self.client.patch(path, json={"status": "invalid"}).status_code, 422)
        self.assertEqual(self.client.patch(path, json={"status": "resolved"}, headers={"Origin": "https://untrusted.example"}).status_code, 403)
        response = self.client.patch(path, json={"status": "resolved"})
        self.assertEqual(response.json()["status"], "resolved")
        self.assertEqual(len(self.client.get(f"/api/alerts/{issue_id}").json()["observations"]), 1)
        self.assertEqual(self.client.get("/api/statistics").json()["resolved_issues"], 1)
        self.assertNotEqual(self.post(self.observation()), issue_id)

    def test_login_logout_and_wrong_password(self):
        self.assertFalse(self.client.get("/api/auth/session").json()["authenticated"])
        self.assertEqual(self.client.post("/api/auth/login", json={"password": "wrong"}).status_code, 401)
        self.login()
        self.assertTrue(self.client.get("/api/auth/session").json()["authenticated"])
        self.client.post("/api/auth/logout")
        self.assertFalse(self.client.get("/api/auth/session").json()["authenticated"])

    def test_invalid_observation_contract(self):
        cases = [{"confidence": 1.1}, {"confidence": True}, {"latitude": 91}, {"longitude": -181}, {"latitude": None},
                 {"event_id": "not-a-uuid"}, {"event_type": "traffic"}, {"bus_id": ""}, {"timestamp": "2026-09-13T10:30:00"},
                 {"gps_timestamp": "2026-09-13T10:00:00Z"}, {"severity": "high"}, {"bbox": [1, 1, 1, 1]}, {"location_source": "unknown"}]
        for changes in cases:
            with self.subTest(changes=changes):
                self.assertEqual(self.client.post("/api/alerts", json=self.observation(**changes)).status_code, 422)
        self.assertEqual(self.client.get("/api/alerts").json()["total"], 0)

    def test_equivalent_timezone_retry_is_idempotent(self):
        payload = self.observation()
        self.post(payload)
        payload.update(timestamp="2026-09-13T16:00:00+05:30", gps_timestamp="2026-09-13T16:00:00+05:30")
        self.assertEqual(self.client.post("/api/alerts", json=payload).status_code, 200)

    def test_filters_pagination_empty_and_unknown(self):
        self.post(self.observation())
        self.post(self.observation(2))
        page = self.client.get("/api/alerts?page_size=1&page=2").json()
        self.assertEqual((page["total"], len(page["items"])), (2, 1))
        self.assertEqual(self.client.get("/api/alerts?priority=high").json()["items"], [])
        for query in ("page=0", "page_size=101", "priority=critical", "date_from=2026-09-14&date_to=2026-09-13"):
            self.assertEqual(self.client.get(f"/api/alerts?{query}").status_code, 422)
        self.assertEqual(self.client.get("/api/alerts/missing").status_code, 404)
        self.login()
        self.assertEqual(self.client.patch("/api/alerts/missing/status", json={"status": "resolved"}).status_code, 404)

    def test_india_day_boundary_and_analytics(self):
        self.post(self.observation(timestamp="2026-09-13T18:29:59Z", gps_timestamp="2026-09-13T18:29:59Z"))
        self.post(self.observation(2, timestamp="2026-09-13T18:30:00Z", gps_timestamp="2026-09-13T18:30:00Z"))
        with patch("app.services.utc_now", return_value=datetime(2026, 9, 13, 20, tzinfo=timezone.utc)):
            self.assertEqual(self.client.get("/api/statistics").json()["new_issues_today"], 1)
        analytics = self.client.get("/api/analytics?date_from=2026-09-14&date_to=2026-09-14").json()
        self.assertEqual(analytics["new_issues_by_day"], [{"date": "2026-09-14", "count": 1}])
        self.assertEqual(sum(item["count"] for item in analytics["observations_by_bus"]), 1)
        self.assertEqual(self.client.get("/api/alerts?date_from=2026-09-14&date_to=2026-09-14").json()["total"], 1)
        self.assertEqual(self.client.get("/api/analytics?date_from=2020-01-01&date_to=2026-09-14").status_code, 422)

    def test_heartbeat_without_detections_and_timeout(self):
        now = datetime(2026, 9, 13, 12, tzinfo=timezone.utc)
        telemetry = {"timestamp": now.isoformat(), "camera_status": "online", "ai_status": "online"}
        with patch("app.services.utc_now", return_value=now):
            response = self.client.post("/api/buses/BUS_01/heartbeat", json=telemetry)
            self.assertTrue(response.json()["online"])
            self.assertIsNone(response.json()["latitude"])
            self.assertEqual(self.client.get("/api/statistics").json()["active_buses"], 1)
            self.assertEqual(self.client.get("/api/statistics").json()["total_issues"], 0)
        with patch("app.services.utc_now", return_value=now + timedelta(seconds=31)):
            self.assertFalse(self.client.get("/api/buses").json()["items"][0]["online"])
            self.assertEqual(self.client.get("/api/statistics").json()["active_buses"], 0)
            self.assertEqual(self.client.post("/api/buses/BUS_01/heartbeat", json=telemetry).status_code, 422)

    def test_out_of_order_heartbeat_does_not_replace_telemetry(self):
        now = datetime.now(timezone.utc)
        telemetry = {"timestamp": now.isoformat(), "camera_status": "online", "ai_status": "online"}
        self.client.post("/api/buses/BUS_01/heartbeat", json=telemetry)
        older = dict(telemetry, timestamp=(now - timedelta(seconds=1)).isoformat(), ai_status="error")
        self.assertEqual(self.client.post("/api/buses/BUS_01/heartbeat", json=older).json()["ai_status"], "online")
        self.assertEqual(self.client.post("/api/buses/BUS_01/heartbeat", json=dict(telemetry, timestamp=(now + timedelta(minutes=1)).isoformat())).status_code, 422)

    def test_concurrent_retries_only_store_once(self):
        payload = self.observation()
        with ThreadPoolExecutor(max_workers=4) as executor:
            responses = list(executor.map(lambda _: self.client.post("/api/alerts", json=payload).status_code, range(4)))
        self.assertEqual(sorted(responses), [200, 200, 200, 201])
        self.assertEqual(self.client.get("/api/alerts").json()["items"][0]["report_count"], 1)

    def test_failed_transaction_rolls_back_issue_and_observation(self):
        with patch("app.services.review_priority", side_effect=RuntimeError("test failure")):
            with self.assertRaises(RuntimeError):
                self.client.post("/api/alerts", json=self.observation())
        self.assertEqual(self.client.get("/api/alerts").json()["total"], 0)

    def test_persistence_across_application_restart(self):
        issue_id = self.post(self.observation())
        self.login()
        self.client.patch(f"/api/alerts/{issue_id}/status", json={"status": "resolved"})
        with TestClient(create_app(self.settings)) as restarted:
            result = restarted.get(f"/api/alerts/{issue_id}").json()
            self.assertEqual(result["status"], "resolved")
            self.assertEqual(len(result["observations"]), 1)

    def test_health_alias(self):
        for path in ("/health", "/api/health"):
            self.assertEqual(self.client.get(path).json()["status"], "healthy")

    def test_legacy_migration_keeps_source_unchanged(self):
        source = Path(self.directory.name) / "legacy.db"
        with sqlite3.connect(source) as db:
            db.execute("CREATE TABLE alerts(id INTEGER PRIMARY KEY,event_type TEXT,bus_id TEXT,confidence REAL,latitude REAL,longitude REAL,timestamp TEXT,bbox TEXT)")
            db.execute("INSERT INTO alerts VALUES(1,'pothole','OLD_BUS',0.9,12.97,77.59,'2026-09-13T10:30:00','[1,2,3,4]')")
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        command = [sys.executable, str(ROOT / "tools/migrate_legacy.py"), "--source", str(source), "--database-url", self.url, "--apply", "--location-source", "simulated", "--legacy-timezone", "UTC", "--assume-gps-at-detection"]
        for _ in range(2):
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)
        self.assertEqual(self.client.get("/api/alerts").json()["items"][0]["report_count"], 1)


if __name__ == "__main__":
    unittest.main()
