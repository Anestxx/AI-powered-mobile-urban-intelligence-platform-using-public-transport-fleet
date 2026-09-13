import cv2
import os
import sys
import time
import requests


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.append(BASE_DIR)

from scripts.detector import RoadDetector
from scripts.alert_manager import AlertManager
from traffic_intelligence import TrafficIntelligence


GPS_DIR = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "05_gps_gis_prioritization"
    )
)

sys.path.append(GPS_DIR)

from gps_priority import GPSSimulator, PriorityEngine
from multi_bus_validator import MultiBusValidator


# ============================================================
# CONFIGURATION
# ============================================================

VIDEO_PATH = os.path.join(
    BASE_DIR,
    "videos",
    "road_test.mp4"
)

RAD_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "best.pt"
)

POTHOLE_MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "pothole.pt"
)

BACKEND_URL = (
    "http://127.0.0.1:8000/api/alerts"
)

BUS_ID = "BMTC-DEMO-01"


# ============================================================
# AI SETTINGS
# ============================================================

# AI inference happens every 3rd frame.
AI_FRAME_INTERVAL = 3

# CPU-friendly inference size.
AI_IMAGE_SIZE = 416


# ============================================================
# PLAYBACK SPEED
# ============================================================

# 1.00 = original speed
# 0.90 = slightly slow
# 0.80 = medium slow
# 0.70 = noticeably slow

PLAYBACK_SPEED = 0.80


# ============================================================
# DRAW DETECTIONS
# ============================================================

