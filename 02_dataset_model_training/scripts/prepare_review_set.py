"""Sample a recording and propose pothole boxes for human labeling, without training on predictions."""
import argparse
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def prepare_review_set(video, output, every_seconds=1.0, max_frames=40, detector=None, confidence=.25):
    import cv2

    video, output = Path(video).resolve(), Path(output).resolve()
    if not video.is_file():
        raise FileNotFoundError(video)
    if not math.isfinite(every_seconds) or every_seconds <= 0 or max_frames < 1:
        raise ValueError("Sampling interval and maximum frames must be positive")
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("Confidence must be between zero and one")
    if output.exists():
        raise FileExistsError(f"Choose a new review folder; existing files are preserved: {output}")
    digest = hashlib.sha256()
    with video.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    group = digest.hexdigest()
    cap = cv2.VideoCapture(str(video))
    records = []
    try:
        if not cap.isOpened():
            raise ValueError(f"Cannot read recording: {video.name}")
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(fps) or fps <= 0:
            raise ValueError("The recording has no usable frame rate")
        step = max(1, round(fps * every_seconds))
        (output / "images").mkdir(parents=True)
        for index in range(max_frames):
            frame_id = index * step
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            ok, frame = cap.read()
            if not ok:
                break
            filename = f"{group[:12]}_{frame_id:07d}.jpg"
            if not cv2.imwrite(str(output / "images" / filename), frame):
                raise OSError(f"Could not save frame {frame_id}")
            proposals = detector.detect(frame, confidence) if detector else []
            records.append({"image": filename, "group": group, "frame_id": frame_id, "video_time": frame_id / fps,
                            "width": frame.shape[1], "height": frame.shape[0], "review_status": "unreviewed",
                            "suggested_boxes": proposals})
        if not records:
            raise ValueError("No readable frames in the recording")
    finally:
        cap.release()
    manifest = {"source_name": video.name, "source_sha256": group, "status": "needs_human_labels",
                "model_version": getattr(detector, "model_version", None), "proposal_threshold": confidence,
                "class_names": ["pothole"], "training_ready": False,
                "note": "Predictions are proposals, not ground truth. Review all objects and missed potholes. No YOLO labels are generated.",
                "frames": records}
    (output / "review.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    with (output / "groups.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["file", "group"])
        writer.writerows((record["image"], group) for record in records)
    cards = []
    for record in records:
        rectangles = []
        for box in record["suggested_boxes"]:
            left, top, right, bottom = box["bbox"]
            rectangles.append(f'<rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}"/>')
        cards.append(f'<article><a href="images/{record["image"]}"><svg viewBox="0 0 {record["width"]} {record["height"]}">'
                     f'<image href="images/{record["image"]}" width="100%" height="100%"/>{"".join(rectangles)}</svg></a>'
                     f'<h2>Frame {record["frame_id"]} · {record["video_time"]:.2f} s</h2>'
                     f'<p>{len(record["suggested_boxes"])} proposed boxes · Needs human review</p></article>')
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    page += '<title>CODYSSEY · Label review set</title><style>body{margin:0;background:#07111e;color:#e9f2fb;font:14px system-ui;padding:32px}h1{font-size:28px}p{color:#b2c0d1;line-height:1.7}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}article{background:#111e30;border:1px solid #29405c;border-radius:12px;padding:12px}svg{display:block;width:100%;height:330px;background:#050b14}rect{fill:none;stroke:#ffcd55;stroke-width:3}h2{font-size:15px}a{color:#59d7ff}</style>'
    page += f'<h1>Frames for labeling · {html.escape(video.name)}</h1><p>{len(records)} sampled frames. Yellow boxes are unverified model proposals. Click a frame to open the original image. No training has been run.</p>'
    page += '<p>Label every pothole, correct wrong boxes and explicitly review negative frames. Keep this entire recording in one dataset split; collect independent recordings for validation and test. Accident examples need separate labels and a model that supports that class.</p><main class="grid">'
    page += "".join(cards) + '</main></html>'
    (output / "index.html").write_text(page, encoding="utf-8")
    (output / "README.md").write_text(
        "# Human review required\n\nOpen index.html to inspect sampled frames and model proposals. "
        "Original images are in images/. review.json records unreviewed proposals; it is not a training label file.\n\n"
        "Annotate the original images using YOLO box labels (0 = pothole), including missed objects. "
        "Review every background frame before creating an empty label. Put reviewed files in a separate labeled dataset. "
        "Use groups.csv when splitting; frames from this recording belong to one source group. "
        "Collect at least three independent groups before train/validation/test splitting. "
        "Do not use the review set as a holdout accuracy claim.\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, default=ROOT / "01_ai_edge/videos/road_test.mp4")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--every-seconds", type=float, default=1.0)
    parser.add_argument("--max-frames", type=int, default=40)
    parser.add_argument("--model", type=Path, default=ROOT / "01_ai_edge/models/pothole.pt")
    parser.add_argument("--confidence", type=float, default=.25, help="Proposal threshold, separate from the runtime alert threshold")
    parser.add_argument("--without-proposals", action="store_true")
    parser.add_argument("--cpu-threads", type=int, default=2)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Choose a new output folder; review files are never overwritten")
    detector = None
    if not args.without_proposals:
        sys.path.insert(0, str(ROOT / "01_ai_edge/scripts"))
        from detector import PotholeDetector
        detector = PotholeDetector(args.model, cpu_threads=args.cpu_threads)
    result = prepare_review_set(args.video, args.output, args.every_seconds, args.max_frames, detector, args.confidence)
    print(f"Prepared {len(result['frames'])} frames and {sum(len(row['suggested_boxes']) for row in result['frames'])} unreviewed proposals.")
    print(f"Review: {args.output.resolve() / 'index.html'}")
    print("Training remains pending human labels and independent holdout footage. Trained weights were not changed.")


if __name__ == "__main__":
    main()
