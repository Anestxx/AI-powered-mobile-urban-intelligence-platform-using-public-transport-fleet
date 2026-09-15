import base64
from io import BytesIO
from pathlib import Path
import sys
import unittest

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "01_ai_edge/scripts"))
from evidence import make_evidence


class EvidenceImageTests(unittest.TestCase):
    def test_saved_image_includes_context_and_box_without_changing_source(self):
        frame = np.full((1024, 576, 3), 60, dtype=np.uint8)
        original = frame.copy()
        payload = make_evidence(frame, [240, 700, 280, 720], "road_test.mp4", 567, 18.9)
        image = Image.open(BytesIO(base64.b64decode(payload["jpeg_base64"])))
        self.assertEqual(image.size, (320, 240))
        self.assertLessEqual(len(base64.b64decode(payload["jpeg_base64"])), 192 * 1024)
        np.testing.assert_array_equal(frame, original)
        pixels = np.asarray(image)
        self.assertGreater(np.count_nonzero(pixels[:, :, 0] > 180), 50)
        self.assertEqual(payload["frame_id"], 567)

    def test_edge_boxes_are_clamped_and_invalid_boxes_rejected(self):
        frame = np.full((600, 800, 3), 70, dtype=np.uint8)
        for box in ([0, 0, 40, 30], [760, 570, 820, 620], [0, 0, 800, 600]):
            payload = make_evidence(frame, box, "road_test.mp4", 1, .03)
            image = Image.open(BytesIO(base64.b64decode(payload["jpeg_base64"])))
            self.assertLessEqual(max(image.size), 480)
        with self.assertRaises(ValueError):
            make_evidence(frame, [900, 700, 950, 730], "road_test.mp4", 1, .03)
