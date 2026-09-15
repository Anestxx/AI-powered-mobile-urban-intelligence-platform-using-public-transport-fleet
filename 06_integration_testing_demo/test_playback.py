from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "01_ai_edge/scripts"))
from playback import PlaybackClock


class PlaybackTests(unittest.TestCase):
    def test_slow_inference_moves_to_current_video_frame(self):
        clock = PlaybackClock(30, 560, 100)
        self.assertEqual(clock.target_frame(100), 560)
        self.assertEqual(clock.target_frame(102), 620)
        self.assertEqual(clock.delay_ms(561, 102), 1)

    def test_pause_does_not_skip_the_paused_interval(self):
        clock = PlaybackClock(30, 0, 100)
        clock.toggle_pause(102)
        self.assertEqual(clock.target_frame(112), 60)
        clock.toggle_pause(112)
        self.assertEqual(clock.target_frame(113), 90)

    def test_fast_inference_waits_for_next_frame(self):
        clock = PlaybackClock(30, 0, 100)
        self.assertEqual(clock.delay_ms(1, 100), 33)


if __name__ == "__main__":
    unittest.main()
