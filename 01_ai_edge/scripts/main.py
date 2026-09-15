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

from detector import RoadDetector
from alert_manager import AlertManager
from traffic_intelligence import TrafficIntelligence
from emergency_intelligence import EmergencyIntelligence

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

EMERGENCY_MODEL_PATH = os.path.join(
    AI_DIR,
    "models",
    "emergency.pt"
)

AMBULANCE_MODEL_PATH = os.path.join(
    AI_DIR,
    "models",
    "ambulance.pt"
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
# AI
# ============================================================

# AI runs continuously in a background worker.
# There is NO visible frame interval and NO skipped playback frames.
AI_IMAGE_SIZE = 416


# ============================================================
# PLAYBACK
# ============================================================

PLAYBACK_SPEED = 0.20


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
        # EVENT
        # ----------------------------------------------------

        event = {
            "event_type": alert[
                "event_type"
            ],
            "confidence": float(
                alert.get(
                    "confidence",
                    0
                )
            ),
            "bus_id": BUS_ID,
            "latitude": location[
                "latitude"
            ],
            "longitude": location[
                "longitude"
            ],
            "timestamp": alert.get(
                "timestamp",
                time.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )
            ),
        }

        # ----------------------------------------------------
        # MULTI-BUS
        # ----------------------------------------------------

        validation = (
            multi_bus_validator.add_event(
                event
            )
        )

        cross_bus = (
            validation.get(
                "cross_bus_validation",
                {}
            )
        )

        bus_count = int(
            cross_bus.get(
                "bus_count",
                1
            )
        )

        # ----------------------------------------------------
        # PRIORITY
        # ----------------------------------------------------

        if alert["event_type"] == "emergency":

            priority = 100.0

        else:

            priority = (
                priority_engine.calculate(
                    alert["event_type"],
                    float(
                        alert.get(
                            "confidence",
                            0
                        )
                    ),
                    bus_count
                )
            )

        # ----------------------------------------------------
        # SEVERITY
        # ----------------------------------------------------

        if alert["event_type"] == "emergency":

            severity = "critical"

        else:

            severity = (
                priority_engine.severity(
                    alert["event_type"],
                    priority
                )
            )

        # ----------------------------------------------------
        # BACKEND PAYLOAD
        # ----------------------------------------------------

        payload = {
            "event_type": alert[
                "event_type"
            ],

            "confidence": float(
                alert.get(
                    "confidence",
                    0
                )
            ),

            "latitude": location[
                "latitude"
            ],

            "longitude": location[
                "longitude"
            ],

            "severity": severity,

            "priority_score": priority,

            "bus_id": BUS_ID,

            "timestamp": event[
                "timestamp"
            ],

            "bbox": str(
                alert.get(
                    "bbox"
                )
            ),
        }

        # ----------------------------------------------------
        # POST
        # ----------------------------------------------------

        response = requests.post(
            BACKEND_URL,
            json=payload,
            timeout=3
        )

        if response.status_code in {
            200,
            201
        }:

            print(
                f"\n[BACKEND SAVED] "
                f"{alert['event_type']} | "
                f"{alert.get('class_name', '')} | "
                f"confidence="
                f"{float(alert.get('confidence', 0)):.0%} | "
                f"priority={priority:.1f} | "
                f"bus_count={bus_count}"
            )

        else:

            print(
                f"\n[BACKEND ERROR] "
                f"HTTP {response.status_code}: "
                f"{response.text}"
            )

    except requests.exceptions.ConnectionError:

        print(
            "\n[BACKEND OFFLINE] "
            "Start FastAPI on port 8000."
        )

    except Exception as e:

        print(
            f"\n[BACKEND ERROR] {e}"
        )


# ============================================================
# TRAFFIC PANEL
# ============================================================

