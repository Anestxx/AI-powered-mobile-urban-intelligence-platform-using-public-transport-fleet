"""Run pothole inference, simulated GPS, durable observation delivery and bus telemetry."""
import argparse
import json
from datetime import datetime, timedelta, timezone
import time
from pathlib import Path

import config
from paths import ALERTS_PATH


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", "--video", default=config.VIDEO_PATH, help="Video path or webcam index (e.g. 0)")
    parser.add_argument("--model", default=config.MODEL_PATH)
    parser.add_argument("--confidence", type=float, default=config.CONFIDENCE_THRESHOLD)
    parser.add_argument("--imgsz", type=int, default=config.IMAGE_SIZE)
    parser.add_argument("--cpu-threads", type=int, default=0, help="Optional measured CPU thread setting; 0 keeps the framework default")
    parser.add_argument("--metrics-file", type=Path, help="Save measured performance counters as JSON")
    parser.add_argument("--save-evidence", action=argparse.BooleanOptionalAction, default=True,
                        help="Save an annotated road image with each alert (default: enabled)")
    parser.add_argument("--frame-interval", type=int, default=config.FRAME_INTERVAL)
    parser.add_argument("--required-detections", type=int, default=config.REQUIRED_DETECTIONS)
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--video-only", action="store_true", help="Use the compact video window without the operator dashboard")
    parser.add_argument("--loop", action="store_true", help="Replay the recording for viewing; only the first pass submits alerts")
    parser.add_argument("--offline", action="store_true", help="Keep observations in the durable outbox without network calls")
    parser.add_argument("--flush-only", action="store_true", help="Retry pending events without opening video or loading a model")
    parser.add_argument("--outbox", type=Path, default=config.OUTBOX_PATH)
    parser.add_argument("--alerts-file", type=Path, default=ALERTS_PATH)
    parser.add_argument("--backend-url", default=config.BACKEND_URL)
    parser.add_argument("--bus-id", default=config.BUS_ID)
    args = parser.parse_args()
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", args.bus_id):
        parser.error("Bus ID must contain letters, digits, underscores or hyphens")
    if min(args.frame_interval, args.required_detections) < 1 or args.imgsz < 32 or min(args.max_frames, args.start_frame, args.cpu_threads) < 0 or not 0 <= args.confidence <= 1:
        parser.error("Invalid frame count, image size or confidence")
    if args.flush_only and args.offline:
        parser.error("flush-only requires a backend connection")
    if args.loop and (args.headless or args.flush_only):
        parser.error("loop requires the video window")
    return args


def draw_frame(frame, detections, location, event_ids, states, latest_alert, video_time, duration, pass_number, confidence, offline, performance=None):
    import cv2
    import numpy as np
    frame = frame.copy()
    for detection in detections:
        x1, y1, x2, y2 = detection["bbox"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 180, 255), 2)
        cv2.putText(frame, f"Pothole {detection['confidence']:.0%}", (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 180, 255), 1)
    canvas = np.full((760, 1100, 3), (24, 20, 15), dtype=np.uint8)
    ratio = min(640 / frame.shape[0], 470 / frame.shape[1])
    width, height = round(frame.shape[1] * ratio), round(frame.shape[0] * ratio)
    canvas[85:85 + height, 20:20 + width] = cv2.resize(frame, (width, height))

    def label(text, x, y, color=(230, 225, 220), scale=.58):
        cv2.putText(canvas, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 1, cv2.LINE_AA)

    label("CODYSSEY | VIDEO DETECTION + LOCATION ALERTS", 20, 32, (140, 230, 220), .72)
    mode = "PLAYING RECORDING - ALERTS ENABLED" if pass_number == 1 else "REPLAY - FIRST-PASS ALERTS PRESERVED"
    label("OFFLINE - ALERTS STAY QUEUED" if offline else mode, 20, 60)
    x = 525
    elapsed = f"{video_time:.1f}s" + (f" / {duration:.1f}s" if duration else "")
    label(f"Video time: {elapsed}", x, 110)
    label(f"Pothole predictions: {len(detections)}", x, 145)
    label(f"Confidence threshold: {confidence:.0%}", x, 180)
    if performance:
        label(f"Inference: {performance['mean_inference_ms']} ms | Frames/s: {performance['recent_frame_rate']}", x, 208, scale=.48)
    label("CURRENT LOCATION - SIMULATED GPS", x, 235, (100, 220, 255))
    label(f"Latitude:  {location['latitude']:.7f}", x, 270)
    label(f"Longitude: {location['longitude']:.7f}", x, 305)
    label("Example bus route; not coordinates from the video.", x, 340, scale=.48)
    sent = sum(state == "sent" for state in states.values())
    pending = sum(states.get(event_id, "pending") == "pending" for event_id in event_ids)
    invalid = sum(state == "invalid" for state in states.values())
    label("ALERTS FROM THIS RUN", x, 395, (140, 230, 220))
    label(f"Confirmed: {len(event_ids)} | Sent: {sent} | Queued: {pending}", x, 430)
    if latest_alert:
        state = states.get(latest_alert["event_id"], "pending")
        text = {"sent": "SENT - BACKEND ACKNOWLEDGED", "pending": "QUEUED - WAITING FOR DELIVERY", "invalid": "REJECTED - CHECK OUTBOX"}[state]
        label(text, x, 480, (110, 230, 120) if state == "sent" else (100, 220, 255))
        label(f"Pothole {latest_alert['confidence']:.0%} | {latest_alert['event_id'][:12]}", x, 515)
        label(f"Alert GPS: {latest_alert['latitude']:.6f}, {latest_alert['longitude']:.6f}", x, 550)
        label(f"Detected: {latest_alert['timestamp'][11:19]} UTC", x, 585)
    else:
        label("Watching for repeated pothole detections...", x, 480, scale=.52)
    if invalid:
        label(f"{invalid} alert(s) rejected; retained in outbox.", x, 620, (100, 150, 255))
    label("Dashboard: http://127.0.0.1:5173/#alerts", x, 675, scale=.50)
    label("Automatic playback | Q: quit | Space: pause/resume", 20, 746, scale=.52)
    return canvas


