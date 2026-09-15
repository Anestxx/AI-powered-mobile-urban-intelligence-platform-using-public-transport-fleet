from datetime import datetime, timezone
import math


def aware_utc(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if not isinstance(result, datetime) or result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamp must include its timezone")
    return result.astimezone(timezone.utc)


def validate_coordinates(latitude, longitude):
    for value, bound, label in ((latitude, 90, "latitude"), (longitude, 180, "longitude")):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not -bound <= value <= bound:
            raise ValueError(f"Invalid or missing {label}")
    return float(latitude), float(longitude)


def validate_location(location, detection_timestamp, tolerance_seconds=5):
    validate_coordinates(location.get("latitude"), location.get("longitude"))
    if location.get("location_source") not in {"simulated", "gps"}:
        raise ValueError("Location source must be simulated or gps")
    gps_time = aware_utc(location.get("gps_timestamp"))
    if abs((gps_time - aware_utc(detection_timestamp)).total_seconds()) > tolerance_seconds:
        raise ValueError("GPS timestamp is stale relative to detection time")
    return location
