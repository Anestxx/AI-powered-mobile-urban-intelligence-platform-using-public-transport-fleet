import cv2
import os

VIDEO_PATH = "videos/road_test.mp4"
OUTPUT_DIR = "extracted_frames"
FRAME_INTERVAL = 15

os.makedirs(OUTPUT_DIR, exist_ok=True)

cap = cv2.VideoCapture(VIDEO_PATH)
frame_count = 0
saved_count = 0

while True:
    success, frame = cap.read()
    if not success:
        break

    if frame_count % FRAME_INTERVAL == 0:
        filename = os.path.join(OUTPUT_DIR, f"frame_{saved_count:04d}.jpg")
        cv2.imwrite(filename, frame)
        saved_count += 1

    frame_count += 1

cap.release()
print(f"Extracted {saved_count} frames to {OUTPUT_DIR}/")