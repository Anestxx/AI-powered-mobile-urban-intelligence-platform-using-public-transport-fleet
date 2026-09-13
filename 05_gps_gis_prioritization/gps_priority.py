import math
import time


class GPSSimulator:

    def __init__(
        self,
        start_lat=12.9716,
        start_lon=77.5946
    ):

        self.latitude = start_lat
        self.longitude = start_lon

    def get_location(self):

        return {
            "latitude": round(
                self.latitude,
                6
            ),
            "longitude": round(
                self.longitude,
                6
            )
        }

    def move(
        self,
        delta_lat=0.00005,
        delta_lon=0.00005
    ):

        self.latitude += delta_lat
        self.longitude += delta_lon

        return self.get_location()


class PriorityEngine:

    EVENT_BASE_PRIORITY = {
        "emergency": 100,
        "pothole": 85,
        "road_damage": 75,
        "unsafe_behaviour": 70,
        "road_infrastructure": 55,
        "traffic": 35
    }

    def calculate(
        self,
        event_type,
        confidence,
        bus_count=1
    ):

        base = self.EVENT_BASE_PRIORITY.get(
            event_type,
            30
        )

        confidence_bonus = confidence * 15

        bus_bonus = min(
            (bus_count - 1) * 10,
            20
        )

        score = (
            base
            + confidence_bonus
            + bus_bonus
        )

        return min(
            round(score, 1),
            100
        )

    def severity(
        self,
        event_type,
        priority
    ):

        if event_type == "emergency":
            return "critical"

        if priority >= 80:
            return "high"

        if priority >= 50:
            return "medium"

        return "low"