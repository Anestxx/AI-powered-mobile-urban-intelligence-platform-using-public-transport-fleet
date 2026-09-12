from pathlib import Path
import shutil

# ============================================================
# CODYSSEY - RAD DATASET IMPORTER
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAD_ROOT = Path(
    r"D:\pothole_training_data\datasets\rohitsuresh15"
    r"\radroad-anomaly-detection\versions\3\images"
)

DATASET_ROOT = PROJECT_ROOT / "02_dataset_model_training" / "dataset"

# RAD split -> our split
SPLITS = {
    "train": "train",
    "valid": "val",
    "test": "test",
}

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


def copy_split(rad_split, project_split):
    source_images = RAD_ROOT / rad_split / "images"
    source_labels = RAD_ROOT / rad_split / "labels"

    destination_images = DATASET_ROOT / "images" / project_split
    destination_labels = DATASET_ROOT / "labels" / project_split

    destination_images.mkdir(parents=True, exist_ok=True)
    destination_labels.mkdir(parents=True, exist_ok=True)

    if not source_images.exists():
        print(f"ERROR: Image directory not found:")
        print(source_images)
        return 0, 0

    if not source_labels.exists():
        print(f"ERROR: Label directory not found:")
        print(source_labels)
        return 0, 0

    images_copied = 0
    labels_copied = 0

    image_files = [
        p for p in source_images.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]

    print(f"\n{rad_split.upper()} -> {project_split.upper()}")
    print(f"Source images: {len(image_files)}")

    for image_path in image_files:
        label_path = source_labels / f"{image_path.stem}.txt"

        # Only import images that have matching YOLO labels.
        if not label_path.exists():
            continue

        destination_image = destination_images / image_path.name
        destination_label = destination_labels / label_path.name

        shutil.copy2(image_path, destination_image)
        shutil.copy2(label_path, destination_label)

        images_copied += 1
        labels_copied += 1

    print(f"Images copied: {images_copied}")
    print(f"Labels copied: {labels_copied}")

    return images_copied, labels_copied


def main():
    print("=" * 70)
    print("CODYSSEY - RAD DATASET IMPORT")
    print("=" * 70)

    print(f"RAD source:")
    print(RAD_ROOT)

    print(f"\nProject dataset:")
    print(DATASET_ROOT)

    if not RAD_ROOT.exists():
        print("\nERROR: RAD dataset path does not exist.")
        return

    total_images = 0
    total_labels = 0

    for rad_split, project_split in SPLITS.items():
        images, labels = copy_split(
            rad_split,
            project_split
        )

        total_images += images
        total_labels += labels

    print("\n" + "=" * 70)
    print("IMPORT COMPLETE")
    print("=" * 70)

    print(f"Total images: {total_images}")
    print(f"Total labels: {total_labels}")

    print("\nDataset location:")
    print(DATASET_ROOT)

    print("\nRAD source remains untouched on D:.")

    if total_images > 0:
        print("\nSUCCESS: Dataset is ready for audit.")
    else:
        print("\nERROR: No images were imported.")


if __name__ == "__main__":
    main()