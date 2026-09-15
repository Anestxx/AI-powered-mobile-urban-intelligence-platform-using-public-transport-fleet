"""Check pothole image/label pairs and YOLO annotations; optionally verify images."""

import argparse
from collections import Counter
import math
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def validate_dataset(dataset, verify_images=False, class_count=1):
    errors = []
    classes = Counter()
    total = 0
    for split in ("train", "val", "test"):
        image_dir, label_dir = dataset / "images" / split, dataset / "labels" / split
        if not image_dir.is_dir() or not label_dir.is_dir():
            errors.append(f"{split}: missing images or labels folder")
            continue
        images = [p for p in image_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        labels = list(label_dir.glob("*.txt"))
        total += len(images)
        print(f"{split}: {len(images)} images, {len(labels)} labels")
        if not images:
            errors.append(f"{split}: no images")
        image_stems, label_stems = {p.stem for p in images}, {p.stem for p in labels}
        errors.extend(f"{split}: missing label for {stem}" for stem in sorted(image_stems - label_stems))
        errors.extend(f"{split}: orphan label {stem}" for stem in sorted(label_stems - image_stems))
        for label in labels:
            try:
                for line_no, line in enumerate(label.read_text(encoding="utf-8").splitlines(), 1):
                    if not line.strip():
                        continue  # Empty labels are valid background images.
                    values = [float(value) for value in line.split()]
                    if len(values) != 5 or not all(math.isfinite(value) for value in values):
                        raise ValueError(f"line {line_no}: expected five finite numbers")
                    cls, x, y, width, height = values
                    if not cls.is_integer() or not 0 <= cls < class_count:
                        raise ValueError(f"line {line_no}: invalid class ID {cls}")
                    if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < width <= 1 and 0 < height <= 1):
                        raise ValueError(f"line {line_no}: invalid normalized bounding box")
                    classes[int(cls)] += 1
            except (OSError, ValueError) as exc:
                errors.append(f"{label}: {exc}")
        if verify_images:
            from PIL import Image
            for path in images:
                try:
                    with Image.open(path) as image:
                        image.verify()
                except (OSError, ValueError) as exc:
                    errors.append(f"{path}: {exc}")
    if not classes:
        errors.append("No annotated objects found; import labeled pothole data before training.")
    print(f"Total: {total} images, {sum(classes.values())} boxes; classes: {dict(sorted(classes.items()))}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_DIR)
    parser.add_argument("--verify-images", action="store_true", help="Also check image file integrity")
    args = parser.parse_args()
    errors = validate_dataset(args.dataset, args.verify_images)
    for error in errors[:30]:
        print(f"ERROR: {error}")
    if errors:
        print(f"Dataset check failed: {len(errors)} errors.")
        return 1
    print("Dataset check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
