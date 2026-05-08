"""FFmpeg service for cutting and converting media."""

import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.paths import ffmpeg_path, sanitize_filename, unique_output_path, default_output_dir
from mediaclipper.infra.process_runner import ProcessRunner

logger = get_logger(__name__)


@dataclass
class ExportOptions:
    input_path: Path
    output_path: Path
    start_time: float  # seconds
    end_time: float    # seconds
    cut_mode: str      # "fast" or "exact"
    output_format: str # "mp4", "m4a", "mp3"


class FFmpegService:
    def __init__(self):
        self._runner = ProcessRunner()

    def export(
        self,
        options: ExportOptions,
        on_progress: Optional[callable] = None,
    ) -> tuple[bool, str]:
        """
        Run FFmpeg to export a clip.
        Returns (success, error_message).
        """
        ffmpeg = str(ffmpeg_path())
        input_path = str(options.input_path.resolve())
        output_path = str(options.output_path.resolve())

        # Ensure output directory exists
        options.output_path.parent.mkdir(parents=True, exist_ok=True)

        start_str = self._format_time(options.start_time)
        duration = options.end_time - options.start_time
        duration_str = self._format_time(duration)

        args = self._build_args(
            ffmpeg, input_path, output_path,
            start_str, duration_str,
            options.cut_mode, options.output_format,
        )

        logger.info(
            "Exporting: start=%s, duration=%s, mode=%s, format=%s -> %s",
            start_str, duration_str, options.cut_mode, options.output_format, output_path,
        )

        # Override progress to report percentage
        total_duration = duration

        def progress_callback(processed_secs: float, _total: float):
            if on_progress and total_duration > 0:
                pct = min(100.0, (processed_secs / total_duration) * 100)
                on_progress(pct)

        result = self._runner.run(
            args,
            on_progress=progress_callback,
            timeout=max(30.0, duration * 3),
        )

        if result.returncode == 0:
            if on_progress:
                on_progress(100.0)
            logger.info("Export complete: %s", output_path)
            return True, ""
        else:
            error_msg = self._parse_error(result.stderr) or "Unknown FFmpeg error"
            logger.error("Export failed: %s", error_msg)
            return False, error_msg

    def _build_args(
        self,
        ffmpeg: str,
        input_path: str,
        output_path: str,
        start: str,
        duration: str,
        cut_mode: str,
        output_format: str,
    ) -> list[str]:
        args = [ffmpeg, "-hide_banner", "-loglevel", "error"]

        if cut_mode == "fast":
            # Fast cut: copy streams without re-encoding
            args += ["-ss", start, "-i", input_path, "-t", duration, "-c", "copy"]
        else:
            # Exact cut: re-encode for frame-accurate cuts
            args += ["-ss", start, "-i", input_path, "-t", duration]
            if output_format == "mp4":
                args += ["-c:v", "libx264", "-preset", "fast", "-c:a", "aac"]
            elif output_format == "m4a":
                args += ["-vn", "-c:a", "aac"]
            elif output_format == "mp3":
                args += ["-vn", "-c:a", "libmp3lame", "-q:a", "2"]

        # Output
        if output_format == "mp4":
            args += ["-movflags", "+faststart"]
        args.append(output_path)
        return args

    def _format_time(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:05.2f}"

    def _parse_error(self, stderr: str) -> Optional[str]:
        if not stderr:
            return None
        lines = stderr.strip().splitlines()
        for line in lines:
            line = line.strip()
            if line:
                return line[:200]
        return None

    def get_duration(self, file_path: Path) -> Optional[float]:
        """Quick probe to get duration only."""
        from mediaclipper.services.ffprobe_service import FFprobeService
        probe = FFprobeService()
        meta = probe.get_metadata(file_path)
        return meta.duration if meta else None
