import os
import re
import subprocess
import tempfile
from pathlib import Path
import hashlib

import music21
import music21.stream
import music21.note
import music21.meter

from core.notes import NoteEvent
from core.time_signature import TimeSignature

# ===========================================================================
# UNIT CONVERSION
# ===========================================================================
UNITS_TO_QUARTER = 8.0
DEFAULT_STAFF_SIZE = 32  # LilyPond default is 20 — we go larger for readability

def units_to_quarter_length(units: int) -> float:
    """Convert 32nd-note units to music21 quarterLength."""
    return units / UNITS_TO_QUARTER

# ===========================================================================
# MUSIC21 STREAM
# ===========================================================================
# ---------------------------------------------------------------------------
# Building a music21 Stream
# ---------------------------------------------------------------------------
def build_stream(
    bars: list[list[NoteEvent]],
    time_sig: TimeSignature,
) -> music21.stream.Score:
    """Convert a generated rhythm into a music21 Score."""
    score = music21.stream.Score()
    part = music21.stream.Part()

    for i, bar in enumerate(bars):
        measure = music21.stream.Measure(number=i + 1)

        if i == 0:
            m21_time_sig = music21.meter.TimeSignature(time_sig.display_name)
            measure.append(m21_time_sig)

        for event in bar:
            ql = units_to_quarter_length(event.units)
            if event.is_rest:
                element = music21.note.Rest(quarterLength=ql)
            else:
                element = music21.note.Note("C4", quarterLength=ql)
            measure.append(element)

        part.append(measure)

    score.append(part)
    return score

# ===========================================================================
# RENDERING
# ===========================================================================
# ---------------------------------------------------------------------------
# LilyPond rendering pipeline
# ---------------------------------------------------------------------------
def _write_ly_file(score: music21.stream.Score, ly_path: str, staff_size: int):
    score.write("lilypond", fp=ly_path)

    with open(ly_path, "r") as f:
        content = f.read()

    content = content.replace('\\include "lilypond-book-preamble.ly"', '')

    # Staff size must come BEFORE \version
    directive = f"#(set-global-staff-size {staff_size})\n\n"
    content = directive + content

    with open(ly_path, "w") as f:
        f.write(content)

def _run_lilypond(ly_path: str, output_dir: str) -> str:
    result = subprocess.run(
        ["lilypond", "-dbackend=svg", "-o", output_dir, ly_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"LilyPond failed:\n{result.stderr}")

    base_name = Path(ly_path).stem
    candidates = list(Path(output_dir).glob(f"{base_name}*.svg"))

    if not candidates:
        raise FileNotFoundError(
            f"No SVG found in {output_dir} matching '{base_name}*.svg'"
        )

    return str(candidates[0])

def _apply_dark_mode(svg_path: str) -> str:
    """
    Set color: white on the root SVG element so all currentColor
    elements (strokes, fills) render white on a dark background.
    """
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Inject color:white into the root <svg> tag's style attribute
    # If a style attribute already exists, append to it
    if 'style="' in content[:500]:
        content = content.replace('style="', 'style="color:white;', 1)
    else:
        content = content.replace('<svg ', '<svg style="color:white;" ', 1)

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(content)

    return svg_path

# ---------------------------------------------------------------------------
# Public rendering API
# ---------------------------------------------------------------------------
def render_to_svg(
    bars, time_sig, output_path=None, dark_mode=False, staff_size=DEFAULT_STAFF_SIZE
):
    score = build_stream(bars, time_sig)

    # Always use a fresh temp dir for LilyPond output
    tmp_dir = tempfile.mkdtemp()
    ly_path = os.path.join(tmp_dir, "rhythm.ly")
    _write_ly_file(score, ly_path, staff_size)
    svg_path = _run_lilypond(ly_path, tmp_dir)

    # If caller wants a persistent path, copy it there
    if output_path is not None:
        output_dir = str(Path(output_path).parent)
        os.makedirs(output_dir, exist_ok=True)
        final_path = output_path + ".svg"
        import shutil
        shutil.copy(svg_path, final_path)
        svg_path = final_path

    if dark_mode:
        _apply_dark_mode(svg_path)

    return svg_path

# ---------------------------------------------------------------------------
# Cached rendering
# ---------------------------------------------------------------------------
_cache: dict[str, str] = {}

def render_cached(
    bars: list[list[NoteEvent]],
    time_sig: TimeSignature,
    dark_mode: bool = False,
    cache_dir: str = "notation/cache",
    staff_size: int = DEFAULT_STAFF_SIZE,
) -> str:
    """
    Render to SVG with a simple in-memory cache.
    Dark mode is part of the cache key — switching theme re-renders.
    """
    cache_key = _make_cache_key(bars, time_sig, dark_mode)

    if cache_key in _cache and os.path.exists(_cache[cache_key]):
        return _cache[cache_key]

    os.makedirs(cache_dir, exist_ok=True)
    output_path = os.path.join(cache_dir, cache_key)
    svg_path = render_to_svg(bars, time_sig, output_path, dark_mode, staff_size)

    _cache[cache_key] = svg_path
    return svg_path

def _make_cache_key(
    bars: list[list[NoteEvent]],
    time_sig: TimeSignature,
    dark_mode: bool = False,
) -> str:
    """Short hash-based cache key to avoid filesystem filename length limits."""
    bar_strings = []
    for bar in bars:
        events = "_".join(
            f"{'R' if e.is_rest else 'N'}{e.units}" for e in bar
        )
        bar_strings.append(events)
    theme = "dark" if dark_mode else "light"
    raw = f"{time_sig.display_name}_{theme}__{'__'.join(bar_strings)}"
    digest = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"{time_sig.display_name.replace('/', '-')}_{theme}_{digest}"