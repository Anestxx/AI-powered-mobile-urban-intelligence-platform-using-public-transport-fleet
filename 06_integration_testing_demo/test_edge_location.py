from contextlib import redirect_stdout
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_ai_edge/scripts"))
sys.path.insert(0, str(ROOT / "03_backend_database"))
from alert_manager import AlertManager
from alert_logger import AlertLogger
from outbox import DeliveryWorker, Outbox
from location_intelligence import GPSSimulator, distance_meters, match_issue, review_priority, validate_location
from app.main import create_app
from app.config import Settings
from fastapi.testclient import TestClient
import requests

BOX = {"event_type": "pothole", "confidence": .9, "bbox": [10, 10, 100, 100]}
TIMESTAMP = "2026-09-13T10:30:00+00:00"


class TrackingTests(unittest.TestCase):
    def test_one_frame_and_low_confidence_do_not_alert(self):
        manager = AlertManager()
        self.assertEqual(manager.process_frame([BOX], 1, 0, TIMESTAMP), [])
        for frame in range(2, 10):
            self.assertEqual(manager.process_frame([dict(BOX, confidence=.2)], frame, frame / 30, TIMESTAMP), [])

    def test_persistent_pothole_emits_once_even_after_cooldown(self):
        manager = AlertManager()
        alerts = []
        for frame in range(100):
            alerts.extend(manager.process_frame([BOX], frame, frame, TIMESTAMP))
        self.assertEqual(len(alerts), 1)
        self.assertIn("event_id", alerts[0])

    def test_distinct_tracks_can_both_alert(self):
        manager = AlertManager()
        second = dict(BOX, bbox=[200, 200, 300, 300])
        alerts = []
        for frame in range(4):
            alerts.extend(manager.process_frame([BOX, second], frame, frame / 30, TIMESTAMP))
        self.assertEqual(len(alerts), 2)
        self.assertNotEqual(alerts[0]["event_id"], alerts[1]["event_id"])

    def test_duplicate_boxes_in_one_frame_are_not_temporal_evidence(self):
        manager = AlertManager()
        self.assertEqual(manager.process_frame([BOX] * 3, 1, 0, TIMESTAMP), [])
        self.assertEqual(manager.process_frame([BOX], 1, 0, TIMESTAMP), [])
        self.assertEqual(len(manager.tracks), 1)

    def test_absence_resets_consecutive_validation(self):
        manager = AlertManager()
        for frame, detections in enumerate(([BOX], [], [BOX], [], [BOX])):
            self.assertEqual(manager.process_frame(detections, frame, frame, TIMESTAMP), [])

    def test_later_pothole_can_create_new_event(self):
        manager = AlertManager(required_detections=1, max_missing_frames=1)
        first = manager.process_frame([BOX], 1, 0, TIMESTAMP)[0]
        manager.process_frame([], 2, 1, TIMESTAMP)
        manager.process_frame([], 3, 2, TIMESTAMP)
        second = manager.process_frame([BOX], 4, 10, TIMESTAMP)[0]
        self.assertNotEqual(first["event_id"], second["event_id"])

    def test_logger_preserves_existing_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alerts.json"
            AlertLogger(path).save_alert({"event_id": "one"})
            AlertLogger(path).save_alert({"event_id": "two"})
            self.assertEqual(len(json.loads(path.read_text())), 2)

    def test_model_with_unknown_labels_is_rejected(self):
        from detector import PotholeDetector
        model = Mock(names={0: "0"})
        with patch.dict(sys.modules, {"torch": SimpleNamespace(), "ultralytics": SimpleNamespace(YOLO=Mock(return_value=model))}):
            with self.assertRaisesRegex(ValueError, "Expected model class"):
                PotholeDetector(ROOT / "01_ai_edge/models/best.pt")