def draw_detections(
    frame,
    detections
):

    for detection in detections:

        bbox = detection.get("bbox")

        if not bbox:
            continue

        x1, y1, x2, y2 = bbox

        confidence = float(
            detection.get(
                "confidence",
                0
            )
        )

        class_name = detection.get(
            "class_name",
            "object"
        )

        label = (
            f"{class_name} "
            f"{confidence:.2f}"
        )

        # ----------------------------------------------------
        # Bounding box
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        # ----------------------------------------------------
        # Label dimensions
        # ----------------------------------------------------

        (
            text_width,
            text_height
        ), _ = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            2
        )

        label_top = max(
            0,
            y1 - text_height - 8
        )

        # ----------------------------------------------------
        # Label background
        # ----------------------------------------------------

        cv2.rectangle(
            frame,
            (x1, label_top),
            (
                x1 + text_width + 8,
                y1
            ),
            (0, 255, 0),
            -1
        )

        # ----------------------------------------------------
        # Label
        # ----------------------------------------------------

        cv2.putText(
            frame,
            label,
            (
                x1 + 4,
                max(
                    text_height + 2,
                    y1 - 4
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            2
        )


# ============================================================
# SEND ALERT
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
        # Event metadata
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
        # Multi-bus validation
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
        # Priority
        # ----------------------------------------------------

        priority = (
            priority_engine.calculate(
                alert["event_type"],
                alert["confidence"],
                bus_count
            )
        )

        # ----------------------------------------------------
        # Severity
        # ----------------------------------------------------

        severity = (
            priority_engine.severity(
                alert["event_type"],
                priority
            )
        )

        # ----------------------------------------------------
        # ONLY METADATA IS SENT
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
        # Extra traffic information
        #
        # The current backend schema does not have dedicated
        # fields for these values, so they are printed locally.
        # The actual alert still goes through the same backend.
        # ----------------------------------------------------

        if alert["event_type"] == "traffic":

            print(
                "\n"
                "------------------------------------------"
            )

            print(
                "TRAFFIC INTELLIGENCE ALERT"
            )

            print(
                f"Traffic Index : "
                f"{alert.get('traffic_index', 0)}"
            )

            print(
                f"Traffic Level : "
                f"{alert.get('traffic_level', 'high')}"
            )

            print(
                f"Vehicles      : "
                f"{alert.get('vehicle_count', 0)}"
            )

            print(
                f"Pedestrians   : "
                f"{alert.get('pedestrian_count', 0)}"
            )

            print(
                f"Confidence    : "
                f"{alert['confidence']:.2f}"
            )

            print(
                f"Severity      : "
                f"{severity}"
            )

            print(
                f"Bus           : "
                f"{BUS_ID}"
            )

            print(
                "------------------------------------------"
            )

        # ----------------------------------------------------
        # Send to FastAPI
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
                f"[ALERT SAVED] "
                f"{alert['event_type']} | "
                f"confidence="
                f"{alert['confidence']:.2f} | "
                f"priority={priority}"
            )

        else:

            print(
                f"[BACKEND ERROR] "
                f"HTTP {response.status_code}"
            )

    except Exception as e:

        print(
            f"[BACKEND] {e}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("CODYSSEY - AI VIDEO DEMO")
    print("=" * 70)

    # ========================================================
    # LOAD MODELS
    # ========================================================

    print("\nLoading AI models...")

    detector = RoadDetector(
        RAD_MODEL_PATH,
        POTHOLE_MODEL_PATH,
        imgsz=AI_IMAGE_SIZE
    )

    # --------------------------------------------------------
    # Normal event alert manager
    # --------------------------------------------------------

    alert_manager = AlertManager(
        required_detections=2,
        cooldown_seconds=8,
        persistence_window=5
    )

    # --------------------------------------------------------
    # Traffic intelligence engine
    # --------------------------------------------------------

    traffic_engine = TrafficIntelligence(
        congestion_index_threshold=60,
        congestion_vehicle_threshold=6,
        required_observations=3,
        persistence_window=6,
        cooldown_seconds=15
    )

    # --------------------------------------------------------
    # GPS
    # --------------------------------------------------------

    gps = GPSSimulator(
        start_lat=12.9716,
        start_lon=77.5946
    )

    # --------------------------------------------------------
    # Priority engine
    # --------------------------------------------------------

    priority_engine = PriorityEngine()

    # --------------------------------------------------------
    # Multi-bus validation
    # --------------------------------------------------------

    multi_bus_validator = (
        MultiBusValidator(
            distance_threshold_m=50,
            time_window_seconds=300
        )
    )

    print("AI models ready.")

    # ========================================================
    # OPEN VIDEO
    # ========================================================

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    if not cap.isOpened():

        print(
            "\nERROR: Could not open video:"
        )

        print(
            VIDEO_PATH
        )

        return

    # ========================================================
    # VIDEO INFORMATION
    # ========================================================

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:

        fps = 30.0

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    print("\nVideo:")

    print(
        f"Original FPS : {fps:.2f}"
    )

    print(
        f"Total frames : {total_frames}"
    )

    print(
        f"Playback     : {PLAYBACK_SPEED:.2f}x"
    )

    print(
        "\nAI processing starts..."
    )

    # ========================================================
    # IN-MEMORY PROCESSED VIDEO
    # ========================================================

    # Nothing is written to disk.
    #
    # Frames temporarily remain in RAM together with
    # the detections belonging to that exact frame.

    processed_video = []

    frame_number = 0

    total_detections = 0

    total_alerts = 0

    total_traffic_alerts = 0

    # ========================================================
    # PASS 1
    # AI PROCESSING
    # ========================================================

    while True:

        ret, frame = cap.read()

        if not ret:

            break

        frame_number += 1

        detections = []

        # ----------------------------------------------------
        # AI inference
        # ----------------------------------------------------

        if (
            frame_number
            % AI_FRAME_INTERVAL
            == 0
        ):

            try:

                detections = (
                    detector.detect(
                        frame
                    )
                )

            except Exception as e:

                print(
                    f"\n[AI ERROR] "
                    f"Frame {frame_number}: "
                    f"{e}"
                )

                detections = []

            total_detections += (
                len(detections)
            )

            # =================================================
            # TRAFFIC INTELLIGENCE
            # =================================================

            traffic_result = (
                traffic_engine.analyze(
                    detections
                )
            )

            vehicle_count = (
                traffic_result[
                    "vehicle_count"
                ]
            )

            pedestrian_count = (
                traffic_result[
                    "pedestrian_count"
                ]
            )

            traffic_index = (
                traffic_result[
                    "traffic_index"
                ]
            )

            traffic_level = (
                traffic_result[
                    "traffic_level"
                ]
            )

            congestion_confirmed = (
                traffic_result[
                    "congestion_confirmed"
                ]
            )

            # -------------------------------------------------
            # Terminal traffic status
            # -------------------------------------------------

            print(
                f"\r"
                f"[TRAFFIC] "
                f"Vehicles={vehicle_count} "
                f"Pedestrians={pedestrian_count} "
                f"Index={traffic_index} "
                f"Level={traffic_level}",
                end="",
                flush=True
            )

            # =================================================
            # CONGESTION ALERT
            # =================================================

            traffic_alert = (
                traffic_result.get(
                    "alert"
                )
            )

            if traffic_alert:

                print(
                    "\n"
                )

                print(
                    "🚦 "
                    "TRAFFIC CONGESTION DETECTED"
                )

                print(
                    f"   Vehicles: "
                    f"{traffic_alert['vehicle_count']}"
                )

                print(
                    f"   Traffic Index: "
                    f"{traffic_alert['traffic_index']}"
                )

                print(
                    f"   Confidence: "
                    f"{traffic_alert['confidence']}"
                )

                print(
                    f"   Severity: "
                    f"{traffic_alert['severity']}"
                )

                # ------------------------------------------------
                # Send traffic alert through normal backend path.
                # ------------------------------------------------

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

                # ------------------------------------------------
                # IMPORTANT:
                #
                # Traffic detections are NOT sent individually
                # through AlertManager.
                #
                # TrafficIntelligence handles them.
                # ------------------------------------------------

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

                if alert is not None:

                    send_alert(
                        alert,
                        gps,
                        priority_engine,
                        multi_bus_validator
                    )

                    total_alerts += 1

        # ====================================================
        # STORE ONLY IN RAM
        # ====================================================

        processed_video.append(
            (
                frame,
                detections
            )
        )

        # ====================================================
        # PROGRESS
        # ====================================================

        if frame_number % 30 == 0:

            percentage = (
                frame_number
                / total_frames
                * 100
            )

            print(
                f"\rAI processing: "
                f"{frame_number}/"
                f"{total_frames} "
                f"({percentage:.1f}%)",
                end="",
                flush=True
            )

    cap.release()

    print("\n")

    # ========================================================
    # AI PROCESSING SUMMARY
    # ========================================================

    print("=" * 70)
    print("AI PROCESSING COMPLETE")
    print("=" * 70)

    print(
        f"Frames            : "
        f"{frame_number}"
    )

    print(
        f"Detections        : "
        f"{total_detections}"
    )

    print(
        f"Total alerts      : "
        f"{total_alerts}"
    )

    print(
        f"Traffic alerts    : "
        f"{total_traffic_alerts}"
    )

    print(
        "Saved files       : NONE"
    )

    # ========================================================
    # PASS 2
    # PLAYBACK
    # ========================================================

    print(
        "\nStarting playback..."
    )

    print(
        f"Speed: "
        f"{PLAYBACK_SPEED:.2f}x"
    )

    print(
        "Press Q to stop."
    )

    # ========================================================
    # PLAYBACK INTERVAL
    # ========================================================

    frame_interval = (
        1.0
        / fps
        / PLAYBACK_SPEED
    )

    next_frame_time = (
        time.perf_counter()
    )

    # ========================================================
    # PLAY
    # ========================================================

    for frame, detections in processed_video:

        # ----------------------------------------------------
        # Draw detections belonging to this exact frame
        # ----------------------------------------------------

        draw_detections(
            frame,
            detections
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        cv2.imshow(
            "CODYSSEY - AI Edge Intelligence",
            frame
        )

        # ----------------------------------------------------
        # Medium-slow playback
        # ----------------------------------------------------

        next_frame_time += (
            frame_interval
        )

        remaining = (
            next_frame_time
            - time.perf_counter()
        )

        if remaining > 0:

            key = cv2.waitKey(
                max(
                    1,
                    int(
                        remaining
                        * 1000
                    )
                )
            ) & 0xFF

        else:

            key = cv2.waitKey(
                1
            ) & 0xFF

            next_frame_time = (
                time.perf_counter()
            )

        # ----------------------------------------------------
        # Quit
        # ----------------------------------------------------

        if key == ord("q"):

            break

    # ========================================================
    # CLEANUP
    # ========================================================

    processed_video.clear()

    cv2.destroyAllWindows()

    print(
        "\n"
        + "=" * 70
    )

    print(
        "CODYSSEY DEMO FINISHED"
    )

    print("=" * 70)

    print(
        f"Frames processed : "
        f"{frame_number}"
    )

    print(
        f"Detections       : "
        f"{total_detections}"
    )

    print(
        f"Alerts           : "
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
        "Backend          : metadata only"
    )

    print("=" * 70)


# ============================================================
# WINDOWS ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main() 