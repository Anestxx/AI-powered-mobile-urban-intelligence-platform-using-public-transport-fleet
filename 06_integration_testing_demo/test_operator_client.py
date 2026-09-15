from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_ai_edge/scripts"))
sys.path.insert(0, str(ROOT / "03_backend_database"))
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from operator_client import OperatorClient, OperatorError


class OperatorClientTests(unittest.TestCase):
    def setUp(self):
        self.backend = TestClient(create_app(Settings(database_url="sqlite://", operator_password="operator-test-only")))
        self.backend.__enter__()
        self.operator = OperatorClient("http://testserver", session=self.backend)
        payload = deepcopy(json.loads((ROOT / "contracts/fixtures/demo.json").read_text())["observations"][0])
        payload["event_id"] = str(uuid4())
        self.issue_id = self.backend.post("/api/alerts", json=payload).json()["issue_id"]

    def tearDown(self):
        self.backend.__exit__(None, None, None)

    def test_python_resolution_updates_shared_alerts_and_statistics(self):
        before = self.operator.details(self.issue_id)
        self.assertEqual(self.operator.snapshot()["statistics"]["resolved_issues"], 0)
        self.operator.login("operator-test-only")
        self.assertTrue(self.operator.snapshot()["authenticated"])
        saved = self.operator.resolve(self.issue_id)
        self.assertEqual(saved["status"], "resolved")
        # These are the same endpoints read by the React dashboard and Alerts page.
        self.assertEqual(self.backend.get("/api/statistics").json()["resolved_issues"], 1)
        self.assertEqual(self.backend.get("/api/alerts", params={"status": "open"}).json()["total"], 0)
        self.assertEqual(self.operator.snapshot("resolved")["alerts"]["total"], 1)
        self.assertEqual(self.operator.details(self.issue_id)["observations"], before["observations"])

    def test_unauthenticated_or_expired_session_cannot_change_an_issue(self):
        for expire in (False, True):
            with self.subTest(expire=expire):
                if expire:
                    self.operator.login("operator-test-only")
                    self.backend.app.state.sessions.clear()
                with self.assertRaises(OperatorError) as error:
                    self.operator.resolve(self.issue_id)
                self.assertEqual(error.exception.status, 401)
                self.assertEqual(self.operator.details(self.issue_id)["status"], "open")

    def test_wrong_password_and_logout_keep_authorization_explicit(self):
        with self.assertRaises(OperatorError):
            self.operator.login("wrong-password")
        self.assertFalse(self.operator.snapshot()["authenticated"])
        self.operator.login("operator-test-only")
        self.operator.logout()
        self.assertFalse(self.operator.snapshot()["authenticated"])

    def test_unacknowledged_resolution_is_not_reported_as_success(self):
        session = Mock()
        session.request.return_value = Mock(status_code=200)
        session.request.return_value.json.return_value = {"issue_id": self.issue_id, "status": "open"}
        operator = OperatorClient("http://testserver", session=session)
        with self.assertRaisesRegex(OperatorError, "did not confirm resolution"):
            operator.resolve(self.issue_id)


if __name__ == "__main__":
    unittest.main()