class LocationTests(unittest.TestCase):
    def test_route_uses_video_time(self):
        first = GPSSimulator(start_time=TIMESTAMP)
        second = GPSSimulator(start_time=TIMESTAMP)
        first.get_location(1)
        self.assertEqual(first.get_location(20), second.get_location(20))
        self.assertEqual(first.get_location(20)["location_source"], "simulated")
        validate_location(first.get_location(20), "2026-09-13T10:30:20Z")

    def test_missing_stale_invalid_locations_fail(self):
        location = GPSSimulator(start_time=TIMESTAMP).get_location(0)
        for changes in ({"latitude": None}, {"latitude": 91}, {"longitude": float("nan")}, {"gps_timestamp": "2026-09-13T10:00:00Z"}, {"location_source": "unknown"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_location(dict(location, **changes), TIMESTAMP)

    def test_distance_is_symmetric_and_rejects_invalid_values(self):
        self.assertEqual(distance_meters(12, 77, 12, 77), 0)
        self.assertAlmostEqual(distance_meters(12, 77, 12.1, 77.1), distance_meters(12.1, 77.1, 12, 77))
        with self.assertRaises(ValueError):
            distance_meters(100, 77, 12, 77)
        self.assertTrue(distance_meters(0, 0, 0, 180) > 20000000)

    def test_match_chooses_nearest_open_same_source_issue(self):
        observation = {"event_type": "pothole", "latitude": 12.97, "longitude": 77.59, "location_source": "simulated"}
        issue = dict(observation, status="open", issue_id="ISSUE_B")
        candidates = [dict(issue, status="resolved", issue_id="CLOSED"), dict(issue, event_type="traffic", issue_id="TRAFFIC"), dict(issue, location_source="gps", issue_id="GPS"), issue, dict(issue, issue_id="ISSUE_A")]
        self.assertEqual(match_issue(observation, candidates)["matched_issue_id"], "ISSUE_A")
        self.assertIsNone(match_issue(dict(observation, latitude=13), candidates)["matched_issue_id"])

    def test_close_distinct_potholes_expose_matching_limitation(self):
        observation = {"event_type": "pothole", "latitude": 12.97, "longitude": 77.59, "location_source": "simulated"}
        separate_pothole = dict(observation, latitude=12.97005, issue_id="NEARBY_BUT_DISTINCT", status="open")
        self.assertEqual(match_issue(observation, [separate_pothole])["matched_issue_id"], "NEARBY_BUT_DISTINCT")

    def test_review_priority_counts_distinct_buses(self):
        self.assertEqual(review_priority(["A", "A"])["priority"], "low")
        self.assertEqual(review_priority(["A", "B"])["priority"], "medium")
        self.assertEqual(review_priority(["A", "B", "C"])["priority"], "high")


class DeliveryTests(unittest.TestCase):
    def test_heartbeats_continue_without_new_frames(self):
        outbox, client = Mock(), Mock()
        worker = DeliveryWorker(outbox, client, "BUS_01")
        worker.heartbeat({"timestamp": TIMESTAMP, "camera_status": "online", "ai_status": "online"})
        worker.stop_event = Mock()
        worker.stop_event.is_set.side_effect = [False, False, True]
        with patch("outbox.time.monotonic", side_effect=[0, 0, 11, 11]):
            worker.run()
        self.assertEqual(client.heartbeat.call_count, 2)
        self.assertNotEqual(client.heartbeat.call_args.args[1]["timestamp"], TIMESTAMP)
        self.assertEqual(outbox.flush_once.call_count, 2)

    def payload(self):
        fixture = json.loads((ROOT / "contracts/fixtures/demo.json").read_text())["observations"][0]
        fixture["event_id"] = str(uuid4())
        return fixture

    def test_outage_restart_and_acknowledgement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "outbox.db"
            outbox = Outbox(path)
            payload = self.payload()
            outbox.enqueue(payload)
            offline = Mock()
            offline.send_observation.side_effect = requests.ConnectionError("offline")
            outbox.flush_once(offline)
            self.assertEqual(outbox.counts()["pending"], 1)
            self.assertEqual(outbox.delivery_states([payload["event_id"], "unknown"]), {payload["event_id"]: "pending"})
            self.assertEqual(outbox.delivery_states([]), {})
            with TestClient(create_app(Settings(database_url="sqlite://", operator_password="test-password"))) as backend:
                client = SimpleNamespace(send_observation=lambda event: backend.post("/api/alerts", json=event))
                # Server accepted before the client received a response: retry must still count once.
                backend.post("/api/alerts", json=payload)
                restarted = Outbox(path)
                restarted.flush_once(client, retry_now=True)
                self.assertEqual(restarted.counts()["sent"], 1)
                self.assertEqual(restarted.delivery_states([payload["event_id"]]), {payload["event_id"]: "sent"})
                self.assertEqual(backend.get("/api/alerts").json()["items"][0]["report_count"], 1)

    def test_permanent_rejection_is_retained_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            outbox = Outbox(Path(directory) / "outbox.db")
            outbox.enqueue(self.payload())
            client = Mock()
            client.send_observation.return_value = SimpleNamespace(status_code=422, text="invalid")
            outbox.flush_once(client)
            self.assertEqual(outbox.counts()["invalid"], 1)
            outbox.flush_once(client, retry_now=True)
            client.send_observation.assert_called_once()

    def test_malformed_acknowledgements_remain_pending_until_valid_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            outbox = Outbox(Path(directory) / "outbox.db")
            payload = self.payload()
            outbox.enqueue(payload)
            client = Mock()
            response = client.send_observation.return_value
            response.status_code = 200
            for receipt in (None, [], "OK", {}, {"event_id": "wrong", "issue_id": "ISSUE_1"}, {"event_id": payload["event_id"], "issue_id": []}):
                with self.subTest(receipt=receipt):
                    response.json.return_value = receipt
                    outbox.flush_once(client, retry_now=True)
                    self.assertEqual(outbox.counts()["pending"], 1)
            response.json.return_value = {"event_id": payload["event_id"], "issue_id": "ISSUE_1"}
            outbox.flush_once(client, retry_now=True)
            self.assertEqual(outbox.counts()["sent"], 1)

    def test_queued_payload_cannot_change(self):
        with tempfile.TemporaryDirectory() as directory:
            outbox = Outbox(Path(directory) / "outbox.db")
            payload = self.payload()
            outbox.enqueue(payload)
            outbox.enqueue(payload)
            with self.assertRaises(ValueError):
                outbox.enqueue(dict(payload, confidence=.5))


if __name__ == "__main__":
    unittest.main()
