"""Measured runtime statistics; no model accuracy is inferred from these numbers."""
from collections import deque
import math
import statistics
import time


class RunMetrics:
    def __init__(self, clock=time.perf_counter):
        self.clock = clock
        self.frame_times = deque(maxlen=120)
        self.inference_ms = deque(maxlen=120)
        self.frames = self.inferences = 0

    def record_frame(self):
        self.frames += 1
        self.frame_times.append(self.clock())

    def record_inference(self, seconds):
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Inference duration must be finite and nonnegative")
        self.inferences += 1
        self.inference_ms.append(seconds * 1000)

    def reset_playback_clock(self):
        self.frame_times.clear()

    def snapshot(self):
        span = self.frame_times[-1] - self.frame_times[0] if len(self.frame_times) > 1 else 0
        return {"processed_frames": self.frames, "inferences": self.inferences,
                "sampled_percent": round(100 * self.inferences / self.frames, 1) if self.frames else 0,
                "recent_frame_rate": round((len(self.frame_times) - 1) / span, 1) if span > 0 else None,
                "mean_inference_ms": round(statistics.mean(self.inference_ms), 1) if self.inference_ms else None,
                "p95_inference_ms": round(sorted(self.inference_ms)[math.ceil(.95 * len(self.inference_ms)) - 1], 1) if self.inference_ms else None,
                "window_size": 120}
