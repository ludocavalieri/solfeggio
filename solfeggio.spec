# solfeggio.spec
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

music21_datas = collect_data_files('music21')

# Include the bundled LilyPond directory if it exists (set by CI)
# In local builds this folder won't exist and LilyPond falls back
# to system PATH detection in app.py
lilypond_datas = []
if os.path.exists('bundled_lilypond'):
    lilypond_datas = [('bundled_lilypond', 'bundled_lilypond')]

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('ui/style_dark.qss',  'ui'),
        ('ui/style_light.qss', 'ui'),
        *music21_datas,
        *lilypond_datas,
    ],
    hiddenimports=[
        *collect_submodules('music21'),
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.QtPrintSupport',
        'numpy',
        'pygame',
        'pygame.mixer',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'scipy',
        'IPython',
        'jupyter',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SolfeggIO',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    # icon='docs/icon.ico',
)
