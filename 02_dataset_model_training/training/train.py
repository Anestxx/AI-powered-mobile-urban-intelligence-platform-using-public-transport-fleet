from pathlib import Path
from ultralytics import YOLO
import torch

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_YAML = BASE_DIR / "training" / "data.yaml"

MODEL = "yolo11s.pt"

PROJECT_DIR = BASE_DIR / "training" / "runs"

EPOCHS = 80
IMAGE_SIZE = 960
BATCH_SIZE = 16
WORKERS = 4

print("=" * 60)
print("POTHOLE DETECTION TRAINING")
print("=" * 60)

print(f"Dataset config : {DATA_YAML}")
print(f"Base model     : {MODEL}")
print(f"Epochs         : {EPOCHS}")
print(f"Image size     : {IMAGE_SIZE}")
print(f"Batch size     : {BATCH_SIZE}")

if torch.cuda.is_available():
    device = 0
    print(f"Device         : {torch.cuda.get_device_name(0)}")
else:
    device = "cpu"
    print("WARNING: CUDA unavailable. Training on CPU.")

print("=" * 60)

model = YOLO(MODEL)

results = model.train(
    data=str(DATA_YAML),

    epochs=EPOCHS,

    imgsz=IMAGE_SIZE,

    batch=BATCH_SIZE,

    device=device,

    workers=WORKERS,

    project=str(PROJECT_DIR),

    name="pothole_yolo11s",

    exist_ok=True,

    pretrained=True,

    optimizer="auto",

    patience=15,

    cache=False,

    amp=True,

    cos_lr=True,

    close_mosaic=10,

    degrees=5.0,

    translate=0.10,

    scale=0.50,

    fliplr=0.50,

    hsv_h=0.015,

    hsv_s=0.50,

    hsv_v=0.40,
)

print("\nTraining completed.")

print("Best model should be located at:")

print(
    PROJECT_DIR /
    "pothole_yolo11s" /
    "weights" /
    "best.pt"
)