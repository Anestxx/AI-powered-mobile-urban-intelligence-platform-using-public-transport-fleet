import cv2
import time

from detector import RoadDetector
from alert_manager import AlertManager


VIDEO_PATH = "videos/road_test.mp4"
MODEL_PATH = "models/best.pt"

# Run AI every N frames; skipped frames reuse the last detections.
FRAME_SKIP = 2

# 1.0 = real video speed. This is your "medium" — not sped up, not slowed.
PLAYBACK_SPEED = 1.0

# Lower = catches weaker/uncertain potholes (shadow, water-logged).
# Raise toward 0.30 only if false positives become a real problem
# even with the ROI filter active.
CONFIDENCE = 0.15

# Trapezoid over the road area — tune these if the yellow outline
# on screen doesn't line up with your actual road edges.
ROI_POINTS = [
    (0.30, 0.42),  # top-left
    (0.70, 0.42),  # top-right
    (1.00, 1.00),  # bottom-right
    (0.00, 1.00),  # bottom-left
]


detector = RoadDetector(MODEL_PATH, imgsz=640, roi_points=ROI_POINTS)

alert_manager = AlertManager(
    confidence_threshold=CONFIDENCE,
    required_detections=3,
    cooldown_seconds=10
)


cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Cannot open video")
    exit()

video_fps = cap.get(cv2.CAP_PROP_FPS)
if not video_fps or video_fps <= 1:
    video_fps = 30

frame_delay_ms = max(1, int((1000 / video_fps) / PLAYBACK_SPEED))


print("EDGE AI GATEWAY STARTED")
print(f"Video FPS: {video_fps:.1f} | Playback delay: {frame_delay_ms}ms")
print("Press Q to quit")


frame_count = 0
last_detections = []

prev_time = time.time()
fps = 0


while True:

    success, frame = cap.read()

    if not success:
        print("Video finished")
        break

    frame_count += 1

    run_ai_this_frame = (frame_count % FRAME_SKIP == 0)

    if run_ai_this_frame or frame_count == 1:

        detections = detector.detect(frame, conf=CONFIDENCE)

        for detection in detections:

            alert = alert_manager.process_detection(detection)

            if alert:
                print("\n🚨 VALIDATED ALERT")
                print(alert)

        last_detections = detections

    annotated_frame = detector.draw_detections(frame.copy(), last_detections)
    annotated_frame = detector.draw_roi(annotated_frame)

    current_time = time.time()
    fps = 1 / (current_time - prev_time) if current_time != prev_time else fps
    prev_time = current_time

    cv2.putText(
        annotated_frame,
        f"FPS: {fps:.1f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Urban Sensing Edge AI Gateway", annotated_frame)

    if cv2.waitKey(frame_delay_ms) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()