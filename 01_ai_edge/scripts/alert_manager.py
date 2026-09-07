import time
import uuid


class AlertManager:

    def __init__(
        self,
        confidence_threshold=0.60,
        required_detections=3,
        cooldown_seconds=10
    ):
        self.confidence_threshold = confidence_threshold
        self.required_detections = required_detections
        self.cooldown_seconds = cooldown_seconds

        self.detection_count = 0
        self.last_alert_time = 0

    def process_detection(self, detection):

        confidence = detection["confidence"]

        # Ignore weak predictions
        if confidence < self.confidence_threshold:
            self.detection_count = 0
            return None

        # Count consecutive valid detections
        self.detection_count += 1

        if self.detection_count < self.required_detections:
            return None

        current_time = time.time()

        # Prevent duplicate alerts
        if current_time - self.last_alert_time < self.cooldown_seconds:
            return None

        self.last_alert_time = current_time
        self.detection_count = 0

        alert = {
            "alert_id": str(uuid.uuid4()),
            "event_type": detection["event_type"],
            "confidence": round(confidence, 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "bbox": detection["bbox"],
            "source": "public_bus_camera",
            "status": "new"
        }

        return alert