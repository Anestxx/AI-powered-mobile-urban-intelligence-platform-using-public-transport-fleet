"""Split labeled images by source group, preserving holdout isolation and original files."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import shutil


def plan_split(source, groups_csv, seed=42):
    groups, seen_files, hashes = {}, set(), {}
    with groups_csv.open(encoding="utf-8-sig", newline="") as source_file:
        reader = csv.DictReader(source_file)
        if not {"file", "group"}.issubset(reader.fieldnames or []):
            raise ValueError("Group CSV needs file and group columns")
        for row in reader:
            name, group = row["file"].strip(), row["group"].strip()
            if not group or not name or Path(name).name != name or name in seen_files:
                raise ValueError(f"Invalid/duplicate flat image filename or group: {name}")
            image, label = source / "images" / name, source / "labels" / f"{Path(name).stem}.txt"
            if not image.is_file() or not label.is_file():
                raise ValueError(f"Missing image/label pair: {name}")
            checksum = hashlib.sha256(image.read_bytes()).hexdigest()
            if checksum in hashes:
                raise ValueError(f"Duplicate image content: {name} and {hashes[checksum]}; review duplicates first")
            hashes[checksum] = name
            seen_files.add(name)
            groups.setdefault(group, []).append((image, label))
    if len(groups) < 3:
        raise ValueError("At least three independent source groups are required for train/val/test")
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)
    train_count = min(len(keys) - 2, max(1, round(len(keys) * .7)))
    val_count = min(len(keys) - train_count - 1, max(1, round(len(keys) * .2)))
    assignment = {group: "train" if index < train_count else "val" if index < train_count + val_count else "test" for index, group in enumerate(keys)}
    return [(group, assignment[group], image, label) for group in keys for image, label in groups[group]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Folder containing flat images/ and labels/")
    parser.add_argument("--groups", type=Path, required=True, help="CSV with file,group columns; group all frames from one source together")
    parser.add_argument("--output", type=Path, required=True, help="New destination folder")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        plan = plan_split(args.source, args.groups, args.seed)
        if args.output.exists() and not args.dry_run:
            raise ValueError("Output already exists; choose a new folder to preserve existing data")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Cannot prepare split: {exc}\n")
    counts = {split: sum(item[1] == split for item in plan) for split in ("train", "val", "test")}
    print(f"Source-group split (seed {args.seed}): {counts}")
    if args.dry_run:
        return
    manifest = []
    for group, split, image, label in plan:
        for kind, source in (("images", image), ("labels", label)):
            destination = args.output / kind / split / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        manifest.append({"file": image.name, "source_group": group, "split": split})
    (args.output / "split-manifest.json").write_text(json.dumps({"seed": args.seed, "counts": counts, "items": manifest}, indent=2), encoding="utf-8")
    print(f"Copied dataset and manifest to {args.output}. Validate labels before training.")


if __name__ == "__main__":
    main()
