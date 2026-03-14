# Import libraries
import threading
import time
import numpy as np
import pygame

# Import custom modules
from core.notes import NoteEvent
from core.time_signature import TimeSignature

# ===========================================================================
# AUDIO CONSTANTS
# ===========================================================================
# Sampling rate and C frequency
SAMPLE_RATE = 44100
MIDDLE_C    = 261.63  # C4 in Hz

# ===========================================================================
# SOUND
# ===========================================================================
# ---------------------------------------------------------------------------
# Sound synthesis
# ---------------------------------------------------------------------------
def _synthesize_piano(duration_sec: float, frequency: float = MIDDLE_C) -> np.ndarray:
    """
    Piano-like tone: additive harmonics with exponential decay.
    Generates audio for the FULL duration so notes are held properly.
    The natural decay means long notes fade out gracefully.
    """
    n = int(SAMPLE_RATE * duration_sec)
    t = np.linspace(0, duration_sec, n, endpoint=False)

    harmonics = [
        (1.0, 1.00, 3.0),
        (2.0, 0.50, 5.0),
        (3.0, 0.25, 7.0),
        (4.0, 0.12, 9.0),
        (5.0, 0.06, 12.0),
    ]

    wave = np.zeros(n)
    for ratio, amp, decay in harmonics:
        envelope = np.exp(-decay * t)
        wave += amp * envelope * np.sin(2 * np.pi * frequency * ratio * t)

    # Short attack to avoid click at note onset
    attack = min(int(0.005 * SAMPLE_RATE), n)
    wave[:attack] *= np.linspace(0, 1, attack)

    peak = np.max(np.abs(wave))
    if peak > 0:
        wave /= peak

    return wave

def _synthesize_click(accent: bool = False) -> np.ndarray:
    """
    Metronome click: a short sine burst with fast decay.
    Accented clicks (beat 1) are higher pitched.
    """
    duration = 0.04  # 40ms
    frequency = 1800.0 if accent else 1200.0
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    wave = np.sin(2 * np.pi * frequency * t)
    envelope = np.exp(-80 * t)
    wave *= envelope

    peak = np.max(np.abs(wave))
    if peak > 0:
        wave /= peak

    return wave

def _to_stereo_int16(wave: np.ndarray, volume: float = 1.0) -> np.ndarray:
    """Convert mono float array [-1,1] to stereo int16 for pygame."""
    clipped = np.clip(wave * volume, -1.0, 1.0)
    mono = (clipped * 32767).astype(np.int16)
    return np.column_stack([mono, mono])

def _make_silence(duration_sec: float) -> np.ndarray:
    """Silent stereo int16 buffer."""
    n = int(SAMPLE_RATE * duration_sec)
    return np.zeros((n, 2), dtype=np.int16)

def _make_sound(wave: np.ndarray, volume: float = 1.0) -> pygame.mixer.Sound:
    return pygame.sndarray.make_sound(_to_stereo_int16(wave, volume))

# ---------------------------------------------------------------------------
# RhythmPlayer
# ---------------------------------------------------------------------------
class RhythmPlayer:
    """
    Plays a generated rhythm with:
      - A count-in bar of metronome clicks before the rhythm starts
      - A background metronome click on every beat throughout playback
      - Piano-like tones held for their full notated duration
      - Rests are silent

    Playback runs on a background thread so the UI stays responsive.
    """
    # Global class variables
    NOTE_VOLUME  = 0.85
    CLICK_VOLUME = 0.45   # metronome sits behind the notes

    def __init__(self):
        pygame.mixer.pre_init(
            frequency=SAMPLE_RATE,
            size=-16,
            channels=2,
            buffer=512,
        )
        pygame.mixer.init()

        # Pre-render click sounds
        self._click_accent = _make_sound(_synthesize_click(accent=True),  self.CLICK_VOLUME)
        self._click_normal = _make_sound(_synthesize_click(accent=False), self.CLICK_VOLUME)

        # Reserve two pygame channels: one for notes, one for metronome
        pygame.mixer.set_num_channels(4)
        self._note_channel  = pygame.mixer.Channel(0)
        self._click_channel = pygame.mixer.Channel(1)

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------------
    def play(
        self,
        bars: list[list[NoteEvent]],
        time_sig: TimeSignature,
        bpm: int = 80,
    ):
        """Start playback on a background thread, stopping any current playback first."""
        self.stop()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._playback_loop,
            args=(bars, time_sig, bpm),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        """Stop playback immediately."""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=2.0)
        self._note_channel.stop()
        self._click_channel.stop()

    def is_playing(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------------
    # Playback Loop
    # ------------------------------------------------------------------------
    def _playback_loop(
        self,
        bars: list[list[NoteEvent]],
        time_sig: TimeSignature,
        bpm: int,
    ):
        beat_sec    = 60.0 / bpm
        beat_units  = time_sig.beat_units          # 32nd-unit length of one beat
        num_beats   = time_sig.numerator            # beats per bar

        def units_to_sec(units: int) -> float:
            return (units / beat_units) * beat_sec

        # ── Count-in: one full bar of metronome only ───────────
        for beat in range(num_beats):
            if self._stop_event.is_set():
                return
            self._play_click(beat == 0)
            self._wait(beat_sec)

        # ── Main playback: notes + metronome ───────────────────
        for bar in bars:
            # Schedule metronome clicks on a parallel thread for this bar
            bar_duration = units_to_sec(time_sig.bar_units)
            click_thread = threading.Thread(
                target=self._metronome_bar,
                args=(num_beats, beat_sec),
                daemon=True,
            )
            click_thread.start()

            # Play each note event sequentially
            for event in bar:
                if self._stop_event.is_set():
                    return

                duration_sec = units_to_sec(event.units)

                if not event.is_rest:
                    tone  = _synthesize_piano(duration_sec)
                    sound = _make_sound(tone, self.NOTE_VOLUME)
                    self._note_channel.play(sound)

                self._wait(duration_sec)

            click_thread.join(timeout=bar_duration + 0.5)

    def _metronome_bar(self, num_beats: int, beat_sec: float):
        """Play metronome clicks for one bar on the click channel."""
        for beat in range(num_beats):
            if self._stop_event.is_set():
                return
            self._play_click(beat == 0)
            self._wait(beat_sec)

    # ------------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------------
    def _play_click(self, accent: bool):
        sound = self._click_accent if accent else self._click_normal
        self._click_channel.play(sound)

    def _wait(self, duration_sec: float):
        """Sleep for duration_sec, checking stop_event every 10ms."""
        end = time.perf_counter() + duration_sec
        while time.perf_counter() < end:
            if self._stop_event.is_set():
                return
            time.sleep(0.01)