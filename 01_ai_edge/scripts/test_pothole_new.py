import cv2
from ultralytics import YOLO

MODEL_PATH = "01_ai_edge/models/pothole.pt"
VIDEO_PATH = "01_ai_edge/videos/road_test.mp4"

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise RuntimeError("Could not open road_test.mp4")

fps = cap.get(cv2.CAP_PROP_FPS) or 30

while True:
    ret, frame = cap.read()

    if not ret:
        break

    results = model.predict(
        frame,
        imgsz=640,
        conf=0.20,
        device="cpu",
        verbose=False
    )

    annotated = results[0].plot()

    cv2.imshow("CODYSSEY - Pothole Model", annotated)

    key = cv2.waitKey(int(1000 / fps)) & 0xFF

    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()