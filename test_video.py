import cv2

VIDEO_PATH = "videos/road_test.mp4"

# Open the road video
cap = cv2.VideoCapture(VIDEO_PATH)

# Check whether the video opened
if not cap.isOpened():
    print("ERROR: Cannot open video.")
    print("Make sure road_test.mp4 is inside the videos folder.")
    exit()

print("Video opened successfully!")
print("Press Q to quit.")

while True:

    # Read the next frame
    success, frame = cap.read()

    # Video has finished
    if not success:
        print("Video finished.")
        break

    # Show the frame
    cv2.imshow("Simulated Bus Camera Feed", frame)

    # Press Q to stop
    if cv2.waitKey(25) & 0xFF == ord("q"):
        print("Stopped by user.")
        break


# Clean up
cap.release()
cv2.destroyAllWindows()