import cv2
import time

from detector import RoadDetector
from alert_manager import AlertManager
from alert_logger import AlertLogger

VIDEO_PATH = "01_ai_edge/videos/road_test.mp4"
MODEL_PATH = "01_ai_edge/models/best.pt"

# Normal video speed
PLAYBACK_SPEED = 1.0

# Detection confidence
CONFIDENCE = 0.40

ROI_POINTS = [
    (0.30, 0.42),
    (0.70, 0.42),
    (1.00, 1.00),
    (0.00, 1.00),
]


# -----------------------------
# INITIALIZE AI
# -----------------------------

detector = RoadDetector(
    MODEL_PATH,
    imgsz=640,
    roi_points=ROI_POINTS
)

alert_manager = AlertManager(
    confidence_threshold=0.60,
    required_detections=3,
    cooldown_seconds=10
)

alert_logger = AlertLogger()


# -----------------------------
# OPEN VIDEO
# -----------------------------

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Cannot open video")
    exit()


video_fps = cap.get(cv2.CAP_PROP_FPS)

if not video_fps or video_fps <= 1:
    video_fps = 30


frame_delay_ms = max(
    1,
    int(1000 / video_fps / PLAYBACK_SPEED)
)


print("===================================")
print(" URBAN SENSING EDGE AI GATEWAY")
print("===================================")
print(f"Video FPS: {video_fps:.1f}")
print("AI: Processing every incoming frame")
print("Storage: NO VIDEO STORAGE")
print("Storage: ONLY VALIDATED ALERTS")
print("Press Q to quit")
print("===================================")


# -----------------------------
# PROCESS VIDEO
# -----------------------------

while True:

    success, frame = cap.read()

    if not success:
        print("Video finished")
        break


    # --------------------------------
    # AI processes frame in memory
    # --------------------------------

    detections = detector.detect(
        frame,
        conf=CONFIDENCE
    )


    # --------------------------------
    # VALIDATE DETECTIONS
    # --------------------------------

    for detection in detections:

        alert = alert_manager.process_detection(
            detection
        )

        if alert:

            print("\n🚨 VALIDATED URBAN ALERT")
            print(alert)

            # Save ONLY alert metadata
            alert_logger.save_alert(alert)


    # --------------------------------
    # DISPLAY
    # --------------------------------

    annotated_frame = detector.draw_detections(
        frame.copy(),
        detections
    )

    annotated_frame = detector.draw_roi(
        annotated_frame
    )


    cv2.putText(
        annotated_frame,
        "EDGE AI | LIVE PROCESSING",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )


    cv2.imshow(
        "Urban Sensing Edge AI Gateway",
        annotated_frame
    )


    # Original video timing
    if cv2.waitKey(frame_delay_ms) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()

print("\nEdge AI stopped.")