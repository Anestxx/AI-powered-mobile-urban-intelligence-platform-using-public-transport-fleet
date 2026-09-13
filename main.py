import cv2
import os
import sys
import time
import requests


# ============================================================
# PATH SETUP
# ============================================================

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

AI_DIR = os.path.dirname(
    SCRIPT_DIR
)

PROJECT_ROOT = os.path.dirname(
    AI_DIR
)

sys.path.append(AI_DIR)

GPS_DIR = os.path.join(
    PROJECT_ROOT,
    "05_gps_gis_prioritization"
)

sys.path.append(GPS_DIR)


# ============================================================
# IMPORTS
# ============================================================

from scripts.detector import RoadDetector
from scripts.alert_manager import AlertManager
from traffic_intelligence import TrafficIntelligence

from gps_priority import (
    GPSSimulator,
    PriorityEngine
)

from multi_bus_validator import (
    MultiBusValidator
)


# ============================================================
# PATHS
# ============================================================

VIDEO_PATH = os.path.join(
    AI_DIR,
    "videos",
    "road_test.mp4"
)

RAD_MODEL_PATH = os.path.join(
    AI_DIR,
    "models",
    "best.pt"
)

POTHOLE_MODEL_PATH = os.path.join(
    AI_DIR,
    "models",
    "pothole.pt"
)


# ============================================================
# BACKEND
# ============================================================

BACKEND_URL = (
    "http://127.0.0.1:8000/api/alerts"
)


# ============================================================
# BUS
# ============================================================

BUS_ID = "BMTC-DEMO-01"


# ============================================================
# AI CONFIGURATION
# ============================================================

# Run AI every N frames.
#
# 1 = every frame
# 2 = every second frame
# 3 = every third frame
#
# 3 is recommended for your CPU.
#
AI_FRAME_INTERVAL = 3


# Inference image size.
AI_IMAGE_SIZE = 416


# ============================================================
# PLAYBACK
# ============================================================

# 1.00 = normal speed
# 0.90 = slightly slower
# 0.80 = medium slow

PLAYBACK_SPEED = 0.80


# ============================================================
# CONFIDENCE
# ============================================================

# IMPORTANT:
#
# This value is NOT directly passed into RoadDetector because
# the current detector has separate confidence thresholds
# for the RAD model and pothole model.
#
# AlertManager performs additional filtering.
#
CONFIDENCE = 0.15


# ============================================================
# SEND ALERT TO BACKEND
# ============================================================

