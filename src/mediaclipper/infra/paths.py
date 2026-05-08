"""Paths and directory management."""

import os
import sys
import shutil
from pathlib import Path


def _app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent.parent.parent


def app_data_dir() -> Path:
    """User-specific app data: settings, logs, temp."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / ".local" / "share"
    return base / "MediaClipper"


def default_output_dir() -> Path:
    """Default output folder for exported files."""
    if os.name == "nt":
        return Path.home() / "Videos" / "MediaClipper"
    return Path.home() / "Videos" / "MediaClipper"


def temp_root() -> Path:
    """Root folder for temporary working files."""
    return app_data_dir() / "temp"


def logs_dir() -> Path:
    return app_data_dir() / "logs"


def tools_dir() -> Path:
    """Folder containing bundled tools (ffmpeg, ffprobe, yt-dlp)."""
    if getattr(sys, "frozen", False):
        subdir = "windows" if os.name == "nt" else "linux"
    else:
        subdir = "windows" if os.name == "nt" else "linux"
    return _app_root() / "scripts" / "tools" / subdir


def ffmpeg_path() -> Path:
    tool = tools_dir() / "ffmpeg.exe" if os.name == "nt" else tools_dir() / "ffmpeg"
    if tool.exists():
        return tool
    return Path("ffmpeg")


def ffprobe_path() -> Path:
    tool = tools_dir() / "ffprobe.exe" if os.name == "nt" else tools_dir() / "ffprobe"
    if tool.exists():
        return tool
    return Path("ffprobe")


def ytdlp_path() -> Path:
    tool = tools_dir() / "yt-dlp.exe" if os.name == "nt" else tools_dir() / "yt-dlp"
    if tool.exists():
        return tool
    return Path("yt-dlp")


def ensure_dirs() -> None:
    """Create necessary directories if they don't exist."""
    for d in [app_data_dir(), temp_root(), logs_dir()]:
        d.mkdir(parents=True, exist_ok=True)

    out_dir = default_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)


def sanitize_filename(name: str) -> str:
    """Remove characters that are problematic in filenames."""
    import re
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip(". ")
    if not name:
        name = "output"
    return name


def unique_output_path(base_dir: Path, base_name: str, extension: str) -> Path:
    """Return a unique output path, appending a counter if needed."""
    path = base_dir / f"{base_name}.{extension}"
    if not path.exists():
        return path
    counter = 1
    while True:
        path = base_dir / f"{base_name}_{counter}.{extension}"
        if not path.exists():
            return path
        counter += 1
