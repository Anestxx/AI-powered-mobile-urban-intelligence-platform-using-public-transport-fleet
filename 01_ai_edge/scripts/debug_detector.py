import cv2
import sys

sys.path.insert(0, "01_ai_edge/scripts")

from detector import RoadDetector


VIDEO_PATH = "01_ai_edge/videos/road_test.mp4"
MODEL_PATH = "01_ai_edge/models/best.pt"

detector = RoadDetector(
    model_path=MODEL_PATH,
    imgsz=640
)

cap = cv2.VideoCapture(VIDEO_PATH)

# Go directly to a frame where our previous test found RoadDamages.
cap.set(cv2.CAP_PROP_POS_FRAMES, 560)

ok, frame = cap.read()

if not ok:
    print("Could not read video.")
    cap.release()
    raise SystemExit

print("\n=== CODYSSEY DETECTOR DEBUG ===")
print("Frame: 560")
print()

detections = detector.detect(frame)

print("DETECTIONS RETURNED BY detector.py:")

for detection in detections:
    print(detection)

print()
print("TOTAL:", len(detections))

print("\nTRAFFIC COUNT:")
print(detector.count_traffic(detections))

print("\nTRAFFIC INDEX:")
print(
    detector.calculate_traffic_index(
        detections,
        frame.shape[1],
        frame.shape[0]
    )
)

cap.release()