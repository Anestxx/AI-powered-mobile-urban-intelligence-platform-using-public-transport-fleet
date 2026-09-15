"""Explicitly extract sampled video frames for dataset preparation."""

import argparse
from pathlib import Path

from paths import EDGE_DIR, VIDEO_PATH, existing_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", default=VIDEO_PATH)
    parser.add_argument("--output", type=Path, default=EDGE_DIR / "extracted_frames")
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--max-frames", type=int, default=0, help="Maximum saved frames; 0 means unlimited")
    args = parser.parse_args()
    if args.interval < 1 or args.max_frames < 0:
        parser.error("interval must be positive and max-frames must be nonnegative")
    import cv2

    cap = cv2.VideoCapture(str(existing_file(args.video)))
    read_count = saved = 0
    try:
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {args.video}")
        args.output.mkdir(parents=True, exist_ok=True)
        while not args.max_frames or saved < args.max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if read_count % args.interval == 0:
                path = args.output / f"frame_{read_count:06d}.jpg"
                if path.exists():
                    raise FileExistsError(f"Choose an empty output folder; file already exists: {path}")
                if not cv2.imwrite(str(path), frame):
                    raise OSError(f"Could not write: {path}")
                saved += 1
            read_count += 1
        if not read_count:
            raise RuntimeError("Video contains no readable frames.")
    finally:
        cap.release()
    print(f"Extracted {saved} frames to {args.output}")


if __name__ == "__main__":
    main()
