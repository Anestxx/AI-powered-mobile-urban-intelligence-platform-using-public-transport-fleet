import math
from .gps_validator import validate_coordinates


def distance_meters(lat1, lon1, lat2, lon2):
    validate_coordinates(lat1, lon1)
    validate_coordinates(lat2, lon2)
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(min(1.0, max(0.0, a))))