def main():
    args = parse_args()
    from api_client import ApiClient
    from outbox import DeliveryWorker, Outbox
    outbox = Outbox(args.outbox)
    client = ApiClient(args.backend_url)
    if args.flush_only:
        outbox.flush_once(client, limit=100, retry_now=True)
        counts = outbox.counts()
        print(f"Delivery state: {counts}")
        return 1 if counts["pending"] or counts["invalid"] else 0

    import cv2
    from alert_logger import AlertLogger
    from alert_manager import AlertManager
    from detector import PotholeDetector
    from video_reader import VideoReader
    from location_intelligence import GPSSimulator, validate_location
    from playback import PlaybackClock
    from metrics import RunMetrics

    detector = PotholeDetector(args.model, args.imgsz, cpu_threads=args.cpu_threads)
    metrics = RunMetrics()
    manager = AlertManager(args.confidence, args.required_detections, config.MAX_MISSING_FRAMES, config.COOLDOWN_SECONDS)
    logger = AlertLogger(args.alerts_file)
    worker = None if args.offline else DeliveryWorker(outbox, client, args.bus_id, config.HEARTBEAT_SECONDS)
    if worker:
        worker.start()
    frames = inferences = alert_count = 0
    detections = []
    event_ids, states = [], {}
    latest_alert = None
    pass_number = 1
    last_delivery_check = -float("inf")
    title = "CODYSSEY - Video and live location alerts"
    window = None

    def wait_key(delay):
        return window.wait_key(delay) if window else cv2.waitKey(delay) & 0xFF

    def window_closed():
        return window.closed if window else cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1

    try:
        with VideoReader(args.source, args.start_frame) as video:
            if args.loop and video.is_camera:
                raise ValueError("A live camera cannot be replayed; remove --loop")
            # Seeking starts the session at the selected video's original time.
            session_start = datetime.now(timezone.utc) - timedelta(seconds=args.start_frame / video.fps)
            gps = GPSSimulator(args.bus_id, session_start)
            clock = PlaybackClock(video.fps, args.start_frame, time.monotonic())
            if not args.headless:
                if not args.video_only and not args.offline:
                    from operator_window import OperatorWindow
                    window = OperatorWindow(args.backend_url)
                else:
                    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
                    cv2.resizeWindow(title, 1100, 760)
            print(f"Bus: {args.bus_id}; location: simulated; source FPS: {video.fps:.1f}; threshold: {args.confidence:.0%}")
            while not args.max_frames or frames < args.max_frames:
                sample = video.read()
                if sample is None:
                    if video.frame_index == args.start_frame:
                        raise RuntimeError("No readable video frames")
                    if args.loop:
                        video.rewind()
                        pass_number += 1
                        detections = []
                        clock = PlaybackClock(video.fps, args.start_frame, time.monotonic())
                        continue
                    if window:
                        if worker:
                            worker.heartbeat({"timestamp": datetime.now(timezone.utc).isoformat(), "camera_status": "offline", "ai_status": "offline"})
                        # Keep review/resolution available after the recording ends.
                        while not window.closed:
                            states = outbox.delivery_states(event_ids)
                            window.show(frame, detections, location, event_ids, states, latest_alert, video_time, video.duration, pass_number, args.confidence, args.offline)
                            window.finish()
                            if window.wait_key(100) == ord("q"):
                                break
                    break
                frame, frame_id, video_time = sample
                frames += 1
                location = gps.get_location(video_time)
                # Report processing time, including slow inference or paused playback.
                # The simulated route still follows the position in the recording.
                timestamp = datetime.now(timezone.utc).isoformat()
                location["gps_timestamp"] = timestamp
                if (frames - 1) % args.frame_interval == 0:
                    inference_started = time.perf_counter()
                    detections = detector.detect(frame, args.confidence)
                    metrics.record_inference(time.perf_counter() - inference_started)
                    inferences += 1
                    observations = manager.process_frame(detections, frame_id, video_time, timestamp) if pass_number == 1 else []
                    for observation in observations:
                        observation.update(bus_id=args.bus_id, model_version=detector.model_version)
                        if args.save_evidence:
                            from evidence import make_evidence
                            try:
                                observation["evidence"] = make_evidence(frame, observation["bbox"], args.source, frame_id, video_time)
                            except ValueError as exc:
                                print(f"Evidence unavailable; retaining the alert metadata: {exc}", flush=True)
                        try:
                            validate_location(location, timestamp)
                            observation.update({key: location[key] for key in ("latitude", "longitude", "location_source", "gps_timestamp")})
                            outbox.enqueue(observation)
                            event_ids.append(observation["event_id"])
                            latest_alert = observation
                        except ValueError as exc:
                            observation["delivery_error"] = str(exc)
                        # The durable outbox owns image bytes; the text log stays compact.
                        log_record = dict(observation)
                        if "evidence" in log_record:
                            log_record["evidence"] = {key: value for key, value in log_record["evidence"].items() if key != "jpeg_base64"}
                        logger.save_alert(log_record)
                        alert_count += 1
                        print(f"Validated pothole: {observation['event_id']} ({observation['confidence']:.0%}) at simulated GPS {location['latitude']}, {location['longitude']}", flush=True)
                metrics.record_frame()
                if worker:
                    worker.heartbeat({"timestamp": datetime.now(timezone.utc).isoformat(), "camera_status": "online", "ai_status": "online",
                                      "latitude": location["latitude"], "longitude": location["longitude"], "location_source": "simulated"})
                if not args.headless:
                    if time.monotonic() - last_delivery_check > .5:
                        updated_states = outbox.delivery_states(event_ids)
                        for event_id, state in updated_states.items():
                            if state == "sent" and states.get(event_id) != "sent":
                                print(f"Alert delivered to dashboard: {event_id}", flush=True)
                        states = updated_states
                        last_delivery_check = time.monotonic()
                    render = window.show if window else draw_frame
                    canvas = render(frame, detections, location, event_ids, states, latest_alert, video_time, video.duration, pass_number, args.confidence, args.offline, metrics.snapshot())
                    if not window:
                        cv2.imshow(title, canvas)
                    if frames == 1:
                        clock = PlaybackClock(video.fps, args.start_frame, time.monotonic())
                        print("Video is playing automatically. Use the player controls to pause or close." if window else "Video is playing automatically. Q: quit; Space: pause/resume.", flush=True)
                    key = wait_key(clock.delay_ms(frame_id, time.monotonic()))
                    if key == ord("q") or window_closed():
                        break
                    if key == ord(" "):
                        clock.toggle_pause(time.monotonic())
                        metrics.reset_playback_clock()
                        if window:
                            window.set_paused(True)
                        else:
                            cv2.rectangle(canvas, (0, 0), (1100, 78), (24, 20, 15), -1)
                            cv2.putText(canvas, "PAUSED - PRESS SPACE TO RESUME VIDEO", (20, 45), cv2.FONT_HERSHEY_SIMPLEX, .72, (100, 220, 255), 1, cv2.LINE_AA)
                            cv2.imshow(title, canvas)
                        while True:
                            key = wait_key(50)
                            if key in (ord(" "), ord("q")) or window_closed():
                                break
                        if key == ord("q") or window_closed():
                            break
                        clock.toggle_pause(time.monotonic())
                        if window:
                            window.set_paused(False)
            if not frames:
                raise RuntimeError("No readable video frames")
    finally:
        if window:
            window.stop()
        if worker:
            worker.stop()
        if not args.headless:
            cv2.destroyAllWindows()
    print(f"Completed: {frames} frames, {inferences} inferences, {alert_count} validated observations.")
    print(f"Durable delivery state: {outbox.counts()}")
    report = dict(metrics.snapshot(), model_version=detector.model_version, device=str(getattr(detector, "device", "unknown")),
                  confidence_threshold=args.confidence, image_size=args.imgsz, frame_interval=args.frame_interval,
                  requested_cpu_threads=args.cpu_threads, note="Measured runtime, not accuracy. Recent window includes model warm-up when present; frame rate includes video pacing.")
    print(f"Performance: {report}")
    if args.metrics_file:
        args.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        args.metrics_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
