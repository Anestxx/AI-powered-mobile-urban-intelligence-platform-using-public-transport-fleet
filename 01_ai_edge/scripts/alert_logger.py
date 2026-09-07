import json
import os


class AlertLogger:

    def __init__(self, output_file="alerts/alerts.json"):
        self.output_file = output_file

        os.makedirs(
            os.path.dirname(output_file),
            exist_ok=True
        )

        if not os.path.exists(self.output_file):
            with open(self.output_file, "w") as f:
                json.dump([], f, indent=4)

    def save_alert(self, alert):

        with open(self.output_file, "r") as f:
            alerts = json.load(f)

        alerts.append(alert)

        with open(self.output_file, "w") as f:
            json.dump(alerts, f, indent=4)

        print("Alert saved.")