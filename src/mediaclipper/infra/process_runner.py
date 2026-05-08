"""Run external processes (FFmpeg, yt-dlp) and stream output."""

import os
import subprocess
import signal
import time
import re
from dataclasses import dataclass
from typing import Optional, Callable

from mediaclipper.infra.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str


class ProcessRunner:
    """
    Runs external commands and optionally parses progress from stdout/stderr.
    """

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None

    def run(
        self,
        args: list[str],
        cwd: Optional[str] = None,
        on_progress: Optional[Callable[[float, float], None]] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
    ) -> ProcessResult:
        """
        Run a command and optionally call on_progress(processed_secs, total_secs).

        Returns ProcessResult with returncode, stdout, stderr.
        """
        merged_env = {**subprocess.os.environ, **(env or {})}

        logger.debug("Running command: %s", " ".join(args))

        self._process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=merged_env,
            bufsize=0,
        )

        stdout_chunks: list[bytes] = []
        stderr_chunks: list[bytes] = []
        total_secs: Optional[float] = None

        try:
            # Stream stdout for progress parsing (ffmpeg writes progress to stdout)
            while True:
                char = self._process.stdout.read(1)
                if not char:
                    break
                stdout_chunks.append(char)
                if on_progress:
                    # Try to detect a full line from the bytes accumulated so far
                    line_bytes = b"".join(stdout_chunks)
                    if b"\n" in line_bytes or b"\r" in line_bytes:
                        try:
                            line = line_bytes.decode("utf-8", errors="replace")
                            secs = self._parse_ffmpeg_time(line)
                            if secs is not None:
                                on_progress(secs, total_secs or 0)
                        except Exception:
                            pass
                        stdout_chunks.clear()

            stderr_data = self._process.stderr.read()
            if stderr_data:
                stderr_chunks.append(stderr_data)

            self._process.wait(timeout=timeout)

        except subprocess.TimeoutExpired:
            logger.warning("Process timed out after %s seconds", timeout)
            self._process.kill()
            self._process.wait()

        returncode = self._process.returncode
        stdout = b"".join(stdout_chunks).decode("utf-8", errors="replace")
        stderr = b"".join(stderr_chunks).decode("utf-8", errors="replace")

        if returncode != 0 and stderr:
            logger.warning("Process exited with code %d: %s", returncode, stderr[:500])

        self._process = None
        return ProcessResult(returncode=returncode, stdout=stdout, stderr=stderr)

    def _parse_ffmpeg_time(self, line: str) -> Optional[float]:
        """Parse ffmpeg time=XX:XX:XX.xxx output."""
        match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
        return None

    def kill(self) -> None:
        """Kill the running process."""
        if self._process is None:
            return
        try:
            if os.name == "nt":
                self._process.terminate()
            else:
                self._process.send_signal(signal.SIGTERM)
                time.sleep(0.3)
                if self._process.poll() is None:
                    self._process.kill()
        except Exception as e:
            logger.warning("Error killing process: %s", e)
        self._process = None
