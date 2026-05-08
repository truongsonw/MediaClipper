"""Cutter panel - preview, set start/end, export media."""

import os
import re
import typing
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox,
    QFrame, QGroupBox, QRadioButton, QProgressBar, QSlider,
)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QStyleOptionSlider, QStyle
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.paths import default_output_dir, unique_output_path, sanitize_filename
from mediaclipper.services.ffmpeg_service import FFmpegService, ExportOptions
from mediaclipper.services.ffprobe_service import FFprobeService
from mediaclipper.services.settings_service import get_settings_service
from mediaclipper.workers.export_worker import ExportWorker

logger = get_logger(__name__)


# ── Slider event filter ─────────────────────────────────────────────────────────


class _TimeInputFormatter(QObject):
    """Auto-format time input as user types: HH:MM:SS.mmm"""

    def __init__(self, line_edit: QLineEdit, color: str, parent=None):
        super().__init__(parent)
        self._line_edit = line_edit
        line_edit.installEventFilter(self)
        line_edit.textChanged.connect(self._on_text_changed)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress and event.key() in (
            Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab
        ):
            self._line_edit.editingFinished.emit()
            return True
        return super().eventFilter(watched, event)

    def _on_text_changed(self, text: str):
        cursor = self._line_edit.cursorPosition()
        formatted = self._format(text, cursor)
        if formatted != text:
            blocked = self._line_edit.blockSignals(True)
            self._line_edit.setText(formatted)
            new_pos = min(cursor, len(formatted))
            self._line_edit.setCursorPosition(new_pos)
            self._line_edit.blockSignals(blocked)

    def _format(self, text: str, cursor: int) -> str:
        digits = re.sub(r"[^0-9]", "", text)
        if len(digits) > 9:
            digits = digits[:9]
        parts = []
        for i, size in enumerate((2, 2, 2, 3)):
            chunk = digits[:size] if len(digits) >= size else digits
            digits = digits[size:]
            parts.append(chunk)
            if not digits:
                break
            if i < 3:
                parts.append(":" if i < 2 else ".")
        return "".join(parts)


class _SliderClickFilter(QObject):
    """Allow clicking anywhere on a QSlider groove (not handle) to jump to that position."""

    def __init__(self, slider, parent=None):
        super().__init__(parent)
        self._slider = slider

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress:
            me = typing.cast(QMouseEvent, event)
            # Only intercept clicks on the groove, not on the handle (which must drag)
            if self._is_on_groove(me):
                self._jump_to_mouse(me)
                return True
        return super().eventFilter(watched, event)

    def _is_on_groove(self, event: QMouseEvent) -> bool:
        opt = QStyleOptionSlider()
        self._slider.initStyleOption(opt)
        handle_rect = self._slider.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self._slider
        )
        # Expand handle rect slightly to avoid intercepting drag attempts near the handle
        expanded = handle_rect.adjusted(-8, -8, 8, 8)
        return not expanded.contains(event.position().toPoint())

    def _jump_to_mouse(self, event: QMouseEvent):
        opt = QStyleOptionSlider()
        self._slider.initStyleOption(opt)
        handle_rect = self._slider.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self._slider
        )
        handle_center = handle_rect.center()
        slider_min = self._slider.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self._slider
        ).left()
        slider_max = self._slider.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self._slider
        ).right()
        span = slider_max - slider_min
        if span <= 0:
            return
        pos_ratio = (event.position().x() - slider_min) / span
        pos_ratio = max(0.0, min(1.0, pos_ratio))
        new_val = self._slider.minimum() + int(pos_ratio * (self._slider.maximum() - self._slider.minimum()))
        self._slider.setValue(new_val)
        self._slider.sliderMoved.emit(new_val)
        self._slider.sliderReleased.emit()


# ── Time parsing ────────────────────────────────────────────────────────────────

_TIME_RE = re.compile(r"^(\d+):(\d{2}):(\d{2}(?:\.\d+)?)$")


def parse_time(text: str) -> float | None:
    """Parse HH:MM:SS.mmm → seconds, or return None."""
    text = text.strip()
    m = _TIME_RE.match(text)
    if m:
        h, m_s, s = m.groups()
        return int(h) * 3600 + int(m_s) * 60 + float(s)
    return None


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


# ── Styles ──────────────────────────────────────────────────────────────────────


