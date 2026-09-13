import torch
from ultralytics import YOLO


class RoadDetector:

    RAD_CLASS_EVENT_MAP = {
        "HMV": "traffic",
        "LMV": "traffic",
        "Pedestrian": "traffic",
        "RoadDamages": "road_damage",
        "SpeedBump": "road_infrastructure",
        "UnsurfacedRoad": "road_infrastructure",
    }

    def __init__(
        self,
        rad_model_path,
        pothole_model_path,
        imgsz=640
    ):
        print("=" * 60)
        print("CODYSSEY DUAL-MODEL AI DETECTOR")
        print("=" * 60)

        self.device = 0 if torch.cuda.is_available() else "cpu"

        print("Device:", self.device)
        print("RAD model:", rad_model_path)
        print("Pothole model:", pothole_model_path)

        self.rad_model = YOLO(rad_model_path)
        self.pothole_model = YOLO(pothole_model_path)

        self.imgsz = imgsz

        print("RAD classes:")
        print(self.rad_model.names)

        print("Pothole classes:")
        print(self.pothole_model.names)

        print("=" * 60)
        print("DUAL-MODEL DETECTOR READY")
        print("=" * 60)

    def detect(self, frame):

        if frame is None:
            return []

        detections = []

        # ==================================================
        # MODEL 1: RAD
        # ==================================================

        rad_results = self.rad_model.predict(
            frame,
            imgsz=self.imgsz,
            conf=0.35,
            device=self.device,
            verbose=False
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

                    detections.append({
                        "event_type": event_type,
                        "class_name": class_name,
                        "class_id": class_id,
                        "confidence": round(confidence, 4),
                        "bbox": [
                            int(x1),
                            int(y1),
                            int(x2),
                            int(y2)
                        ],
                        "model": "rad"
                    })

        # ==================================================
        # MODEL 2: POTHOLE
        # ==================================================

        pothole_results = self.pothole_model.predict(
            frame,
            imgsz=self.imgsz,
            conf=0.25,
            device=self.device,
            verbose=False
        )

        if pothole_results:
            result = pothole_results[0]

            if result.boxes is not None:

                for box in result.boxes:

                    confidence = float(box.conf[0])

                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    detections.append({
                        "event_type": "pothole",
                        "class_name": "pothole",
                        "class_id": 0,
                        "confidence": round(confidence, 4),
                        "bbox": [
                            int(x1),
                            int(y1),
                            int(x2),
                            int(y2)
                        ],
                        "model": "pothole"
                    })

        return detections

    # ======================================================
    # TRAFFIC
    # ======================================================

    def count_traffic(self, detections):

        result = {
            "vehicle_count": 0,
            "hmv_count": 0,
            "lmv_count": 0,
            "pedestrian_count": 0
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
            result["hmv_count"] +
            result["lmv_count"]
        )

        return result

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

        vehicle_score = min(vehicle_count * 12, 80)
        pedestrian_score = min(pedestrian_count * 5, 20)

        return min(
            int(vehicle_score + pedestrian_score),
            100
        )

    # ======================================================
    # EVENT HELPERS
    # ======================================================

    def is_road_event(self, detection):

        return detection["event_type"] in {
            "road_damage",
            "pothole",
            "road_infrastructure"
        }

    def is_traffic_event(self, detection):

        return detection["event_type"] == "traffic"