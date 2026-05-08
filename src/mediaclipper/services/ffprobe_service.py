"""FFprobe service for reading media metadata."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.paths import ffprobe_path
from mediaclipper.infra.process_runner import ProcessRunner

logger = get_logger(__name__)


@dataclass
class MediaMetadata:
    duration: float  # seconds
    width: int
    height: int
    codec: str
    audio_codec: str
    bitrate: Optional[float]
    is_audio: bool
    is_video: bool
    file_size: int


class FFprobeService:
    def __init__(self):
        self._runner = ProcessRunner()

    def get_metadata(self, file_path: Path) -> Optional[MediaMetadata]:
        """
        Get metadata for a local media file using ffprobe.
        Returns MediaMetadata or None on failure.
        """
        if not file_path.exists():
            logger.error("File does not exist: %s", file_path)
            return None

        ffprobe = str(ffprobe_path())
        args = [
            ffprobe,
            "-v", "error",
            "-show_format",
            "-show_streams",
            "-of", "json",
            str(file_path),
        ]

        result = self._runner.run(args)

        if result.returncode != 0:
            logger.error("ffprobe failed for %s: %s", file_path, result.stderr[:300])
            return None

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse ffprobe JSON: %s", e)
            return None

        streams = data.get("streams", [])
        fmt = data.get("format", {})

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        duration_str = fmt.get("duration", "0")
        try:
            duration = float(duration_str)
        except ValueError:
            duration = 0.0

        try:
            file_size = int(fmt.get("size", 0))
        except ValueError:
            file_size = 0

        width = 0
        height = 0
        codec = ""
        if video_stream:
            width = int(video_stream.get("width", 0) or 0)
            height = int(video_stream.get("height", 0) or 0)
            codec = video_stream.get("codec_name", "")

        audio_codec = ""
        if audio_stream:
            audio_codec = audio_stream.get("codec_name", "")

        bitrate_str = fmt.get("bit_rate", "")
        try:
            bitrate = float(bitrate_str) if bitrate_str else None
        except ValueError:
            bitrate = None

        is_video = video_stream is not None
        is_audio = audio_stream is not None

        logger.debug(
            "Metadata for %s: duration=%.1fs, %dx%d, video=%s, audio=%s",
            file_path, duration, width, height, codec, audio_codec,
        )

        return MediaMetadata(
            duration=duration,
            width=width,
            height=height,
            codec=codec,
            audio_codec=audio_codec,
            bitrate=bitrate,
            is_audio=is_audio,
            is_video=is_video,
            file_size=file_size,
        )

    def format_duration(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS.mmm."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"

    def parse_time(self, time_str: str) -> Optional[float]:
        """Parse time string like HH:MM:SS.mmm or MM:SS to seconds."""
        import re
        time_str = time_str.strip()
        if not time_str:
            return None
        # Try HH:MM:SS.mmm or HH:MM:SS
        match = re.match(r"^(\d+):(\d{1,2}):(\d{1,2}(?:\.\d+)?)$", time_str)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
        # Try MM:SS or H:MM
        match2 = re.match(r"^(\d+):(\d{2}(?:\.\d+)?)$", time_str)
        if match2:
            a, b = match2.groups()
            # If first part > 59, treat as H:MM
            if int(a) > 59:
                return int(a) * 60 + float(b)
            else:
                return int(a) * 60 + float(b)
        # Single number (seconds)
        try:
            return float(time_str)
        except ValueError:
            return None
