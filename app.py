# Import libraries
import music21
import sys
from PyQt6.QtWidgets import QApplication
import shutil
import atexit
from pathlib import Path

# Import custom modules
from ui.main_window import MainWindow

# ===========================================================================
# FUNCTIONS
# ===========================================================================
def check_lilypond():
    path = music21.environment.get('lilypondPath')
    if not path:
        raise EnvironmentError(
            "LilyPond not found. Please run: python scripts/setup_env.py"
        )

CACHE_DIR = "notation/cache"

def _cleanup_cache():
    if Path(CACHE_DIR).exists():
        shutil.rmtree(CACHE_DIR)
        print("Cache cleared.")

def run():
    check_lilypond()
    
    atexit.register(_cleanup_cache)
    
    app = QApplication(sys.argv)
    app.setApplicationName("Solfio")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

# ===========================================================================
# MAIN
# ===========================================================================
if __name__ == "__main__":
    run()