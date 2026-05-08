"""Metadata worker - fetches URL metadata using yt-dlp in background."""

from PySide6.QtCore import QThread, Signal

from mediaclipper.infra.logger import get_logger
from mediaclipper.services.ytdlp_service import YtDlpService, MediaInfo

logger = get_logger(__name__)


class MetadataWorker(QThread):
    """Background worker for fetching URL metadata."""

    finished = Signal(object)   # MediaInfo or None
    error = Signal(str)          # error message

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        logger.debug("Fetching metadata for: %s", self._url)
        service = YtDlpService()
        info = service.get_metadata(self._url)
        if info:
            self.finished.emit(info)
        else:
            self.error.emit(f"Không thể lấy thông tin video từ link này.\n\nCó thể do:\n- Link không hợp lệ.\n- Video riêng tư hoặc cần đăng nhập.\n- Nền tảng vừa thay đổi.\n- Kết nối mạng không ổn định.")
