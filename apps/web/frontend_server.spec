# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

# Get paths
SPEC_DIR = os.path.abspath(SPECPATH)  # apps/web
APPS_DIR = os.path.dirname(SPEC_DIR)  # apps
ROOT_DIR = os.path.dirname(APPS_DIR)  # DiPeO

# Icon path
icon_path = os.path.join(ROOT_DIR, 'apps', 'desktop', 'src-tauri', 'icons', 'icon.ico')
if not os.path.exists(icon_path):
    icon_path = None

a = Analysis(
    ['frontend_server.py'],
    pathex=[SPEC_DIR],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'PyQt5',
        'PySide2',
        'notebook',
        'jupyter',
        'IPython',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='dipeo-frontend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for seeing server output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
