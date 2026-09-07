from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

splits = ["train", "val", "test"]

print("=" * 60)
print("POTHOLE DATASET VALIDATION")
print("=" * 60)

total_images = 0
total_labels = 0

for split in splits:
    image_dir = DATASET_DIR / "images" / split
    label_dir = DATASET_DIR / "labels" / split

    images = [
        f for f in image_dir.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]

    labels = [
        f for f in label_dir.iterdir()
        if f.is_file() and f.suffix.lower() == ".txt"
    ]

    total_images += len(images)
    total_labels += len(labels)

    image_names = {f.stem for f in images}
    label_names = {f.stem for f in labels}

    missing_labels = image_names - label_names
    missing_images = label_names - image_names

    print(f"\n[{split.upper()}]")
    print(f"Images : {len(images)}")
    print(f"Labels : {len(labels)}")

    if missing_labels:
        print(f"WARNING: {len(missing_labels)} images have no labels")

    if missing_images:
        print(f"WARNING: {len(missing_images)} labels have no images")

print("\n" + "=" * 60)
print(f"TOTAL IMAGES : {total_images}")
print(f"TOTAL LABELS : {total_labels}")
print("=" * 60)

if total_images == 0:
    print("\nDataset is currently empty.")
    print("Add the dataset on the NVIDIA training machine.")
else:
    print("\nDataset validation completed.")