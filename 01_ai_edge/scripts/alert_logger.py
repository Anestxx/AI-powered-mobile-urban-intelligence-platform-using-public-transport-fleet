"""Persist alert metadata without saving camera frames."""

import json
from pathlib import Path

from paths import ALERTS_PATH


class AlertLogger:
    def __init__(self, output_file=ALERTS_PATH):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.output_file.exists():
            self.output_file.write_text("[]\n", encoding="utf-8")

    def save_alert(self, alert):
        alerts = json.loads(self.output_file.read_text(encoding="utf-8"))
        if not isinstance(alerts, list):
            raise ValueError(f"Expected an alert list in {self.output_file}")
        alerts.append(alert)
        temporary = self.output_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(alerts, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.output_file)
