"""Home page - main screen with URL input and drag-drop."""

import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QFrame, QStackedWidget,
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.paths import default_output_dir
from mediaclipper.services.settings_service import get_settings_service

logger = get_logger(__name__)

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mp3", ".m4a", ".wav", ".flac", ".ogg"}
AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".aac"}


def _btn_style(color: str) -> str:
    return (
        f"QPushButton {{ background: {color}; color: white; border: none; "
        f"border-radius: 4px; padding: 8px 16px; font-size: 14px; font-weight: bold; }}"
        f"QPushButton:hover {{ background: {color}bb; }}"
        f"QPushButton:pressed {{ background: {color}99; }}"
        f"QPushButton:disabled {{ background: #bdc3c7; }}"
    )


class HomePage(QWidget):
    """Home screen with URL input and drag-drop zone."""

    file_selected = Signal(str)   # file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = get_settings_service()
        self._download_panel = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # Title
        title = QLabel("MediaClipper")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Tải video/audio từ link hoặc cắt nhanh file local")
        subtitle.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        # URL Section
        url_label = QLabel("Dán link video/audio để tải:")
        url_label.setStyleSheet("font-weight: bold; color: #34495e;")
        layout.addWidget(url_label)

        url_layout = QHBoxLayout()
        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self._url_input.setMinimumHeight(40)
        self._url_input.setStyleSheet("padding: 6px 10px; font-size: 14px; border: 1px solid #bdc3c7; border-radius: 4px;")
        self._url_input.returnPressed.connect(self._on_fetch_clicked)
        url_layout.addWidget(self._url_input, 1)

        self._fetch_btn = QPushButton("Lấy thông tin")
        self._fetch_btn.setMinimumHeight(40)
        self._fetch_btn.setStyleSheet(_btn_style("#3498db"))
        self._fetch_btn.clicked.connect(self._on_fetch_clicked)
        url_layout.addWidget(self._fetch_btn)

        layout.addLayout(url_layout)

        # OR separator
        or_label = QLabel("— hoặc —")
        or_label.setAlignment(Qt.AlignCenter)
        or_label.setStyleSheet("color: #95a5a6; font-style: italic;")
        layout.addWidget(or_label)

        # Drag-Drop Zone
        self._drop_zone = DropZone(self)
        self._drop_zone.file_dropped.connect(self._on_file_dropped)
        layout.addWidget(self._drop_zone, 1)

        # Output folder
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Thư mục lưu mặc định:")
        folder_label.setStyleSheet("color: #7f8c8d;")
        folder_layout.addWidget(folder_label)

        self._folder_display = QLabel(str(self._settings.get_default_output_dir()))
        self._folder_display.setStyleSheet("color: #2c3e50; font-weight: bold;")
        folder_layout.addWidget(self._folder_display, 1)

        btn_change = QPushButton("Đổi thư mục")
        btn_change.setStyleSheet(_btn_style("#27ae60"))
        btn_change.clicked.connect(self._change_output_folder)
        folder_layout.addWidget(btn_change)

        layout.addLayout(folder_layout)

    def _on_fetch_clicked(self):
        url = self._url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Chưa nhập link", "Vui lòng dán link video/audio.")
            return

        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self, "Link không hợp lệ",
                               "Vui lòng nhập link bắt đầu bằng http:// hoặc https://")
            return

        from mediaclipper.ui.download_panel import DownloadPanel
        if self._download_panel is None:
            self._download_panel = DownloadPanel(self.window())
            self._download_panel.back_home.connect(self._go_home)
            self._download_panel.file_downloaded.connect(self.file_selected)
            self.window()._stack.addWidget(self._download_panel)

        self._download_panel.load_url(url)
        self.window()._stack.setCurrentWidget(self._download_panel)

    def _on_file_dropped(self, file_path: str):
        self.file_selected.emit(file_path)

    def _change_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục lưu file", str(self._settings.get_default_output_dir())
        )
        if folder:
            self._settings.set_default_output_dir(Path(folder))
            self._folder_display.setText(folder)

    def _go_home(self):
        self.window()._stack.setCurrentWidget(self.window()._home)


class DropZone(QFrame):
    """Draggable area for dropping media files."""

    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "DropZone { border: 2px dashed #3498db; border-radius: 8px; "
            "background: #ecf0f1; }"
            "DropZone:hover { border-color: #2980b9; background: #d5e8f7; }"
        )

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        icon_label = QLabel("🎬")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        text = QLabel("Kéo file video/audio vào đây\nhoặc nhấn để chọn")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet("font-size: 16px; color: #7f8c8d;")
        layout.addWidget(text)

        self._browse_btn = QPushButton("Chọn file")
        self._browse_btn.setStyleSheet(_btn_style("#3498db"))
        self._browse_btn.clicked.connect(self._browse)
        layout.addWidget(self._browse_btn)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(
                "DropZone { border: 2px solid #2980b9; border-radius: 8px; "
                "background: #d5e8f7; }"
            )

    def dragLeaveEvent(self, event):
        self.setStyleSheet(
            "DropZone { border: 2px dashed #3498db; border-radius: 8px; "
            "background: #ecf0f1; }"
        )

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(
            "DropZone { border: 2px dashed #3498db; border-radius: 8px; "
            "background: #ecf0f1; }"
        )
        for url in event.mimeData().urls():
            if url.isLocalFile():
                file_path = url.toLocalFile()
                ext = Path(file_path).suffix.lower()
                if ext in VIDEO_EXTS or ext in AUDIO_EXTS:
                    self.file_dropped.emit(file_path)
                    return

        QMessageBox.warning(self, "Tệp không hợp lệ",
                            "Vui lòng kéo thả file video hoặc audio.")

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file video hoặc audio",
            str(Path.home()),
            "Media files (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v *.mp3 *.m4a *.wav *.flac *.ogg *.aac)"
        )
        if path:
            self.file_dropped.emit(path)