def send_alert(
    alert,
    gps,
    priority_engine,
    multi_bus_validator
):

    try:

        # ----------------------------------------------------
        # GPS
        # ----------------------------------------------------

        location = gps.move()

        # ----------------------------------------------------
        # Base event
        # ----------------------------------------------------

        event = {
            "event_type": alert["event_type"],
            "confidence": alert["confidence"],
            "bus_id": BUS_ID,
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "timestamp": alert["timestamp"]
        }

        # ----------------------------------------------------
        # MULTI-BUS VALIDATION
        # ----------------------------------------------------

        validation = (
            multi_bus_validator.add_event(
                event
            )
        )

        cross_bus = (
            validation[
                "cross_bus_validation"
            ]
        )

        bus_count = (
            cross_bus["bus_count"]
        )

        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        priority = (
            priority_engine.calculate(
                alert["event_type"],
                alert["confidence"],
                bus_count
            )
        )

        # ----------------------------------------------------
        # SEVERITY
        # ----------------------------------------------------

        severity = (
            priority_engine.severity(
                alert["event_type"],
                priority
            )
        )

        # ----------------------------------------------------
        # BACKEND PAYLOAD
        #
        # Only metadata is transmitted.
        # ----------------------------------------------------

        payload = {
            "event_type": alert["event_type"],
            "confidence": alert["confidence"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "severity": severity,
            "priority_score": priority,
            "bus_id": BUS_ID,
            "timestamp": alert["timestamp"],
            "bbox": str(
                alert.get("bbox")
            )
        }

        # ----------------------------------------------------
        # SEND
        # ----------------------------------------------------

        response = requests.post(
            BACKEND_URL,
            json=payload,
            timeout=2
        )

        if response.status_code in (
            200,
            201
        ):

            print(
                f"\n[ALERT SAVED] "
                f"{alert['event_type']} | "
                f"confidence="
                f"{alert['confidence']:.2f} | "
                f"priority={priority} | "
                f"bus_count={bus_count}"
            )

        else:

            print(
                f"\n[BACKEND ERROR] "
                f"HTTP {response.status_code}"
            )

    except Exception as e:

        print(
            f"\n[BACKEND] {e}"
        )


# ============================================================
# DRAW TRAFFIC INFORMATION
# ============================================================

def draw_traffic_panel(
    frame,
    traffic_result
):

    height, width = frame.shape[:2]

    vehicle_count = (
        traffic_result.get(
            "vehicle_count",
            0
        )
    )

    pedestrian_count = (
        traffic_result.get(
            "pedestrian_count",
            0
        )
    )

    traffic_index = (
        traffic_result.get(
            "traffic_index",
            0
        )
    )

    traffic_level = (
        traffic_result.get(
            "traffic_level",
            "low"
        )
    )

    congestion_confirmed = (
        traffic_result.get(
            "congestion_confirmed",
            False
        )
    )

    # --------------------------------------------------------
    # Panel background
    # --------------------------------------------------------

    panel_width = 360
    panel_height = 145

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (
            width - panel_width - 15,
            15
        ),
        (
            width - 15,
            15 + panel_height
        ),
        (20, 20, 20),
        -1
    )

    # Transparent panel
    frame = cv2.addWeighted(
        overlay,
        0.82,
        frame,
        0.18,
        0
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    cv2.putText(
        frame,
        "CODYSSEY TRAFFIC INTELLIGENCE",
        (
            width - panel_width,
            42
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 255),
        2
    )

    # --------------------------------------------------------
    # Vehicle count
    # --------------------------------------------------------

    cv2.putText(
        frame,
        f"Vehicles: {vehicle_count}",
        (
            width - panel_width,
            70
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    # --------------------------------------------------------
    # Pedestrians
    # --------------------------------------------------------

    cv2.putText(
        frame,
        f"Pedestrians: {pedestrian_count}",
        (
            width - panel_width,
            95
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    # --------------------------------------------------------
    # Traffic index
    # --------------------------------------------------------

    cv2.putText(
        frame,
        f"Traffic Index: {traffic_index}",
        (
            width - panel_width,
            120
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 0),
        2
    )

    # --------------------------------------------------------
    # Traffic level
    # --------------------------------------------------------

    level_text = (
        f"Level: {traffic_level.upper()}"
    )

    cv2.putText(
        frame,
        level_text,
        (
            width - panel_width,
            145
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 200, 255),
        2
    )

    # --------------------------------------------------------
    # Congestion status
    # --------------------------------------------------------

    if congestion_confirmed:

        cv2.putText(
            frame,
            "CONGESTION CONFIRMED",
            (
                width - panel_width,
                172
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            (0, 0, 255),
            2
        )

    return frame


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "CODYSSEY - EDGE AI GATEWAY"
    )
    print("=" * 70)

    # ========================================================
    # CHECK FILES
    # ========================================================

    print("\nChecking files...")

    if not os.path.exists(
        VIDEO_PATH
    ):

        print(
            "ERROR: Video not found:"
        )

        print(
            VIDEO_PATH
        )

        return

    if not os.path.exists(
        RAD_MODEL_PATH
    ):

        print(
            "ERROR: RAD model not found:"
        )

        print(
            RAD_MODEL_PATH
        )

        return

    if not os.path.exists(
        POTHOLE_MODEL_PATH
    ):

        print(
            "ERROR: Pothole model not found:"
        )

        print(
            POTHOLE_MODEL_PATH
        )

        return

    print(
        "All required files found."
    )

    # ========================================================
    # LOAD AI
    # ========================================================

    print(
        "\nLoading dual AI detector..."
    )

    detector = RoadDetector(
        RAD_MODEL_PATH,
        POTHOLE_MODEL_PATH,
        imgsz=AI_IMAGE_SIZE
    )

    # ========================================================
    # ALERT MANAGER
    # ========================================================

    alert_manager = AlertManager(
        required_detections=3,
        cooldown_seconds=10,
        persistence_window=5
    )

    # ========================================================
    # TRAFFIC INTELLIGENCE
    # ========================================================

    traffic_engine = TrafficIntelligence(
        congestion_index_threshold=60,
        congestion_vehicle_threshold=6,
        required_observations=3,
        persistence_window=6,
        cooldown_seconds=15
    )

    # ========================================================
    # GPS
    # ========================================================

    gps = GPSSimulator(
        start_lat=12.9716,
        start_lon=77.5946
    )

    # ========================================================
    # PRIORITY
    # ========================================================

    priority_engine = PriorityEngine()

    # ========================================================
    # MULTI-BUS
    # ========================================================

    multi_bus_validator = (
        MultiBusValidator(
            distance_threshold_m=50,
            time_window_seconds=300
        )
    )

    print(
        "\nEDGE AI SYSTEM READY."
    )

    # ========================================================
    # OPEN VIDEO
    # ========================================================

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    if not cap.isOpened():

        print(
            "ERROR: Cannot open video."
        )

        return

    # ========================================================
    # VIDEO INFORMATION
    # ========================================================

    video_fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if (
        not video_fps
        or video_fps <= 1
    ):

        video_fps = 30.0

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    print(
        f"\nVideo FPS: "
        f"{video_fps:.2f}"
    )

    print(
        f"Total frames: "
        f"{total_frames}"
    )

    print(
        f"AI interval: "
        f"Every {AI_FRAME_INTERVAL} frames"
    )

    print(
        f"Playback speed: "
        f"{PLAYBACK_SPEED:.2f}x"
    )

    print(
        "\nPress Q to quit."
    )

    # ========================================================
    # PLAYBACK DELAY
    # ========================================================

    frame_delay_ms = max(
        1,
        int(
            (
                1000
                / video_fps
            )
            / PLAYBACK_SPEED
        )
    )

    # ========================================================
    # STATE
    # ========================================================

    frame_count = 0

    last_detections = []

    last_traffic_result = {
        "vehicle_count": 0,
        "pedestrian_count": 0,
        "traffic_index": 0,
        "traffic_level": "low",
        "congestion_confirmed": False
    }

    total_detections = 0

    total_alerts = 0

    total_traffic_alerts = 0

    # ========================================================
    # FPS
    # ========================================================

    prev_time = time.perf_counter()

    display_fps = 0.0

    # ========================================================
    # MAIN LOOP
    # ========================================================

    while True:

        success, frame = cap.read()

        if not success:

            print(
                "\nVideo finished."
            )

            break

        frame_count += 1

        # ====================================================
        # RUN AI
        # ====================================================

        run_ai = (
            frame_count
            % AI_FRAME_INTERVAL
            == 0
        )

        if run_ai:

            try:

                detections = (
                    detector.detect(
                        frame
                    )
                )

            except Exception as e:

                print(
                    f"\n[AI ERROR] "
                    f"Frame {frame_count}: "
                    f"{e}"
                )

                detections = []

            total_detections += (
                len(detections)
            )

            # =================================================
            # TRAFFIC INTELLIGENCE
            # =================================================

            try:

                traffic_result = (
                    traffic_engine.analyze(
                        detections
                    )
                )

                last_traffic_result = (
                    traffic_result
                )

            except Exception as e:

                print(
                    f"\n[TRAFFIC ERROR] "
                    f"{e}"
                )

                traffic_result = (
                    last_traffic_result
                )

            # =================================================
            # TRAFFIC ALERT
            # =================================================

            traffic_alert = (
                traffic_result.get(
                    "alert"
                )
            )

            if traffic_alert:

                print(
                    "\n"
                    "=========================================="
                )

                print(
                    "🚦 TRAFFIC CONGESTION DETECTED"
                )

                print(
                    f"Vehicles: "
                    f"{traffic_alert['vehicle_count']}"
                )

                print(
                    f"Traffic Index: "
                    f"{traffic_alert['traffic_index']}"
                )

                print(
                    f"Confidence: "
                    f"{traffic_alert['confidence']:.2f}"
                )

                print(
                    f"Severity: "
                    f"{traffic_alert['severity']}"
                )

                print(
                    "=========================================="
                )

                send_alert(
                    traffic_alert,
                    gps,
                    priority_engine,
                    multi_bus_validator
                )

                total_alerts += 1

                total_traffic_alerts += 1

            # =================================================
            # NORMAL EVENT ALERTS
            # =================================================

            for detection in detections:

                # Traffic is already handled by
                # TrafficIntelligence.
                if (
                    detection.get(
                        "event_type"
                    )
                    == "traffic"
                ):

                    continue

                alert = (
                    alert_manager
                    .process_detection(
                        detection
                    )
                )

                if alert:

                    print(
                        "\n🚨 VALIDATED ALERT"
                    )

                    print(
                        alert
                    )

                    send_alert(
                        alert,
                        gps,
                        priority_engine,
                        multi_bus_validator
                    )

                    total_alerts += 1

            last_detections = (
                detections
            )

        # ====================================================
        # DRAW DETECTIONS
        # ====================================================

        annotated_frame = frame.copy()

        annotated_frame = (
            detector.draw_detections(
                annotated_frame,
                last_detections
            )
        )

        # ====================================================
        # TRAFFIC PANEL
        # ====================================================

        annotated_frame = (
            draw_traffic_panel(
                annotated_frame,
                last_traffic_result
            )
        )

        # ====================================================
        # FPS
        # ====================================================

        current_time = (
            time.perf_counter()
        )

        elapsed = (
            current_time
            - prev_time
        )

        if elapsed > 0:

            display_fps = (
                1.0
                / elapsed
            )

        prev_time = current_time

        cv2.putText(
            annotated_frame,
            f"FPS: {display_fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        # ====================================================
        # BUS ID
        # ====================================================

        cv2.putText(
            annotated_frame,
            f"BUS: {BUS_ID}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        # ====================================================
        # EDGE AI STATUS
        # ====================================================

        cv2.putText(
            annotated_frame,
            "EDGE AI: ACTIVE",
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2
        )

        # ====================================================
        # DISPLAY
        # ====================================================

        cv2.imshow(
            "CODYSSEY - Urban Intelligence Edge",
            annotated_frame
        )

        # ====================================================
        # WAIT
        # ====================================================

        key = cv2.waitKey(
            frame_delay_ms
        ) & 0xFF

        if key == ord("q"):

            print(
                "\nQ pressed. Stopping..."
            )

            break

    # ========================================================
    # CLEANUP
    # ========================================================

    cap.release()

    cv2.destroyAllWindows()

    # ========================================================
    # SUMMARY
    # ========================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "CODYSSEY EDGE AI FINISHED"
    )

    print("=" * 70)

    print(
        f"Frames processed : "
        f"{frame_count}"
    )

    print(
        f"AI detections    : "
        f"{total_detections}"
    )

    print(
        f"Total alerts     : "
        f"{total_alerts}"
    )

    print(
        f"Traffic alerts   : "
        f"{total_traffic_alerts}"
    )

    print(
        "Frames saved     : 0"
    )

    print(
        "Video saved      : 0"
    )

    print(
        "Raw video upload : 0"
    )

    print(
        "Backend data     : Metadata only"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()