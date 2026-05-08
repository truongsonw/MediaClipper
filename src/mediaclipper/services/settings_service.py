"""Settings service using QSettings."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QSettings

from mediaclipper.infra.logger import get_logger

logger = get_logger(__name__)


class SettingsService:
    """Lightweight settings storage using QSettings (no database)."""

    def __init__(self):
        self._qsettings = QSettings("MediaClipper", "MediaClipper")

    # ── Output ──────────────────────────────────────────────

    def get_default_output_dir(self) -> Path:
        path = self._qsettings.value("default_output_dir", "")
        if path:
            p = Path(path)
            if p.is_dir():
                return p
        from mediaclipper.infra.paths import default_output_dir
        return default_output_dir()

    def set_default_output_dir(self, path: Path) -> None:
        self._qsettings.setValue("default_output_dir", str(path.resolve()))
        logger.debug("Set default_output_dir: %s", path)

    # ── Video format ────────────────────────────────────────

    def get_default_video_format(self) -> str:
        return self._qsettings.value("default_video_format", "mp4")

    def set_default_video_format(self, fmt: str) -> None:
        self._qsettings.setValue("default_video_format", fmt)

    # ── Audio format ─────────────────────────────────────────

    def get_default_audio_format(self) -> str:
        return self._qsettings.value("default_audio_format", "m4a")

    def set_default_audio_format(self, fmt: str) -> None:
        self._qsettings.setValue("default_audio_format", fmt)

    # ── Download quality ─────────────────────────────────────

    def get_default_quality(self) -> str:
        return self._qsettings.value("default_quality", "best")

    def set_default_quality(self, quality: str) -> None:
        self._qsettings.setValue("default_quality", quality)

    # ── Auto cleanup ─────────────────────────────────────────

    def get_auto_cleanup_temp(self) -> bool:
        val = self._qsettings.value("auto_cleanup_temp", "true")
        return val in ("true", "1", "True", True)

    def set_auto_cleanup_temp(self, enabled: bool) -> None:
        self._qsettings.setValue("auto_cleanup_temp", "true" if enabled else "false")

    # ── Language ─────────────────────────────────────────────

    def get_language(self) -> str:
        return self._qsettings.value("language", "vi")

    def set_language(self, lang: str) -> None:
        self._qsettings.setValue("language", lang)

    # ── Reset ────────────────────────────────────────────────

    def reset_all(self) -> None:
        self._qsettings.clear()
        logger.info("Settings reset to defaults")

    def all_settings(self) -> dict:
        return {
            "default_output_dir": str(self.get_default_output_dir()),
            "default_video_format": self.get_default_video_format(),
            "default_audio_format": self.get_default_audio_format(),
            "default_quality": self.get_default_quality(),
            "auto_cleanup_temp": self.get_auto_cleanup_temp(),
            "language": self.get_language(),
        }


_settings_service: Optional[SettingsService] = None


def get_settings_service() -> SettingsService:
    global _settings_service
    if _settings_service is None:
        _settings_service = SettingsService()
    return _settings_service
