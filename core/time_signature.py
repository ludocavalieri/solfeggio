# Import libraries
from dataclasses import dataclass
from core.notes import UNITS_PER_WHOLE

# ===========================================================================
# TIME SIGNATURE CLASS
# ===========================================================================
# ---------------------------------------------------------------------------
# TimeSignature
# ---------------------------------------------------------------------------
# A time signature is defined by:
#   - numerator:   how many beats per bar  (the top number, e.g. 3 in 3/4)
#   - denominator: the note value of one beat (the bottom number, e.g. 4 in 3/4)
#
# From these two numbers we can derive:
#   - how many 32nd-note units fit in one bar
#   - the duration of the beat unit itself
#
# Example: 6/8
#   numerator   = 6
#   denominator = 8
#   one beat    = UNITS_PER_WHOLE // 8 = 4 units  (an eighth note)
#   bar total   = 6 × 4 = 24 units
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TimeSignature:
    # -----------------------------------------------------------------------
    # Global Variables
    # -----------------------------------------------------------------------
    # Define numerator and denominator variable
    numerator: int
    denominator: int

    def __post_init__(self):
        if self.denominator not in (1, 2, 4, 8, 16, 32):
            raise ValueError(
                f"Denominator must be a power of 2 (1–32), got {self.denominator}"
            )
        if self.numerator < 1:
            raise ValueError(f"Numerator must be >= 1, got {self.numerator}")

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    @property
    def beat_units(self) -> int:
        """Duration of a single beat in 32nd-note units."""
        return UNITS_PER_WHOLE // self.denominator

    @property
    def bar_units(self) -> int:
        """Total duration of one bar in 32nd-note units."""
        return self.numerator * self.beat_units

    @property
    def display_name(self) -> str:
        """Human-readable label, e.g. '3/4'."""
        return f"{self.numerator}/{self.denominator}"

    # -----------------------------------------------------------------------
    # Representation
    # -----------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"TimeSignature({self.display_name}, bar={self.bar_units} units)"

# ===========================================================================
# HELPERS
# ===========================================================================
# ---------------------------------------------------------------------------
# Preset time signatures
# ---------------------------------------------------------------------------
# These are the ones the user can pick from in the UI.
# You can add more at any time — the generator doesn't care which one is used.
# ---------------------------------------------------------------------------
COMMON_TIME_SIGNATURES: list[TimeSignature] = [
    TimeSignature(2, 4),   # 2/4  — march feel
    TimeSignature(3, 4),   # 3/4  — waltz feel
    TimeSignature(4, 4),   # 4/4  — most common
    TimeSignature(3, 8),   # 3/8
    TimeSignature(6, 8),   # 6/8  — compound duple
    TimeSignature(9, 8),   # 9/8  — compound triple
    TimeSignature(12, 8),  # 12/8 — compound quadruple
    TimeSignature(5, 4),   # 5/4  — irregular (fun challenge!)
    TimeSignature(7, 8),   # 7/8  — irregular
]

# Quick lookup by display name, useful for the UI
TIME_SIGNATURE_MAP: dict[str, TimeSignature] = {
    ts.display_name: ts for ts in COMMON_TIME_SIGNATURES
}

# Get time signature
def get_time_signature(display_name: str) -> TimeSignature:
    """
    Retrieve a preset TimeSignature by its display name (e.g. '4/4').
    Raises KeyError if the name is not found.
    """
    if display_name not in TIME_SIGNATURE_MAP:
        raise KeyError(
            f"Unknown time signature '{display_name}'. "
            f"Available: {list(TIME_SIGNATURE_MAP.keys())}"
        )
    return TIME_SIGNATURE_MAP[display_name]