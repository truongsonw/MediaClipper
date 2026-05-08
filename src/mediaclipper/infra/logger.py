"""Logging setup with rotation."""

import logging
import logging.handlers
import sys
from pathlib import Path

from mediaclipper.infra.paths import logs_dir


def setup_logger(name: str = "mediaclipper") -> logging.Logger:
    logs = logs_dir()
    logs.mkdir(parents=True, exist_ok=True)

    log_file = logs / "mediaclipper.log"

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)

    # File handler with rotation (5 MB max, keep 3 files)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s:%(lineno)d  %(message)s"
    )
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "mediaclipper") -> logging.Logger:
    return logging.getLogger(name)
