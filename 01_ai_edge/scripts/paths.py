"""Asset locations independent of the terminal's current directory."""

from pathlib import Path

EDGE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EDGE_DIR.parent
VIDEO_PATH = EDGE_DIR / "videos" / "road_test.mp4"
RAD_MODEL_PATH = EDGE_DIR / "models" / "best.pt"
POTHOLE_MODEL_PATH = EDGE_DIR / "models" / "pothole.pt"
GENERAL_MODEL_PATH = EDGE_DIR / "models" / "yolo11n.pt"
EMERGENCY_MODEL_PATH = EDGE_DIR / "models" / "emergency.pt"
AMBULANCE_VIDEO_PATH = EDGE_DIR / "videos" / "ambulance_test.mp4"
ALERTS_PATH = EDGE_DIR / "alerts" / "alerts.json"


def existing_file(value):
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    return path
