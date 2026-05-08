"""Cleanup service."""

from mediaclipper.infra.temp_manager import get_temp_manager
from mediaclipper.infra.logger import get_logger

logger = get_logger(__name__)


class CleanupService:
    """Handles cleanup of temporary files."""

    def __init__(self):
        self._temp_mgr = get_temp_manager()

    def cleanup_old_temp(self, max_age_hours: int = 24) -> int:
        """Remove temp files older than specified hours."""
        removed = self._temp_mgr.cleanup_old(max_age_hours=max_age_hours)
        logger.info("Cleanup removed %d old temp directories", removed)
        return removed

    def cleanup_all_temp(self) -> None:
        """Remove all temp files immediately."""
        self._temp_mgr.cleanup_all()
        logger.info("All temp files cleaned")

    def cleanup_current_task(self) -> None:
        """Remove temp files for the current task."""
        self._temp_mgr.cleanup_current()
