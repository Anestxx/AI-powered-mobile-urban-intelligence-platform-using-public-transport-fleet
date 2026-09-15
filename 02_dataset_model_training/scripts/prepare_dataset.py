"""Create the empty RAD dataset directory structure."""

import argparse
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parents[1] / "dataset"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_DIR)
    args = parser.parse_args()
    for kind in ("images", "labels"):
        for split in ("train", "val", "test"):
            (args.dataset / kind / split).mkdir(parents=True, exist_ok=True)
    print(f"Dataset folders ready: {args.dataset.resolve()}")


if __name__ == "__main__":
    main()
