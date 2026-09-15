"""Conservative bounds for a great-circle distance query; exact distance follows."""
import math
from .gps_validator import validate_coordinates


def search_bounds(latitude, longitude, radius_m):
    validate_coordinates(latitude, longitude)
    if not isinstance(radius_m, (int, float)) or not math.isfinite(radius_m) or radius_m < 0:
        raise ValueError("Search radius must be finite and nonnegative")
    # The one-millimetre margin prevents roundoff from excluding boundary points.
    angular = (radius_m + .001) / 6371000
    delta_lat = math.degrees(angular)
    lower_lat, upper_lat = max(-90, latitude - delta_lat), min(90, latitude + delta_lat)
    if lower_lat <= -90 or upper_lat >= 90:
        return lower_lat, upper_lat, [(-180, 180)]
    delta_lon = math.degrees(math.asin(min(1, math.sin(angular) / math.cos(math.radians(latitude)))))
    centre = (longitude + 180) % 360 - 180
    lower_lon, upper_lon = centre - delta_lon, centre + delta_lon
    if lower_lon < -180:
        intervals = [(lower_lon + 360, 180), (-180, upper_lon)]
    elif upper_lon > 180:
        intervals = [(lower_lon, 180), (-180, upper_lon - 360)]
    else:
        intervals = [(lower_lon, upper_lon)]
    return lower_lat, upper_lat, intervals
