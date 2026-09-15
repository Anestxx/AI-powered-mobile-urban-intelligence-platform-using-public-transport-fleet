"""Preview the camera video or one model; replaces the old test_* demo scripts."""

import argparse
import math
import time

from paths import AMBULANCE_VIDEO_PATH, EMERGENCY_MODEL_PATH, GENERAL_MODEL_PATH, POTHOLE_MODEL_PATH, RAD_MODEL_PATH, VIDEO_PATH, existing_file
from playback import PlaybackClock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["none", "general", "rad", "pothole", "emergency"], default="none")
    parser.add_argument("--video", help="Local recording; emergency preview defaults to ambulance_test.mp4")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--max-frames", type=int, default=0)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--confidence", type=float, default=.25)
    parser.add_argument("--loop", action="store_true", help="Replay the recording until Q or the window close button")
    parser.add_argument("--paused", action="store_true", help="Show the first frame and wait for Space to play")
    args = parser.parse_args()
    args.video = args.video or (AMBULANCE_VIDEO_PATH if args.model == "emergency" else VIDEO_PATH)
    if args.max_frames < 0 or args.start_frame < 0 or not 0 <= args.confidence <= 1:
        parser.error("Frame counts must be nonnegative and confidence must be in [0, 1].")
    if args.headless and (args.loop or args.paused):
        parser.error("Loop and pause controls require the video window.")
    import cv2

    model = None
    if args.model != "none":
        from ultralytics import YOLO
        model_path = {"general": GENERAL_MODEL_PATH, "rad": RAD_MODEL_PATH, "pothole": POTHOLE_MODEL_PATH, "emergency": EMERGENCY_MODEL_PATH}[args.model]
        model = YOLO(str(existing_file(model_path)))
        print(f"Model classes: {model.names}")
        if args.model == "emergency":
            print("Checkpoint preview only. Verify its actual class labels; the supplied emergency.pt contains general objects, not an ambulance class.")
    cap = cv2.VideoCapture(str(existing_file(args.video)))
    frames = detections = skipped = 0
    title = f"CODYSSEY - {args.model} detection preview"
    try:
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {args.video}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, args.start_frame)
        fps = cap.get(cv2.CAP_PROP_FPS)
        fps = fps if math.isfinite(fps) and fps > 1 else 30.0
        next_frame = args.start_frame
        pass_frames = 0
        clock = PlaybackClock(fps, args.start_frame, time.monotonic())
        paused = args.paused
        if paused:
            clock.toggle_pause(time.monotonic())
        if not args.headless:
            cv2.namedWindow(title, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(title, 1100, 720)
            print("Recorded-video preview: Space = pause/play, R = replay, Q = quit.", flush=True)
            print("Boxes are model predictions. Preview does not create dashboard alerts. Overdue frames are skipped to keep playback moving.", flush=True)
        first_frame = True
        rendered = None
        inference_ms = 0
        while not args.max_frames or frames < args.max_frames:
            if paused and rendered is not None:
                paused_view = rendered.copy()
                cv2.rectangle(paused_view, (0, 85), (1100, 115), (25, 20, 15), -1)
                cv2.putText(paused_view, "PAUSED | Space: play   R: replay   Q: quit", (12, 101), cv2.FONT_HERSHEY_SIMPLEX, .52, (100, 230, 255), 1, cv2.LINE_AA)
                cv2.imshow(title, paused_view)
                key = cv2.waitKey(50) & 0xFF
                if key == ord("q") or cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                    break
                if key == ord(" "):
                    paused = False
                    clock.toggle_pause(time.monotonic())
                elif key == ord("r"):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, args.start_frame)
                    next_frame, pass_frames = args.start_frame, 0
                    clock = PlaybackClock(fps, args.start_frame, time.monotonic())
                    clock.toggle_pause(time.monotonic())
                    rendered = None
                continue
            if not args.headless and not first_frame:
                target = clock.target_frame(time.monotonic())
                while next_frame < target and cap.grab():
                    next_frame += 1
                    skipped += 1
            ok, frame = cap.read()
            if not ok:
                if not pass_frames:
                    raise RuntimeError("No readable frames at the requested starting position.")
                if args.loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, args.start_frame)
                    next_frame, pass_frames = args.start_frame, 0
                    clock = PlaybackClock(fps, args.start_frame, time.monotonic())
                    continue
                break
            video_time = next_frame / fps
            next_frame += 1
            frames += 1
            pass_frames += 1
            current_detections = 0
            started = time.monotonic()
            if model is not None:
                result = model.predict(frame, conf=args.confidence, verbose=False)[0]
                current_detections = len(result.boxes) if result.boxes is not None else 0
                detections += current_detections
                inference_ms = (time.monotonic() - started) * 1000
                if not args.headless:
                    frame = result.plot()
            if not args.headless:
                if first_frame:
                    # Model warm-up must not jump past the beginning of the example.
                    clock = PlaybackClock(fps, args.start_frame, time.monotonic())
                    if paused:
                        clock.toggle_pause(time.monotonic())
                rendered = cv2.resize(frame, (1100, round(frame.shape[0] * 1100 / frame.shape[1])))
                # A separate header keeps controls readable without covering evidence.
                rendered = cv2.copyMakeBorder(rendered, 115, 0, 0, 0, cv2.BORDER_CONSTANT, value=(25, 20, 15))
                lines = [
                    "RECORDED VIDEO | Inference during playback | Pothole preview" if args.model == "pothole" else "RECORDED VIDEO | Model preview",
                    f"Time {video_time:.1f}s | Boxes {current_detections} | Threshold {args.confidence:.0%} | Inference {inference_ms:.0f} ms",
                    "Space: pause/play   R: replay   Q: quit | Preview only; no new dashboard alerts",
                    "Starts paused - press Space to play" if paused else f"Source {fps:.0f} fps | Skipped {skipped} frames to keep playback moving",
                ]
                for row, line in enumerate(lines):
                    cv2.putText(rendered, line, (12, 23 + row * 26), cv2.FONT_HERSHEY_SIMPLEX, .52, (240, 230, 215), 1, cv2.LINE_AA)
                cv2.imshow(title, rendered)
                key = cv2.waitKey(clock.delay_ms(next_frame, time.monotonic())) & 0xFF
                if key == ord("q") or cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                    break
                if key == ord(" "):
                    paused = not paused
                    clock.toggle_pause(time.monotonic())
                elif key == ord("r"):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, args.start_frame)
                    next_frame, pass_frames = args.start_frame, 0
                    clock = PlaybackClock(fps, args.start_frame, time.monotonic())
            first_frame = False
        if not frames:
            raise RuntimeError("No readable frames at the requested starting position.")
    finally:
        cap.release()
        if not args.headless:
            cv2.destroyAllWindows()
    print(f"Preview completed: {frames} frames, {detections} detections.")


if __name__ == "__main__":
    main()
