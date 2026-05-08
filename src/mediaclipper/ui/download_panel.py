"""Download panel - paste URL, get metadata, download media."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QGroupBox, QRadioButton,
    QProgressBar, QComboBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PySide6.QtCore import QUrl as QtUrl

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.paths import default_output_dir, unique_output_path, sanitize_filename
from mediaclipper.services.ytdlp_service import YtDlpService, MediaInfo
from mediaclipper.services.settings_service import get_settings_service
from mediaclipper.workers.metadata_worker import MetadataWorker
from mediaclipper.workers.download_worker import DownloadWorker

logger = get_logger(__name__)


class DownloadPanel(QWidget):
    """Panel for downloading media from URL."""

    back_home = Signal()
    file_downloaded = Signal(str)   # path to downloaded file

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = get_settings_service()
        self._current_url = ""
        self._media_info: MediaInfo | None = None
        self._metadata_worker: MetadataWorker | None = None
        self._download_worker: DownloadWorker | None = None
        self._thumb_pixmap: QPixmap | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        btn_back = QPushButton("← Quay lại")
        btn_back.setStyleSheet("QPushButton { color: #3498db; border: none; font-size: 13px; }")
        btn_back.clicked.connect(self._on_back)
        header.addWidget(btn_back)
        header.addStretch()

        title = QLabel("Tải video/audio")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ── URL input ──────────────────────────────────────────────
        url_layout = QHBoxLayout()
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self._url_input.setMinimumHeight(36)
        self._url_input.setStyleSheet("padding: 6px 10px; font-size: 14px; border: 1px solid #bdc3c7; border-radius: 4px;")
        self._url_input.returnPressed.connect(self._on_fetch)
        url_layout.addWidget(self._url_input, 1)

        self._fetch_btn = QPushButton("Lấy thông tin")
        self._fetch_btn.setMinimumHeight(36)
        self._fetch_btn.setStyleSheet(self._btn_style("#3498db"))
        self._fetch_btn.clicked.connect(self._on_fetch)
        url_layout.addWidget(self._fetch_btn)
        layout.addWidget(QLabel("Link video/audio:"))
        layout.addLayout(url_layout)

        # ── Metadata display ────────────────────────────────────────
        meta_container = QWidget()
        meta_layout = QHBoxLayout(meta_container)

        self._thumbnail_label = QLabel()
        self._thumbnail_label.setFixedSize(200, 120)
        self._thumbnail_label.setStyleSheet("background: #ecf0f1; border-radius: 4px;")
        self._thumbnail_label.setAlignment(Qt.AlignCenter)
        self._thumbnail_label.setText("Chưa có thumbnail")
        meta_layout.addWidget(self._thumbnail_label)

        info_layout = QVBoxLayout()
        self._title_label = QLabel("Chưa có thông tin")
        self._title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #2c3e50;")
        self._title_label.setWordWrap(True)
        info_layout.addWidget(self._title_label)

        self._duration_label = QLabel("Thời lượng: --:--")
        self._duration_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        info_layout.addWidget(self._duration_label)

        self._platform_label = QLabel("Nền tảng: --")
        self._platform_label.setStyleSheet("color: #7f8c8d; font-size: 13px;")
        info_layout.addWidget(self._platform_label)

        info_layout.addStretch()
        meta_layout.addLayout(info_layout, 1)
        meta_layout.addStretch()

        self._meta_container = meta_container
        self._meta_container.setVisible(False)
        layout.addWidget(self._meta_container)

        # ── Download options ────────────────────────────────────────
        opt_container = QWidget()
        opt_layout = QVBoxLayout(opt_container)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Tải dưới dạng:"))
        self._type_video = QRadioButton("Video MP4")
        self._type_video.setChecked(True)
        type_layout.addWidget(self._type_video)
        self._type_audio_m4a = QRadioButton("Audio M4A")
        type_layout.addWidget(self._type_audio_m4a)
        self._type_audio_mp3 = QRadioButton("Audio MP3")
        type_layout.addWidget(self._type_audio_mp3)
        type_layout.addStretch()
        opt_layout.addLayout(type_layout)

        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Chất lượng:"))
        self._quality_combo = QComboBox()
        self._quality_combo.addItems(["Best", "1080p", "720p", "Audio only"])
        quality_layout.addWidget(self._quality_combo)
        quality_layout.addStretch()
        opt_layout.addLayout(quality_layout)

        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Tên file:"))
        self._output_name = QLineEdit()
        self._output_name.setMinimumHeight(30)
        self._output_name.setStyleSheet("border: 1px solid #bdc3c7; border-radius: 4px; padding: 4px 8px;")
        output_layout.addWidget(self._output_name, 1)

        self._btn_change_folder = QPushButton("Đổi thư mục")
        self._btn_change_folder.setStyleSheet(self._btn_style("#27ae60"))
        self._btn_change_folder.clicked.connect(self._change_folder)
        output_layout.addWidget(self._btn_change_folder)
        self._folder_label = QLabel(str(self._settings.get_default_output_dir()))
        self._folder_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        output_layout.addWidget(self._folder_label)
        opt_layout.addLayout(output_layout)

        self._opt_container = opt_container
        self._opt_container.setVisible(False)
        layout.addWidget(self._opt_container)

        # ── Legal notice ─────────────────────────────────────────────
        notice = QLabel(
            "Bạn chịu trách nhiệm đảm bảo mình có quyền tải và sử dụng nội dung này. "
            "Ứng dụng không hỗ trợ vượt cơ chế bảo vệ, DRM, CAPTCHA hoặc nội dung không có quyền truy cập."
        )
        notice.setStyleSheet("font-size: 11px; color: #95a5a6; font-style: italic;")
        notice.setWordWrap(True)
        layout.addWidget(notice)

        # ── Progress ────────────────────────────────────────────────
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_label = QLabel("")
        self._progress_label.setAlignment(Qt.AlignCenter)
        self._progress_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._progress_label)

        # ── Actions ──────────────────────────────────────────────────
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self._btn_download = QPushButton("Tải ngay")
        self._btn_download.setStyleSheet(self._btn_style("#e74c3c"))
        self._btn_download.clicked.connect(self._on_download)
        self._btn_download.setEnabled(False)
        action_layout.addWidget(self._btn_download)

        self._btn_cancel = QPushButton("Hủy")
        self._btn_cancel.setStyleSheet(self._btn_style("#95a5a6"))
        self._btn_cancel.setVisible(False)
        self._btn_cancel.clicked.connect(self._on_cancel_download)
        action_layout.addWidget(self._btn_cancel)

        layout.addLayout(action_layout)

        # ── After-download ────────────────────────────────────────────
        self._after_layout = QHBoxLayout()
        self._after_layout.addStretch()
        self._btn_open_file = QPushButton("Mở file")
        self._btn_open_file.setStyleSheet(self._btn_style("#27ae60"))
        self._btn_open_file.clicked.connect(self._open_file)
        self._btn_open_file.setVisible(False)
        self._after_layout.addWidget(self._btn_open_file)

        self._btn_open_folder = QPushButton("Mở thư mục")
        self._btn_open_folder.setStyleSheet(self._btn_style("#27ae60"))
        self._btn_open_folder.clicked.connect(self._open_folder)
        self._btn_open_folder.setVisible(False)
        self._after_layout.addWidget(self._btn_open_folder)

        self._btn_cut = QPushButton("Cắt tiếp video này")
        self._btn_cut.setStyleSheet(self._btn_style("#3498db"))
        self._btn_cut.clicked.connect(self._cut_downloaded)
        self._btn_cut.setVisible(False)
        self._after_layout.addWidget(self._btn_cut)

        self._btn_new_download = QPushButton("Tải link khác")
        self._btn_new_download.setStyleSheet(self._btn_style("#3498db"))
        self._btn_new_download.clicked.connect(self._reset)
        self._btn_new_download.setVisible(False)
        self._after_layout.addWidget(self._btn_new_download)

        layout.addLayout(self._after_layout)

        # ── Loading indicator ─────────────────────────────────────────
        self._fetching_label = QLabel("Đang lấy thông tin...")
        self._fetching_label.setAlignment(Qt.AlignCenter)
        self._fetching_label.setStyleSheet("color: #3498db; font-size: 14px;")
        self._fetching_label.setVisible(False)
        layout.addWidget(self._fetching_label)

    def _btn_style(self, color: str) -> str:
        return (
            f"QPushButton {{ background: {color}; color: white; border: none; "
            f"border-radius: 4px; padding: 8px 20px; font-size: 14px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {color}bb; }}"
            f"QPushButton:pressed {{ background: {color}99; }}"
            f"QPushButton:disabled {{ background: #bdc3c7; }}"
        )

    def load_url(self, url: str):
        self._current_url = url
        self._url_input.setText(url)
        self._reset()
        self._on_fetch()

    def _on_fetch(self):
        url = self._url_input.text().strip()
        if not url or not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Link không hợp lệ", "Vui lòng nhập link hợp lệ.")
            return

        self._current_url = url
        self._fetch_btn.setEnabled(False)
        self._fetching_label.setVisible(True)
        self._meta_container.setVisible(False)
        self._opt_container.setVisible(False)
        self._btn_download.setEnabled(False)

        self._metadata_worker = MetadataWorker(url, self)
        self._metadata_worker.finished.connect(self._on_metadata_ready)
        self._metadata_worker.error.connect(self._on_metadata_error)
        self._metadata_worker.start()

    def _on_metadata_ready(self, info: MediaInfo):
        self._fetch_btn.setEnabled(True)
        self._fetching_label.setVisible(False)
        self._media_info = info

        # Update UI
        self._title_label.setText(info.title)
        self._duration_label.setText(f"Thời lượng: {self._format_duration(info.duration)}")
        self._platform_label.setText(f"Nền tảng: {info.platform}")

        # Set default output name
        safe_name = sanitize_filename(info.title)[:100]
        self._output_name.setText(safe_name)

        # Load thumbnail asynchronously
        if info.thumbnail:
            self._load_thumbnail(info.thumbnail)

        self._meta_container.setVisible(True)
        self._opt_container.setVisible(True)
        self._btn_download.setEnabled(True)

    def _load_thumbnail(self, url: str):
        try:
            from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
            from PySide6.QtCore import QUrl, QUrlQuery

            manager = QNetworkAccessManager(self)
            reply = manager.get(QNetworkRequest(QUrl(url)))
            reply.finished.connect(lambda: self._on_thumbnail_loaded(reply))
        except Exception as e:
            logger.warning("Failed to load thumbnail: %s", e)

    def _on_thumbnail_loaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self._thumbnail_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._thumbnail_label.setPixmap(scaled)
                self._thumb_pixmap = scaled
        reply.deleteLater()

    def _on_metadata_error(self, message: str):
        self._fetch_btn.setEnabled(True)
        self._fetching_label.setVisible(False)
        QMessageBox.warning(self, "Lỗi", message)

    def _on_download(self):
        if not self._media_info:
            return

        url = self._current_url

        # Determine type
        if self._type_audio_mp3.isChecked():
            download_type = "audio"
            ext = "mp3"
        elif self._type_audio_m4a.isChecked():
            download_type = "audio"
            ext = "m4a"
        else:
            download_type = "video"
            ext = "mp4"

        # Quality
        quality_map = {"Best": "best", "1080p": "1080p", "720p": "720p", "Audio only": "audio_only"}
        quality = quality_map[self._quality_combo.currentText()]

        # Output name
        output_name = self._output_name.text().strip() or "download"
        output_name = sanitize_filename(output_name)

        output_dir = self._settings.get_default_output_dir()
        output_path = unique_output_path(output_dir, output_name, ext)

        self._last_output = output_path
        self._last_folder = output_dir

        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._progress_label.setText("Đang tải...")
        self._progress_label.setVisible(True)
        self._btn_download.setVisible(False)
        self._btn_cancel.setVisible(True)
        self._opt_container.setEnabled(False)

        self._download_worker = DownloadWorker(
            url, output_path, download_type, quality, self
        )
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.cancelled.connect(self._on_download_cancelled)
        self._download_worker.start()

    def _on_download_progress(self, pct: float):
        self._progress_bar.setValue(int(pct))
        self._progress_label.setText(f"Đang tải... {int(pct)}%")

    def _on_download_finished(self, success: bool, message: str):
        self._progress_bar.setVisible(False)
        self._progress_label.setText("")
        self._btn_cancel.setVisible(False)
        self._opt_container.setEnabled(True)

        if success:
            self._progress_label.setText("Tải hoàn tất!")
            self._progress_label.setStyleSheet("color: #27ae60; font-size: 14px; font-weight: bold;")
            self._progress_label.setVisible(True)
            self._btn_open_file.setVisible(True)
            self._btn_open_folder.setVisible(True)
            self._btn_cut.setVisible(True)
            self._btn_new_download.setVisible(True)
            logger.info("Download complete: %s", message)
        else:
            self._btn_download.setVisible(True)
            self._btn_download.setEnabled(True)
            QMessageBox.critical(self, "Lỗi tải", f"Không thể tải video.\n\n{message}")

    def _on_download_cancelled(self):
        self._progress_bar.setVisible(False)
        self._progress_label.setText("Đã hủy tải.")
        self._progress_label.setStyleSheet("color: #e67e22; font-size: 13px;")
        self._progress_label.setVisible(True)
        self._btn_download.setVisible(True)
        self._btn_download.setEnabled(True)
        self._btn_cancel.setVisible(False)

    def _on_cancel_download(self):
        if self._download_worker and self._download_worker.isRunning():
            self._download_worker.cancel()

    def _format_duration(self, seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    def _open_file(self):
        if hasattr(self, "_last_output"):
            import subprocess, sys
            path = self._last_output
            if sys.platform == "win32":
                __import__("os").startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])

    def _open_folder(self):
        if hasattr(self, "_last_folder"):
            import subprocess, sys
            folder = str(self._last_folder)
            if sys.platform == "win32":
                __import__("os").startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])

    def _cut_downloaded(self):
        if hasattr(self, "_last_output"):
            self.file_downloaded.emit(str(self._last_output))

    def _reset(self):
        self._progress_bar.setVisible(False)
        self._progress_label.setVisible(False)
        self._progress_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self._btn_download.setVisible(True)
        self._btn_download.setEnabled(False)
        self._btn_cancel.setVisible(False)
        self._btn_open_file.setVisible(False)
        self._btn_open_folder.setVisible(False)
        self._btn_cut.setVisible(False)
        self._btn_new_download.setVisible(False)
        self._meta_container.setVisible(False)
        self._opt_container.setVisible(False)
        self._title_label.setText("Chưa có thông tin")
        self._duration_label.setText("Thời lượng: --:--")
        self._platform_label.setText("Nền tảng: --")
        self._thumbnail_label.setText("Chưa có thumbnail")
        self._thumbnail_label.setPixmap(QPixmap())

    def _change_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục lưu file", str(self._settings.get_default_output_dir())
        )
        if folder:
            self._settings.set_default_output_dir(Path(folder))
            self._folder_label.setText(folder)

    def _on_back(self):
        self._on_cancel_download()
        self.back_home.emit()
