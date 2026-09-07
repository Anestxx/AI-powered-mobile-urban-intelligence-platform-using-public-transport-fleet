from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"

folders = [
    DATASET_DIR / "images/train",
    DATASET_DIR / "images/val",
    DATASET_DIR / "images/test",
    DATASET_DIR / "labels/train",
    DATASET_DIR / "labels/val",
    DATASET_DIR / "labels/test",
]

for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)

print("Dataset structure verified.")
print(f"Dataset location: {DATASET_DIR}")