import cv2
import os
import torch
import threading
import time
from ultralytics import YOLOWorld


# ============================================================
# CODYSSEY - REAL-TIME EMERGENCY AI TEST
# ============================================================
#
# Video playback and AI inference run independently.
#
# Video:
#     Plays at original FPS
#
# AI:
#     Runs in a background thread
#     Processes selected frames
#     Keeps the latest detection
#
# This prevents slow CPU inference from slowing down
# the actual video playback.
# ============================================================


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "emergency.pt"
)

VIDEO_PATH = os.path.join(
    BASE_DIR,
    "videos",
    "ambulance_test.mp4"
)


# ============================================================
# SETTINGS
# ============================================================

EMERGENCY_CLASSES = [
    "ambulance",
    "emergency vehicle",
    "police car",
    "fire truck"
]

# Lower = more detections but slower
# Higher = faster but less sensitive
CONFIDENCE_THRESHOLD = 0.25

# Smaller image = faster CPU inference
IMAGE_SIZE = 416

# AI will process one frame every N frames.
#
# Example:
# 30 FPS video + AI_FRAME_SKIP = 5
# means AI checks approximately 6 frames/second.
AI_FRAME_SKIP = 5


# ============================================================
# GLOBAL AI STATE
# ============================================================

latest_detections = []

ai_lock = threading.Lock()

ai_running = True

ai_frames_processed = 0


# ============================================================
# CHECK FILES
# ============================================================

print("=" * 70)
print("CODYSSEY - REAL-TIME EMERGENCY AI TEST")
print("=" * 70)

print("\nModel:")
print(MODEL_PATH)

print("\nVideo:")
print(VIDEO_PATH)

if not os.path.exists(MODEL_PATH):

    print("\nERROR: emergency.pt not found!")

    print(
        "Expected:",
        MODEL_PATH
    )

    raise SystemExit


if not os.path.exists(VIDEO_PATH):

    print("\nERROR: ambulance_test.mp4 not found!")

    print(
        "Expected:",
        VIDEO_PATH
    )

    raise SystemExit


# ============================================================
# DEVICE
# ============================================================

device = 0 if torch.cuda.is_available() else "cpu"

print("\nDevice:", device)

if device == "cpu":

    print(
        "CPU mode detected."
    )

    print(
        "AI inference will run in background."
    )

else:

    print(
        "GPU mode detected."
    )


# ============================================================
# LOAD MODEL
# ============================================================

print("\nLoading YOLO-World...")

model = YOLOWorld(MODEL_PATH)

model.set_classes(
    EMERGENCY_CLASSES
)

print("\nEmergency classes:")

for index, name in enumerate(
    EMERGENCY_CLASSES
):

    print(
        f"  {index}: {name}"
    )


print("\nYOLO-World loaded successfully.")


# ============================================================
# OPEN VIDEO
# ============================================================

cap = cv2.VideoCapture(
    VIDEO_PATH
)

if not cap.isOpened():

    print(
        "\nERROR: Could not open video."
    )

    raise SystemExit


fps = cap.get(
    cv2.CAP_PROP_FPS
)

if fps <= 0:

    fps = 30


total_frames = int(
    cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    )
)

duration = (
    total_frames / fps
    if fps > 0
    else 0
)


print("\nVideo information:")
print(
    "FPS:",
    round(fps, 2)
)

print(
    "Frames:",
    total_frames
)

print(
    "Duration:",
    round(duration, 2),
    "seconds"
)

print(
    "AI frame skip:",
    AI_FRAME_SKIP
)

print(
    "Approx AI processing rate:",
    round(
        fps / AI_FRAME_SKIP,
        2
    ),
    "frames/sec"
)


# ============================================================
# AI WORKER
# ============================================================

def ai_worker():

    global latest_detections
    global ai_running
    global ai_frames_processed

    while ai_running:

        # Get the most recent frame
        with ai_lock:

            if "current_frame" not in shared_frame:

                frame = None

            else:

                frame = shared_frame["current_frame"]

        if frame is None:

            time.sleep(0.001)

            continue


        # ----------------------------------------------------
        # RUN YOLO
        # ----------------------------------------------------

        try:

            results = model.predict(
                frame,
                imgsz=IMAGE_SIZE,
                conf=CONFIDENCE_THRESHOLD,
                device=device,
                verbose=False
            )

            detections = []

            if results:

                result = results[0]

                if result.boxes is not None:

                    for box in result.boxes:

                        class_id = int(
                            box.cls[0]
                        )

                        confidence = float(
                            box.conf[0]
                        )

                        class_name = model.names[
                            class_id
                        ]

                        x1, y1, x2, y2 = (
                            box.xyxy[0].tolist()
                        )

                        detections.append({

                            "event_type":
                                "emergency",

                            "class_name":
                                class_name,

                            "class_id":
                                class_id,

                            "confidence":
                                round(
                                    confidence,
                                    4
                                ),

                            "bbox": [
                                int(x1),
                                int(y1),
                                int(x2),
                                int(y2)
                            ]

                        })


            # ------------------------------------------------
            # UPDATE LATEST DETECTIONS
            # ------------------------------------------------

            with ai_lock:

                latest_detections = detections

                ai_frames_processed += 1

        except Exception as error:

            print(
                "\nAI ERROR:",
                error
            )

            time.sleep(0.1)