def draw_traffic_panel(
    frame,
    traffic_result
):

    height, width = frame.shape[:2]

    vehicle_count = traffic_result.get(
        "vehicle_count",
        0
    )

    pedestrian_count = traffic_result.get(
        "pedestrian_count",
        0
    )

    traffic_index = traffic_result.get(
        "traffic_index",
        0
    )

    traffic_level = traffic_result.get(
        "traffic_level",
        "low"
    )

    congestion_confirmed = (
        traffic_result.get(
            "congestion_confirmed",
            False
        )
    )

    panel_x = max(
        width - 390,
        10
    )

    panel_y = 15

    panel_width = 375

    panel_height = 175

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (
            panel_x,
            panel_y
        ),
        (
            panel_x + panel_width,
            panel_y + panel_height
        ),
        (20, 20, 20),
        -1
    )

    frame = cv2.addWeighted(
        overlay,
        0.82,
        frame,
        0.18,
        0
    )

    cv2.putText(
        frame,
        "CODYSSEY TRAFFIC INTELLIGENCE",
        (
            panel_x + 15,
            panel_y + 30
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (0, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Vehicles: {vehicle_count}",
        (
            panel_x + 15,
            panel_y + 60
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Pedestrians: {pedestrian_count}",
        (
            panel_x + 15,
            panel_y + 88
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        f"Traffic Index: {traffic_index}",
        (
            panel_x + 15,
            panel_y + 116
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 0),
        2
    )

    cv2.putText(
        frame,
        f"Level: {traffic_level.upper()}",
        (
            panel_x + 15,
            panel_y + 144
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 200, 255),
        2
    )

    if congestion_confirmed:

        cv2.putText(
            frame,
            "CONGESTION CONFIRMED",
            (
                panel_x + 15,
                panel_y + 168
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            (0, 0, 255),
            2
        )

    return frame


# ============================================================
# EMERGENCY PANEL
# ============================================================

def draw_emergency_panel(
    frame,
    emergency_status
):

    if not emergency_status.get(
        "active",
        False
    ):
        return frame

    height, width = frame.shape[:2]

    panel_width = 500

    x = max(
        (width - panel_width) // 2,
        10
    )

    y = 15

    overlay = frame.copy()

    cv2.rectangle(
        overlay,
        (
            x,
            y
        ),
        (
            x + panel_width,
            y + 85
        ),
        (0, 0, 120),
        -1
    )

    frame = cv2.addWeighted(
        overlay,
        0.88,
        frame,
        0.12,
        0
    )

    cv2.putText(
        frame,
        "EMERGENCY PRIORITY CORRIDOR ACTIVE",
        (
            x + 20,
            y + 32
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    cv2.putText(
        frame,
        "CRITICAL PRIORITY | REQUEST SIGNAL PRIORITY",
        (
            x + 20,
            y + 62
        ),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (0, 255, 255),
        2
    )

    return frame


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("CODYSSEY URBAN INTELLIGENCE PLATFORM")
    print("EDGE AI GATEWAY")
    print("=" * 70)

    # ========================================================
    # FILE CHECK
    # ========================================================

    required_files = [
        VIDEO_PATH,
        RAD_MODEL_PATH,
        POTHOLE_MODEL_PATH,
        EMERGENCY_MODEL_PATH,
        AMBULANCE_MODEL_PATH,
    ]

    for path in required_files:

        if not os.path.exists(path):

            print(
                "\nERROR: Required file missing:"
            )

            print(path)

            return

    print(
        "\nAll required files found."
    )

    # ========================================================
    # DETECTOR
    # ========================================================

    detector = RoadDetector(
        RAD_MODEL_PATH,
        POTHOLE_MODEL_PATH,
        EMERGENCY_MODEL_PATH,
        AMBULANCE_MODEL_PATH,
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
    # TRAFFIC
    # ========================================================

    traffic_engine = TrafficIntelligence(
        congestion_index_threshold=60,
        congestion_vehicle_threshold=6,
        required_observations=3,
        persistence_window=6,
        cooldown_seconds=15
    )

    # ========================================================
    # EMERGENCY
    # ========================================================

    emergency_engine = (
        EmergencyIntelligence(
            confidence_threshold=0.50,
            cooldown_seconds=15
        )
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
    # MULTI BUS
    # ========================================================

    multi_bus_validator = (
        MultiBusValidator(
            distance_threshold_m=50,
            time_window_seconds=300
        )
    )

    # ========================================================
    # VIDEO
    # ========================================================

    cap = cv2.VideoCapture(
        VIDEO_PATH
    )

    if not cap.isOpened():

        print(
            "ERROR: Cannot open video."
        )

        return

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
    # STATUS
    # ========================================================

    print("\n" + "=" * 70)
    print("SYSTEM READY")
    print("=" * 70)

    print(
        f"Video FPS      : {video_fps:.1f}"
    )

    print(
        f"Total frames   : {total_frames}"
    )

    print(
        "AI processing   : Every original frame, synchronized"
    )

    print(
        "Playback        : Every original video frame"
    )

    print(
        "AI sampling     : No interval / no frame skipping"
    )

    print(
        f"Playback speed : "
        f"{PLAYBACK_SPEED:.2f}x"
    )

    print(
        "AI strategy     : Detect current frame, then display current frame"
    )

    print(
        "\nControls:"
    )

    print(
        "  Q = Quit"
    )

    print(
        "  Emergency = AI detected automatically"
    )

    print(
        "  Playback = Original video, continuous"
    )

    print(
        "  Storage = No extracted/saved frames"
    )

    print("=" * 70)

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
        "congestion_confirmed": False,
    }

    emergency_status = {
        "active": False,
        "priority": 0,
        "event": None,
        "expires_at": 0.0,
    }

    EMERGENCY_DISPLAY_SECONDS = 8

    total_detections = 0

    total_alerts = 0

    total_traffic_alerts = 0

    total_emergency_alerts = 0

    # ========================================================
    # LOOP
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
        # SYNCHRONOUS AI - EXACT CURRENT FRAME
        # ====================================================
        #
        # Every frame read from road_test.mp4 is sent directly
        # through the detector before that same frame is shown.
        #
        # There is NO frame interval, NO frame skipping, and NO
        # background worker. This prevents stale detections.
        #
        # The original recording is never written or modified.
        # ====================================================

        try:
            detections = detector.detect(frame)
        except Exception as e:
            print(
                f"\n[AI ERROR] Frame {frame_count}: {e}"
            )
            detections = []

        total_detections += len(detections)

        # --------------------------------------------------------
        # TRAFFIC
        # --------------------------------------------------------

        try:
            traffic_result = traffic_engine.analyze(detections)
            last_traffic_result = traffic_result
        except Exception as e:
            print(f"\n[TRAFFIC ERROR] {e}")
            traffic_result = last_traffic_result

        traffic_alert = traffic_result.get("alert")

        if traffic_alert:
            print("\n" + "=" * 60)
            print("TRAFFIC CONGESTION DETECTED")
            print(
                f"Vehicles: "
                f"{traffic_alert.get('vehicle_count', 0)}"
            )
            print(
                f"Traffic index: "
                f"{traffic_alert.get('traffic_index', 0)}"
            )
            print(
                f"Confidence: "
                f"{traffic_alert.get('confidence', 0):.0%}"
            )
            print("=" * 60)

            send_alert(
                traffic_alert,
                gps,
                priority_engine,
                multi_bus_validator
            )

            total_alerts += 1
            total_traffic_alerts += 1

        # --------------------------------------------------------
        # AUTOMATIC EMERGENCY AI
        # --------------------------------------------------------

        emergency_detections = [
            detection
            for detection in detections
            if detection.get("event_type") == "emergency"
        ]

        if emergency_detections:

            location = gps.get_location()

            emergency_alert = emergency_engine.process(
                emergency_detections,
                location["latitude"],
                location["longitude"]
            )

            if emergency_alert:

                print("\n" + "=" * 70)
                print("🚑 EMERGENCY VEHICLE DETECTED")
                print(
                    f"Vehicle: "
                    f"{emergency_alert['class_name']}"
                )
                print(
                    f"Confidence: "
                    f"{emergency_alert['confidence']:.0%}"
                )
                print("Priority: CRITICAL / 100")
                print("🚦 REQUEST SIGNAL PRIORITY")
                print("🚨 EMERGENCY CORRIDOR ACTIVE")
                print("=" * 70)

                send_alert(
                    emergency_alert,
                    gps,
                    priority_engine,
                    multi_bus_validator
                )

                emergency_status = {
                    "active": True,
                    "priority": 100,
                    "event": emergency_alert,
                    "expires_at": (
                        time.time()
                        + EMERGENCY_DISPLAY_SECONDS
                    ),
                }

                total_alerts += 1
                total_emergency_alerts += 1

        # --------------------------------------------------------
        # NORMAL EVENTS
        # --------------------------------------------------------

        for detection in detections:

            event_type = detection.get("event_type")

            if event_type in {
                "traffic",
                "emergency",
            }:
                continue

            try:
                alert = alert_manager.process_detection(
                    detection
                )
            except Exception as e:
                print(f"\n[ALERT ERROR] {e}")
                alert = None

            if alert:

                print("\n🚨 VALIDATED ALERT")
                print(alert)

                send_alert(
                    alert,
                    gps,
                    priority_engine,
                    multi_bus_validator
                )

                total_alerts += 1

        # These detections belong to the exact frame below.
        last_detections = detections

        # Expire the emergency UI after the live display window.
        if (
            emergency_status.get("active", False)
            and time.time()
            >= emergency_status.get("expires_at", 0.0)
        ):
            emergency_status = {
                "active": False,
                "priority": 0,
                "event": None,
                "expires_at": 0.0,
            }

        # ====================================================
        # DRAW
        # ====================================================

        annotated_frame = frame.copy()

        annotated_frame = (
            detector.draw_detections(
                annotated_frame,
                last_detections
            )
        )

        # ----------------------------------------------------
        # TRAFFIC
        # ----------------------------------------------------

        annotated_frame = (
            draw_traffic_panel(
                annotated_frame,
                last_traffic_result
            )
        )

        # ----------------------------------------------------
        # EMERGENCY
        # ----------------------------------------------------

        annotated_frame = (
            draw_emergency_panel(
                annotated_frame,
                emergency_status
            )
        )

        # ----------------------------------------------------
        # BUS
        # ----------------------------------------------------

        cv2.putText(
            annotated_frame,
            f"BUS: {BUS_ID}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )

        # ----------------------------------------------------
        # EDGE
        # ----------------------------------------------------

        cv2.putText(
            annotated_frame,
            "EDGE AI: ACTIVE",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 255),
            2
        )

        # ----------------------------------------------------
        # GPS
        # ----------------------------------------------------

        location = gps.get_location()

        cv2.putText(
            annotated_frame,
            (
                f"GPS: "
                f"{location['latitude']:.4f}, "
                f"{location['longitude']:.4f}"
            ),
            (10, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (255, 255, 255),
            2
        )

        # ====================================================
        # DISPLAY ORIGINAL VIDEO + LIVE AI OVERLAY
        # ====================================================
        #
        # `frame` is the original frame read from road_test.mp4.
        # `annotated_frame` is only an in-memory display image.
        # It is NEVER saved and NEVER written into a new video.
        # ====================================================

        cv2.imshow(
            "CODYSSEY - Urban Intelligence Edge",
            annotated_frame
        )

        # ====================================================
        # KEYBOARD
        # ====================================================

        key = (
            cv2.waitKey(
                frame_delay_ms
            )
            & 0xFF
        )

        # ----------------------------------------------------
        # QUIT
        # ----------------------------------------------------

        if key == ord("q"):

            print(
                "\nStopping..."
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
        "\n" + "=" * 70
    )

    print(
        "CODYSSEY EDGE AI SESSION COMPLETE"
    )

    print("=" * 70)

    print(
        f"Frames processed  : "
        f"{frame_count}"
    )

    print(
        f"AI detections     : "
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
        f"Emergency alerts  : "
        f"{total_emergency_alerts}"
    )

    print(
        "Original video    : Displayed directly"
    )

    print(
        "Frames extracted  : 0"
    )

    print(
        "Original video    : Displayed directly"
    )

    print(
        "Frames extracted  : 0"
    )

    print(
        "Frames saved      : 0"
    )

    print(
        "Output video      : 0"
    )

    print(
        "Raw video upload  : 0"
    )

    print(
        "Backend payload   : Metadata only"
    )

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()