import cv2
import numpy as np
import torch
from ultralytics import YOLO


class RoadDetector:

    def __init__(self, model_path, imgsz=640, roi_points=None):
        """
        roi_points: list of 4 (x_ratio, y_ratio) points defining a
        trapezoid over the road area, as fractions of frame width/height,
        in order: top-left, top-right, bottom-right, bottom-left.

        Default assumes the road fills most of the lower frame and
        narrows toward the horizon — matches a forward-facing bus/dashcam.
        Tune these if your camera angle is different.
        """

        print("Loading pothole detection model...")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        self.model = YOLO(model_path)
        self.imgsz = imgsz

        self.roi_points = roi_points or [
            (0.30, 0.42),  # top-left
            (0.70, 0.42),  # top-right
            (1.00, 1.00),  # bottom-right
            (0.00, 1.00),  # bottom-left
        ]

    def get_roi_polygon(self, frame_width, frame_height):

        return np.array([
            (int(x * frame_width), int(y * frame_height))
            for x, y in self.roi_points
        ], dtype=np.int32)

    def brighten_shadows(self, frame, shadow_thresh=100, gamma=1.8):
        """
        Brightens ONLY the dark/shadow regions of the frame, leaving
        well-lit areas untouched. This is far more targeted than global
        CLAHE — it reveals pothole edges hidden in shadow without
        washing out or blocking the rest of the image.
        """

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
        h, s, v = cv2.split(hsv)

        # Mask of shadow pixels (low brightness)
        shadow_mask = (v < shadow_thresh).astype(np.float32)

        # Smooth the mask edges so the brightening blends naturally
        shadow_mask = cv2.GaussianBlur(shadow_mask, (25, 25), 0)

        # Gamma-brighten the V channel
        v_norm = v / 255.0
        v_gamma = np.power(v_norm, 1.0 / gamma) * 255.0

        # Blend: only apply the brightened version where shadow_mask says so
        v_result = (v * (1 - shadow_mask)) + (v_gamma * shadow_mask)
        v_result = np.clip(v_result, 0, 255).astype(np.uint8)

        hsv_result = cv2.merge((h.astype(np.uint8), s.astype(np.uint8), v_result))
        corrected = cv2.cvtColor(hsv_result, cv2.COLOR_HSV2BGR)

        return corrected

    def is_in_roi(self, x1, y1, x2, y2, roi_polygon):
        """
        True if the detection's center point falls inside the road
        trapezoid. This filters out trees/sky/roadside clutter even
        when they're low or wide in the frame.
        """

        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)

        result = cv2.pointPolygonTest(
            roi_polygon, (center_x, center_y), False
        )

        return result >= 0

    def detect(self, frame, conf=0.15):
        """
        Runs inference on a shadow-corrected COPY of the frame.
        The original 'frame' is never modified — it stays full
        quality for display.
        """

        frame_height, frame_width = frame.shape[:2]
        roi_polygon = self.get_roi_polygon(frame_width, frame_height)

        processed_frame = self.brighten_shadows(frame)

        results = self.model(
            processed_frame,
            conf=conf,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False
        )

        detections = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = result.names[class_id]
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                if not self.is_in_roi(x1, y1, x2, y2, roi_polygon):
                    continue

                detections.append({
                    "event_type": class_name,
                    "confidence": confidence,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)]
                })

        return detections

    def draw_detections(self, frame, detections):
        """Draws boxes on the ORIGINAL full-quality frame."""

        for det in detections:

            x1, y1, x2, y2 = det["bbox"]
            label = f'{det["event_type"]} {det["confidence"]:.2f}'

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            (text_w, text_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )

            cv2.rectangle(
                frame,
                (x1, y1 - text_h - 8),
                (x1 + text_w + 4, y1),
                (0, 0, 255),
                -1
            )

            cv2.putText(
                frame,
                label,
                (x1 + 2, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

        return frame

    def draw_roi(self, frame):
        """Draws the trapezoid ROI so you can visually tune roi_points."""

        frame_height, frame_width = frame.shape[:2]
        roi_polygon = self.get_roi_polygon(frame_width, frame_height)

        cv2.polylines(
            frame, [roi_polygon], isClosed=True,
            color=(0, 255, 255), thickness=2
        )

        return frame