# ============================================================
# SHARED FRAME
# ============================================================

shared_frame = {
    "current_frame": None
}


# ============================================================
# START AI THREAD
# ============================================================

ai_thread = threading.Thread(
    target=ai_worker,
    daemon=True
)

ai_thread.start()

print(
    "\nAI background worker started."
)

print(
    "Video playback started."
)

print(
    "Press Q to quit."
)

print("=" * 70)


# ============================================================
# VIDEO PLAYBACK
# ============================================================

frame_count = 0

start_time = time.time()

last_detection_time = 0

# Original video frame duration
frame_duration = 1.0 / fps


while True:

    ret, frame = cap.read()

    if not ret:

        break


    frame_count += 1


    # --------------------------------------------------------
    # SEND FRAME TO AI EVERY N FRAMES
    # --------------------------------------------------------

    if frame_count % AI_FRAME_SKIP == 0:

        with ai_lock:

            # Copy so playback can continue safely
            shared_frame["current_frame"] = (
                frame.copy()
            )


    # --------------------------------------------------------
    # GET LATEST AI DETECTIONS
    # --------------------------------------------------------

    with ai_lock:

        detections = list(
            latest_detections
        )


    # --------------------------------------------------------
    # DRAW AI DETECTIONS
    # --------------------------------------------------------

    display_frame = frame.copy()


    if detections:

        last_detection_time = time.time()


    for detection in detections:

        x1, y1, x2, y2 = (
            detection["bbox"]
        )

        confidence = (
            detection["confidence"]
        )

        class_name = (
            detection["class_name"]
        )


        # Red emergency box
        cv2.rectangle(

            display_frame,

            (x1, y1),

            (x2, y2),

            (0, 0, 255),

            3

        )


        label = (

            f"EMERGENCY: "
            f"{class_name} "
            f"{confidence:.2f}"

        )


        (
            text_width,
            text_height
        ), baseline = cv2.getTextSize(

            label,

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            2

        )


        label_y = max(
            0,
            y1 - text_height - 15
        )


        cv2.rectangle(

            display_frame,

            (
                x1,
                label_y
            ),

            (
                x1 + text_width + 10,
                y1
            ),

            (0, 0, 255),

            -1

        )


        cv2.putText(

            display_frame,

            label,

            (
                x1 + 5,
                y1 - 7
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (255, 255, 255),

            2

        )


    # --------------------------------------------------------
    # EMERGENCY STATUS
    # --------------------------------------------------------

    if detections:

        status = (
            "EMERGENCY VEHICLE DETECTED"
        )

        status_color = (
            0,
            0,
            255
        )

    else:

        status = (
            "NORMAL TRAFFIC"
        )

        status_color = (
            0,
            255,
            0
        )


    # --------------------------------------------------------
    # STATUS PANEL
    # --------------------------------------------------------

    cv2.rectangle(

        display_frame,

        (10, 10),

        (680, 105),

        (20, 20, 20),

        -1

    )


    cv2.putText(

        display_frame,

        status,

        (25, 45),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.8,

        status_color,

        2

    )


    cv2.putText(

        display_frame,

        f"Frame: {frame_count}",

        (25, 72),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (255, 255, 255),

        1

    )


    cv2.putText(

        display_frame,

        f"AI frames: {ai_frames_processed}",

        (25, 95),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.50,

        (200, 200, 200),

        1

    )


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    cv2.imshow(

        "CODYSSEY - Emergency AI",

        display_frame

    )


    # --------------------------------------------------------
    # ORIGINAL PLAYBACK SPEED
    # --------------------------------------------------------

    key = cv2.waitKey(
        max(
            1,
            int(
                frame_duration * 1000
            )
        )
    ) & 0xFF


    if key == ord("q"):

        break


# ============================================================
# STOP AI THREAD
# ============================================================

ai_running = False

ai_thread.join(
    timeout=2
)


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()


# ============================================================
# FINAL REPORT
# ============================================================

elapsed = (
    time.time() - start_time
)

print("\n" + "=" * 70)

print(
    "EMERGENCY AI TEST COMPLETE"
)

print("=" * 70)

print(
    "Video frames:",
    frame_count
)

print(
    "AI frames processed:",
    ai_frames_processed
)

print(
    "Elapsed time:",
    round(elapsed, 2),
    "seconds"
)

if elapsed > 0:

    print(
        "Playback processing rate:",
        round(
            frame_count / elapsed,
            2
        ),
        "FPS"
    )


print("=" * 70)