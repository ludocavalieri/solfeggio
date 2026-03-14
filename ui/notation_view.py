# Import libraries
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSizePolicy, QScrollArea, QHBoxLayout
)
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import Qt, QSize

# Import custom modules
from core.notes import Duration
from core.time_signature import TimeSignature

# ===========================================================================
# NOTATION VIEW CLASS
# ===========================================================================
class NotationView(QWidget):
    """
    Main display area that renders the SVG notation produced by LilyPond.
    Includes an info bar below the notation showing current rhythm settings.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("notation_view")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._current_svg_path: str | None = None

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(32, 32, 32, 24)
        outer_layout.setSpacing(0)

        # ── Placeholder ────────────────────────────────────────
        self._placeholder = QLabel("Press GENERATE to create a rhythm")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            "color: #999; font-style: italic; font-size: 15px; background: transparent;"
        )
        outer_layout.addWidget(self._placeholder, stretch=1)

        # ── Scroll area + SVG ──────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._scroll.setStyleSheet("border: none; background: transparent;")
        self._scroll.hide()
        outer_layout.addWidget(self._scroll, stretch=1)

        self._svg_widget = QSvgWidget()
        self._svg_widget.setStyleSheet("background: transparent;")
        self._scroll.setWidget(self._svg_widget)

    # ── Public API ─────────────────────────────────────────────
    def load_svg(self, svg_path: str):
        self._current_svg_path = svg_path
        self._placeholder.hide()
        self._svg_widget.load(svg_path)
        self._resize_svg()
        self._scroll.show()

    def clear(self):
        """Reset to the placeholder state."""
        self._scroll.hide()
        self._info_bar.hide()
        self._placeholder.show()
        self._current_svg_path = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._current_svg_path:
            self._resize_svg()

    # ── Internal helpers ───────────────────────────────────────
    def _resize_svg(self):
        """Scale the SVG to fill available width, preserving aspect ratio."""
        renderer = QSvgRenderer(self._current_svg_path)
        if not renderer.isValid():
            return

        default_size = renderer.defaultSize()
        if default_size.isEmpty():
            return

        available_width = self.width() - 64
        available_height = self.height() - 120  # leave room for info bar

        aspect = default_size.height() / default_size.width()
        scaled_width = available_width
        scaled_height = int(scaled_width * aspect)

        if scaled_height > available_height:
            scaled_height = available_height
            scaled_width = int(scaled_height / aspect)

        scaled_width = max(scaled_width, 400)
        scaled_height = max(scaled_height, 200)

        self._svg_widget.setFixedSize(QSize(scaled_width, scaled_height))

    def _update_info_bar(
        self,
        time_sig: TimeSignature | None,
        num_bars: int | None,
        durations: list[Duration] | None,
        allow_upbeat: bool,
    ):
        """Populate the info bar labels with current rhythm metadata."""
        if time_sig:
            self._info_time_sig.setText(f"♩ {time_sig.display_name}")
        if num_bars:
            bar_word = "bar" if num_bars == 1 else "bars"
            self._info_bars.setText(f"▪ {num_bars} {bar_word}")
        if durations:
            names = ", ".join(d.display_name for d in durations)
            # Truncate if too many selected
            if len(names) > 48:
                names = f"{len(durations)} durations"
            self._info_durations.setText(f"𝅘𝅥  {names}")
        self._info_upbeat.setText("~ upbeats on" if allow_upbeat else "~ upbeats off")
        self._info_bar.show()

    def _info_label(self) -> QLabel:
        label = QLabel()
        label.setStyleSheet(
            "color: #999; font-size: 12px; font-family: 'Courier New', monospace;"
            "font-style: italic; background: transparent;"
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return label

    def _info_separator(self) -> QLabel:
        sep = QLabel("·")
        sep.setStyleSheet("color: #555; font-size: 12px; background: transparent;")
        return sep