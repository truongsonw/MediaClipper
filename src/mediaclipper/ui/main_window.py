"""Main window."""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QStackedWidget, QMenuBar, QMenu, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

from mediaclipper.infra.logger import get_logger
from mediaclipper.ui.home_page import HomePage
from mediaclipper.ui.settings_dialog import SettingsDialog

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MediaClipper")
        self.setMinimumSize(700, 500)
        self.resize(900, 640)

        self._setup_ui()

    def _setup_ui(self):
        # Menu bar
        menubar = self.menuBar()
        menu_file = menubar.addMenu("&Tệp")
        menu_file.addAction("&Cài đặt", self._open_settings, QKeySequence("Ctrl+O"))
        menu_file.addSeparator()
        menu_file.addAction("&Thoát", self.close, QKeySequence("Ctrl+Q"))

        menu_help = menubar.addMenu("&Trợ giúp")
        menu_help.addAction("&Giới thiệu", self._about)

        # Stacked widget for different panels
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # Home page
        self._home = HomePage(self)
        self._home.file_selected.connect(self._on_file_selected)
        self._stack.addWidget(self._home)

        # Other panels will be added when switching views
        self._cutter_panel = None
        self._download_panel = None

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _about(self):
        QMessageBox.about(
            self,
            "Giới thiệu MediaClipper",
            "<b>MediaClipper 1.0.0</b><br><br>"
            "Công cụ tải và cắt video/audio đơn giản.<br><br>"
            "Chỉ sử dụng cho nội dung bạn có quyền tải và sử dụng."
        )

    def _on_file_selected(self, file_path: str):
        """Switch to cutter panel with the selected file."""
        from mediaclipper.ui.cutter_panel import CutterPanel
        if self._cutter_panel is None:
            self._cutter_panel = CutterPanel(self)
            self._cutter_panel.back_home.connect(self._go_home)
            self._stack.addWidget(self._cutter_panel)

        self._cutter_panel.load_file(file_path)
        self._stack.setCurrentWidget(self._cutter_panel)

    def _on_download_metadata_ready(self, file_path: str):
        """Switch to cutter panel with downloaded file."""
        self._on_file_selected(file_path)

    def _go_home(self):
        self._stack.setCurrentWidget(self._home)
