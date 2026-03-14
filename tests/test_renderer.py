import os
import unittest

import music21.stream
import music21.note
import music21.meter

from core.notes import BASIC_DURATIONS, Duration, make_note, make_rest, NoteEvent
from core.time_signature import TimeSignature, COMMON_TIME_SIGNATURES
from core.rhythm import generate_rhythm
from notation.renderer import (
    units_to_quarter_length,
    build_stream,
    render_to_svg,
    render_cached,
    _make_cache_key,
    UNITS_TO_QUARTER,
)

# ===========================================================================
# RENDERER TESTING CLASSES
# ===========================================================================
class TestUnitsToQuarterLength(unittest.TestCase):
    """Tests for the unit conversion helper."""

    def test_whole_note(self):
        self.assertEqual(units_to_quarter_length(32), 4.0)

    def test_half_note(self):
        self.assertEqual(units_to_quarter_length(16), 2.0)

    def test_quarter_note(self):
        self.assertEqual(units_to_quarter_length(8), 1.0)

    def test_eighth_note(self):
        self.assertEqual(units_to_quarter_length(4), 0.5)

    def test_sixteenth_note(self):
        self.assertEqual(units_to_quarter_length(2), 0.25)

    def test_dotted_quarter(self):
        self.assertEqual(units_to_quarter_length(12), 1.5)

    def test_dotted_eighth(self):
        self.assertEqual(units_to_quarter_length(6), 0.75)

class TestBuildStream(unittest.TestCase):
    """Tests for the music21 Stream builder."""

    def setUp(self):
        self.ts = TimeSignature(4, 4)
        self.bars = generate_rhythm(self.ts, BASIC_DURATIONS, num_bars=2, allow_upbeat=False)

    def test_returns_score(self):
        """build_stream should return a music21 Score."""
        score = build_stream(self.bars, self.ts)
        self.assertIsInstance(score, music21.stream.Score)

    def test_correct_number_of_measures(self):
        """Score should contain exactly as many measures as input bars."""
        score = build_stream(self.bars, self.ts)
        measures = score.parts[0].getElementsByClass(music21.stream.Measure)
        self.assertEqual(len(measures), len(self.bars))

    def test_time_signature_in_first_measure(self):
        """Time signature should appear in the first measure only."""
        score = build_stream(self.bars, self.ts)
        measures = list(score.parts[0].getElementsByClass(music21.stream.Measure))

        first_measure_ts = measures[0].getElementsByClass(music21.meter.TimeSignature)
        self.assertEqual(len(list(first_measure_ts)), 1)

        second_measure_ts = measures[1].getElementsByClass(music21.meter.TimeSignature)
        self.assertEqual(len(list(second_measure_ts)), 0)

    def test_rests_are_rests(self):
        """NoteEvents with is_rest=True should produce music21 Rest objects."""
        rest_bar = [[make_rest(Duration.WHOLE)]]
        score = build_stream(rest_bar, self.ts)
        measure = list(score.parts[0].getElementsByClass(music21.stream.Measure))[0]
        notes_and_rests = list(measure.notesAndRests)
        self.assertIsInstance(notes_and_rests[0], music21.note.Rest)

    def test_notes_are_notes(self):
        """NoteEvents with is_rest=False should produce music21 Note objects."""
        note_bar = [[make_note(Duration.WHOLE)]]
        score = build_stream(note_bar, self.ts)
        measure = list(score.parts[0].getElementsByClass(music21.stream.Measure))[0]
        notes_and_rests = list(measure.notesAndRests)
        self.assertIsInstance(notes_and_rests[0], music21.note.Note)

    def test_quarter_lengths_are_correct(self):
        """Each element's quarterLength should match the NoteEvent's units."""
        note_bar = [[make_note(Duration.QUARTER), make_note(Duration.HALF), make_rest(Duration.QUARTER)]]
        score = build_stream(note_bar, self.ts)
        measure = list(score.parts[0].getElementsByClass(music21.stream.Measure))[0]
        elements = list(measure.notesAndRests)
        self.assertEqual(elements[0].quarterLength, 1.0)  # quarter
        self.assertEqual(elements[1].quarterLength, 2.0)  # half
        self.assertEqual(elements[2].quarterLength, 1.0)  # quarter rest

    def test_various_time_signatures(self):
        """build_stream should work for all preset time signatures."""
        for ts in COMMON_TIME_SIGNATURES:
            with self.subTest(ts=ts.display_name):
                bars = generate_rhythm(ts, BASIC_DURATIONS, num_bars=2, allow_upbeat=False)
                score = build_stream(bars, ts)
                self.assertIsInstance(score, music21.stream.Score)

class TestRenderToSvg(unittest.TestCase):
    """Tests for the SVG rendering pipeline."""

    def setUp(self):
        self.ts = TimeSignature(4, 4)
        self.bars = generate_rhythm(self.ts, BASIC_DURATIONS, num_bars=2, allow_upbeat=False)

    def test_returns_a_string_path(self):
        """render_to_svg should return a string path."""
        path = render_to_svg(self.bars, self.ts)
        self.assertIsInstance(path, str)

    def test_file_exists(self):
        """The returned path should point to an existing file."""
        path = render_to_svg(self.bars, self.ts)
        self.assertTrue(os.path.exists(path), f"SVG file not found at: {path}")

    def test_file_is_svg(self):
        """The output file should have a .svg extension."""
        path = render_to_svg(self.bars, self.ts)
        self.assertTrue(path.endswith(".svg"), f"Expected .svg, got: {path}")

    def test_svg_content_is_valid(self):
        """The SVG file should start with an SVG tag."""
        path = render_to_svg(self.bars, self.ts)
        with open(path, "r") as f:
            content = f.read()
        self.assertIn("<svg", content)

class TestCacheKey(unittest.TestCase):
    """Tests for the cache key generator."""

    def test_same_rhythm_same_key(self):
        """The same rhythm should always produce the same cache key."""
        bars = [[make_note(Duration.QUARTER), make_rest(Duration.QUARTER),
                 make_note(Duration.HALF)]]
        ts = TimeSignature(4, 4)
        self.assertEqual(_make_cache_key(bars, ts), _make_cache_key(bars, ts))

    def test_different_rhythms_different_keys(self):
        """Different rhythms should produce different cache keys."""
        ts = TimeSignature(4, 4)
        bars_a = [[make_note(Duration.WHOLE)]]
        bars_b = [[make_note(Duration.HALF), make_note(Duration.HALF)]]
        self.assertNotEqual(_make_cache_key(bars_a, ts), _make_cache_key(bars_b, ts))

    def test_different_time_signatures_different_keys(self):
        """Same rhythm with different time signatures should produce different keys."""
        bars = [[make_note(Duration.QUARTER), make_note(Duration.QUARTER),
                 make_note(Duration.HALF)]]
        ts_4_4 = TimeSignature(4, 4)
        ts_3_4 = TimeSignature(3, 4)
        self.assertNotEqual(_make_cache_key(bars, ts_4_4), _make_cache_key(bars, ts_3_4))

    def test_note_vs_rest_different_keys(self):
        """A note and a rest of the same duration should produce different keys."""
        ts = TimeSignature(4, 4)
        bars_note = [[make_note(Duration.WHOLE)]]
        bars_rest = [[make_rest(Duration.WHOLE)]]
        self.assertNotEqual(_make_cache_key(bars_note, ts), _make_cache_key(bars_rest, ts))


if __name__ == "__main__":
    unittest.main()