def _btn_style(color: str) -> str:
    return (
        f"QPushButton {{ background: {color}; color: white; border: none; "
        f"border-radius: 4px; padding: 8px 20px; font-size: 14px; font-weight: bold; }}"
        f"QPushButton:hover {{ background: {color}bb; }}"
        f"QPushButton:pressed {{ background: {color}99; }}"
        f"QPushButton:disabled {{ background: #bdc3c7; }}"
    )


def _icon_btn_style(color: str) -> str:
    return (
        f"QPushButton {{ background: {color}22; color: {color}; border: 1px solid {color}; "
        f"border-radius: 4px; padding: 4px 10px; font-size: 16px; font-weight: bold; }}"
        f"QPushButton:hover {{ background: {color}55; }}"
    )


def _time_input_style(color: str) -> str:
    return (
        f"QLineEdit {{ border: 1px solid {color}; border-radius: 4px; "
        f"padding: 5px 8px; font-family: monospace; font-size: 14px; color: {color}; "
        f"background: {color}11; }}"
        f"QLineEdit:focus {{ border: 2px solid {color}; background: {color}22; }}"
    )


def _slider_style() -> str:
    return """
        QSlider::groove:horizontal {
            border: 1px solid #bbb;
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
        }
        QSlider::sub-page:horizontal {
            background: #3498db;
            border-radius: 3px;
        }
        QSlider::add-page:horizontal {
            background: #e0e0e0;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #3498db;
            width: 14px;
            margin: -5px 0;
            border-radius: 7px;
        }
        QSlider::handle:horizontal:hover {
            background: #2980b9;
        }
    """


# ── Panel ──────────────────────────────────────────────────────────────────────


