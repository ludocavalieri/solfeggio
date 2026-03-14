# Import libraries
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox,
    QCheckBox, QSpinBox, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

# Import custom modules
from core.notes import ALL_DURATIONS, Duration
from core.time_signature import COMMON_TIME_SIGNATURES

# ===========================================================================
# SETTINGS PANEL
# ===========================================================================
class SettingsPanel(QWidget):
    """
    Right sidebar containing all user controls:
      - Time signature selector
      - Note/rest duration checkboxes
      - Number of bars spinner
      - Upbeat toggle
      - BPM spinner
      - Theme toggle, Play, and Generate buttons
    """

    theme_toggle_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 28, 20, 28)
        layout.setSpacing(8)

        # ── App title ──────────────────────────────────────────
        title = QLabel("SolfeggIO")
        title.setObjectName("section_label")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet(
            "font-size: 18px; letter-spacing: 6px; color: #d4a853; margin-bottom: 4px;"
        )
        layout.addWidget(title)

        subtitle = QLabel("rhythm trainer")
        subtitle.setStyleSheet(
            "color: #666668; font-size: 12px; font-style: italic; margin-bottom: 16px;"
        )
        layout.addWidget(subtitle)

        layout.addWidget(self._divider())

        # ── Time signature ─────────────────────────────────────
        layout.addSpacing(12)
        layout.addWidget(self._section_label("Time Signature"))

        self.time_sig_combo = QComboBox()
        for ts in COMMON_TIME_SIGNATURES:
            self.time_sig_combo.addItem(ts.display_name)
        self.time_sig_combo.setCurrentText("4/4")
        layout.addWidget(self.time_sig_combo)

        # ── Note durations ─────────────────────────────────────
        layout.addSpacing(16)
        layout.addWidget(self._section_label("Note Durations"))

        self.duration_checkboxes: dict[Duration, QCheckBox] = {}
        for duration in ALL_DURATIONS:
            cb = QCheckBox(duration.display_name)
            cb.setChecked(not duration.is_dotted)
            self.duration_checkboxes[duration] = cb
            layout.addWidget(cb)

        # ── Number of bars ─────────────────────────────────────
        layout.addSpacing(16)
        layout.addWidget(self._section_label("Bars"))

        self.bars_spinbox = QSpinBox()
        self.bars_spinbox.setMinimum(1)
        self.bars_spinbox.setMaximum(16)
        self.bars_spinbox.setValue(4)
        layout.addWidget(self.bars_spinbox)

        # ── BPM ────────────────────────────────────────────────
        layout.addSpacing(16)
        layout.addWidget(self._section_label("Tempo (BPM)"))

        self.bpm_spinbox = QSpinBox()
        self.bpm_spinbox.setMinimum(40)
        self.bpm_spinbox.setMaximum(200)
        self.bpm_spinbox.setValue(80)
        self.bpm_spinbox.setSingleStep(5)
        layout.addWidget(self.bpm_spinbox)

        # ── Options ────────────────────────────────────────────
        layout.addSpacing(16)
        layout.addWidget(self._section_label("Options"))

        self.upbeat_checkbox = QCheckBox("Allow upbeats")
        self.upbeat_checkbox.setChecked(False)
        layout.addWidget(self.upbeat_checkbox)

        # ── Spacer ─────────────────────────────────────────────
        layout.addStretch()
        layout.addWidget(self._divider())
        layout.addSpacing(12)

        # ── Theme toggle ───────────────────────────────────────
        self.theme_button = QPushButton("☀  LIGHT MODE")
        self.theme_button.setObjectName("theme_button")
        self.theme_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.theme_button.clicked.connect(self.theme_toggle_requested.emit)
        layout.addWidget(self.theme_button)

        layout.addSpacing(8)

        # ── Play button ────────────────────────────────────────
        self.play_button = QPushButton("▶  PLAY")
        self.play_button.setObjectName("play_button")
        self.play_button.setEnabled(False)
        self.play_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.play_button)

        layout.addSpacing(8)

        # ── Generate button ────────────────────────────────────
        self.generate_button = QPushButton("GENERATE")
        self.generate_button.setObjectName("generate_button")
        self.generate_button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(self.generate_button)

    # ── Helpers ────────────────────────────────────────────────
    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setObjectName("section_label")
        return label

    def _divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        return line

    def set_theme_button_label(self, is_dark: bool):
        self.theme_button.setText("☀  LIGHT MODE" if is_dark else "☾  DARK MODE")

    def set_playing(self, is_playing: bool):
        """Toggle play button label between Play and Stop."""
        self.play_button.setText("■  STOP" if is_playing else "▶  PLAY")

    def enable_play(self):
        """Enable play button after first rhythm is generated."""
        self.play_button.setEnabled(True)

    # ── Public accessors ───────────────────────────────────────
    def selected_time_signature(self) -> str:
        return self.time_sig_combo.currentText()

    def selected_durations(self) -> list[Duration]:
        return [d for d, cb in self.duration_checkboxes.items() if cb.isChecked()]

    def num_bars(self) -> int:
        return self.bars_spinbox.value()

    def allow_upbeat(self) -> bool:
        return self.upbeat_checkbox.isChecked()

    def bpm(self) -> int:
        return self.bpm_spinbox.value()