from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "01_ai_edge/scripts"), str(ROOT / "03_backend_database")]
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.config import Settings
from app.database import Base, create_database
from app.main import create_app
from app.models import Issue
from app.services import nearby_issue_query, record_dict
from location_intelligence import match_issue, search_bounds
from metrics import RunMetrics


def destination(latitude, longitude, metres, bearing):
    phi, lam, angle = map(math.radians, (latitude, longitude, bearing))
    distance = metres / 6371000
    lat = math.asin(math.sin(phi) * math.cos(distance) + math.cos(phi) * math.sin(distance) * math.cos(angle))
    lon = lam + math.atan2(math.sin(angle) * math.sin(distance) * math.cos(phi), math.cos(distance) - math.sin(phi) * math.sin(lat))
    return math.degrees(lat), (math.degrees(lon) + 180) % 360 - 180


class GeographicQueryTests(unittest.TestCase):
    def test_bounds_include_circle_at_dateline_poles_and_equator(self):
        for centre in ((0, 0), (12.97, 77.59), (89.9999, 80), (-89.9999, -120), (12, 179.99999), (-12, -179.99999)):
            lower, upper, intervals = search_bounds(*centre, 25)
            for bearing in range(0, 360, 5):
                latitude, longitude = destination(*centre, 25, bearing)
                self.assertTrue(lower <= latitude <= upper, (centre, bearing))
                self.assertTrue(any(start <= longitude <= end for start, end in intervals), (centre, bearing))

    def test_sql_prefilter_keeps_same_match_across_dateline(self):
        engine, factory = create_database("sqlite://")
        Base.metadata.create_all(engine)
        observation = {"latitude": 12, "longitude": 179.99999, "event_type": "pothole", "location_source": "simulated"}
        with factory() as db:
            for index, distance in enumerate((5, 24, 26, 1000)):
                latitude, longitude = destination(12, 179.99999, distance, 90)
                db.add(Issue(issue_id=f"ISSUE_{index}", latitude=latitude, longitude=longitude, event_type="pothole", location_source="simulated", status="open",
                             first_seen="2026-09-14T00:00:00Z", last_seen="2026-09-14T00:00:00Z", priority_reason="test"))
            db.commit()
            all_candidates = db.scalars(select(Issue)).all()
            nearby = db.scalars(nearby_issue_query(observation, 25)).all()
            self.assertLess(len(nearby), len(all_candidates))
            self.assertEqual(match_issue(observation, [record_dict(item) for item in all_candidates]), match_issue(observation, [record_dict(item) for item in nearby]))
        engine.dispose()


class StatusHistoryTests(unittest.TestCase):
    def test_history_records_real_changes_and_preserves_notes_on_retry(self):
        with TestClient(create_app(Settings(database_url="sqlite://", operator_password="history-test"))) as client:
            payload = deepcopy(json.loads((ROOT / "contracts/fixtures/demo.json").read_text())["observations"][0])
            issue_id = client.post("/api/alerts", json=payload).json()["issue_id"]
            path = "/api/alerts/" + issue_id
            self.assertEqual(client.get(path).json()["activity"], [])
            self.assertEqual(client.patch(path + "/status", json={"status": "resolved", "note": "unauthorized"}).status_code, 401)
            client.post("/api/auth/login", json={"password": "history-test"})
            for _ in range(2):
                self.assertEqual(client.patch(path + "/status", json={"status": "resolved", "note": "  Reviewed in prototype demonstration  "}).status_code, 200)
            detail = client.get(path).json()
            self.assertEqual(len(detail["activity"]), 1)
            self.assertEqual(detail["activity"][0]["note"], "Reviewed in prototype demonstration")
            self.assertEqual(detail["activity"][0]["previous_status"], "open")
            self.assertEqual(len(detail["observations"]), 1)
            self.assertEqual(client.patch(path + "/status", json={"status": "open", "note": "x" * 501}).status_code, 422)
            self.assertEqual(client.get(path).json()["status"], "resolved")
            client.patch(path + "/status", json={"status": "open", "note": "Needs another inspection"})
            history = client.get(path).json()["activity"]
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["status"], "open")


class MetricsTests(unittest.TestCase):
    def test_measured_rate_sampling_and_pause_reset(self):
        moments = iter((0, .1, .2, 20, 20.1))
        metrics = RunMetrics(clock=lambda: next(moments))
        metrics.record_inference(.05)
        for _ in range(3):
            metrics.record_frame()
        result = metrics.snapshot()
        self.assertEqual(result["recent_frame_rate"], 10)
        self.assertEqual(result["sampled_percent"], 33.3)
        self.assertEqual(result["mean_inference_ms"], 50)
        metrics.reset_playback_clock()
        metrics.record_frame()
        metrics.record_frame()
        self.assertEqual(metrics.snapshot()["recent_frame_rate"], 10)

    def test_empty_metrics_do_not_invent_speed(self):
        self.assertIsNone(RunMetrics().snapshot()["mean_inference_ms"])
        with self.assertRaises(ValueError):
            RunMetrics().record_inference(float("nan"))
