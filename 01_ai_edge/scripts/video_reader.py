import math
from pathlib import Path
import time


class VideoReader:
    def __init__(self, source, start_frame=0):
        self.source = str(source)
        self.start_frame = start_frame
        self.capture = None
        self.is_camera = self.source.isdigit() and not Path(self.source).exists()

    def __enter__(self):
        import cv2
        source = int(self.source) if self.is_camera else str(Path(self.source).expanduser().resolve())
        if not self.is_camera and not Path(source).is_file():
            raise FileNotFoundError(f"Video does not exist: {source}")
        self.capture = cv2.VideoCapture(source)
        if not self.capture.isOpened():
            self.capture.release()
            raise RuntimeError(f"Cannot open video/camera: {source}")
        fps = self.capture.get(cv2.CAP_PROP_FPS)
        self.fps = fps if math.isfinite(fps) and fps > 1 else 30.0
        total_frames = self.capture.get(cv2.CAP_PROP_FRAME_COUNT)
        self.duration = total_frames / self.fps if math.isfinite(total_frames) and total_frames > 0 else None
        self.frame_index = self.start_frame
        if self.start_frame and not self.is_camera:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        self.opened_at = time.monotonic()
        return self

    def read(self):
        ok, frame = self.capture.read()
        if not ok:
            return None
        video_time = time.monotonic() - self.opened_at if self.is_camera else self.frame_index / self.fps
        self.frame_index += 1
        return frame, self.frame_index, video_time

    def rewind(self):
        import cv2
        if self.is_camera:
            raise ValueError("A live camera cannot be replayed")
        if not self.capture.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame):
            raise RuntimeError("This recording could not be rewound")
        self.frame_index = self.start_frame

    def __exit__(self, *_):
        if self.capture is not None:
            self.capture.release()
