"""Shared-backend operator operations, independent of the video UI."""
from queue import Empty, Queue
import threading
import time
from urllib.parse import quote
import requests


class OperatorError(Exception):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class OperatorClient:
    def __init__(self, base_url, session=None, timeout=2):
        self.base_url = base_url.rstrip("/")
        self.session = session if session is not None else requests.Session()
        self.timeout = timeout

    def request(self, method, path, **kwargs):
        try:
            response = self.session.request(method, self.base_url + "/api" + path, timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise OperatorError("Cannot reach the backend. Start it and use Refresh.") from exc
        try:
            data = response.json()
        except ValueError as exc:
            raise OperatorError("The backend returned an unreadable response.", response.status_code) from exc
        if not 200 <= response.status_code < 300:
            detail = data.get("detail") if isinstance(data, dict) else None
            raise OperatorError(detail if isinstance(detail, str) else "The request failed.", response.status_code)
        if not isinstance(data, dict):
            raise OperatorError("The backend returned an unexpected response.", response.status_code)
        return data

    def snapshot(self, status="", page=1):
        params = {"page": page, "page_size": 10}
        if status:
            params["status"] = status
        return {"statistics": self.request("GET", "/statistics"),
                "alerts": self.request("GET", "/alerts", params=params),
                "authenticated": self.request("GET", "/auth/session")["authenticated"]}

    def details(self, issue_id):
        return self.request("GET", "/alerts/" + quote(issue_id, safe=""))

    def login(self, password):
        return self.request("POST", "/auth/login", json={"password": password})

    def logout(self):
        return self.request("POST", "/auth/logout")

    def resolve(self, issue_id, note="", status="resolved", expected_status=None):
        payload = {"status": status, "note": note}
        if expected_status is not None:
            payload["expected_status"] = expected_status
        result = self.request("PATCH", "/alerts/" + quote(issue_id, safe="") + "/status", json=payload)
        if result.get("issue_id") != issue_id or result.get("status") != status:
            raise OperatorError("The backend did not confirm resolution. Refresh the issue before retrying.")
        return result

    def evidence(self, event_id):
        try:
            response = self.session.get(self.base_url + "/api/observations/" + quote(event_id, safe="") + "/evidence", timeout=self.timeout)
            response.raise_for_status()
            if not response.headers.get("content-type", "").startswith("image/jpeg") or len(response.content) > 192 * 1024:
                raise OperatorError("The evidence response was not a supported JPEG")
            return response.content
        except requests.RequestException as exc:
            raise OperatorError("Could not load saved evidence. Refresh and try again.") from exc


class OperatorSync:
    """A single network thread; the UI consumes messages without blocking playback."""
    def __init__(self, client):
        self.client = client
        self.commands, self.messages = Queue(), Queue()
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True, name="codyssey-operator")

    def start(self):
        self.thread.start()

    def submit(self, action, **payload):
        self.commands.put((action, payload))

    def run(self):
        view = {"status": "", "page": 1, "version": 0}
        next_poll = 0
        while not self.stopped.is_set():
            try:
                action, payload = self.commands.get(timeout=.1)
            except Empty:
                action, payload = None, {}
            try:
                if action == "refresh":
                    view = payload
                    next_poll = 0
                elif action in ("login", "logout", "resolve", "details", "evidence"):
                    value = getattr(self.client, action)(**payload)
                    self.messages.put({"kind": action, "data": value, "issue_id": payload.get("issue_id"), "event_id": payload.get("event_id")})
                    if action not in ("details", "evidence"):
                        next_poll = 0
            except OperatorError as exc:
                self.messages.put({"kind": "action_error", "action": action, "issue_id": payload.get("issue_id"), "error": str(exc), "status": exc.status})
            if time.monotonic() >= next_poll and not self.stopped.is_set():
                try:
                    value = self.client.snapshot(view["status"], view["page"])
                    self.messages.put({"kind": "snapshot", "data": value, "view": dict(view)})
                except OperatorError as exc:
                    self.messages.put({"kind": "poll_error", "error": str(exc)})
                next_poll = time.monotonic() + 2
        self.client.session.close()

    def stop(self):
        self.stopped.set()
        self.thread.join(timeout=.5)
