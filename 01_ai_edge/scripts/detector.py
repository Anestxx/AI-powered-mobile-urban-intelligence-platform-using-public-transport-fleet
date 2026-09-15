import cv2
import torch
from ultralytics import YOLO, YOLOWorld


class RoadDetector:

    # ============================================================
    # RAD MODEL
    # ============================================================

    RAD_CLASS_EVENT_MAP = {
        "HMV": "traffic",
        "LMV": "traffic",
        "Pedestrian": "traffic",
        "RoadDamages": "road_damage",
        "SpeedBump": "road_infrastructure",
        "UnsurfacedRoad": "road_infrastructure",
    }

    # ============================================================
    # EMERGENCY CLASSES
    # ============================================================

    EMERGENCY_WORLD_CLASSES = [
        "ambulance",
        "emergency vehicle",
        "police car",
        "fire truck",
    ]

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        rad_model_path,
        pothole_model_path,
        emergency_world_model_path=None,
        ambulance_model_path=None,
        imgsz=640,
    ):

        print("=" * 70)
        print("CODYSSEY MULTI-MODEL AI DETECTOR")
        print("=" * 70)

        # --------------------------------------------------------
        # DEVICE
        # --------------------------------------------------------

        self.device = 0 if torch.cuda.is_available() else "cpu"

        print("Device:", self.device)

        self.imgsz = imgsz

        # ========================================================
        # RAD MODEL
        # ========================================================

        print("\nLoading RAD model:")
        print(rad_model_path)

        self.rad_model = YOLO(rad_model_path)

        # ========================================================
        # POTHOLE MODEL
        # ========================================================

        print("\nLoading pothole model:")
        print(pothole_model_path)

        self.pothole_model = YOLO(pothole_model_path)

        # ========================================================
        # YOLO-WORLD EMERGENCY MODEL
        # ========================================================

        self.emergency_world_model = None

        if emergency_world_model_path:

            print("\nLoading YOLO-World emergency model:")
            print(emergency_world_model_path)

            self.emergency_world_model = YOLOWorld(
                emergency_world_model_path
            )

            self.emergency_world_model.set_classes(
                self.EMERGENCY_WORLD_CLASSES
            )

            print(
                "YOLO-World emergency classes:",
                self.EMERGENCY_WORLD_CLASSES
            )

        # ========================================================
        # INDIAN AMBULANCE MODEL
        # ========================================================

        self.ambulance_model = None

        if ambulance_model_path:

            print("\nLoading Indian ambulance model:")
            print(ambulance_model_path)

            self.ambulance_model = YOLO(
                ambulance_model_path
            )

            print(
                "Indian ambulance classes:",
                self.ambulance_model.names
            )

        # ========================================================
        # PRINT MODEL CLASSES
        # ========================================================

        print("\nRAD classes:")
        print(self.rad_model.names)

        print("\nPothole classes:")
        print(self.pothole_model.names)

        if self.emergency_world_model is not None:
            print("\nYOLO-World emergency classes:")
            print(self.emergency_world_model.names)

        if self.ambulance_model is not None:
            print("\nIndian ambulance classes:")
            print(self.ambulance_model.names)

        print("=" * 70)
        print("MULTI-MODEL DETECTOR READY")
        print("=" * 70)

    # ============================================================
    # MAIN DETECTION
    # ============================================================

    def detect(self, frame):

        if frame is None:
            return []

        detections = []

        # ========================================================
        # RAD DETECTION
        # ========================================================

        rad_results = self.rad_model.predict(
            frame,
            imgsz=self.imgsz,
            conf=0.35,
            device=self.device,
            verbose=False,
        )

        if rad_results:

            result = rad_results[0]

            if result.boxes is not None:

                for box in result.boxes:

                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])

                    class_name = self.rad_model.names[class_id]

                    event_type = self.RAD_CLASS_EVENT_MAP.get(
                        class_name
                    )

                    if event_type is None:
                        continue

                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    detections.append(
                        {
                            "event_type": event_type,
                            "class_name": class_name,
                            "class_id": class_id,
                            "confidence": round(confidence, 4),
                            "bbox": [
                                int(x1),
                                int(y1),
                                int(x2),
                                int(y2),
                            ],
                            "model": "rad",
                        }
                    )

        # ========================================================
        # POTHOLE DETECTION
        # ========================================================

        pothole_results = self.pothole_model.predict(
            frame,
            imgsz=self.imgsz,
            conf=0.25,
            device=self.device,
            verbose=False,
        )

        if pothole_results:

            result = pothole_results[0]

            if result.boxes is not None:

                for box in result.boxes:

                    confidence = float(box.conf[0])

                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    detections.append(
                        {
                            "event_type": "pothole",
                            "class_name": "pothole",
                            "class_id": 0,
                            "confidence": round(confidence, 4),
                            "bbox": [
                                int(x1),
                                int(y1),
                                int(x2),
                                int(y2),
                            ],
                            "model": "pothole",
                        }
                    )

        # ========================================================
        # YOLO-WORLD EMERGENCY DETECTION
        # ========================================================

        if self.emergency_world_model is not None:

            world_results = self.emergency_world_model.predict(
                frame,
                imgsz=416,
                conf=0.30,
                device=self.device,
                verbose=False,
            )

            if world_results:

                result = world_results[0]

                if result.boxes is not None:

                    for box in result.boxes:

                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])

                        class_name = (
                            self.emergency_world_model.names[
                                class_id
                            ]
                        )

                        x1, y1, x2, y2 = box.xyxy[0].tolist()

                        detections.append(
                            {
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
                                "model": "yolo_world",
                            }
                        )

        # ========================================================
        # INDIAN AMBULANCE MODEL
        # ========================================================

        if self.ambulance_model is not None:

            ambulance_results = self.ambulance_model.predict(
                frame,
                imgsz=self.imgsz,
                conf=0.35,
                device=self.device,
                verbose=False,
            )

            if ambulance_results:

                result = ambulance_results[0]

                if result.boxes is not None:

                    for box in result.boxes:

                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])

                        x1, y1, x2, y2 = box.xyxy[0].tolist()

                        # Get actual class name if available
                        try:
                            class_name = (
                                self.ambulance_model.names[
                                    class_id
                                ]
                            )
                        except Exception:
                            class_name = "ambulance"

                        detections.append(
                            {
                                "event_type": "emergency",
                                "class_name": "ambulance",
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
                                "model": "indian_ambulance",
                            }
                        )

        return detections

    # ============================================================
    # DRAW DETECTIONS
    # ============================================================

    def draw_detections(self, frame, detections):

        """
        Draw AI detections on the live video frame.

        Important:
        - This only draws detections in memory.
        - It does NOT save frames.
        - It does NOT create an output video.
        - It does NOT upload frames.
        """

        if frame is None:
            return frame

        if not detections:
            return frame

        for detection in detections:

            bbox = detection.get("bbox")

            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox

            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)

            event_type = detection.get(
                "event_type",
                "event"
            )

            class_name = detection.get(
                "class_name",
                event_type
            )

            confidence = float(
                detection.get(
                    "confidence",
                    0
                )
            )

            model_name = detection.get(
                "model",
                "ai"
            )

            # ====================================================
            # DETECTION COLORS
            # ====================================================

            if event_type == "emergency":

                # RED = emergency
                color = (0, 0, 255)

            elif event_type == "pothole":

                # MAGENTA = pothole
                color = (255, 0, 255)

            elif event_type == "road_damage":

                # ORANGE = road damage
                color = (0, 165, 255)

            elif event_type == "road_infrastructure":

                # BLUE = infrastructure
                color = (255, 165, 0)

            elif event_type == "traffic":

                # GREEN = traffic
                color = (0, 255, 0)

            else:

                # WHITE = unknown/general event
                color = (255, 255, 255)

            # ====================================================
            # DRAW BOUNDING BOX
            # ====================================================

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                color,
                2,
            )

            # ====================================================
            # LABEL
            # ====================================================

            if event_type == "emergency":

                label = (
                    f"EMERGENCY: "
                    f"{class_name} "
                    f"{confidence:.2f}"
                )

            else:

                label = (
                    f"{class_name} "
                    f"{confidence:.2f}"
                )

            # ====================================================
            # LABEL SIZE
            # ====================================================

            (
                (text_width, text_height),
                baseline,
            ) = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                2,
            )

            # Make sure label does not go outside frame
            label_top = max(
                0,
                y1 - text_height - baseline - 6
            )

            label_bottom = max(
                text_height + baseline + 6,
                y1
            )

            label_right = min(
                frame.shape[1] - 1,
                x1 + text_width + 8
            )

            # ====================================================
            # LABEL BACKGROUND
            # ====================================================

            cv2.rectangle(
                frame,
                (x1, label_top),
                (label_right, label_bottom),
                color,
                -1,
            )

            # ====================================================
            # LABEL TEXT
            # ====================================================

            cv2.putText(
                frame,
                label,
                (
                    x1 + 4,
                    label_bottom - 5,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            # ====================================================
            # MODEL NAME
            # ====================================================

            model_text = f"[{model_name}]"

            model_y = min(
                frame.shape[0] - 5,
                y2 + 18
            )

            cv2.putText(
                frame,
                model_text,
                (x1, model_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1,
                cv2.LINE_AA,
            )

        return frame

    # ============================================================
    # TRAFFIC COUNT
    # ============================================================

    def count_traffic(self, detections):

        result = {
            "vehicle_count": 0,
            "hmv_count": 0,
            "lmv_count": 0,
            "pedestrian_count": 0,
        }

        for detection in detections:

            class_name = detection["class_name"]

            if class_name == "HMV":

                result["hmv_count"] += 1

            elif class_name == "LMV":

                result["lmv_count"] += 1

            elif class_name == "Pedestrian":

                result["pedestrian_count"] += 1

        result["vehicle_count"] = (
            result["hmv_count"]
            + result["lmv_count"]
        )

        return result

    # ============================================================
    # TRAFFIC INDEX
    # ============================================================

    def calculate_traffic_index(
        self,
        detections,
        frame_width,
        frame_height
    ):

        vehicle_count = 0
        pedestrian_count = 0

        for detection in detections:

            class_name = detection["class_name"]

            if class_name in {"HMV", "LMV"}:

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

    # ============================================================
    # EVENT HELPERS
    # ============================================================

    def is_road_event(self, detection):

        return detection["event_type"] in {
            "road_damage",
            "pothole",
            "road_infrastructure",
        }

    def is_traffic_event(self, detection):

        return detection["event_type"] == "traffic"

    def is_emergency_event(self, detection):

        return detection["event_type"] == "emergency"