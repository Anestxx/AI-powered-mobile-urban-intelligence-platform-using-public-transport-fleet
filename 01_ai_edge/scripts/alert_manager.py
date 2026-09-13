import time
import uuid
from collections import defaultdict


class AlertManager:

    EVENT_SEVERITY = {
        "road_damage": "high",
        "pothole": "high",
        "road_infrastructure": "medium",
        "traffic": "low",
        "emergency": "critical",
        "unsafe_behaviour": "high",
    }

    EVENT_PRIORITY = {
        "road_damage": 75,
        "pothole": 85,
        "road_infrastructure": 55,
        "traffic": 35,
        "emergency": 100,
        "unsafe_behaviour": 70,
    }

    def __init__(
        self,
        required_detections=2,
        cooldown_seconds=8,
        persistence_window=5
    ):

        self.required_detections = required_detections
        self.cooldown_seconds = cooldown_seconds
        self.persistence_window = persistence_window

        self.history = defaultdict(list)
        self.last_alert_times = {}

        self.total_alerts = 0

    def calculate_priority(
        self,
        event_type,
        confidence
    ):

        base = self.EVENT_PRIORITY.get(
            event_type,
            30
        )

        score = base + (confidence * 25)

        return min(
            round(score, 1),
            100
        )

    def process_detection(
        self,
        detection
    ):

        event_type = detection.get("event_type")
        class_name = detection.get("class_name")

        confidence = float(
            detection.get("confidence", 0)
        )

        if not event_type or not class_name:
            return None

        # Basic confidence gate
        if event_type == "pothole" and confidence < 0.20:
            return None

        if event_type == "traffic" and confidence < 0.35:
            return None

        if event_type == "road_damage" and confidence < 0.30:
            return None

        key = event_type + ":" + class_name

        now = time.time()

        self.history[key].append({
            "time": now,
            "confidence": confidence,
            "bbox": detection.get("bbox"),
            "model": detection.get("model")
        })

        # Keep only recent observations
        self.history[key] = [
            item
            for item in self.history[key]
            if now - item["time"]
            <= self.persistence_window
        ]

        observations = self.history[key]

        # Temporal validation
        if len(observations) < self.required_detections:
            return None

        last_alert = self.last_alert_times.get(
            key,
            0
        )

        if now - last_alert < self.cooldown_seconds:
            return None

        recent = observations[
            -self.required_detections:
        ]

        avg_confidence = (
            sum(
                item["confidence"]
                for item in recent
            )
            / len(recent)
        )

        best_observation = max(
            recent,
            key=lambda x: x["confidence"]
        )

        severity = self.EVENT_SEVERITY.get(
            event_type,
            "medium"
        )

        priority = self.calculate_priority(
            event_type,
            avg_confidence
        )

        alert = {
            "alert_id": str(uuid.uuid4()),

            "event_type": event_type,

            "class_name": class_name,

            "confidence": round(
                avg_confidence,
                3
            ),

            "severity": severity,

            "priority_score": priority,

            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),

            "bbox": best_observation["bbox"],

            "source": "public_bus_camera",

            "status": "new",

            "validation": {
                "required_observations":
                    self.required_detections,

                "observed_observations":
                    len(recent),

                "validation_method":
                    "temporal_persistence"
            }
        }

        self.last_alert_times[key] = now

        self.total_alerts += 1

        return alert

    def get_tracking_status(self):

        result = {}

        for key, observations in self.history.items():

            result[key] = {
                "observations": len(observations)
            }

        return result