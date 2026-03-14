# Import libraries
import random

# Import custom modules
from core.notes import NoteEvent, Duration, make_note, make_rest
from core.time_signature import TimeSignature

# ===========================================================================
# GENERATE RHYTHM
# ===========================================================================
def generate_rhythm(
    time_sig: TimeSignature,        # from time_signature.py
    allowed_durations: list[Duration],  # from notes.py
    num_bars: int,
    allow_upbeat: bool,
) -> list[list[NoteEvent]]:         # returns bars of NoteEvents
    # Iterate over the bars
    bars = []
    for _ in range(num_bars):
        # STEP 1: Read time_sig to know the number of units to fill
        remaining = time_sig.bar_units
        bar = []

        # STEP 2: Iteratively fill the bar at random 
        while remaining > 0: 
            # Extract allowed durations compatible with remaining space
            options = [d for d in allowed_durations if d.value <= remaining]

            # Select a random one
            chosen = random.choice(options)

            # Create NoteEvent
            position = time_sig.bar_units - remaining
            on_beat = (position % time_sig.beat_units == 0)

            if not allow_upbeat and on_beat:
                event = make_note(chosen)   # beat → always a note
            else:
                if random.random() < 0.5:
                    event = make_rest(chosen)
                else:
                    event = make_note(chosen)

            # Update remaining space
            remaining -= event.units

            # Update bar
            bar.append(event)
    
        # Update bars
        bars.append(bar)

    # Return bars
    return bars