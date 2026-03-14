# scripts/setup_env.py
import subprocess
import music21

# ===========================================================================
# LILYPOND SETUP
# ===========================================================================
def find_lilypond():
    result = subprocess.run(['which', 'lilypond'], capture_output=True, text=True)
    return result.stdout.strip()

path = find_lilypond()
if not path:
    print("[FAIL] LilyPond not found. Please install it first:") 
    print("       sudo apt install lilypond   (Linux)")
    print("       brew install lilypond       (macOS)")
else:
    us = music21.environment.UserSettings()
    us['lilypondPath'] = path
    print(f"[SUCCESS] LilyPond found and configured at: {path}")