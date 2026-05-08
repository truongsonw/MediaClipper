"""Download worker - runs yt-dlp in a background QThread."""

from pathlib import Path
from PySide6.QtCore import QThread, Signal, QMutex

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.temp_manager import get_temp_manager
from mediaclipper.services.ytdlp_service import YtDlpService, DownloadOptions

logger = get_logger(__name__)


class DownloadWorker(QThread):
    """Background worker for downloading media from URL."""

    progress = Signal(float)          # percentage 0-100
    finished = Signal(bool, str)      # success, output_path_or_error
    cancelled = Signal()

    def __init__(self, url: str, output_path: Path, download_type: str, quality: str, parent=None):
        super().__init__(parent)
        self._url = url
        self._output_path = output_path
        self._download_type = download_type
        self._quality = quality
        self._cancelled = False
        self._mutex = QMutex()

    def cancel(self) -> None:
        with QMutex():
            self._cancelled = True
        self._service._runner.kill()

    def run(self) -> None:
        self._cancelled = False
        temp_mgr = get_temp_manager()
        temp_mgr.create_task_dir()

        self._service = YtDlpService()
        options = DownloadOptions(
            url=self._url,
            output_path=self._output_path,
            download_type=self._download_type,
            quality=self._quality,
        )

        # We'll parse progress from yt-dlp stderr
        # yt-dlp outputs: [download]  42.3% ...
        import re
        progress_pattern = re.compile(r"\[download\]\s+([\d.]+)%")

        def on_progress(pct: float):
            if self._cancelled:
                self._service._runner.kill()
                return
            self.progress.emit(pct)

        # Simple approach: run yt-dlp and poll
        success, output = self._service.download(options, on_progress=on_progress)

        if self._cancelled:
            temp_mgr.cleanup_current()
            self.cancelled.emit()
            return

        if success:
            temp_mgr.cleanup_current()
            self.finished.emit(True, output)
        else:
            temp_mgr.cleanup_current()
            self.finished.emit(False, output)
