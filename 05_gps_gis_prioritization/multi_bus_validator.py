import math
import time


class MultiBusValidator:

    def __init__(
        self,
        distance_threshold_m=50,
        time_window_seconds=300
    ):

        self.distance_threshold_m = (
            distance_threshold_m
        )

        self.time_window_seconds = (
            time_window_seconds
        )

        self.events = []

    def haversine_distance(
        self,
        lat1,
        lon1,
        lat2,
        lon2
    ):

        R = 6371000

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)

        dphi = math.radians(
            lat2 - lat1
        )

        dlambda = math.radians(
            lon2 - lon1
        )

        a = (
            math.sin(dphi / 2) ** 2
            +
            math.cos(phi1)
            * math.cos(phi2)
            * math.sin(dlambda / 2) ** 2
        )

        return (
            2
            * R
            * math.atan2(
                math.sqrt(a),
                math.sqrt(1 - a)
            )
        )

    def add_event(
        self,
        event
    ):

        now = time.time()

        latitude = event.get(
            "latitude"
        )

        longitude = event.get(
            "longitude"
        )

        event_type = event.get(
            "event_type"
        )

        bus_id = event.get(
            "bus_id"
        )

        if latitude is None or longitude is None:
            return event

        # Remove old events
        self.events = [
            e
            for e in self.events
            if now - e["_time"]
            <= self.time_window_seconds
        ]

        matching_buses = set()

        for existing in self.events:

            if existing["event_type"] != event_type:
                continue

            if existing["bus_id"] == bus_id:
                continue

            distance = self.haversine_distance(
                latitude,
                longitude,
                existing["latitude"],
                existing["longitude"]
            )

            if distance <= self.distance_threshold_m:

                matching_buses.add(
                    existing["bus_id"]
                )

        matching_buses.add(bus_id)

        bus_count = len(
            matching_buses
        )

        event["cross_bus_validation"] = {
            "bus_count": bus_count,
            "buses": list(matching_buses),
            "validated": bus_count >= 2,
            "method": "multi_bus_spatial_corroboration"
        }

        # Store internally only.
        # No image/frame is stored.
        self.events.append({
            "event_type": event_type,
            "latitude": latitude,
            "longitude": longitude,
            "bus_id": bus_id,
            "_time": now
        })

        return event