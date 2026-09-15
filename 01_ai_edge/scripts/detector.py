import hashlib
from paths import POTHOLE_MODEL_PATH, existing_file


class PotholeDetector:
    def __init__(self, model_path=POTHOLE_MODEL_PATH, imgsz=640, cpu_threads=0):
        import torch
        from ultralytics import YOLO

        path = existing_file(model_path)
        self.model = YOLO(str(path))
        if self.model.names != {0: "pothole"}:
            raise ValueError(f"Expected model class {{0: 'pothole'}}, found {self.model.names}. Select labeled pothole weights with --model.")
        self.device = 0 if torch.cuda.is_available() else "cpu"
        self.cpu_threads = cpu_threads
        if cpu_threads < 0:
            raise ValueError("CPU threads must be nonnegative")
        if self.device == "cpu" and self.cpu_threads:
            torch.set_num_threads(self.cpu_threads)
        self.imgsz = imgsz
        with path.open("rb") as source:
            checksum = hashlib.sha256()
            for block in iter(lambda: source.read(1024 * 1024), b""):
                checksum.update(block)
        self.model_version = f"{path.name}:{checksum.hexdigest()[:16]}"
        print(f"Pothole model: {self.model_version}; device: {self.device}")

    def detect(self, frame, confidence=.7):
        if frame is None:
            return []
        results = self.model.predict(frame, conf=confidence, imgsz=self.imgsz, device=self.device, verbose=False)
        # Ultralytics may reset the CPU pool when initializing its predictor.
        # Apply the requested setting again after that first initialization.
        if self.device == "cpu" and self.cpu_threads:
            import torch
            if torch.get_num_threads() != self.cpu_threads:
                torch.set_num_threads(self.cpu_threads)
        detections = []
        for result in results:
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = [max(0, int(value)) for value in box.xyxy[0].tolist()]
                    if x2 > x1 and y2 > y1:
                        detections.append({"event_type": "pothole", "class_name": "pothole", "confidence": float(box.conf[0]), "bbox": [x1, y1, x2, y2]})
        return detections
