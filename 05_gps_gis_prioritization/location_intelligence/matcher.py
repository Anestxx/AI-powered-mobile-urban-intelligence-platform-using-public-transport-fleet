from .config import MATCH_RADIUS_METERS
from .distance import distance_meters
from .gps_validator import validate_coordinates


def match_issue(observation, candidate_issues, radius_meters=MATCH_RADIUS_METERS):
    validate_coordinates(observation["latitude"], observation["longitude"])
    if radius_meters <= 0:
        raise ValueError("Matching radius must be positive")
    matches = []
    for issue in candidate_issues:
        if issue["status"] != "open" or issue["event_type"] != observation["event_type"] or issue["location_source"] != observation["location_source"]:
            continue
        distance = distance_meters(observation["latitude"], observation["longitude"], issue["latitude"], issue["longitude"])
        if distance <= radius_meters:
            matches.append((distance, issue["issue_id"]))
    if not matches:
        return {"matched_issue_id": None, "distance_m": None, "match_reason": "no_suitable_candidate"}
    distance, issue_id = min(matches)
    return {"matched_issue_id": issue_id, "distance_m": round(distance, 2), "match_reason": "same_type_within_demo_radius"}
