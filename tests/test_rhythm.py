# Import libraries
import unittest

# Import custom modules
from core.time_signature import TimeSignature, COMMON_TIME_SIGNATURES
from core.notes import BASIC_DURATIONS, Duration
from core.rhythm import generate_rhythm

# ===========================================================================
# RHYTHM TESTING CLASS
# ===========================================================================
class TestGenerateRhythm(unittest.TestCase):
    def test_bar_units_sum_correctly(self):
        """Each bar's note units should sum to exactly bar_units."""
        ts = TimeSignature(4, 4)
        rhythm = generate_rhythm(ts, BASIC_DURATIONS, num_bars=4, allow_upbeat=False)
        for bar in rhythm:
            self.assertEqual(sum(e.units for e in bar), ts.bar_units)

    def test_correct_number_of_bars(self):
        """Output should contain exactly num_bars bars."""
        ts = TimeSignature(3, 4)
        rhythm = generate_rhythm(ts, BASIC_DURATIONS, num_bars=5, allow_upbeat=False)
        self.assertEqual(len(rhythm), 5)

    def test_only_allowed_durations_used(self):
        """Generator should never use a duration the user didn't allow."""
        ts = TimeSignature(4, 4)
        allowed = [Duration.QUARTER, Duration.HALF]
        rhythm = generate_rhythm(ts, allowed, num_bars=4, allow_upbeat=False)
        for bar in rhythm:
            for event in bar:
                self.assertIn(event.duration, allowed)

    def test_various_time_signatures(self):
        """Bar units should sum correctly across all preset time signatures."""
        for ts in COMMON_TIME_SIGNATURES:
            with self.subTest(ts=ts.display_name):
                rhythm = generate_rhythm(ts, BASIC_DURATIONS, num_bars=2, allow_upbeat=False)
                for bar in rhythm:
                    self.assertEqual(sum(e.units for e in bar), ts.bar_units)

if __name__ == "__main__":
    unittest.main()