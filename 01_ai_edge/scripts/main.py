import cv2
import time
import requests
from datetime import datetime

from detector import RoadDetector
from alert_manager import AlertManager
from alert_logger import AlertLogger


# ============================================================
# CODYSSEY CONFIGURATION
# ============================================================

VIDEO_PATH = "01_ai_edge/videos/road_test.mp4"
MODEL_PATH = "01_ai_edge/models/best.pt"

BUS_ID = "BMTC-DEMO-01"

BACKEND_URL = "http://127.0.0.1:8000/api/alerts"

# ============================================================
# PERFORMANCE
# ============================================================

# AI does NOT need to run on every camera frame.
#
# Frames are processed only in RAM and immediately discarded.
# Nothing is saved to disk.
AI_FRAME_INTERVAL = 3

# Smaller inference size makes CPU inference substantially faster.
AI_IMAGE_SIZE = 416

# Lower threshold helps recover weaker road-damage detections.
CONFIDENCE = 0.12

# Keep video playback close to its original speed.
PLAYBACK_SPEED = 1.0

# ============================================================
# DEMO GPS
# ============================================================

# Temporary simulated bus location.
# Later replaced with actual GPS.
BUS_LATITUDE = 12.9716
BUS_LONGITUDE = 77.5946


# ============================================================
# INITIALIZE DETECTOR
# ============================================================

detector = RoadDetector(
    MODEL_PATH,
    imgsz=AI_IMAGE_SIZE
)


# ============================================================
# INITIALIZE ALERT MANAGER
# ============================================================

alert_manager = AlertManager(
    required_detections=2,
    cooldown_seconds=8,
    persistence_window=5
)


# ============================================================
# ALERT LOGGER
# ============================================================

alert_logger = AlertLogger()


# ============================================================
# OPEN VIDEO
# ============================================================

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():

    print("ERROR: Cannot open video.")

    raise SystemExit(1)


video_fps = cap.get(
    cv2.CAP_PROP_FPS
)

if not video_fps or video_fps <= 1:
    video_fps = 30


frame_width = int(
    cap.get(cv2.CAP_PROP_FRAME_WIDTH)
)

frame_height = int(
    cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
)


# ============================================================
# DISPLAY TIMING
# ============================================================

frame_delay_ms = max(
    1,
    int(
        1000
        /
        video_fps
        /
        PLAYBACK_SPEED
    )
)


# ============================================================
# START MESSAGE
# ============================================================

print()

print("=" * 65)
print(" CODYSSEY - MOBILE URBAN INTELLIGENCE")
print("=" * 65)

print(f"Bus ID          : {BUS_ID}")
print(f"Video resolution: {frame_width}x{frame_height}")
print(f"Source FPS      : {video_fps:.1f}")
print(f"AI interval     : Every {AI_FRAME_INTERVAL} frames")
print(f"AI image size   : {AI_IMAGE_SIZE}x{AI_IMAGE_SIZE}")
print(f"AI confidence   : {CONFIDENCE}")
print(f"Playback speed  : {PLAYBACK_SPEED}x")

print()

print("EDGE PROCESSING")
print("-----------------------------")
print("Video storage   : DISABLED")
print("Frame storage   : DISABLED")
print("Alert storage   : ENABLED")
print("AI processing   : IN MEMORY")
print("Backend payload : METADATA ONLY")

print()

print("Detected classes:")
print("  HMV")
print("  LMV")
print("  Pedestrian")
print("  RoadDamages")
print("  SpeedBump")
print("  UnsurfacedRoad")

print()

print("Press Q to quit.")

print("=" * 65)


# ============================================================
# RUNTIME VARIABLES
# ============================================================

frame_number = 0

ai_processed_frames = 0

total_alerts = 0

current_detections = []

traffic_stats = {
    "vehicle_count": 0,
    "hmv_count": 0,
    "lmv_count": 0,
    "pedestrian_count": 0
}

traffic_index = 0

last_inference_time = 0

backend_online = True


# ============================================================
# SEND ALERT TO BACKEND
# ============================================================

