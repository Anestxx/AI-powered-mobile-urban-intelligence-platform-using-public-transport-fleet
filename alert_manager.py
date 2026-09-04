import time


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

        # Ignore weak AI predictions
        if confidence < self.confidence_threshold:
            self.detection_count = 0
            return None

        # Count repeated detections
        self.detection_count += 1

        # Not enough evidence yet
        if self.detection_count < self.required_detections:
            return None

        current_time = time.time()

        # Prevent duplicate alerts
        if (
            current_time - self.last_alert_time
            < self.cooldown_seconds
        ):
            return None

        # Create alert
        self.last_alert_time = current_time
        self.detection_count = 0

        alert = {
            "event_type": "pothole",
            "confidence": round(confidence, 2),
            "timestamp": time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "bbox": detection["bbox"]
        }

        return alert 