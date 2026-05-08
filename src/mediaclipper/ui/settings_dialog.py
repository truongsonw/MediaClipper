"""Settings dialog."""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QComboBox, QFileDialog, QMessageBox,
    QGroupBox, QProgressBar,
)
from PySide6.QtCore import Qt

from mediaclipper.infra.logger import get_logger
from mediaclipper.services.settings_service import get_settings_service
from mediaclipper.services.cleanup_service import CleanupService
from mediaclipper.infra.tool_locator import get_tool_locator

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt - MediaClipper")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._settings = get_settings_service()
        self._cleanup = CleanupService()
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # ── Output folder ────────────────────────────────────────────
        folder_group = QGroupBox("Thư mục lưu file")
        folder_layout = QHBoxLayout(folder_group)
        self._folder_input = QLineEdit()
        self._folder_input.setReadOnly(True)
        self._folder_input.setStyleSheet("padding: 6px; border: 1px solid #bdc3c7; border-radius: 4px;")
        folder_layout.addWidget(self._folder_input, 1)
        btn_browse = QPushButton("Chọn thư mục")
        btn_browse.setStyleSheet(self._btn_style("#27ae60"))
        btn_browse.clicked.connect(self._browse_folder)
        folder_layout.addWidget(btn_browse)
        layout.addWidget(folder_group)

        # ── Defaults ────────────────────────────────────────────────
        defaults_group = QGroupBox("Mặc định khi tải/xuất")
        defaults_layout = QVBoxLayout(defaults_group)

        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("Chất lượng tải mặc định:"))
        self._quality_combo = QComboBox()
        self._quality_combo.addItems(["Best", "1080p", "720p", "Audio only"])
        quality_row.addWidget(self._quality_combo)
        quality_row.addStretch()
        defaults_layout.addLayout(quality_row)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Định dạng video mặc định:"))
        self._video_fmt_combo = QComboBox()
        self._video_fmt_combo.addItems(["mp4"])
        fmt_row.addWidget(self._video_fmt_combo)
        fmt_row.addWidget(QLabel("  Định dạng audio mặc định:"))
        self._audio_fmt_combo = QComboBox()
        self._audio_fmt_combo.addItems(["m4a", "mp3"])
        fmt_row.addWidget(self._audio_fmt_combo)
        fmt_row.addStretch()
        defaults_layout.addLayout(fmt_row)

        layout.addWidget(defaults_group)

        # ── Cleanup ──────────────────────────────────────────────────
        cleanup_group = QGroupBox("Dọn file tạm")
        cleanup_layout = QVBoxLayout(cleanup_group)

        self._auto_cleanup = QCheckBox("Tự xóa file tạm sau khi hoàn tất")
        cleanup_layout.addWidget(self._auto_cleanup)

        btn_cleanup_now = QPushButton("Dọn file tạm ngay")
        btn_cleanup_now.setStyleSheet(self._btn_style("#e67e22"))
        btn_cleanup_now.clicked.connect(self._cleanup_now)
        cleanup_layout.addWidget(btn_cleanup_now)

        self._cleanup_status = QLabel("")
        self._cleanup_status.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        cleanup_layout.addWidget(self._cleanup_status)
        layout.addWidget(cleanup_group)

        # ── Tools ────────────────────────────────────────────────────
        tools_group = QGroupBox("Công cụ xử lý")
        tools_layout = QVBoxLayout(tools_group)

        locator = get_tool_locator()
        tools = locator.check_all()
        for name, info in tools.items():
            status = "✓ Sẵn sàng" if info.available else "✗ Không tìm thấy"
            color = "#27ae60" if info.available else "#e74c3c"
            label = QLabel(f"{name.upper()}: {status} (phiên bản: {info.version})")
            label.setStyleSheet(f"color: {color}; font-size: 13px;")
            tools_layout.addWidget(label)

        btn_update_ytdlp = QPushButton("Cập nhật công cụ tải video")
        btn_update_ytdlp.setStyleSheet(self._btn_style("#3498db"))
        btn_update_ytdlp.clicked.connect(self._update_ytdlp)
        tools_layout.addWidget(btn_update_ytdlp)

        self._update_status = QLabel("")
        self._update_status.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        tools_layout.addWidget(self._update_status)
        layout.addWidget(tools_group)

        # ── Language ─────────────────────────────────────────────────
        lang_group = QGroupBox("Ngôn ngữ")
        lang_layout = QHBoxLayout(lang_group)
        lang_layout.addWidget(QLabel("Giao diện:"))
        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["Tiếng Việt", "English"])
        lang_layout.addWidget(self._lang_combo)
        lang_layout.addStretch()
        layout.addWidget(lang_group)

        # ── Reset ────────────────────────────────────────────────────
        btn_reset = QPushButton("Khôi phục mặc định")
        btn_reset.setStyleSheet(self._btn_style("#95a5a6"))
        btn_reset.clicked.connect(self._reset_settings)
        layout.addWidget(btn_reset)

        # ── Save / Cancel ────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Hủy")
        btn_cancel.setStyleSheet(self._btn_style("#95a5a6"))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_save = QPushButton("Lưu")
        btn_save.setStyleSheet(self._btn_style("#27ae60"))
        btn_save.clicked.connect(self._save_and_close)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _btn_style(self, color: str) -> str:
        return (
            f"QPushButton {{ background: {color}; color: white; border: none; "
            f"border-radius: 4px; padding: 8px 20px; font-size: 13px; font-weight: bold; }}"
            f"QPushButton:hover {{ background: {color}bb; }}"
            f"QPushButton:pressed {{ background: {color}99; }}"
        )

    def _load_settings(self):
        s = self._settings
        self._folder_input.setText(str(s.get_default_output_dir()))

        quality_map = {"best": 0, "1080p": 1, "720p": 2, "audio_only": 3}
        self._quality_combo.setCurrentIndex(quality_map.get(s.get_default_quality(), 0))

        self._auto_cleanup.setChecked(s.get_auto_cleanup_temp())

        lang_map = {"vi": 0, "en": 1}
        self._lang_combo.setCurrentIndex(lang_map.get(s.get_language(), 0))

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn thư mục lưu file mặc định",
            self._folder_input.text() or str(Path.home())
        )
        if folder:
            self._folder_input.setText(folder)

    def _cleanup_now(self):
        removed = self._cleanup.cleanup_all_temp()
        self._cleanup_status.setText(f"Đã dọn {removed} thư mục tạm.")
        self._cleanup_status.setStyleSheet("color: #27ae60; font-size: 12px;")

    def _update_ytdlp(self):
        self._update_status.setText("Đang cập nhật...")
        self._update_status.setStyleSheet("color: #3498db; font-size: 12px;")
        from mediaclipper.services.ytdlp_service import YtDlpService
        success, msg = YtDlpService().update()
        if success:
            self._update_status.setText(f"Cập nhật thành công: {msg}")
            self._update_status.setStyleSheet("color: #27ae60; font-size: 12px;")
        else:
            self._update_status.setText(f"Cập nhật thất bại: {msg}")
            self._update_status.setStyleSheet("color: #e74c3c; font-size: 12px;")

    def _reset_settings(self):
        reply = QMessageBox.question(
            self, "Khôi phục mặc định",
            "Bạn có chắc muốn khôi phục tất cả cài đặt về mặc định?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._settings.reset_all()
            self._load_settings()

    def _save_and_close(self):
        s = self._settings
        folder = self._folder_input.text()
        if folder:
            s.set_default_output_dir(Path(folder))

        quality_map = {0: "best", 1: "1080p", 2: "720p", 3: "audio_only"}
        s.set_default_quality(quality_map.get(self._quality_combo.currentIndex(), "best"))

        s.set_default_video_format("mp4")
        s.set_default_audio_format(self._audio_fmt_combo.currentText())

        s.set_auto_cleanup_temp(self._auto_cleanup.isChecked())

        lang_map = {0: "vi", 1: "en"}
        s.set_language(lang_map.get(self._lang_combo.currentIndex(), "vi"))

        logger.info("Settings saved: %s", s.all_settings())
        self.accept()
