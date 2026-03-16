# solfeggio.spec
# PyInstaller spec file for SolfeggIO
# Build with: pyinstaller solfeggio.spec

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect music21 data files (it has a lot of internal data)
music21_datas = collect_data_files('music21')

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # UI assets
        ('ui/style_dark.qss',  'ui'),
        ('ui/style_light.qss', 'ui'),
        # music21 internal data
        *music21_datas,
    ],
    hiddenimports=[
        # music21 uses dynamic imports internally
        *collect_submodules('music21'),
        # PyQt6 modules that may not be auto-detected
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PyQt6.QtPrintSupport',
        # numpy & pygame
        'numpy',
        'pygame',
        'pygame.mixer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Keep the bundle lean — exclude things we don't use
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
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # no terminal window on launch
    disable_windowed_traceback=False,
    # icon='docs/icon.ico',  # uncomment when you have an icon
)
