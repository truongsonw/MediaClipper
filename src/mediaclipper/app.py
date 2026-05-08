"""QApplication setup and startup."""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from mediaclipper.infra.logger import setup_logger, get_logger
from mediaclipper.infra.paths import ensure_dirs, app_data_dir
from mediaclipper.infra.temp_manager import get_temp_manager
from mediaclipper.infra.tool_locator import get_tool_locator
from mediaclipper.ui.main_window import MainWindow


def _check_tools() -> bool:
    """Check if required tools are available. Show dialog if not."""
    locator = get_tool_locator()
    tools = locator.check_all()

    missing = [name for name, info in tools.items() if not info.available]
    if not missing:
        return True

    msg = "Không tìm thấy các công cụ sau:\n"
    for name in missing:
        msg += f"  - {name}\n"
    msg += "\nVui lòng kiểm tra lại cài đặt app."
    QMessageBox.critical(None, "Thiếu công cụ", msg)
    return False


def _startup_cleanup() -> None:
    """Clean up old temp files on startup."""
    temp_mgr = get_temp_manager()
    removed = temp_mgr.cleanup_old()
    logger = get_logger()
    if removed > 0:
        logger.info("Cleaned up %d old temp directories on startup", removed)


def _apply_stylesheet(app: QApplication) -> None:
    app.setStyle("Fusion")
    stylesheet = """
    QMainWindow {
        background: #f5f6fa;
    }
    QWidget {
        font-family: "Segoe UI", "Ubuntu", sans-serif;
        font-size: 13px;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #dcdde1;
        border-radius: 6px;
        margin-top: 8px;
        padding-top: 8px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 4px;
        color: #2c3e50;
    }
    QProgressBar {
        border: 1px solid #bdc3c7;
        border-radius: 4px;
        text-align: center;
        background: #ecf0f1;
        height: 20px;
    }
    QProgressBar::chunk {
        background: #3498db;
        border-radius: 3px;
    }
    QSpinBox, QDoubleSpinBox {
        padding: 4px 6px;
        border: 1px solid #bdc3c7;
        border-radius: 4px;
    }
    """
    app.setStyleSheet(stylesheet)


def main() -> int:
    """Main entry point."""
    # Ensure directories exist
    ensure_dirs()

    # Setup logging
    logger = setup_logger()
    logger.info("MediaClipper starting...")

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("MediaClipper")
    app.setOrganizationName("MediaClipper")
    app.setApplicationVersion("1.0.0")

    # Apply custom stylesheet
    _apply_stylesheet(app)

    # Startup cleanup
    _startup_cleanup()

    # Check tools (optional - don't block startup if missing)
    # _check_tools()

    # Create and show main window
    window = MainWindow()
    window.show()

    logger.info("MediaClipper started successfully")

    return app.exec()
