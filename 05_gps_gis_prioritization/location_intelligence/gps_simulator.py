from datetime import datetime, timedelta, timezone
import math
from .gps_validator import aware_utc, validate_coordinates

DEFAULT_ROUTE = [(0, 12.9716, 77.5946), (30, 12.9721, 77.5951), (60, 12.9730, 77.5963), (120, 12.9750, 77.5985)]


class GPSSimulator:
    def __init__(self, bus_id="BUS_01", start_time=None, route=None):
        self.bus_id = bus_id
        self.start_time = aware_utc(start_time or datetime.now(timezone.utc))
        self.route = list(route if route is not None else DEFAULT_ROUTE)
        if len(self.route) < 2 or self.route[0][0] != 0:
            raise ValueError("Route needs at least two points starting at video time zero")
        previous = -1
        for seconds, latitude, longitude in self.route:
            if not math.isfinite(seconds) or seconds <= previous:
                raise ValueError("Route times must increase")
            validate_coordinates(latitude, longitude)
            previous = seconds

    def get_location(self, video_time_seconds):
        if not math.isfinite(video_time_seconds) or video_time_seconds < 0:
            raise ValueError("Video time must be finite and nonnegative")
        latitude, longitude = self.route[-1][1:]
        for start, end in zip(self.route, self.route[1:]):
            if video_time_seconds <= end[0]:
                fraction = (video_time_seconds - start[0]) / (end[0] - start[0])
                latitude = start[1] + fraction * (end[1] - start[1])
                longitude = start[2] + fraction * (end[2] - start[2])
                break
        return {"bus_id": self.bus_id, "latitude": round(latitude, 7), "longitude": round(longitude, 7),
                "gps_timestamp": (self.start_time + timedelta(seconds=video_time_seconds)).isoformat(), "location_source": "simulated"}