def send_alert_to_backend(alert):

    global backend_online

    payload = {
        "event_type": alert["event_type"],

        "confidence": alert["confidence"],

        "latitude": BUS_LATITUDE,

        "longitude": BUS_LONGITUDE,

        "severity": alert["severity"],

        "priority_score": alert["priority_score"],

        "bus_id": BUS_ID,

        "timestamp": datetime.now().isoformat(),

        "bbox": str(alert["bbox"])
    }

    try:

        response = requests.post(
            BACKEND_URL,
            json=payload,
            timeout=2
        )

        if response.status_code in (200, 201):

            backend_online = True

            print()
            print("🚨 CODYSSEY ALERT → BACKEND")
            print("-" * 55)

            print(
                f"Event      : "
                f"{alert['event_type']}"
            )

            print(
                f"Class      : "
                f"{alert['class_name']}"
            )

            print(
                f"Confidence : "
                f"{alert['confidence']}"
            )

            print(
                f"Severity   : "
                f"{alert['severity']}"
            )

            print(
                f"Priority   : "
                f"{alert['priority_score']}"
            )

            print(
                f"Bus        : "
                f"{BUS_ID}"
            )

            print(
                f"GPS        : "
                f"{BUS_LATITUDE}, "
                f"{BUS_LONGITUDE}"
            )

            print(
                "Storage    : ALERT METADATA ONLY"
            )

            print("-" * 55)

            return True

        backend_online = False

        print(
            f"Backend HTTP error: "
            f"{response.status_code}"
        )

    except requests.RequestException:

        if backend_online:

            print()
            print(
                "⚠ Backend unavailable."
            )

            print(
                "Alert remains available "
                "for local logging."
            )

            backend_online = False

    return False


# ============================================================
# DRAW DETECTIONS
# ============================================================

