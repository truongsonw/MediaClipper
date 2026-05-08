"""yt-dlp service for downloading media from URLs."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.paths import ytdlp_path
from mediaclipper.infra.process_runner import ProcessRunner

logger = get_logger(__name__)


@dataclass
class MediaInfo:
    title: str
    duration: float      # seconds
    thumbnail: Optional[str]
    platform: str
    webpage_url: str
    formats: list[dict]  # list of available formats


@dataclass
class DownloadOptions:
    url: str
    output_path: Path
    download_type: str   # "video" or "audio"
    quality: str         # "best", "1080p", "720p", "audio_only"


class YtDlpService:
    def __init__(self):
        self._runner = ProcessRunner()

    def get_metadata(self, url: str) -> Optional[MediaInfo]:
        """Fetch metadata for a URL using yt-dlp."""
        ytdlp = str(ytdlp_path())

        node_path = self._find_node_runtime()
        args = [ytdlp, "--dump-json", "--no-playlist", url]
        if node_path:
            args.extend(["--js-runtimes", f"node:{node_path}"])
        args.extend(self._get_auth_args())

        result = self._runner.run(args, timeout=30)

        if result.returncode != 0:
            logger.error("yt-dlp metadata failed: %s", result.stderr[:300])
            return None

        try:
            data = json.loads(result.stdout.strip().splitlines()[0])
        except (json.JSONDecodeError, IndexError) as e:
            logger.error("Failed to parse yt-dlp JSON: %s", e)
            return None

        title = data.get("title", "Unknown")
        duration = float(data.get("duration", 0) or 0)
        thumbnail = data.get("thumbnail")
        webpage_url = data.get("webpage_url", url)

        # Extract platform from extractor
        extractor = data.get("extractor", "")
        platform = extractor.replace("-", " ").replace("_", " ").title()

        formats = []
        for f in data.get("formats", []):
            formats.append({
                "format_id": f.get("format_id", ""),
                "ext": f.get("ext", ""),
                "resolution": f.get("resolution", ""),
                "filesize": f.get("filesize"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
                "format_note": f.get("format_note", ""),
            })

        logger.debug("Metadata: %s (%s), duration=%.1fs", title, platform, duration)
        return MediaInfo(
            title=title,
            duration=duration,
            thumbnail=thumbnail,
            platform=platform,
            webpage_url=webpage_url,
            formats=formats,
        )

    def download(
        self,
        options: DownloadOptions,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> tuple[bool, str]:
        """
        Download media from URL.
        Returns (success, output_path_or_error).
        """
        ytdlp = str(ytdlp_path())
        args = self._build_download_args(ytdlp, options)

        logger.info("Downloading: %s", options.url)

        def progress_hook(data: dict):
            if on_progress and data.get("_total_bytes") and data.get("_downloaded_bytes"):
                pct = (data["_downloaded_bytes"] / data["_total_bytes"]) * 100
                on_progress(pct)
            elif on_progress and data.get("_total_bytes_estimate"):
                pct = (data.get("_downloaded_bytes", 0) / data["_total_bytes_estimate"]) * 100
                on_progress(pct)

        # For now, use simple progress parsing from stderr
        def on_progress_simple(secs: float, _total: float):
            # yt-dlp outputs progress info to stderr in format:
            # [download]  42.3% of ~150.5MiB at  2.5MiB/s ETA 00:01
            if on_progress:
                on_progress(secs)  # we'll update via stderr parsing

        result = self._runner.run(args, timeout=3600)

        if result.returncode == 0:
            logger.info("Download complete: %s", options.output_path)
            return True, str(options.output_path)
        else:
            error = self._parse_error(result.stderr) or "Download failed"
            logger.error("Download failed: %s", error)
            return False, error

    def _build_download_args(self, ytdlp: str, options: DownloadOptions) -> list[str]:
        args = [ytdlp, "--no-playlist", "--newline", "-o", str(options.output_path)]

        node_path = self._find_node_runtime()
        if node_path:
            args.extend(["--js-runtimes", f"node:{node_path}"])

        args.extend(self._get_auth_args())

        if options.download_type == "audio":
            args += ["-x", "--audio-format", options.quality_to_audio_format(options.quality)]
        else:
            args += ["-f", self._quality_to_video_format(options.quality)]

        args.append(options.url)
        return args

    def _get_auth_args(self) -> list[str]:
        """Get yt-dlp auth arguments. Tries to use browser cookies via yt-dlp's native support."""
        # --cookies-from-browser: reads cookies directly from Chrome
        # --remote-components ejs:github: downloads EJS challenge-solver scripts from GitHub
        return ["--cookies-from-browser", "chrome", "--remote-components", "ejs:github"]

    def _quality_to_video_format(self, quality: str) -> str:
        mapping = {
            "best": "bestvideo+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "audio_only": "bestaudio/best",
        }
        return mapping.get(quality, "bestvideo+bestaudio/best")

    def quality_to_audio_format(self, quality: str) -> str:
        mapping = {
            "best": "m4a",
            "audio_only": "m4a",
        }
        return mapping.get(quality, "m4a")

    def _find_node_runtime(self) -> Optional[str]:
        """Find Node.js runtime path for yt-dlp."""
        import shutil, os
        candidates = [
            "/opt/cursor/usr/share/cursor/resources/app/resources/helpers/node",
            shutil.which("node"),
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate
        return None

    def _parse_error(self, stderr: str) -> Optional[str]:
        if not stderr:
            return None
        lines = stderr.strip().splitlines()
        for line in lines:
            if "ERROR" in line or "error" in line:
                return line.strip()[:200]
        return None

    def update(self) -> tuple[bool, str]:
        """Update yt-dlp to the latest version."""
        ytdlp = str(ytdlp_path())
        args = [ytdlp, "-U"]
        result = self._runner.run(args, timeout=60)
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip()[:200]
