# Import libraries
from dataclasses import dataclass
from enum import Enum

# Define constants
UNITS_PER_WHOLE = 32  # reference constant — don't change this 
#! ---> Will this work for time signatures like 7/8?  

# ===========================================================================
# DURATION CLASS
# ===========================================================================
# ---------------------------------------------------------------------------
# Duration
# ---------------------------------------------------------------------------
# All durations are expressed in 32nd-note units.
# This makes arithmetic easy: every duration is a plain integer,
# and a bar's total is just a sum.
#
#   Whole note      = 32 units  (4/4 of a whole bar)
#   Half note       = 16 units  (2/4)
#   Quarter note    =  8 units  (1/4)
#   Eighth note     =  4 units  (1/8)
#   Sixteenth note  =  2 units  (1/16)
#   32nd note       =  1 unit   (1/32)
#
# Dotted notes add half their own value:
#   Dotted half     = 16 + 8  = 24 units
#   Dotted quarter  =  8 + 4  = 12 units
#   Dotted eighth   =  4 + 2  =  6 units
# ---------------------------------------------------------------------------
class Duration(Enum):
    # -----------------------------------------------------------------------
    # Global Variables
    # -----------------------------------------------------------------------
    # Define supported note durations
    WHOLE           = 32
    DOTTED_HALF     = 24
    HALF            = 16
    DOTTED_QUARTER  = 12
    QUARTER         = 8
    DOTTED_EIGHTH   = 6
    EIGHTH          = 4
    SIXTEENTH       = 2
    THIRTY_SECOND   = 1

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    @property
    def display_name(self) -> str:
        """Human-readable name for UI labels."""
        return self.name.replace("_", " ").title()

    @property
    def is_dotted(self) -> bool:
        return "DOTTED" in self.name

# ===========================================================================
# RHYTHMIC EVENT CLASS
# ===========================================================================
# ---------------------------------------------------------------------------
# NoteEvent
# ---------------------------------------------------------------------------
# A single event in a rhythm: either a note or a rest, with a duration.
# This is the atom that rhythm.py works with.
# ---------------------------------------------------------------------------
@dataclass
class NoteEvent:
    # -----------------------------------------------------------------------
    # Global Variables
    # -----------------------------------------------------------------------
    duration: Duration
    is_rest: bool = False

    # -----------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------
    @property
    def units(self) -> int:
        """Duration expressed in 32nd-note units."""
        return self.duration.value

    # -----------------------------------------------------------------------
    # Representation
    # -----------------------------------------------------------------------
    def __repr__(self) -> str:
        kind = "Rest" if self.is_rest else "Note"
        return f"{kind}({self.duration.display_name})"

# ===========================================================================
# HELPERS
# ===========================================================================
# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------
# All durations available in the app, ordered from longest to shortest.
# The UI can display these as checkboxes for the user to pick from.
ALL_DURATIONS: list[Duration] = list(Duration)

# Durations that are "basic" (non-dotted) — a sensible default selection
# for a beginner just starting out.
BASIC_DURATIONS: list[Duration] = [
    Duration.WHOLE,
    Duration.HALF,
    Duration.QUARTER,
    Duration.EIGHTH,
    Duration.SIXTEENTH,
    Duration.THIRTY_SECOND,
]
DOTTED_DURATIONS: list[Duration] = [d for d in Duration if d.is_dotted]

# Make note function
def make_note(duration: Duration) -> NoteEvent:
    """Shorthand to create a note event."""
    return NoteEvent(duration=duration, is_rest=False)

# Make rest function
def make_rest(duration: Duration) -> NoteEvent:
    """Shorthand to create a rest event."""
    return NoteEvent(duration=duration, is_rest=True)