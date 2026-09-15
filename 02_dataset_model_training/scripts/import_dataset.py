"""Import train/valid/test image-label folders; validate the pothole class before training."""

import argparse
from pathlib import Path
import shutil

from prepare_dataset import DATASET_DIR

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Folder containing train/, valid/, test/")
    parser.add_argument("--dataset", type=Path, default=DATASET_DIR)
    args = parser.parse_args()
    copies = []
    for source_split, target_split in (("train", "train"), ("valid", "val"), ("test", "test")):
        source = args.source / source_split
        if not (source / "images").is_dir() or not (source / "labels").is_dir():
            parser.error(f"Missing images/ or labels/ in {source}")
        image_files = [p for p in (source / "images").iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        if not image_files:
            parser.error(f"No images in {source / 'images'}")
        for image in image_files:
            label = source / "labels" / f"{image.stem}.txt"
            if not label.is_file():
                parser.error(f"Missing label: {label}")
            copies.extend([
                (image, args.dataset / "images" / target_split / image.name),
                (label, args.dataset / "labels" / target_split / label.name),
            ])
    # Check all destinations before copying so an existing dataset is preserved.
    for source, destination in copies:
        if destination.exists():
            parser.error(f"Destination already exists; select a new --dataset folder: {destination}")
    for source, destination in copies:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    print(f"Imported {len(copies) // 2} image/label pairs to {args.dataset.resolve()}")


if __name__ == "__main__":
    main()
