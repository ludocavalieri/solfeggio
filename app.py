import sys
import shutil
import subprocess
import atexit
from pathlib import Path

import music21
from PyQt6.QtWidgets import QApplication, QMessageBox

from ui.main_window import MainWindow

# ===========================================================================
# CONSTANTS
# ===========================================================================
CACHE_DIR = "notation/cache"

# ===========================================================================
# LILYPOND SETUP
# ===========================================================================
def _get_bundle_dir() -> Path:
    """
    When running as a PyInstaller executable, sys._MEIPASS points to the
    temporary directory where bundled files are extracted.
    When running from source, use the project root.
    """
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def _find_bundled_lilypond() -> str | None:
    """
    Look for LilyPond inside the PyInstaller bundle.
    Returns the path to the binary if found, None otherwise.
    """
    bundle_dir = _get_bundle_dir()
    candidates = [
        bundle_dir / 'bundled_lilypond' / 'bin' / 'lilypond',       # Linux/macOS
        bundle_dir / 'bundled_lilypond' / 'bin' / 'lilypond.exe',   # Windows
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    return None

def _find_system_lilypond() -> str | None:
    """
    Search for LilyPond on the system PATH.
    Uses 'which' on macOS/Linux and 'where' on Windows.
    """
    # macOS / Linux
    try:
        result = subprocess.run(
            ['which', 'lilypond'],
            capture_output=True, text=True
        )
        path = result.stdout.strip()
        if path:
            return path
    except FileNotFoundError:
        pass

    # Windows
    try:
        result = subprocess.run(
            ['where', 'lilypond'],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().splitlines()
        if lines:
            return lines[0]
    except FileNotFoundError:
        pass

    return None

def setup_lilypond():
    """
    Configure LilyPond for music21.

    Priority:
      1. Already configured in music21's settings — skip
      2. Bundled LilyPond inside the PyInstaller executable — use it
      3. LilyPond found on system PATH — use and save to music21 config
      4. Not found anywhere — show error dialog and exit

    This means:
      - Executable users: fully automatic, no installation needed
      - Source users: need LilyPond on their PATH (configured once)
    """
    # 1. Already configured
    if music21.environment.get('lilypondPath'):
        return

    # 2. Bundled binary (executable users)
    path = _find_bundled_lilypond()
    if path:
        us = music21.environment.UserSettings()
        us['lilypondPath'] = path
        return

    # 3. System PATH (source users)
    path = _find_system_lilypond()
    if path:
        us = music21.environment.UserSettings()
        us['lilypondPath'] = path
        return

    # 4. Not found
    raise EnvironmentError(
        "LilyPond not found on your system.\n\n"
        "Please install it first:\n"
        "  macOS:   brew install lilypond\n"
        "  Linux:   sudo apt install lilypond\n"
        "  Windows: https://lilypond.org/download.html\n\n"
        "Then relaunch SolfeggIO."
    )

# ===========================================================================
# CACHE CLEANUP
# ===========================================================================
def _cleanup_cache():
    """Remove the notation cache directory on exit."""
    if Path(CACHE_DIR).exists():
        shutil.rmtree(CACHE_DIR)

# ===========================================================================
# MAIN
# ===========================================================================
def run():
    app = QApplication(sys.argv)
    app.setApplicationName("SolfeggIO")

    try:
        setup_lilypond()
    except EnvironmentError as e:
        QMessageBox.critical(None, "LilyPond not found", str(e))
        sys.exit(1)

    atexit.register(_cleanup_cache)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    run()