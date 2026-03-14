# Import libraries
import shutil
import atexit
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QMessageBox

# Import custom modules
from ui.settings_panel import SettingsPanel
from ui.notation_view import NotationView
from core.time_signature import get_time_signature
from core.rhythm import generate_rhythm
from notation.renderer import render_cached
from audio.player import RhythmPlayer

# ===========================================================================
# MAIN WINDOW CLASS
# ===========================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SolfeggIO")
        self.setMinimumSize(900, 720)
        self.resize(1200, 900)

        self._is_dark = True
        self._apply_stylesheet()

        # Last generated rhythm — needed for theme switching and playback
        self._last_bars = None
        self._last_time_sig = None
        self._last_num_bars = None
        self._last_durations = None
        self._last_upbeat = False

        # Audio player
        self._player = RhythmPlayer()
        atexit.register(self._player.stop)

        # ── Layout ─────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.notation_view = NotationView()
        layout.addWidget(self.notation_view)

        self.settings_panel = SettingsPanel()
        layout.addWidget(self.settings_panel)

        # ── Wire buttons ───────────────────────────────────────
        self.settings_panel.generate_button.clicked.connect(self._on_generate)
        self.settings_panel.theme_toggle_requested.connect(self._on_theme_toggle)
        self.settings_panel.play_button.clicked.connect(self._on_play)

    # ── Stylesheet ─────────────────────────────────────────────
    def _apply_stylesheet(self):
        name = "style_dark.qss" if self._is_dark else "style_light.qss"
        qss_path = Path(__file__).parent / name
        if qss_path.exists():
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())

    # ── Theme toggle ───────────────────────────────────────────
    def _on_theme_toggle(self):
        self._is_dark = not self._is_dark
        self._apply_stylesheet()
        self.settings_panel.set_theme_button_label(self._is_dark)

        if self._last_bars is not None:
            svg_path = render_cached(
                self._last_bars, self._last_time_sig, dark_mode=self._is_dark
            )
            self.notation_view.load_svg(svg_path)

    # ── Generate ───────────────────────────────────────────────
    def _on_generate(self):
        # Stop any playing audio when a new rhythm is generated
        if self._player.is_playing():
            self._player.stop()
            self.settings_panel.set_playing(False)

        selected_durations = self.settings_panel.selected_durations()
        if not selected_durations:
            QMessageBox.warning(
                self,
                "No durations selected",
                "Please select at least one note duration before generating."
            )
            return

        time_sig = get_time_signature(self.settings_panel.selected_time_signature())
        num_bars = self.settings_panel.num_bars()
        allow_upbeat = self.settings_panel.allow_upbeat()

        bars = generate_rhythm(
            time_sig=time_sig,
            allowed_durations=selected_durations,
            num_bars=num_bars,
            allow_upbeat=allow_upbeat,
        )

        svg_path = render_cached(bars, time_sig, dark_mode=self._is_dark)
        self.notation_view.load_svg(svg_path)

        # Store for theme switching and playback
        self._last_bars = bars
        self._last_time_sig = time_sig
        self._last_num_bars = num_bars
        self._last_durations = selected_durations
        self._last_upbeat = allow_upbeat

        self.settings_panel.enable_play()

    # ── Play / Stop ────────────────────────────────────────────
    def _on_play(self):
        if self._player.is_playing():
            self._player.stop()
            self.settings_panel.set_playing(False)
        else:
            self._player.play(
                self._last_bars,
                self._last_time_sig,
                bpm=self.settings_panel.bpm(),
            )
            self.settings_panel.set_playing(True)

            # Reset button label when playback finishes naturally
            self._poll_playback()

    def _poll_playback(self):
        """Check every 200ms if playback has finished and reset the button."""
        from PyQt6.QtCore import QTimer
        def check():
            if not self._player.is_playing():
                self.settings_panel.set_playing(False)
            else:
                QTimer.singleShot(200, check)
        QTimer.singleShot(200, check)