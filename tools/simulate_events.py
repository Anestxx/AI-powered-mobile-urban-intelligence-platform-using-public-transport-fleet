"""Exercise observation retries, spatial matching and heartbeats with simulated data."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4
import requests

ROOT = Path(__file__).resolve().parents[1]


def run_scenario(base_url):
    data = json.loads((ROOT / "contracts/fixtures/demo.json").read_text(encoding="utf-8"))
    session = requests.Session()
    base_url = base_url.rstrip("/")

    def request(method, path, payload=None):
        response = session.request(method, base_url + path, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    observations = data["observations"]
    now = datetime.now(timezone.utc).isoformat()
    for observation in observations:
        observation.update(event_id=str(uuid4()), timestamp=now, gps_timestamp=now, model_version="event_simulator_v2")
    try:
        first = request("POST", "/api/alerts", observations[0])
        before = request("GET", f"/api/alerts/{first['issue_id']}")["report_count"]
        retry = request("POST", "/api/alerts", observations[0])
        if not retry["duplicate"] or retry["issue_id"] != first["issue_id"]:
            raise RuntimeError("Duplicate event was not acknowledged correctly")
        if request("GET", f"/api/alerts/{first['issue_id']}")["report_count"] != before:
            raise RuntimeError("Retry changed report count")
        second = request("POST", "/api/alerts", observations[1])
        distant = request("POST", "/api/alerts", observations[2])
        if second["issue_id"] != first["issue_id"] or distant["issue_id"] == first["issue_id"]:
            raise RuntimeError("Nearby/distant matching did not follow the contract")
        combined = request("GET", f"/api/alerts/{first['issue_id']}")
        if combined["report_count"] != before + 1:
            raise RuntimeError("Second observation was not counted once")
        for observation in observations:
            request("POST", f"/api/buses/{observation['bus_id']}/heartbeat", {"timestamp": datetime.now(timezone.utc).isoformat(), "camera_status": "online", "ai_status": "online", "latitude": observation["latitude"], "longitude": observation["longitude"], "location_source": "simulated"})
        print(f"PASS: retry did not add a report; two nearby buses matched {first['issue_id']}")
        print(f"PASS: distant report matched separate issue {distant['issue_id']}")
        print(f"PASS: heartbeats sent; combined reports={combined['report_count']}, priority={combined['priority']}")
        print("This scenario demonstrates backend integration with simulated observations, not AI inference.")
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    try:
        run_scenario(args.backend_url)
    except (requests.RequestException, RuntimeError, KeyError) as exc:
        parser.exit(1, f"Scenario failed: {exc}\n")


if __name__ == "__main__":
    main()
