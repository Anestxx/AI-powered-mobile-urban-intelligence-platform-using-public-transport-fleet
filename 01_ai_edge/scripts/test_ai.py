import cv2
from ultralytics import YOLO

VIDEO_PATH = "videos/road_test.mp4"

print("Loading AI model...")
model = YOLO("yolo11n.pt")

print("Opening video...")
cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Cannot open video")
    exit()

print("AI processing started")
print("Press Q to quit")

while True:

    success, frame = cap.read()

    if not success:
        print("Video finished")
        break

    # Run AI inference
    results = model(frame)

    # Draw AI detections
    annotated_frame = results[0].plot()

    # Show output
    cv2.imshow(
        "Edge AI - Urban Road Detection",
        annotated_frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()