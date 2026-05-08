"""Export worker - runs FFmpeg in a background QThread."""

from pathlib import Path
from PySide6.QtCore import QThread, Signal, QMutex

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.temp_manager import get_temp_manager
from mediaclipper.services.ffmpeg_service import FFmpegService, ExportOptions

logger = get_logger(__name__)


class ExportWorker(QThread):
    """Background worker for media export."""

    progress = Signal(float)         # percentage 0-100
    finished = Signal(bool, str)     # success, error_message
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._options: ExportOptions | None = None
        self._cancelled = False
        self._mutex = QMutex()

    def set_options(self, options: ExportOptions) -> None:
        self._options = options

    def cancel(self) -> None:
        with QMutex():
            self._cancelled = True
        self._ffmpeg_runner.kill()

    def run(self) -> None:
        if self._options is None:
            self.finished.emit(False, "No export options set")
            return

        self._cancelled = False
        temp_mgr = get_temp_manager()
        temp_mgr.create_task_dir()

        ffmpeg = FFmpegService()

        def on_progress(pct: float):
            if self._cancelled:
                self._ffmpeg_runner.kill()
                return
            self.progress.emit(pct)

        self._ffmpeg_runner = ffmpeg._runner

        success, error = ffmpeg.export(self._options, on_progress=on_progress)

        if self._cancelled:
            temp_mgr.cleanup_current()
            self.cancelled.emit()
            return

        if success:
            temp_mgr.cleanup_current()
            self.finished.emit(True, str(self._options.output_path))
        else:
            temp_mgr.cleanup_current()
            self.finished.emit(False, error)
