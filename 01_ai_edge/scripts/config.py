from paths import EDGE_DIR, POTHOLE_MODEL_PATH, VIDEO_PATH
import os
from pathlib import Path

environment_file = EDGE_DIR / ".env"
if environment_file.is_file():
    for line in environment_file.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() and not key.lstrip().startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))

MODEL_PATH = Path(os.environ.get("CODYSSEY_MODEL_PATH", str(POTHOLE_MODEL_PATH)))
CONFIDENCE_THRESHOLD = float(os.environ.get("CODYSSEY_CONFIDENCE", "0.70"))  # Provisional; requires holdout evaluation.
IMAGE_SIZE = 640
FRAME_INTERVAL = 3
REQUIRED_DETECTIONS = 3
MAX_MISSING_FRAMES = 5
COOLDOWN_SECONDS = 5.0
BACKEND_URL = os.environ.get("CODYSSEY_BACKEND_URL", "http://127.0.0.1:8000")
HEARTBEAT_SECONDS = 10
OUTBOX_PATH = EDGE_DIR / "alerts" / "outbox.db"
BUS_ID = os.environ.get("CODYSSEY_BUS_ID", "BUS_01")
