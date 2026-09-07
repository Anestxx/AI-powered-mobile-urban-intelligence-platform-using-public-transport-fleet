from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    BASE_DIR /
    "training" /
    "runs" /
    "pothole_yolo11s" /
    "weights" /
    "best.pt"
)

DATA_YAML = BASE_DIR / "training" / "data.yaml"

print("=" * 60)
print("POTHOLE MODEL VALIDATION")
print("=" * 60)

if not MODEL_PATH.exists():
    print("ERROR: best.pt was not found.")
    print(f"Expected: {MODEL_PATH}")
    raise SystemExit(1)

model = YOLO(str(MODEL_PATH))

print(f"Model   : {MODEL_PATH}")
print(f"Dataset : {DATA_YAML}")

metrics = model.val(
    data=str(DATA_YAML),
    imgsz=960,
    split="test",
    device=0
)

print("\n" + "=" * 60)
print("VALIDATION RESULTS")
print("=" * 60)

print(f"mAP50      : {metrics.box.map50:.4f}")
print(f"mAP50-95   : {metrics.box.map:.4f}")
print(f"Precision  : {metrics.box.mp:.4f}")
print(f"Recall     : {metrics.box.mr:.4f}")

print("=" * 60)