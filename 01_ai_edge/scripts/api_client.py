import requests


class ApiClient:
    def __init__(self, base_url, timeout=2):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def send_observation(self, observation):
        return requests.post(f"{self.base_url}/api/alerts", json=observation, timeout=self.timeout)

    def heartbeat(self, bus_id, telemetry):
        return requests.post(f"{self.base_url}/api/buses/{bus_id}/heartbeat", json=telemetry, timeout=self.timeout)
