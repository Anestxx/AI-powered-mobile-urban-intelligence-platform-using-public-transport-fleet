"""Evaluate a pothole checkpoint and write measured results to a model report."""

import argparse
import hashlib
from pathlib import Path

from config import DATA_YAML, RUNS_DIR, TRAINED_MODEL, resolve_dataset, write_runtime_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=TRAINED_MODEL)
    parser.add_argument("--data", type=Path, default=DATA_YAML)
    parser.add_argument("--split", choices=["val", "test"], default="test")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", type=Path, default=RUNS_DIR / "model-report.md")
    args = parser.parse_args()
    if args.imgsz < 32:
        parser.error("imgsz must be at least 32")
    try:
        data = resolve_dataset(args.data, splits=(args.split,))
        if not args.model.is_file():
            raise FileNotFoundError(f"Trained weights not found: {args.model}. Use --model to select a checkpoint.")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Validation inputs unavailable: {exc}\n")
    if args.check:
        print(f"Validation inputs ready: {data['path']}")
        return
    import torch
    from ultralytics import YOLO

    model = YOLO(str(args.model.resolve()))
    if model.names != {0: "pothole"}:
        parser.exit(1, f"Expected class 0=pothole; found {model.names}\n")
    metrics = model.val(
        data=write_runtime_config(data), imgsz=args.imgsz, split=args.split,
        device=0 if torch.cuda.is_available() else "cpu",
        project=str(RUNS_DIR), name="validation",
    )
    print(f"mAP50: {metrics.box.map50:.4f}; mAP50-95: {metrics.box.map:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}; Recall: {metrics.box.mr:.4f}")
    checksum = hashlib.sha256(args.model.read_bytes()).hexdigest()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        f"# Pothole model evaluation\n\nModel: `{args.model.resolve()}`\n\nSHA-256: `{checksum}`\n\n"
        f"Dataset: `{data['path']}`; split: {args.split}; image size: {args.imgsz}.\n\n"
        f"| Metric | Measured value |\n| --- | --- |\n| Precision | {metrics.box.mp:.4f} |\n"
        f"| Recall | {metrics.box.mr:.4f} |\n| mAP50 | {metrics.box.map50:.4f} |\n| mAP50-95 | {metrics.box.map:.4f} |\n\n"
        f"Timing (ms/image, Ultralytics): `{metrics.speed}`\n\n"
        "Precision and recall are reported by Ultralytics; select an operating threshold using a separate error review. "
        "Record dataset provenance and split manifest, unseen-video results, and shadow/puddle/patch mistakes before model handoff.\n",
        encoding="utf-8",
    )
    print(f"Evaluation report: {args.report}")


if __name__ == "__main__":
    main()
