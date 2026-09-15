"""Prototype rule module retained from 47cba0f; not connected to live alert delivery."""
import time

class EmergencyIntelligence:
    EMERGENCY_CLASSES = {'ambulance', 'emergency_vehicle', 'police', 'police_car', 'fire_truck', 'fire_engine', 'firetruck'}

    def __init__(self, confidence_threshold=0.5, cooldown_seconds=15):
        self.confidence_threshold = confidence_threshold
        self.cooldown_seconds = cooldown_seconds
        self.last_alert_time = 0
        self.active_emergency = None

    def detect_emergency(self, detections):
        candidates = []
        for detection in detections:
            class_name = str(detection.get('class_name', '')).strip().lower()
            confidence = float(detection.get('confidence', 0))
            if class_name in self.EMERGENCY_CLASSES and confidence >= self.confidence_threshold:
                candidates.append(detection)
        if not candidates:
            return None
        best = max(candidates, key=lambda x: float(x.get('confidence', 0)))
        now = time.time()
        if now - self.last_alert_time < self.cooldown_seconds:
            return None
        confidence = float(best.get('confidence', 0))
        self.last_alert_time = now
        alert = {'event_type': 'emergency', 'class_name': best.get('class_name', 'ambulance'), 'confidence': round(confidence, 3), 'severity': 'critical', 'priority_score': 100.0, 'source': 'edge_emergency_intelligence', 'bbox': best.get('bbox'), 'status': 'active', 'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')}
        self.active_emergency = alert
        return alert

    def simulate_emergency(self, class_name='ambulance', confidence=0.96):
        now = time.time()
        if now - self.last_alert_time < self.cooldown_seconds:
            return None
        self.last_alert_time = now
        alert = {'event_type': 'emergency', 'class_name': class_name, 'confidence': round(confidence, 3), 'severity': 'critical', 'priority_score': 100.0, 'source': 'emergency_simulation', 'bbox': None, 'status': 'active', 'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')}
        self.active_emergency = alert
        return alert

    def generate_corridor(self, latitude, longitude):
        return {'status': 'priority_corridor_active', 'center': {'latitude': round(latitude, 6), 'longitude': round(longitude, 6)}, 'radius_meters': 500, 'recommended_action': 'Prioritize emergency vehicle movement through upcoming intersections', 'signal_action': 'REQUEST_PRIORITY', 'corridor_type': 'recommended_emergency_route', 'generated_at': time.strftime('%Y-%m-%dT%H:%M:%S')}

    def process(self, detections, latitude, longitude):
        emergency = self.detect_emergency(detections)
        if emergency is None:
            return None
        emergency['corridor'] = self.generate_corridor(latitude, longitude)
        return emergency

    def get_status(self):
        if self.active_emergency is None:
            return {'active': False, 'priority': 0, 'message': 'No active emergency'}
        return {'active': True, 'priority': 100, 'event': self.active_emergency}

    def clear_emergency(self):
        self.active_emergency = None
        return {'active': False, 'priority': 0, 'message': 'Emergency corridor cleared'}
