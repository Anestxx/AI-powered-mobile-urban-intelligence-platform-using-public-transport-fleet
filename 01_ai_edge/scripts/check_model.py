import cv2
from ultralytics import YOLO

MODEL_PATH = "01_ai_edge/models/best.pt"
VIDEO_PATH = "01_ai_edge/videos/road_test.mp4"

model = YOLO(MODEL_PATH)

print("MODEL CLASSES:")
print(model.names)
print()

cap = cv2.VideoCapture(VIDEO_PATH)

frame_number = 0
checked = 0
detections = []

while True:
    ok, frame = cap.read()

    if not ok:
        break

    frame_number += 1

    # Test every 10th frame.
    if frame_number % 10 != 0:
        continue

    checked += 1

    results = model.predict(
        frame,
        imgsz=640,
        conf=0.05,
        verbose=False
    )

    for box in results[0].boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])

        detections.append(
            (
                frame_number,
                model.names[class_id],
                round(confidence, 3)
            )
        )

    # Only test first 1000 frames for now.
    if frame_number >= 1000:
        break

cap.release()

print("Frames checked:", checked)
print("Total detections:", len(detections))
print()

detections.sort(key=lambda x: x[2], reverse=True)

print("TOP DETECTIONS:")
for item in detections[:30]:
    print(item)