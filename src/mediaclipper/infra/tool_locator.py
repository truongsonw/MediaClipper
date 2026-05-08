"""Locate bundled or system tools (FFmpeg, FFprobe, yt-dlp)."""

import shutil
import sys
from dataclasses import dataclass
from typing import Optional

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.paths import (
    ffmpeg_path,
    ffprobe_path,
    ytdlp_path,
    tools_dir,
)

logger = get_logger(__name__)


@dataclass
class ToolInfo:
    path: str
    version: str
    available: bool


class ToolLocator:
    """Locate and validate external tools."""

    def __init__(self):
        self._ffmpeg: Optional[ToolInfo] = None
        self._ffprobe: Optional[ToolInfo] = None
        self._ytdlp: Optional[ToolInfo] = None

    def ffmpeg(self) -> ToolInfo:
        if self._ffmpeg is None:
            self._ffmpeg = self._locate(
                "ffmpeg",
                ffmpeg_path(),
                ["--version"],
                version_pattern=r"ffmpeg version (\S+)",
            )
        return self._ffmpeg

    def ffprobe(self) -> ToolInfo:
        if self._ffprobe is None:
            self._ffprobe = self._locate(
                "ffprobe",
                ffprobe_path(),
                ["--version"],
                version_pattern=r"ffprobe version (\S+)",
            )
        return self._ffprobe

    def ytdlp(self) -> ToolInfo:
        if self._ytdlp is None:
            self._ytdlp = self._locate(
                "yt-dlp",
                ytdlp_path(),
                ["--version"],
                version_pattern=r"(\S+)",
            )
        return self._ytdlp

    def _locate(
        self,
        name: str,
        preferred_path: str,
        version_args: list[str],
        version_pattern: str,
    ) -> ToolInfo:
        """Try to find and validate a tool."""
        import re
        import subprocess

        # Try preferred path first (bundled tools)
        candidates = [preferred_path]
        # Fall back to system PATH
        system_path = shutil.which(name)
        if system_path:
            candidates.append(system_path)

        for candidate in candidates:
            try:
                result = subprocess.run(
                    [candidate] + version_args,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if result.returncode == 0:
                    version = "unknown"
                    match = re.search(version_pattern, result.stdout + result.stderr)
                    if match:
                        version = match.group(1)
                    logger.info("%s found at %s (version %s)", name, candidate, version)
                    return ToolInfo(path=candidate, version=version, available=True)
            except Exception as e:
                logger.debug("Failed to run %s from %s: %s", name, candidate, e)

        logger.warning("%s not found", name)
        return ToolInfo(path="", version="", available=False)

    def check_all(self) -> dict[str, ToolInfo]:
        return {
            "ffmpeg": self.ffmpeg(),
            "ffprobe": self.ffprobe(),
            "yt-dlp": self.ytdlp(),
        }

    def all_available(self) -> bool:
        return all(t.available for t in self.check_all().values())


_tool_locator: Optional[ToolLocator] = None


def get_tool_locator() -> ToolLocator:
    global _tool_locator
    if _tool_locator is None:
        _tool_locator = ToolLocator()
    return _tool_locator
