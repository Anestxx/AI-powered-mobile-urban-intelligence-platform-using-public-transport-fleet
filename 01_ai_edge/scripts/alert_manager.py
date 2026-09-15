from dataclasses import dataclass, field
import math
from uuid import uuid4


def overlap(first, second):
    left, top = max(first[0], second[0]), max(first[1], second[1])
    right, bottom = min(first[2], second[2]), min(first[3], second[3])
    intersection = max(0, right - left) * max(0, bottom - top)
    union = (first[2] - first[0]) * (first[3] - first[1]) + (second[2] - second[0]) * (second[3] - second[1]) - intersection
    return intersection / union if union > 0 else 0


@dataclass
class Track:
    bbox: list
    event_id: str = field(default_factory=lambda: str(uuid4()))
    confidences: list = field(default_factory=list)
    missed: int = 0
    alerted: bool = False


class AlertManager:
    """Associate boxes across sampled frames; emit once per continuously visible track."""
    def __init__(self, confidence_threshold=.7, required_detections=3, max_missing_frames=5, cooldown_seconds=5, iou_threshold=.2):
        if not 0 <= confidence_threshold <= 1 or required_detections < 1 or max_missing_frames < 0 or cooldown_seconds < 0 or not 0 < iou_threshold <= 1:
            raise ValueError("Invalid tracking configuration")
        self.confidence_threshold = confidence_threshold
        self.required_detections = required_detections
        self.max_missing_frames = max_missing_frames
        self.cooldown_seconds = cooldown_seconds
        self.iou_threshold = iou_threshold
        self.tracks = []
        self.recent_alerts = []
        self.last_frame_id = -1

    def process_frame(self, detections, frame_id, video_time, timestamp):
        if frame_id <= self.last_frame_id:
            return []
        self.last_frame_id = frame_id
        self.recent_alerts = [(bbox, expiry) for bbox, expiry in self.recent_alerts if expiry > video_time]
        unmatched = set(range(len(self.tracks)))
        seen = []
        alerts = []
        for detection in sorted(detections, key=lambda value: value.get("confidence", 0), reverse=True):
            confidence = detection.get("confidence", 0)
            bbox = detection.get("bbox")
            if detection.get("event_type") != "pothole" or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not self.confidence_threshold <= confidence <= 1:
                continue
            if not isinstance(bbox, list) or len(bbox) != 4 or not all(isinstance(x, (int, float)) and math.isfinite(x) and x >= 0 for x in bbox) or bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                continue
            # Suppress near-identical boxes in a single frame before association.
            if any(overlap(bbox, other.bbox) >= .85 for other in seen):
                continue
            matches = [(overlap(bbox, self.tracks[index].bbox), index) for index in unmatched]
            score, index = max(matches, default=(0, -1))
            if score >= self.iou_threshold:
                unmatched.remove(index)
                track = self.tracks[index]
            else:
                track = Track(list(bbox))
                self.tracks.append(track)
            track.bbox = list(bbox)
            track.missed = 0
            track.confidences = (track.confidences + [confidence])[-self.required_detections:]
            seen.append(track)
            if track.alerted or len(track.confidences) < self.required_detections:
                continue
            if any(overlap(track.bbox, previous) >= self.iou_threshold for previous, _ in self.recent_alerts):
                continue
            track.alerted = True
            self.recent_alerts.append((list(track.bbox), video_time + self.cooldown_seconds))
            alerts.append({"event_id": track.event_id, "event_type": "pothole", "confidence": round(sum(track.confidences) / len(track.confidences), 6),
                           "bbox": list(track.bbox), "timestamp": timestamp})
        for index in unmatched:
            self.tracks[index].missed += 1
            self.tracks[index].confidences.clear()
        self.tracks = [track for track in self.tracks if track.missed <= self.max_missing_frames]
        return alerts
