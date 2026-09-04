import cv2
from ultralytics import YOLO

VIDEO_PATH = "videos/road_test.mp4"
MODEL_PATH = "models/best.pt"

print("Loading pothole detection model...")
model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Cannot open video")
    exit()

print("Pothole AI processing started")
print("Press Q to quit")

while True:

    success, frame = cap.read()

    if not success:
        print("Video finished")
        break

    results = model(frame, conf=0.40)

    annotated_frame = results[0].plot()

    cv2.imshow(
        "Edge AI - Pothole Detection",
        annotated_frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()