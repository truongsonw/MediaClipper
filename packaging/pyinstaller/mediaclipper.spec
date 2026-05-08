"""PyInstaller spec file for MediaClipper."""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

project_root = Path(SPECPATH).parent.parent

a = Analysis(
    ["src/mediaclipper/main.py"],
    pathex=[str(project_root / "src")],
    binaries=[
        # Bundle external tools
        ("tools/windows/ffmpeg.exe", "tools/windows"),
        ("tools/windows/ffprobe.exe", "tools/windows"),
        ("tools/windows/yt-dlp.exe", "tools/windows"),
    ],
    datas=[],
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "yt_dlp",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MediaClipper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / "packaging" / "icon.ico")
    if (project_root / "packaging" / "icon.ico").exists()
    else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MediaClipper",
)
