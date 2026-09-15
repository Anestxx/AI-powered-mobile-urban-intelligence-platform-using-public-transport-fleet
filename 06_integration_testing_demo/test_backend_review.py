import base64
from copy import deepcopy
import csv
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "03_backend_database"), str(ROOT / "01_ai_edge/scripts")]
import requests
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from app.config import Settings
from app.main import create_app
from app.models import Issue, Observation, ObservationEvidence
from app.schemas import ObservationCreate
from app.services import iso
from outbox import DeliveryWorker, Outbox


def observation():
    return deepcopy(json.loads((ROOT / "contracts/fixtures/demo.json").read_text())["observations"][0])


def evidence(size=(80, 60), format="JPEG"):
    data = BytesIO()
    Image.new("RGB", size, (65, 70, 75)).save(data, format=format)
    return {"jpeg_base64": base64.b64encode(data.getvalue()).decode(), "source_name": "road_test.mp4", "frame_id": 560, "video_time": 18.66}


class BackendReviewTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(Settings(database_url="sqlite://", operator_password="review-test")))
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def create(self, **changes):
        payload = dict(observation(), **changes)
        response = self.client.post("/api/alerts", json=payload)
        self.assertEqual(response.status_code, 201, response.text)
        return payload, response.json()["issue_id"]

    def test_gallery_paginates_every_image_and_filters_current_issue_status(self):
        first, issue_id = self.create(evidence=evidence())
        second, same_issue = self.create(event_id=str(uuid4()), evidence=dict(evidence(), frame_id=570))
        self.assertEqual(same_issue, issue_id)
        self.create(event_id=str(uuid4()))  # This report has no image and must not hide the saved images.
        third, resolved_id = self.create(event_id=str(uuid4()), latitude=13.0, evidence=evidence())
        self.client.post("/api/auth/login", json={"password": "review-test"})
        self.client.patch(f"/api/alerts/{resolved_id}/status", json={"status": "resolved"})
        ids = []
        for page in (1, 2):
            response = self.client.get(f"/api/evidence?status=open&page_size=1&page={page}")
            self.assertEqual(response.status_code, 200, response.text)
            data = response.json()
            self.assertEqual(data["total"], 2)
            self.assertNotIn("jpeg_base64", response.text)
            item = data["items"][0]
            self.assertEqual((item["issue_id"], item["status"]), (issue_id, "open"))
            self.assertEqual(self.client.get(item["evidence"]["url"]).status_code, 200)
            ids.append(item["event_id"])
        self.assertEqual(set(ids), {first["event_id"], second["event_id"]})
        self.assertEqual(self.client.get("/api/evidence?status=resolved").json()["items"][0]["event_id"], third["event_id"])
        self.assertEqual(self.client.get("/api/evidence?page=9").json()["items"], [])
        self.assertEqual(self.client.get("/api/evidence?priority=high").json()["total"], 0)
        self.assertEqual(self.client.get("/api/evidence?date_from=2099-01-01").json()["total"], 0)
        summary = next(item for item in self.client.get("/api/alerts").json()["items"] if item["issue_id"] == issue_id)
        self.assertEqual((summary["report_count"], summary["evidence_count"]), (3, 2))
        self.assertIn(summary["latest_evidence"]["event_id"], ids)
        self.assertIn("confidence", summary["latest_evidence"])
        self.assertEqual(self.client.get("/api/alerts/" + issue_id).json()["latest_evidence"], summary["latest_evidence"])

    def test_gallery_empty_legacy_issues_and_invalid_filters(self):
        self.create()
        self.assertEqual(self.client.get("/api/evidence").json()["total"], 0)
        summary = self.client.get("/api/alerts").json()["items"][0]
        self.assertEqual(summary["evidence_count"], 0)
        self.assertIsNone(summary["latest_evidence"])
        for query in ("page=0", "page_size=101", "status=invalid", "date_to=9999-12-31", "date_from=2026-09-15&date_to=2026-09-14"):
            self.assertEqual(self.client.get("/api/evidence?" + query).status_code, 422)

    def test_evidence_survives_outbox_restart_and_acknowledgement_loss(self):
        payload = dict(observation(), evidence=evidence())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "outbox.db"
            Outbox(path).enqueue(payload)
            accepted = self.client.post("/api/alerts", json=payload)
            self.assertEqual(accepted.status_code, 201)
            client = Mock()
            client.send_observation.side_effect = lambda value: self.client.post("/api/alerts", json=value)
            restarted = Outbox(path)
            restarted.flush_once(client, retry_now=True)
            self.assertEqual(restarted.counts()["sent"], 1)
        detail = self.client.get("/api/alerts/" + accepted.json()["issue_id"]).json()
        self.assertEqual(detail["report_count"], 1)
        saved = detail["observations"][0]["evidence"]
        self.assertNotIn("jpeg_base64", json.dumps(detail))
        image = self.client.get(saved["url"])
        self.assertEqual(image.content, base64.b64decode(payload["evidence"]["jpeg_base64"]))
        self.assertEqual(image.headers["content-type"], "image/jpeg")
        payload["evidence"]["frame_id"] += 1
        self.assertEqual(self.client.post("/api/alerts", json=payload).status_code, 409)

    def test_invalid_evidence_rejects_entire_observation(self):
        examples = [dict(evidence(), jpeg_base64="bad!"), evidence(format="PNG"), evidence(size=(641, 20)),
                    dict(evidence(), source_name="C:/private/video.mp4"), dict(evidence(), frame_id=-1)]
        for item in examples:
            response = self.client.post("/api/alerts", json=dict(observation(), evidence=item))
            self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.get("/api/statistics").json()["total_issues"], 0)
        self.assertEqual(self.client.get("/api/observations/missing/evidence").status_code, 404)

    def test_evidence_and_observation_roll_back_together(self):
        factory = self.client.app.state.session_factory
        with patch("sqlalchemy.orm.Session.commit", side_effect=RuntimeError("disk failed")):
            with self.assertRaises(RuntimeError):
                self.client.post("/api/alerts", json=dict(observation(), evidence=evidence()))
        with factory() as db:
            for model in (Issue, Observation, ObservationEvidence):
                self.assertEqual(db.scalar(select(func.count()).select_from(model)), 0)

    def test_old_event_fingerprint_is_still_accepted(self):
        payload, issue_id = self.create()
        parsed = ObservationCreate(**payload)
        old = parsed.model_dump(mode="json", exclude={"evidence"})
        old["timestamp"], old["gps_timestamp"] = iso(parsed.timestamp), iso(parsed.gps_timestamp)
        previous_fingerprint = hashlib.sha256(json.dumps(old, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        with self.client.app.state.session_factory() as db:
            self.assertEqual(db.get(Observation, payload["event_id"]).fingerprint, previous_fingerprint)
        self.assertEqual(self.client.post("/api/alerts", json=dict(payload, evidence=None)).status_code, 200)
        self.assertIsNone(self.client.get("/api/alerts/" + issue_id).json()["observations"][0]["evidence"])

    def test_false_detection_reopen_conflict_and_counts(self):
        payload, issue_id = self.create(evidence=evidence())
        path = "/api/alerts/" + issue_id
        self.assertEqual(self.client.patch(path + "/status", json={"status": "dismissed", "note": "Shadow"}).status_code, 401)
        self.client.post("/api/auth/login", json={"password": "review-test"})
        self.assertEqual(self.client.patch(path + "/status", json={"status": "dismissed", "note": "  "}).status_code, 422)
        decision = {"status": "dismissed", "expected_status": "open", "note": "Shadow, not a pothole"}
        for _ in range(2):
            self.assertEqual(self.client.patch(path + "/status", json=decision).status_code, 200)
        stats = self.client.get("/api/statistics").json()
        self.assertEqual((stats["total_issues"], stats["open_issues"], stats["resolved_issues"], stats["dismissed_issues"]), (1, 0, 0, 1))
        self.assertEqual(self.client.get("/api/alerts?status=dismissed").json()["total"], 1)
        conflict = self.client.patch(path + "/status", json={"status": "resolved", "expected_status": "open"})
        self.assertEqual(conflict.status_code, 409)
        detail = self.client.get(path).json()
        self.assertEqual(len(detail["activity"]), 1)
        self.assertIsNotNone(detail["observations"][0]["evidence"])
        self.assertEqual(self.client.patch(path + "/status", json={"status": "open", "expected_status": "dismissed", "note": "Recheck footage"}).status_code, 200)
        self.assertEqual(self.client.get("/api/statistics").json()["open_issues"], 1)

    def test_filtered_csv_exports_all_matching_rows(self):
        _, issue_id = self.create()
        response = self.client.get("/api/reports/issues.csv?status=open")
        self.assertEqual(response.status_code, 200)
        rows = list(csv.DictReader(StringIO(response.text)))
        self.assertEqual([row["issue_id"] for row in rows], [issue_id])
        self.assertEqual(list(csv.DictReader(StringIO(self.client.get("/api/reports/issues.csv?status=resolved").text))), [])
        self.assertEqual(self.client.get("/api/reports/issues.csv?status=garbage").status_code, 422)

    def test_invalid_calendar_extremes_and_unicode_password_do_not_crash(self):
        for path in ("/api/alerts", "/api/analytics", "/api/reports/issues.csv"):
            for query in ("date_to=9999-12-31", "date_from=0001-01-01", "date_from=2026-09-15&date_to=2026-09-14"):
                self.assertEqual(self.client.get(path + "?" + query).status_code, 422)
        self.assertEqual(self.client.post("/api/auth/login", json={"password": "incorrect-\u263a"}).status_code, 401)


class BackendPersistenceTests(unittest.TestCase):
    def test_evidence_available_after_backend_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Settings(database_url="sqlite:///" + (Path(directory) / "app.db").as_posix(), operator_password="test")
            payload = dict(observation(), evidence=evidence())
            with TestClient(create_app(settings)) as client:
                self.assertEqual(client.post("/api/alerts", json=payload).status_code, 201)
            with TestClient(create_app(settings)) as client:
                self.assertEqual(client.post("/api/alerts", json=payload).status_code, 200)
                self.assertEqual(client.get("/api/observations/" + payload["event_id"] + "/evidence").status_code, 200)

    def test_heartbeat_failure_does_not_block_alert_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            outbox = Outbox(Path(directory) / "outbox.db")
            payload = observation()
            outbox.enqueue(payload)
            client = Mock()
            client.heartbeat.side_effect = requests.ConnectionError("heartbeat failed")
            client.send_observation.return_value.status_code = 201
            client.send_observation.return_value.json.return_value = {"event_id": payload["event_id"], "issue_id": "ISSUE_TEST"}
            worker = DeliveryWorker(outbox, client, "BUS_01")
            worker.heartbeat({"camera_status": "online", "ai_status": "online"})
            worker.start()
            try:
                deadline = time.monotonic() + 5
                while outbox.counts()["sent"] == 0 and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertEqual(outbox.counts()["sent"], 1)
                client.heartbeat.assert_called_once()
            finally:
                worker.stop()
