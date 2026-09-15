"""Train the single-class pothole model on a labeled local dataset."""

import argparse
from pathlib import Path

from config import DATA_YAML, DEFAULT_MODEL, RUNS_DIR, resolve_dataset, write_runtime_config, validate_training_inputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_YAML)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--check", action="store_true", help="Validate input paths without starting training")
    args = parser.parse_args()
    if min(args.epochs, args.batch) < 1 or args.imgsz < 32 or args.workers < 0:
        parser.error("epochs/batch must be positive, imgsz >= 32, and workers >= 0")
    try:
        data = resolve_dataset(args.data)
        if not args.model.is_file():
            raise FileNotFoundError(f"Base model not found: {args.model}")
        validate_training_inputs(data)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Training inputs unavailable: {exc}\n")
    if args.check:
        print(f"Training inputs ready: {data['path']}")
        return
    import torch
    from ultralytics import YOLO

    device = 0 if torch.cuda.is_available() else "cpu"
    model = YOLO(str(args.model.resolve()))
    results = model.train(
        data=write_runtime_config(data), epochs=args.epochs, imgsz=args.imgsz,
        device=device, batch=args.batch, workers=args.workers,
        project=str(RUNS_DIR), name="pothole_v1", exist_ok=False,
        pretrained=True, optimizer="auto", patience=12, cache=False, amp=False,
        cos_lr=True, close_mosaic=10, degrees=5, translate=.1, scale=.5,
        fliplr=.5, hsv_h=.015, hsv_s=.5, hsv_v=.4,
    )
    print(f"Training output: {results.save_dir}")


if __name__ == "__main__":
    main()
