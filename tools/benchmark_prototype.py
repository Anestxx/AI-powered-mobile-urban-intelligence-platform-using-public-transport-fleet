"""Reproducible, local CPU-inference and geographic-query checks; not accuracy tests."""
import argparse
import json
from pathlib import Path
import platform
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "01_ai_edge/scripts"), str(ROOT / "03_backend_database")]


def benchmark_location():
    from sqlalchemy import select
    from app.database import Base, create_database
    from app.models import Issue
    from app.services import nearby_issue_query, record_dict
    from location_intelligence import match_issue
    engine, factory = create_database("sqlite://")
    Base.metadata.create_all(engine)
    observation = dict(latitude=12.9716, longitude=77.5946, location_source="simulated", event_type="pothole")
    with factory() as db:
        for index in range(10000):
            db.add(Issue(issue_id=f"BENCH_{index:05}", event_type="pothole", status="open", location_source="simulated",
                         latitude=12.9716 if index == 0 else 11 + (index % 200) * .02,
                         longitude=77.5946 if index == 0 else 75 + (index // 200) * .03,
                         first_seen="2026-09-14T00:00:00Z", last_seen="2026-09-14T00:00:00Z", priority_reason="Synthetic benchmark"))
        db.commit()
        results = {}
        for name, query in (("all_open_issues", select(Issue).where(Issue.status == "open", Issue.event_type == "pothole", Issue.location_source == "simulated")),
                            ("geographic_prefilter", nearby_issue_query(observation, 25))):
            elapsed = []
            for repeat in range(6):
                db.expunge_all()
                started = time.perf_counter()
                candidates = db.scalars(query).all()
                matched = match_issue(observation, [record_dict(issue) for issue in candidates], 25)
                if repeat:
                    elapsed.append((time.perf_counter() - started) * 1000)
            results[name] = {"candidates_loaded": len(candidates), "median_query_and_match_ms": round(statistics.median(elapsed), 3), "matched_issue": matched["matched_issue_id"]}
        assert results["all_open_issues"]["matched_issue"] == results["geographic_prefilter"]["matched_issue"] == "BENCH_00000"
    engine.dispose()
    return results


def benchmark_inference():
    import cv2
    import torch
    from detector import PotholeDetector
    from paths import VIDEO_PATH
    indices = [450, 500, 560, 580, 600, 650, 700, 800]
    capture = cv2.VideoCapture(str(VIDEO_PATH))
    frames = []
    try:
        for index in indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, index)
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Missing benchmark frame {index}")
            frames.append(frame)
    finally:
        capture.release()
    results = []
    for threads in (0, 1, 2, 4):
        detector = PotholeDetector(cpu_threads=threads)
        if detector.device != "cpu":
            return {"skipped": "CPU comparison requires CPU execution; GPU is active"}
        detector.detect(frames[0], .7)  # Excluded initialization/warm-up.
        elapsed, counts = [], []
        for _ in range(2):
            for frame in frames:
                started = time.perf_counter()
                detections = detector.detect(frame, .7)
                elapsed.append((time.perf_counter() - started) * 1000)
                counts.append(len(detections))
        result = {"requested_threads": threads, "actual_threads": torch.get_num_threads(), "model_version": detector.model_version,
                  "median_inference_ms": round(statistics.median(elapsed), 2), "p95_inference_ms": round(sorted(elapsed)[-1], 2),
                  "predicted_box_counts": counts, "samples": len(elapsed)}
        results.append(result)
        print(f"CPU benchmark: {result}", flush=True)
    return {"frame_indices": indices, "confidence": .7, "imgsz": 640, "runs": results,
            "note": "Same eight recorded frames, two passes, warm-up excluded. Counts are prediction agreement, not accuracy. Results depend on hardware/load/order."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-inference", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/prototype-benchmark.json")
    args = parser.parse_args()
    report = {"environment": platform.platform(), "python": platform.python_version(), "location": benchmark_location()}
    if not args.skip_inference:
        report["inference"] = benchmark_inference()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["location"], indent=2))
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
