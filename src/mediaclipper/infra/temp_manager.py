"""Temporary file and folder management."""

import shutil
import time
from pathlib import Path
from typing import Optional
import tempfile
import uuid

from mediaclipper.infra.logger import get_logger
from mediaclipper.infra.paths import temp_root

logger = get_logger(__name__)

TEMP_MAX_AGE_HOURS = 24


class TempManager:
    """Manages temporary working directories for each task."""

    def __init__(self):
        self._current_temp_dir: Optional[Path] = None

    def create_task_dir(self) -> Path:
        """Create a new temporary working directory for the current task."""
        temp_root().mkdir(parents=True, exist_ok=True)
        task_id = uuid.uuid4().hex[:8]
        task_dir = temp_root() / f"task_{task_id}"
        task_dir.mkdir(parents=True, exist_ok=True)
        self._current_temp_dir = task_dir
        logger.debug("Created temp task dir: %s", task_dir)
        return task_dir

    def current_dir(self) -> Optional[Path]:
        return self._current_temp_dir

    def cleanup_current(self) -> None:
        """Remove the current task's temp directory."""
        if self._current_temp_dir and self._current_temp_dir.exists():
            try:
                shutil.rmtree(self._current_temp_dir)
                logger.debug("Removed temp dir: %s", self._current_temp_dir)
            except Exception as e:
                logger.warning("Failed to remove temp dir %s: %s", self._current_temp_dir, e)
            self._current_temp_dir = None

    def cleanup_old(self, max_age_hours: int = TEMP_MAX_AGE_HOURS) -> int:
        """
        Remove temp directories older than max_age_hours.
        Returns number of directories removed.
        """
        temp = temp_root()
        if not temp.exists():
            return 0

        removed = 0
        now = time.time()
        max_age_seconds = max_age_hours * 3600

        for entry in temp.iterdir():
            if not entry.is_dir():
                continue
            try:
                age = now - entry.stat().st_mtime
                if age > max_age_seconds:
                    shutil.rmtree(entry)
                    logger.info("Removed old temp dir: %s (age=%.1fh)", entry, age / 3600)
                    removed += 1
            except Exception as e:
                logger.warning("Failed to remove old temp dir %s: %s", entry, e)

        return removed

    def cleanup_all(self) -> None:
        """Remove all temp directories."""
        temp = temp_root()
        if not temp.exists():
            return
        for entry in temp.iterdir():
            if entry.is_dir():
                try:
                    shutil.rmtree(entry)
                except Exception as e:
                    logger.warning("Failed to remove temp dir %s: %s", entry, e)
        logger.info("Cleaned up all temp directories")


_temp_manager: Optional[TempManager] = None


def get_temp_manager() -> TempManager:
    global _temp_manager
    if _temp_manager is None:
        _temp_manager = TempManager()
    return _temp_manager
