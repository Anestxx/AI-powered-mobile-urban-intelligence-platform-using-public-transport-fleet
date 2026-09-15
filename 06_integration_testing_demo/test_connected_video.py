from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_ai_edge/scripts"))
spec = importlib.util.spec_from_file_location("connected_video_main", ROOT / "01_ai_edge/scripts/main.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class TinyVideo:
    fps, duration, is_camera = 30, .1, False
    frame_index = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def read(self):
        if self.frame_index == 3:
            return None
        self.frame_index += 1
        return object(), self.frame_index, (self.frame_index - 1) / self.fps

    def rewind(self):
        self.frame_index = 0


class ConnectedVideoTests(unittest.TestCase):
    def test_autoplay_confirms_alert_with_location_and_replay_does_not_duplicate(self):
        from outbox import Outbox
        with tempfile.TemporaryDirectory() as directory:
            outbox_path, log_path = Path(directory) / "outbox.db", Path(directory) / "alerts.json"
            detector = Mock(model_version="test-model")
            detector.detect.return_value = [{"event_type": "pothole", "confidence": .9, "bbox": [10, 10, 100, 100]}]
            cv2 = SimpleNamespace(namedWindow=Mock(), resizeWindow=Mock(), imshow=Mock(), waitKey=Mock(return_value=-1),
                                  getWindowProperty=Mock(return_value=1), destroyAllWindows=Mock(), WINDOW_NORMAL=0, WND_PROP_VISIBLE=4)
            argv = ["main.py", "--offline", "--loop", "--no-save-evidence", "--max-frames", "6", "--frame-interval", "1",
                    "--outbox", str(outbox_path), "--alerts-file", str(log_path)]
            with patch.object(sys, "argv", argv), patch.dict(sys.modules, {"cv2": cv2}), \
                 patch("detector.PotholeDetector", return_value=detector), patch("video_reader.VideoReader", return_value=TinyVideo()), \
                 patch.object(runner, "draw_frame", return_value=object()), redirect_stdout(io.StringIO()):
                self.assertEqual(runner.main(), 0)
            self.assertEqual(detector.detect.call_count, 6)
            self.assertEqual(cv2.imshow.call_count, 6)
            observations = json.loads(log_path.read_text())
            self.assertEqual(len(observations), 1)
            self.assertEqual(observations[0]["location_source"], "simulated")
            self.assertEqual(observations[0]["timestamp"], observations[0]["gps_timestamp"])
            self.assertIn("latitude", observations[0])
            self.assertEqual(Outbox(outbox_path).counts()["pending"], 1)


if __name__ == "__main__":
    unittest.main()