def draw_detection(
    frame,
    detection
):

    x1, y1, x2, y2 = detection["bbox"]

    class_name = detection[
        "class_name"
    ]

    confidence = detection[
        "confidence"
    ]

    event_type = detection[
        "event_type"
    ]


    # Road events = red
    if event_type in (
        "road_damage",
        "road_infrastructure"
    ):

        color = (
            0,
            0,
            255
        )

    # Traffic = blue
    elif event_type == "traffic":

        color = (
            255,
            180,
            0
        )

    else:

        color = (
            0,
            255,
            0
        )


    # Bounding box

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        color,
        3
    )


    # Label

    label = (
        f"{class_name} "
        f"{confidence:.2f}"
    )


    label_y = max(
        25,
        y1 - 8
    )


    cv2.putText(
        frame,
        label,
        (x1, label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2
    )


# ============================================================
# DRAW CODYSSEY UI
# ============================================================

def draw_interface(
    frame,
    traffic_stats,
    traffic_index,
    alert_count
):

    # --------------------------------------------------------
    # TOP BAR
    # --------------------------------------------------------

    cv2.rectangle(
        frame,
        (0, 0),
        (frame.shape[1], 100),
        (15, 15, 15),
        -1
    )


    cv2.putText(
        frame,
        "CODYSSEY | MOBILE URBAN INTELLIGENCE",
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.70,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        f"BUS: {BUS_ID}",
        (15, 62),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        "EDGE AI | METADATA ONLY",
        (15, 88),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.50,
        (180, 220, 255),
        2
    )


    # --------------------------------------------------------
    # TRAFFIC PANEL
    # --------------------------------------------------------

    panel_x = 15

    panel_y = 120


    lines = [
        (
            "Vehicles",
            traffic_stats["vehicle_count"]
        ),

        (
            "HMV",
            traffic_stats["hmv_count"]
        ),

        (
            "LMV",
            traffic_stats["lmv_count"]
        ),

        (
            "Pedestrians",
            traffic_stats[
                "pedestrian_count"
            ]
        ),

        (
            "Traffic Index",
            traffic_index
        ),

        (
            "Validated Alerts",
            alert_count
        )
    ]


    for i, (
        name,
        value
    ) in enumerate(lines):

        y = (
            panel_y
            +
            i * 28
        )


        cv2.putText(
            frame,
            f"{name}: {value}",
            (
                panel_x,
                y
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (255, 255, 255),
            2
        )


# ============================================================
# MAIN EDGE LOOP
# ============================================================

while True:

    success, frame = cap.read()

    if not success:

        print()
        print("Video finished.")

        break


    frame_number += 1


    # ========================================================
    # AI INFERENCE
    # ========================================================

    if (
        frame_number
        %
        AI_FRAME_INTERVAL
        == 0
    ):

        inference_start = time.time()


        # IMPORTANT:
        #
        # The frame exists only in RAM.
        #
        # Nothing is saved.
        #
        # YOLO processes it and the frame continues
        # through the display pipeline.

        current_detections = detector.detect(
            frame,
            confidence=CONFIDENCE
        )


        ai_processed_frames += 1


        # ----------------------------------------------------
        # TRAFFIC
        # ----------------------------------------------------

        traffic_stats = detector.count_traffic(
            current_detections
        )


        traffic_index = detector.calculate_traffic_index(
            current_detections,
            frame.shape[1],
            frame.shape[0]
        )


        # ----------------------------------------------------
        # ALERT VALIDATION
        # ----------------------------------------------------

        for detection in current_detections:

            alert = alert_manager.process_detection(
                detection
            )


            if alert is None:
                continue


            total_alerts += 1


            # Add bus information.

            alert["bus_id"] = BUS_ID


            # Add GPS information.

            alert["latitude"] = BUS_LATITUDE

            alert["longitude"] = BUS_LONGITUDE


            # ------------------------------------------------
            # CONSOLE
            # ------------------------------------------------

            print()

            print(
                "🚨🚨 VALIDATED URBAN EVENT 🚨🚨"
            )

            print(
                "=" * 55
            )

            print(
                f"Event      : "
                f"{alert['event_type']}"
            )

            print(
                f"Class      : "
                f"{alert['class_name']}"
            )

            print(
                f"Confidence : "
                f"{alert['confidence']}"
            )

            print(
                f"Severity   : "
                f"{alert['severity']}"
            )

            print(
                f"Priority   : "
                f"{alert['priority_score']}"
            )

            print(
                f"Bus ID     : "
                f"{BUS_ID}"
            )

            print(
                f"GPS        : "
                f"{BUS_LATITUDE}, "
                f"{BUS_LONGITUDE}"
            )

            print(
                "Storage    : "
                "METADATA ONLY"
            )

            print(
                "=" * 55
            )


            # ------------------------------------------------
            # LOCAL ALERT LOGGER
            # ------------------------------------------------

            alert_logger.save_alert(
                alert
            )


            # ------------------------------------------------
            # BACKEND
            # ------------------------------------------------

            send_alert_to_backend(
                alert
            )


        last_inference_time = (
            time.time()
            -
            inference_start
        )


    # ========================================================
    # DRAW
    # ========================================================

    display_frame = frame.copy()


    for detection in current_detections:

        draw_detection(
            display_frame,
            detection
        )


    draw_interface(
        display_frame,
        traffic_stats,
        traffic_index,
        total_alerts
    )


    # ========================================================
    # VIDEO INFORMATION
    # ========================================================

    cv2.putText(
        display_frame,
        f"Source FPS: {video_fps:.1f}",
        (
            15,
            display_frame.shape[0] - 45
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (200, 200, 200),
        1
    )


    cv2.putText(
        display_frame,
        f"AI frames: {ai_processed_frames}",
        (
            15,
            display_frame.shape[0] - 22
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (200, 200, 200),
        1
    )


    # ========================================================
    # SHOW
    # ========================================================

    cv2.imshow(
        "CODYSSEY - Urban Intelligence Edge Gateway",
        display_frame
    )


    # ========================================================
    # MAINTAIN ORIGINAL VIDEO SPEED
    # ========================================================

    key = cv2.waitKey(
        frame_delay_ms
    ) & 0xFF


    if key == ord("q"):

        print()
        print(
            "User stopped Edge AI."
        )

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

cv2.destroyAllWindows()


print()
print("=" * 65)
print("CODYSSEY EDGE AI STOPPED")
print("=" * 65)

print(
    f"Video frames read : "
    f"{frame_number}"
)

print(
    f"AI inferences     : "
    f"{ai_processed_frames}"
)

print(
    f"Validated alerts  : "
    f"{total_alerts}"
)

print(
    "Frames saved      : 0"
)

print(
    "Video saved       : 0"
)

print(
    "Persistent data   : ALERT METADATA ONLY"
)

print("=" * 65)