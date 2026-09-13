import os
import cv2
import torch

from ultralytics import YOLO
from ultralytics import YOLOWorld


class RoadDetector:

    RAD_CLASS_EVENT_MAP = {
        "HMV": "traffic",
        "LMV": "traffic",
        "Pedestrian": "traffic",
        "RoadDamages": "road_damage",
        "SpeedBump": "road_infrastructure",
        "UnsurfacedRoad": "road_infrastructure",
    }

    EMERGENCY_CLASSES = [
        "ambulance",
        "emergency vehicle",
        "police car",
        "fire truck",
    ]

    def __init__(
        self,
        rad_model_path,
        pothole_model_path,
        emergency_model_path=None,
        imgsz=416,
    ):

        print("=" * 70)
        print("CODYSSEY MULTI-MODEL AI DETECTOR")
        print("=" * 70)

        self.device = (
            0
            if torch.cuda.is_available()
            else "cpu"
        )

        print("Device:", self.device)

        self.imgsz = imgsz

        # ====================================================
        # RAD MODEL
        # ====================================================

        print("\nLoading RAD model...")

        self.rad_model = YOLO(
            rad_model_path
        )

        print(
            "RAD classes:",
            self.rad_model.names
        )

        # ====================================================
        # POTHOLE MODEL
        # ====================================================

        print("\nLoading pothole model...")

        self.pothole_model = YOLO(
            pothole_model_path
        )

        print(
            "Pothole classes:",
            self.pothole_model.names
        )

        # ====================================================
        # EMERGENCY YOLO-WORLD
        # ====================================================

        print(
            "\nLoading automatic emergency AI..."
        )

        try:

            if (
                emergency_model_path
                and os.path.exists(
                    emergency_model_path
                )
            ):

                self.emergency_model = YOLOWorld(
                    emergency_model_path
                )

            else:

                self.emergency_model = YOLOWorld(
                    "yolov8s-worldv2.pt"
                )

            self.emergency_model.set_classes(
                self.EMERGENCY_CLASSES
            )

            print(
                "Emergency classes:",
                self.EMERGENCY_CLASSES
            )

            print(
                "Emergency AI: ACTIVE"
            )

        except Exception as e:

            print(
                "\n[EMERGENCY AI ERROR]"
            )

            print(e)

            self.emergency_model = None

        print("\n" + "=" * 70)
        print("CODYSSEY AI DETECTOR READY")
        print("=" * 70)

    # ========================================================
    # DETECT
    # ========================================================

    def detect(self, frame):

        if frame is None:
            return []

        detections = []

        # ====================================================
        # RAD
        # ====================================================

        try:

            results = self.rad_model.predict(
                frame,
                imgsz=self.imgsz,
                conf=0.35,
                device=self.device,
                verbose=False,
            )

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

                        class_name = (
                            self.rad_model
                            .names[class_id]
                        )

                        event_type = (
                            self.RAD_CLASS_EVENT_MAP
                            .get(class_name)
                        )

                        if event_type is None:
                            continue

                        x1, y1, x2, y2 = (
                            box.xyxy[0]
                            .tolist()
                        )

                        detections.append({
                            "event_type": event_type,
                            "class_name": class_name,
                            "class_id": class_id,
                            "confidence": round(
                                confidence,
                                4
                            ),
                            "bbox": [
                                int(x1),
                                int(y1),
                                int(x2),
                                int(y2),
                            ],
                            "model": "rad",
                        })

        except Exception as e:

            print(
                "[RAD ERROR]",
                e
            )

        # ====================================================
        # POTHOLE
        # ====================================================

        try:

            results = (
                self.pothole_model.predict(
                    frame,
                    imgsz=self.imgsz,
                    conf=0.20,
                    device=self.device,
                    verbose=False,
                )
            )

            if results:

                result = results[0]

                if result.boxes is not None:

                    for box in result.boxes:

                        confidence = float(
                            box.conf[0]
                        )

                        x1, y1, x2, y2 = (
                            box.xyxy[0]
                            .tolist()
                        )

                        detections.append({
                            "event_type": "pothole",
                            "class_name": "pothole",
                            "class_id": 0,
                            "confidence": round(
                                confidence,
                                4
                            ),
                            "bbox": [
                                int(x1),
                                int(y1),
                                int(x2),
                                int(y2),
                            ],
                            "model": "pothole",
                        })

        except Exception as e:

            print(
                "[POTHOLE ERROR]",
                e
            )

        # ====================================================
        # AUTOMATIC EMERGENCY DETECTION
        # ====================================================

        if self.emergency_model is not None:

            try:

                results = (
                    self.emergency_model.predict(
                        frame,
                        imgsz=self.imgsz,
                        conf=0.35,
                        device=self.device,
                        verbose=False,
                    )
                )

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

                            class_name = str(
                                self.emergency_model
                                .names[class_id]
                            )

                            x1, y1, x2, y2 = (
                                box.xyxy[0]
                                .tolist()
                            )

                            detections.append({
                                "event_type": "emergency",
                                "class_name": class_name,
                                "class_id": class_id,
                                "confidence": round(
                                    confidence,
                                    4
                                ),
                                "bbox": [
                                    int(x1),
                                    int(y1),
                                    int(x2),
                                    int(y2),
                                ],
                                "model": "yolo_world_emergency",
                            })

            except Exception as e:

                print(
                    "[EMERGENCY AI ERROR]",
                    e
                )

        return detections

    # ========================================================
    # TRAFFIC
    # ========================================================

    def count_traffic(
        self,
        detections
    ):

        result = {
            "vehicle_count": 0,
            "hmv_count": 0,
            "lmv_count": 0,
            "pedestrian_count": 0,
        }

        for detection in detections:

            class_name = detection.get(
                "class_name"
            )

            if class_name == "HMV":

                result["hmv_count"] += 1

            elif class_name == "LMV":

                result["lmv_count"] += 1

            elif class_name == "Pedestrian":

                result[
                    "pedestrian_count"
                ] += 1

        result["vehicle_count"] = (
            result["hmv_count"]
            + result["lmv_count"]
        )

        return result

    # ========================================================
    # TRAFFIC INDEX
    # ========================================================

    def calculate_traffic_index(
        self,
        detections,
        frame_width=640,
        frame_height=640,
    ):

        vehicle_count = 0
        pedestrian_count = 0

        for detection in detections:

            class_name = detection.get(
                "class_name"
            )

            if class_name in {
                "HMV",
                "LMV",
            }:

                vehicle_count += 1

            elif class_name == "Pedestrian":

                pedestrian_count += 1

        vehicle_score = min(
            vehicle_count * 12,
            80
        )

        pedestrian_score = min(
            pedestrian_count * 5,
            20
        )

        return min(
            int(
                vehicle_score
                + pedestrian_score
            ),
            100
        )

    # ========================================================
    # EVENT HELPERS
    # ========================================================

    def is_road_event(
        self,
        detection
    ):

        return detection.get(
            "event_type"
        ) in {
            "road_damage",
            "pothole",
            "road_infrastructure",
        }

    def is_traffic_event(
        self,
        detection
    ):

        return (
            detection.get(
                "event_type"
            )
            == "traffic"
        )

    def is_emergency_event(
        self,
        detection
    ):

        return (
            detection.get(
                "event_type"
            )
            == "emergency"
        )

    # ========================================================
    # DRAW
    # ========================================================

    def draw_detections(
        self,
        frame,
        detections
    ):

        if frame is None:
            return frame

        for detection in detections:

            bbox = detection.get(
                "bbox"
            )

            if not bbox:
                continue

            x1, y1, x2, y2 = bbox

            event_type = detection.get(
                "event_type",
                "unknown"
            )

            class_name = detection.get(
                "class_name",
                "unknown"
            )

            confidence = float(
                detection.get(
                    "confidence",
                    0
                )
            )

            if event_type == "emergency":

                color = (
                    0,
                    0,
                    255
                )

                label = (
                    f"EMERGENCY: "
                    f"{class_name} "
                    f"{confidence:.0%}"
                )

            elif event_type in {
                "pothole",
                "road_damage",
            }:

                color = (
                    0,
                    165,
                    255
                )

                label = (
                    f"{class_name} "
                    f"{confidence:.0%}"
                )

            elif event_type == "traffic":

                color = (
                    255,
                    200,
                    0
                )

                label = (
                    f"{class_name} "
                    f"{confidence:.0%}"
                )

            else:

                color = (
                    0,
                    255,
                    0
                )

                label = (
                    f"{class_name} "
                    f"{confidence:.0%}"
                )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            cv2.putText(
                frame,
                label,
                (
                    x1,
                    max(
                        y1 - 8,
                        20
                    )
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2
            )

        return frame