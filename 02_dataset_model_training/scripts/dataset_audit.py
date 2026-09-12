from pathlib import Path
from PIL import Image
from collections import Counter
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

print("=" * 70)
print("CODYSSEY DATASET AUDIT")
print("=" * 70)

splits = ["train", "val", "test"]

total_images = 0
total_labels = 0
total_boxes = 0
class_counter = Counter()
errors = []

for split in splits:
    image_dir = DATASET_DIR / "images" / split
    label_dir = DATASET_DIR / "labels" / split

    images = [
        p for p in image_dir.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]

    labels = list(label_dir.glob("*.txt"))

    print(f"\n[{split.upper()}]")
    print(f"Images : {len(images)}")
    print(f"Labels : {len(labels)}")

    total_images += len(images)
    total_labels += len(labels)

    image_stems = {p.stem for p in images}
    label_stems = {p.stem for p in labels}

    missing_labels = image_stems - label_stems
    orphan_labels = label_stems - image_stems

    if missing_labels:
        print(f"WARNING: {len(missing_labels)} images have no labels")

    if orphan_labels:
        print(f"WARNING: {len(orphan_labels)} labels have no image")

    for image_path in images:
        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception as e:
            errors.append((str(image_path), str(e)))

    for label_path in labels:
        try:
            with open(label_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            for line_number, line in enumerate(lines, 1):
                parts = line.split()

                if len(parts) != 5:
                    errors.append(
                        (str(label_path),
                         f"Line {line_number}: expected 5 values")
                    )
                    continue

                cls, x, y, w, h = map(float, parts)

                if cls != int(cls):
                    errors.append(
                        (str(label_path),
                         f"Line {line_number}: invalid class")
                    )
                    continue

                cls = int(cls)

                if not (0 <= x <= 1 and
                        0 <= y <= 1 and
                        0 < w <= 1 and
                        0 < h <= 1):
                    errors.append(
                        (str(label_path),
                         f"Line {line_number}: invalid YOLO coordinates")
                    )
                    continue

                class_counter[cls] += 1
                total_boxes += 1

        except Exception as e:
            errors.append((str(label_path), str(e)))

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print(f"Total images : {total_images}")
print(f"Total labels : {total_labels}")
print(f"Total boxes  : {total_boxes}")

print("\nClass distribution:")

if class_counter:
    for cls, count in sorted(class_counter.items()):
        print(f"  Class {cls}: {count}")
else:
    print("  No annotations found.")

print("\nImage/label errors:")

if errors:
    for path, error in errors[:30]:
        print(f"  {path}")
        print(f"    {error}")

    if len(errors) > 30:
        print(f"  ... and {len(errors) - 30} more errors")
else:
    print("  None")

print("\nDataset location:")
print(DATASET_DIR)

print("=" * 70)

if total_images == 0:
    print("\n❌ DATASET EMPTY")
    print("Add/import the dataset before training.")

elif total_boxes == 0:
    print("\n❌ NO ANNOTATIONS")
    print("Images exist, but YOLO labels are missing.")

elif errors:
    print("\n⚠️ DATASET HAS ERRORS")
    print("Fix the reported problems before training.")

else:
    print("\n✅ DATASET PASSED BASIC AUDIT")