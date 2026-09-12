from pathlib import Path
import torch
from ultralytics import YOLO


# ============================================================
# CODYSSEY - ROAD INTELLIGENCE MODEL TRAINING
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_YAML = BASE_DIR / "training" / "data.yaml"
RUNS_DIR = BASE_DIR / "training" / "runs"

MODEL_NAME = "yolo11s.pt"

# ------------------------------------------------------------
# TRAINING CONFIGURATION
# ------------------------------------------------------------

EPOCHS = 30

# 640 first because we are NOT using NVIDIA GPU.
# We can run a higher-resolution experiment later.
IMAGE_SIZE = 640

# CPU-friendly batch size.
BATCH_SIZE = 4

# CPU-friendly worker count.
WORKERS = 2

CONFIDENCE = 0.25


# ============================================================
# DEVICE DETECTION
# ============================================================

if torch.cuda.is_available():
    DEVICE = 0
    DEVICE_NAME = torch.cuda.get_device_name(0)

    print(f"GPU detected: {DEVICE_NAME}")
    print(f"CUDA version: {torch.version.cuda}")

else:
    DEVICE = "cpu"
    DEVICE_NAME = "CPU"

    print("No CUDA GPU detected.")
    print("Training will run on CPU.")


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("CODYSSEY ROAD INTELLIGENCE TRAINING")
print("=" * 70)

print(f"Dataset config : {DATA_YAML}")
print(f"Base model     : {MODEL_NAME}")
print(f"Epochs         : {EPOCHS}")
print(f"Image size     : {IMAGE_SIZE}")
print(f"Batch size     : {BATCH_SIZE}")
print(f"Workers        : {WORKERS}")
print(f"Device         : {DEVICE_NAME}")
print("=" * 70)


if not DATA_YAML.exists():
    raise FileNotFoundError(
        f"\nDataset configuration not found:\n{DATA_YAML}"
    )


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading YOLO11s...")

model = YOLO(MODEL_NAME)

print("Model loaded successfully.")


# ============================================================
# TRAIN
# ============================================================

results = model.train(

    # Dataset
    data=str(DATA_YAML),

    # Training duration
    epochs=EPOCHS,

    # Resolution
    imgsz=IMAGE_SIZE,

    # Hardware
    device=DEVICE,

    # Batch
    batch=BATCH_SIZE,

    # Workers
    workers=WORKERS,

    # Output
    project=str(RUNS_DIR),
    name="codyssey_road_v1",
    exist_ok=True,

    # Pretrained weights
    pretrained=True,

    # Optimizer
    optimizer="auto",

    # Stop if validation stops improving
    patience=12,

    # Don't cache entire dataset in RAM
    cache=False,

    # Disable AMP on CPU.
    # Ultralytics can handle AMP on GPU, but CPU training
    # does not benefit from it in the same way.
    amp=False,

    # Learning-rate scheduling
    cos_lr=True,

    # Mosaic augmentation
    close_mosaic=10,

    # Geometric augmentation
    degrees=5.0,
    translate=0.10,
    scale=0.50,

    # Horizontal flip
    fliplr=0.50,

    # Color augmentation
    hsv_h=0.015,
    hsv_s=0.50,
    hsv_v=0.40,

    # Prevent excessive verbose output
    verbose=True,
)


# ============================================================
# TRAINING COMPLETE
# ============================================================

BEST_MODEL = (
    RUNS_DIR
    / "codyssey_road_v1"
    / "weights"
    / "best.pt"
)

LAST_MODEL = (
    RUNS_DIR
    / "codyssey_road_v1"
    / "weights"
    / "last.pt"
)


print("\n" + "=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)

print(f"Best model:")
print(BEST_MODEL)

print(f"\nLast checkpoint:")
print(LAST_MODEL)

if BEST_MODEL.exists():
    print("\n✅ best.pt successfully created.")
else:
    print("\n❌ best.pt was not found.")

print("=" * 70)