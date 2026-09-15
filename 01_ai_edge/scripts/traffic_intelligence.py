"""Prototype rule module retained from 47cba0f; not connected to live alert delivery."""
import time

class TrafficIntelligence:
    """
    Converts raw vehicle detections into traffic intelligence.

    This module does NOT simply count cars.
    It estimates:
        - vehicle count
        - pedestrian count
        - traffic index
        - traffic level
        - congestion state
        - congestion confidence

    It keeps short-term history so that one crowded frame
    does not immediately become a congestion alert.
    """
    VEHICLE_CLASSES = {'HMV', 'LMV'}
    PEDESTRIAN_CLASS = 'Pedestrian'

    def __init__(self, congestion_index_threshold=60, congestion_vehicle_threshold=6, required_observations=3, persistence_window=6, cooldown_seconds=15):
        self.congestion_index_threshold = congestion_index_threshold
        self.congestion_vehicle_threshold = congestion_vehicle_threshold
        self.required_observations = required_observations
        self.persistence_window = persistence_window
        self.cooldown_seconds = cooldown_seconds
        self.history = []
        self.last_congestion_alert = 0

    def count_objects(self, detections):
        vehicle_count = 0
        hmv_count = 0
        lmv_count = 0
        pedestrian_count = 0
        for detection in detections:
            class_name = detection.get('class_name')
            if class_name == 'HMV':
                hmv_count += 1
            elif class_name == 'LMV':
                lmv_count += 1
            elif class_name == 'Pedestrian':
                pedestrian_count += 1
        vehicle_count = hmv_count + lmv_count
        return {'vehicle_count': vehicle_count, 'hmv_count': hmv_count, 'lmv_count': lmv_count, 'pedestrian_count': pedestrian_count}

    def calculate_index(self, counts):
        vehicle_count = counts['vehicle_count']
        pedestrian_count = counts['pedestrian_count']
        hmv_score = counts['hmv_count'] * 14
        lmv_score = counts['lmv_count'] * 9
        pedestrian_score = pedestrian_count * 3
        index = hmv_score + lmv_score + pedestrian_score
        return min(int(index), 100)

    def classify_level(self, traffic_index):
        if traffic_index >= 80:
            return 'severe'
        if traffic_index >= 60:
            return 'high'
        if traffic_index >= 35:
            return 'moderate'
        return 'low'

    def analyze(self, detections):
        counts = self.count_objects(detections)
        traffic_index = self.calculate_index(counts)
        traffic_level = self.classify_level(traffic_index)
        now = time.time()
        observation = {'timestamp': now, 'vehicle_count': counts['vehicle_count'], 'hmv_count': counts['hmv_count'], 'lmv_count': counts['lmv_count'], 'pedestrian_count': counts['pedestrian_count'], 'traffic_index': traffic_index, 'traffic_level': traffic_level}
        self.history.append(observation)
        self.history = [item for item in self.history if now - item['timestamp'] <= self.persistence_window]
        recent = self.history[-self.required_observations:]
        avg_index = sum((item['traffic_index'] for item in recent)) / len(recent) if recent else 0
        avg_vehicle_count = sum((item['vehicle_count'] for item in recent)) / len(recent) if recent else 0
        congestion_observations = sum((1 for item in recent if item['traffic_index'] >= self.congestion_index_threshold or item['vehicle_count'] >= self.congestion_vehicle_threshold))
        congestion_confirmed = len(recent) >= self.required_observations and congestion_observations >= self.required_observations
        if congestion_confirmed:
            persistence_score = congestion_observations / max(len(recent), 1)
            density_score = min(avg_index / 100, 1.0)
            congestion_confidence = persistence_score * 0.6 + density_score * 0.4
        else:
            congestion_confidence = min(avg_index / 150, 0.6)
        can_alert = now - self.last_congestion_alert >= self.cooldown_seconds
        congestion_alert = None
        if congestion_confirmed and can_alert:
            severity = 'high'
            if avg_index >= 80:
                severity = 'critical'
            congestion_alert = {'event_type': 'traffic', 'class_name': 'congestion', 'confidence': round(congestion_confidence, 3), 'severity': severity, 'traffic_index': round(avg_index, 1), 'traffic_level': 'severe' if avg_index >= 80 else 'high', 'vehicle_count': round(avg_vehicle_count), 'pedestrian_count': round(sum((item['pedestrian_count'] for item in recent)) / len(recent)), 'source': 'edge_traffic_intelligence'}
            self.last_congestion_alert = now
        return {'vehicle_count': counts['vehicle_count'], 'hmv_count': counts['hmv_count'], 'lmv_count': counts['lmv_count'], 'pedestrian_count': counts['pedestrian_count'], 'traffic_index': traffic_index, 'traffic_level': traffic_level, 'average_traffic_index': round(avg_index, 1), 'average_vehicle_count': round(avg_vehicle_count, 1), 'congestion_confirmed': congestion_confirmed, 'congestion_confidence': round(congestion_confidence, 3), 'alert': congestion_alert}

    def get_status(self):
        if not self.history:
            return {'traffic_index': 0, 'traffic_level': 'low', 'vehicle_count': 0, 'congestion_confirmed': False}
        latest = self.history[-1]
        return {'traffic_index': latest['traffic_index'], 'traffic_level': latest['traffic_level'], 'vehicle_count': latest['vehicle_count'], 'pedestrian_count': latest['pedestrian_count'], 'congestion_confirmed': latest['traffic_index'] >= self.congestion_index_threshold}
