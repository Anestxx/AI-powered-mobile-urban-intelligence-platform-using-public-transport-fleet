"""A video-time clock that skips overdue frames and excludes time spent paused."""


class PlaybackClock:
    def __init__(self, fps, start_frame, now):
        self.fps = fps
        self.start_frame = start_frame
        self.started_at = now
        self.paused_at = None

    def target_frame(self, now):
        current = self.paused_at if self.paused_at is not None else now
        return self.start_frame + max(0, int((current - self.started_at) * self.fps))

    def toggle_pause(self, now):
        if self.paused_at is None:
            self.paused_at = now
        else:
            self.started_at += now - self.paused_at
            self.paused_at = None

    def delay_ms(self, next_frame, now):
        deadline = self.started_at + (next_frame - self.start_frame) / self.fps
        return max(1, min(1000, round((deadline - now) * 1000)))
