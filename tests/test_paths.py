"""Tests for paths module."""

import pytest
from pathlib import Path
from mediaclipper.infra.paths import sanitize_filename


def test_sanitize_filename():
    assert sanitize_filename("video") == "video"
    assert sanitize_filename("my video file") == "my video file"
    assert sanitize_filename("<video>:test") == "_video__test"
    assert sanitize_filename("CON") == "CON"  # On Windows this might be reserved, but our function doesn't block it
    assert sanitize_filename("   ") == "output"
