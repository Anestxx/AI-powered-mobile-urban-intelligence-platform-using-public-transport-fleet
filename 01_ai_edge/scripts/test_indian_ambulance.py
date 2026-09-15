import cv2
import os
import time
from ultralytics import YOLO

# ============================================================
# CODYSSEY - INDIAN AMBULANCE MODEL TEST
# ============================================================

VIDEO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "videos",
    "ambulance_test.mp4"
)

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "models",
    "ambulance.pt"
)

CONFIDENCE_THRESHOLD = 0.35
IMAGE_SIZE = 640

# Process every Nth frame
FRAME_SKIP = 3

print("=" * 70)
print("CODYSSEY INDIAN AMBULANCE DETECTOR TEST")
print("=" * 70)

print("Video :", VIDEO_PATH)
print("Model :", MODEL_PATH)

if not os.path.exists(VIDEO_PATH):
    print("\nERROR: ambulance_test.mp4 not found")
    raise SystemExit

if not os.path.exists(MODEL_PATH):
    print("\nERROR: ambulance.pt not found")
    raise SystemExit

print("\nLoading model...")

model = YOLO(MODEL_PATH)

print("Model loaded.")
print("Classes:", model.names)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Could not open video")
    raise SystemExit

fps = cap.get(cv2.CAP_PROP_FPS)

if fps <= 0:
    fps = 30

frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

print("\nVideo:")
print("Resolution:", frame_width, "x", frame_height)
print("FPS:", fps)

frame_number = 0
processed_frames = 0
detections_count = 0
max_confidence = 0.0

latest_detections = []

print("\nStarting playback...")
print("Press Q to quit.")
print("=" * 70)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    # Run AI only every Nth frame
    if frame_number % FRAME_SKIP == 0:

        results = model.predict(
            frame,
            imgsz=IMAGE_SIZE,
            conf=CONFIDENCE_THRESHOLD,
            device="cpu",
            verbose=False
        )

        latest_detections = []
        processed_frames += 1

        if results:

            result = results[0]

            if result.boxes is not None:

                for box in result.boxes:

                    confidence = float(box.conf[0])

                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    detection = {
                        "event_type": "emergency",
                        "class_name": "ambulance",
                        "class_id": 0,
                        "confidence": round(confidence, 4),
                        "bbox": [
                            int(x1),
                            int(y1),
                            int(x2),
                            int(y2)
                        ],
                        "model": "indian_ambulance"
                    }

                    latest_detections.append(detection)

                    detections_count += 1

                    max_confidence = max(
                        max_confidence,
                        confidence
                    )

    # ========================================================
    # DRAW DETECTIONS
    # ========================================================

    display = frame.copy()

    ambulance_found = False

    for detection in latest_detections:

        x1, y1, x2, y2 = detection["bbox"]
        confidence = detection["confidence"]

        ambulance_found = True

        cv2.rectangle(
            display,
            (x1, y1),
            (x2, y2),
            (0, 0, 255),
            3
        )

        label = f"AMBULANCE {confidence:.2f}"

        cv2.rectangle(
            display,
            (x1, max(0, y1 - 35)),
            (x1 + 250, y1),
            (0, 0, 255),
            -1
        )

        cv2.putText(
            display,
            label,
            (x1 + 5, max(22, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    # ========================================================
    # STATUS PANEL
    # ========================================================

    if ambulance_found:

        cv2.rectangle(
            display,
            (10, 10),
            (450, 85),
            (0, 0, 255),
            -1
        )

        cv2.putText(
            display,
            "EMERGENCY VEHICLE DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2
        )

        cv2.putText(
            display,
            "INDIAN AMBULANCE",
            (20, 68),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    else:

        cv2.rectangle(
            display,
            (10, 10),
            (350, 55),
            (0, 0, 0),
            -1
        )

        cv2.putText(
            display,
            "Scanning for ambulance...",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

    cv2.imshow(
        "CODYSSEY - Indian Ambulance AI",
        display
    )

    # Maintain approximate video speed
    delay = max(1, int(1000 / fps))

    key = cv2.waitKey(delay) & 0xFF

    if key == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)

print("Total video frames:", frame_number)
print("AI processed frames:", processed_frames)
print("Ambulance detections:", detections_count)
print("Maximum confidence:", round(max_confidence, 3))

print("=" * 70)