class CutterPanel(QWidget):
    """Panel for cutting local media files."""

    back_home = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = get_settings_service()
        self._current_file: Path | None = None
        self._metadata = None
        self._duration = 0.0
        self._is_playing = False
        self._slider_dragging = False
        self._export_worker: ExportWorker | None = None
        self._setup_ui()

    # ── UI setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        btn_back = QPushButton("← Quay lại")
        btn_back.setStyleSheet("QPushButton { color: #3498db; border: none; font-size: 13px; }")
        btn_back.clicked.connect(self._on_back)
        header.addWidget(btn_back)
        header.addStretch()
        self._file_name_label = QLabel("")
        self._file_name_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #2c3e50;")
        header.addWidget(self._file_name_label)
        header.addStretch()
        layout.addLayout(header)

        # Video preview
        self._video_widget = QVideoWidget()
        self._video_widget.setMinimumHeight(280)
        self._video_widget.setStyleSheet("background: #000; border-radius: 4px;")
        layout.addWidget(self._video_widget)

        self._audio_label = QLabel("🔊 File audio")
        self._audio_label.setAlignment(Qt.AlignCenter)
        self._audio_label.setStyleSheet("font-size: 48px; color: #7f8c8d;")
        self._audio_label.setMinimumHeight(200)
        self._audio_label.setVisible(False)
        layout.addWidget(self._audio_label)

        # Playback controls
        ctrl_layout = QHBoxLayout()
        self._btn_play = QPushButton("▶ Phát")
        self._btn_play.setStyleSheet(_btn_style("#3498db"))
        self._btn_play.clicked.connect(self._on_play_pause)

        self._time_label = QLabel("00:00:00.000 / 00:00:00.000")
        self._time_label.setStyleSheet("color: #7f8c8d; font-family: monospace; font-size: 13px; min-width: 160px;")

        # Volume controls
        self._btn_mute = QPushButton("🔊")
        self._btn_mute.setStyleSheet(_icon_btn_style("#7f8c8d"))
        self._btn_mute.setToolTip("Tắt / Bật tiếng")
        self._btn_mute.clicked.connect(self._on_mute_toggle)

        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(80)
        self._volume_slider.setMaximumWidth(120)
        self._volume_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #bdc3c7; border-radius: 2px; }
            QSlider::handle:horizontal { width: 12px; background: #3498db; border-radius: 6px; margin: -4px 0; }
        """)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)

        ctrl_layout.addWidget(self._btn_play)
        ctrl_layout.addWidget(self._time_label)
        ctrl_layout.addSpacing(16)
        ctrl_layout.addWidget(self._btn_mute)
        ctrl_layout.addWidget(self._volume_slider)
        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        # Timeline slider
        slider_layout = QVBoxLayout()

        self._timeline_slider = QSlider(Qt.Horizontal)
        self._timeline_slider.setRange(0, 1000)
        self._timeline_slider.setStyleSheet(_slider_style())
        self._timeline_slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self._timeline_slider.sliderMoved.connect(self._on_slider_seek)
        self._timeline_slider.sliderPressed.connect(self._on_slider_pressed)
        self._timeline_slider.sliderReleased.connect(self._on_slider_released)
        self._slider_click_filter = _SliderClickFilter(self._timeline_slider)
        self._timeline_slider.installEventFilter(self._slider_click_filter)
        slider_layout.addWidget(self._timeline_slider)

        # Start / End markers
        marker_layout = QHBoxLayout()
        marker_layout.addStretch()

        lbl_s = QLabel("Start")
        lbl_s.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 12px;")
        self._start_marker = QLabel("00:00:00.000")
        self._start_marker.setStyleSheet("color: #27ae60; font-family: monospace; font-size: 12px;")
        marker_layout.addWidget(lbl_s)
        marker_layout.addWidget(self._start_marker)
        marker_layout.addSpacing(40)

        lbl_e = QLabel("End")
        lbl_e.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 12px;")
        self._end_marker = QLabel("00:00:00.000")
        self._end_marker.setStyleSheet("color: #e74c3c; font-family: monospace; font-size: 12px;")
        marker_layout.addWidget(lbl_e)
        marker_layout.addWidget(self._end_marker)
        marker_layout.addStretch()

        slider_layout.addLayout(marker_layout)
        layout.addLayout(slider_layout)

        # Time input group
        time_group = QGroupBox("Thời gian đoạn cắt")
        time_layout = QHBoxLayout(time_group)
        time_layout.setSpacing(8)

        # Start
        lbl_s2 = QLabel("Bắt đầu:")
        lbl_s2.setStyleSheet("font-weight: bold; color: #27ae60;")
        self._start_input = QLineEdit()
        self._start_input.setPlaceholderText("HH:MM:SS.mmm")
        self._start_input.setText("00:00:00.000")
        self._start_input.setMaximumWidth(160)
        self._start_input.setStyleSheet(_time_input_style("#27ae60"))
        self._start_input.editingFinished.connect(self._on_start_input_changed)
        self._start_formatter = _TimeInputFormatter(self._start_input, "#27ae60")
        btn_set_s = QPushButton("⏮")
        btn_set_s.setToolTip("Đặt điểm bắt đầu tại vị trí hiện tại")
        btn_set_s.setStyleSheet(_icon_btn_style("#27ae60"))
        btn_set_s.clicked.connect(self._set_start_from_position)

        time_layout.addWidget(lbl_s2)
        time_layout.addWidget(self._start_input)
        time_layout.addWidget(btn_set_s)
        time_layout.addSpacing(30)

        # End
        lbl_e2 = QLabel("Kết thúc:")
        lbl_e2.setStyleSheet("font-weight: bold; color: #e74c3c;")
        self._end_input = QLineEdit()
        self._end_input.setPlaceholderText("HH:MM:SS.mmm")
        self._end_input.setMaximumWidth(160)
        self._end_input.setStyleSheet(_time_input_style("#e74c3c"))
        self._end_input.editingFinished.connect(self._on_end_input_changed)
        self._end_formatter = _TimeInputFormatter(self._end_input, "#e74c3c")
        btn_set_e = QPushButton("⏭")
        btn_set_e.setToolTip("Đặt điểm kết thúc tại vị trí hiện tại")
        btn_set_e.setStyleSheet(_icon_btn_style("#e74c3c"))
        btn_set_e.clicked.connect(self._set_end_from_position)

        time_layout.addWidget(lbl_e2)
        time_layout.addWidget(self._end_input)
        time_layout.addWidget(btn_set_e)
        time_layout.addStretch()

        layout.addWidget(time_group)

        # Cut mode
        mode_group = QGroupBox("Chế độ cắt")
        mode_layout = QHBoxLayout(mode_group)
        self._cut_fast = QRadioButton("Cắt nhanh (nhanh, giữ nguyên chất lượng)")
        self._cut_fast.setChecked(True)
        mode_layout.addWidget(self._cut_fast)
        mode_layout.addSpacing(10)
        self._cut_exact = QRadioButton("Cắt chính xác (điểm cắt chuẩn hơn, xử lý lâu hơn)")
        mode_layout.addWidget(self._cut_exact)
        mode_layout.addStretch()
        layout.addWidget(mode_group)

        # Output
        fmt_group = QGroupBox("Xuất ra")
        fmt_layout = QHBoxLayout(fmt_group)
        self._fmt_mp4 = QRadioButton("Video MP4")
        self._fmt_mp4.setChecked(True)
        fmt_layout.addWidget(self._fmt_mp4)
        self._fmt_m4a = QRadioButton("Audio M4A")
        fmt_layout.addWidget(self._fmt_m4a)
        self._fmt_mp3 = QRadioButton("Audio MP3")
        fmt_layout.addWidget(self._fmt_mp3)
        fmt_layout.addStretch()
        fmt_layout.addWidget(QLabel("Tên file:"))
        self._output_name = QLineEdit()
        self._output_name.setPlaceholderText("ten_file_xuat")
        self._output_name.setMinimumWidth(200)
        fmt_layout.addWidget(self._output_name)
        layout.addWidget(fmt_group)

        # Progress
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_label = QLabel("")
        self._progress_label.setAlignment(Qt.AlignCenter)
        self._progress_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._progress_label)

        # Actions
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        self._btn_export = QPushButton("Xuất file")
        self._btn_export.setStyleSheet(_btn_style("#e74c3c"))
        self._btn_export.clicked.connect(self._on_export)
        action_layout.addWidget(self._btn_export)
        self._btn_cancel = QPushButton("Hủy")
        self._btn_cancel.setStyleSheet(_btn_style("#95a5a6"))
        self._btn_cancel.setVisible(False)
        self._btn_cancel.clicked.connect(self._on_cancel)
        action_layout.addWidget(self._btn_cancel)
        layout.addLayout(action_layout)

        # After-export buttons
        self._after_layout = QHBoxLayout()
        self._after_layout.addStretch()
        self._btn_open_file = QPushButton("Mở file")
        self._btn_open_file.setStyleSheet(_btn_style("#27ae60"))
        self._btn_open_file.clicked.connect(self._open_output_file)
        self._btn_open_file.setVisible(False)
        self._after_layout.addWidget(self._btn_open_file)
        self._btn_open_folder = QPushButton("Mở thư mục")
        self._btn_open_folder.setStyleSheet(_btn_style("#27ae60"))
        self._btn_open_folder.clicked.connect(self._open_output_folder)
        self._btn_open_folder.setVisible(False)
        self._after_layout.addWidget(self._btn_open_folder)
        self._btn_new = QPushButton("Làm file khác")
        self._btn_new.setStyleSheet(_btn_style("#3498db"))
        self._btn_new.clicked.connect(self._on_new_file)
        self._btn_new.setVisible(False)
        self._after_layout.addWidget(self._btn_new)
        layout.addLayout(self._after_layout)

    # ── File loading ──────────────────────────────────────────────────────────

    def load_file(self, file_path: str):
        self._current_file = Path(file_path)
        self._file_name_label.setText(self._current_file.name)

        probe = FFprobeService()
        self._metadata = probe.get_metadata(self._current_file)
        if self._metadata is None:
            QMessageBox.warning(self, "Lỗi", f"Không thể đọc file: {file_path}")
            self.back_home.emit()
            return

        self._duration = self._metadata.duration
        ext = self._current_file.suffix.lower()
        audio_only = not self._metadata.is_video or ext in {".mp3", ".m4a", ".wav", ".flac", ".ogg"}

        if audio_only:
            self._video_widget.setVisible(False)
            self._audio_label.setVisible(True)
            self._audio_label.setText("🔊 " + self._current_file.name)
        else:
            self._video_widget.setVisible(True)
            self._audio_label.setVisible(False)
            if not hasattr(self, "_player"):
                self._player = QMediaPlayer()
                self._audio_output = QAudioOutput()
                self._player.setAudioOutput(self._audio_output)
                self._audio_output.setVolume(self._volume_slider.value() / 100)
                self._player.setVideoOutput(self._video_widget)
                self._player.positionChanged.connect(self._on_position_changed)
                self._player.durationChanged.connect(self._on_duration_changed)

        if not hasattr(self, "_player"):
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            self._audio_output.setVolume(self._volume_slider.value() / 100)
            self._player.positionChanged.connect(self._on_position_changed)
            self._player.durationChanged.connect(self._on_duration_changed)

        from PySide6.QtCore import QUrl
        self._player.setSource(QUrl.fromLocalFile(str(self._current_file)))

        # Default output name
        base_name = sanitize_filename(self._current_file.stem)
        self._output_name.setText(base_name + "_clip")

        # Default times
        self._start_input.setText("00:00:00.000")
        self._end_input.setText(format_time(self._duration))
        self._start_marker.setText("00:00:00.000")
        self._end_marker.setText(format_time(self._duration))
        self._timeline_slider.setValue(0)

        # Reset UI
        self._progress_bar.setVisible(False)
        self._progress_label.setText("")
        self._btn_export.setVisible(True)
        self._btn_cancel.setVisible(False)
        self._btn_open_file.setVisible(False)
        self._btn_open_folder.setVisible(False)
        self._btn_new.setVisible(False)

        logger.info("Loaded file: %s (duration=%.1fs)", file_path, self._duration)

    # ── Playback ──────────────────────────────────────────────────────────────

    def _on_play_pause(self):
        if not hasattr(self, "_player"):
            return
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
            self._btn_play.setText("▶ Phát")
            self._is_playing = False
        else:
            self._player.play()
            self._btn_play.setText("⏸ Tạm dừng")
            self._is_playing = True

    def _on_mute_toggle(self):
        if not hasattr(self, "_audio_output"):
            return
        muted = self._audio_output.isMuted()
        self._audio_output.setMuted(not muted)
        self._btn_mute.setText("🔇" if not muted else "🔊")

    def _on_volume_changed(self, value: int):
        if hasattr(self, "_audio_output"):
            self._audio_output.setVolume(value / 100)

    def _on_position_changed(self, position: int):
        secs = position / 1000.0
        self._time_label.setText(f"{format_time(secs)} / {format_time(self._duration)}")
        if not self._slider_dragging and self._duration > 0:
            self._timeline_slider.blockSignals(True)
            self._timeline_slider.setValue(int(secs / self._duration * 1000))
            self._timeline_slider.blockSignals(False)

    def _on_duration_changed(self, duration: int):
        self._duration = duration / 1000.0

    def _on_slider_pressed(self):
        self._slider_dragging = True

    def _on_slider_released(self):
        self._slider_dragging = False
        if hasattr(self, "_player") and self._duration > 0:
            pos = int(self._timeline_slider.value() / 1000.0 * self._duration * 1000)
            self._player.setPosition(pos)

    def _on_slider_seek(self, value: int):
        if hasattr(self, "_player") and self._duration > 0:
            pos = int(value / 1000.0 * self._duration * 1000)
            self._player.setPosition(pos)

    # ── Time input handlers ──────────────────────────────────────────────────

    def _set_start_from_position(self):
        if not hasattr(self, "_player"):
            return
        pos = self._player.position() / 1000.0
        text = format_time(pos)
        self._start_input.setText(text)
        self._start_marker.setText(text)

    def _set_end_from_position(self):
        if not hasattr(self, "_player"):
            return
        pos = self._player.position() / 1000.0
        text = format_time(pos)
        self._end_input.setText(text)
        self._end_marker.setText(text)

    def _on_start_input_changed(self):
        text = self._start_input.text()
        secs = parse_time(text)
        if secs is None:
            self._start_input.selectAll()
            self._start_input.setFocus()
            return
        if secs < 0:
            QMessageBox.warning(self, "Lỗi", "Thời gian bắt đầu không được nhỏ hơn 0.")
            self._start_input.selectAll()
            self._start_input.setFocus()
            return
        if secs > self._duration:
            QMessageBox.warning(self, "Lỗi", "Thời gian bắt đầu vượt quá thời lượng video.")
            self._start_input.selectAll()
            self._start_input.setFocus()
            return
        self._start_input.setText(format_time(secs))
        self._start_marker.setText(format_time(secs))

    def _on_end_input_changed(self):
        text = self._end_input.text()
        secs = parse_time(text)
        if secs is None:
            self._end_input.selectAll()
            self._end_input.setFocus()
            return
        if secs < 0:
            QMessageBox.warning(self, "Lỗi", "Thời gian kết thúc không được nhỏ hơn 0.")
            self._end_input.selectAll()
            self._end_input.setFocus()
            return
        if secs > self._duration:
            QMessageBox.warning(self, "Lỗi", "Thời gian kết thúc vượt quá thời lượng video.")
            self._end_input.selectAll()
            self._end_input.setFocus()
            return
        self._end_input.setText(format_time(secs))
        self._end_marker.setText(format_time(secs))

    # ── Export ────────────────────────────────────────────────────────────────

    def _on_export(self):
        if not self._current_file:
            return

        start_secs = parse_time(self._start_input.text()) or 0.0
        end_secs = parse_time(self._end_input.text()) or self._duration

        if end_secs <= start_secs:
            QMessageBox.warning(self, "Lỗi", "Thời gian kết thúc phải lớn hơn thời gian bắt đầu.")
            return
        if end_secs > self._duration:
            QMessageBox.warning(self, "Lỗi", "Thời gian kết thúc vượt quá thời lượng video.")
            return

        if self._fmt_mp4.isChecked():
            output_ext = "mp4"
        elif self._fmt_m4a.isChecked():
            output_ext = "m4a"
        else:
            output_ext = "mp3"

        output_name = self._output_name.text().strip() or "output"
        output_name = sanitize_filename(output_name)
        output_dir = self._settings.get_default_output_dir()
        output_path = unique_output_path(output_dir, output_name, output_ext)
        cut_mode = "fast" if self._cut_fast.isChecked() else "exact"

        options = ExportOptions(
            input_path=self._current_file,
            output_path=output_path,
            start_time=start_secs,
            end_time=end_secs,
            cut_mode=cut_mode,
            output_format=output_ext,
        )

        self._btn_export.setVisible(False)
        self._btn_cancel.setVisible(True)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._progress_label.setText("Đang xuất file...")

        self._export_worker = ExportWorker(self)
        self._export_worker.progress.connect(self._on_export_progress)
        self._export_worker.finished.connect(self._on_export_finished)
        self._export_worker.cancelled.connect(self._on_export_cancelled)
        self._export_worker.set_options(options)
        self._export_worker.start()

        logger.info("Export started: %s", output_path)

    def _on_export_progress(self, pct: float):
        self._progress_bar.setValue(int(pct))
        self._progress_label.setText(f"Đang xuất file... {int(pct)}%")

    def _on_export_finished(self, success: bool, message: str):
        self._progress_bar.setVisible(False)
        self._progress_label.setText("")
        self._btn_cancel.setVisible(False)

        if success:
            self._last_output = message
            self._progress_label.setText("Xuất file hoàn tất!")
            self._progress_label.setStyleSheet("color: #27ae60; font-size: 14px; font-weight: bold;")
            self._progress_label.setVisible(True)
            self._btn_open_file.setVisible(True)
            self._btn_open_folder.setVisible(True)
            self._btn_new.setVisible(True)
            logger.info("Export complete: %s", message)
        else:
            self._btn_export.setVisible(True)
            QMessageBox.critical(
                self, "Lỗi xuất file",
                f"Không thể xuất file.\n\n{message}\n\n"
                "Bạn có thể thử lại hoặc đổi tên file."
            )

    def _on_export_cancelled(self):
        self._progress_bar.setVisible(False)
        self._progress_label.setText("Đã hủy.")
        self._progress_label.setStyleSheet("color: #e67e22; font-size: 13px;")
        self._progress_label.setVisible(True)
        self._btn_export.setVisible(True)
        self._btn_cancel.setVisible(False)

    def _on_cancel(self):
        if self._export_worker and self._export_worker.isRunning():
            self._export_worker.cancel()

    def _open_output_file(self):
        if hasattr(self, "_last_output"):
            import subprocess, sys
            path = self._last_output
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])

    def _open_output_folder(self):
        if hasattr(self, "_last_output"):
            import subprocess, sys
            folder = str(Path(self._last_output).parent)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])

    def _on_new_file(self):
        self._progress_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self._progress_label.setText("")
        self._progress_label.setVisible(False)
        self._btn_open_file.setVisible(False)
        self._btn_open_folder.setVisible(False)
        self._btn_new.setVisible(False)
        self._btn_export.setVisible(True)

    def _on_back(self):
        self._on_cancel()
        self.back_home.emit()
