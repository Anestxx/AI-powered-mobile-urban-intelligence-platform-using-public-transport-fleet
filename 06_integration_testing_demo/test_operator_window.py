import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "01_ai_edge/scripts"), str(ROOT / "03_backend_database")]
from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
from operator_client import OperatorClient


class OperatorWindowTests(unittest.TestCase):
    def test_desktop_resolution_handles_rejection_then_updates_shared_records(self):
        try:
            import tkinter as tk
            from operator_window import OperatorWindow
        except ImportError:
            self.skipTest("Tkinter desktop support is unavailable")
        fixture = json.loads((ROOT / "contracts/fixtures/demo.json").read_text())["observations"][0]
        from test_backend_review import evidence
        fixture["evidence"] = evidence()
        with TestClient(create_app(Settings(database_url="sqlite://", operator_password="desktop-test-only"))) as backend:
            issue_id = backend.post("/api/alerts", json=fixture).json()["issue_id"]
            client = OperatorClient("http://testserver", session=backend)
            try:
                with patch("operator_window.OperatorClient", return_value=client):
                    window = OperatorWindow("http://testserver")
            except tk.TclError:
                self.skipTest("No desktop display is available")

            def until(predicate):
                deadline = time.monotonic() + 8
                while not predicate():
                    self.assertLess(time.monotonic(), deadline, window.connection.get() + " / " + window.message.get())
                    window.wait_key(20)

            try:
                window.root.geometry("1100x650+0+0")
                window.notebook.select(window.alerts_tab)
                until(lambda: window.selected_id == issue_id and window.detail_record is not None)
                until(lambda: bool(window.evidence_label.cget("image")))
                window.authenticated = True  # Simulate a session that has expired on the server.
                window.request_resolution()
                window.root.update_idletasks()
                self.assertLessEqual(window.confirm_frame.winfo_rooty() + window.confirm_frame.winfo_height(),
                                     window.alerts_tab.winfo_rooty() + window.alerts_tab.winfo_height())
                window.confirm_resolution()
                until(lambda: not window.busy)
                self.assertFalse(window.authenticated)
                self.assertEqual(window.tree.set(issue_id, "status"), "open")
                self.assertEqual(window.counts["open"].get(), "1")
                window.sync.submit("login", password="desktop-test-only")
                until(lambda: window.authenticated)
                window.request_resolution()
                window.resolution_note.set("Reviewer demo resolution")
                window.confirm_resolution()
                until(lambda: window.counts["resolved"].get() == "1" and not window.busy)
                self.assertEqual(window.tree.set(issue_id, "status"), "resolved")
                self.assertEqual(window.counts["open"].get(), "0")
                self.assertEqual(len(backend.get("/api/alerts/" + issue_id).json()["observations"]), 1)
                self.assertEqual(backend.get("/api/alerts/" + issue_id).json()["activity"][0]["note"], "Reviewer demo resolution")
                window.review_action.set("Reopen")
                window.request_resolution()
                window.confirm_resolution()
                until(lambda: window.counts["open"].get() == "1" and not window.busy)
                window.review_action.set("False detection")
                window.request_resolution()
                window.confirm_resolution()
                self.assertFalse(window.busy)
                self.assertIn("reason", window.message.get())
                window.resolution_note.set("Reviewed as a shadow")
                window.confirm_resolution()
                until(lambda: window.counts["open"].get() == "0" and not window.busy)
                self.assertEqual(window.counts["resolved"].get(), "0")
                self.assertEqual(window.tree.set(issue_id, "status"), "dismissed")
                self.assertIsNotNone(backend.get("/api/alerts/" + issue_id).json()["observations"][0]["evidence"])
            finally:
                window.stop()


if __name__ == "__main__":
    unittest.main()
