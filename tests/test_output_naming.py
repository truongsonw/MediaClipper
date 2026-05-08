"""Tests for path utilities."""

import pytest
from pathlib import Path
from mediaclipper.infra.paths import sanitize_filename, unique_output_path
import tempfile
import os


def test_sanitize_filename():
    assert sanitize_filename("normal_file.mp4") == "normal_file.mp4"
    assert sanitize_filename("file<with>invalid:chars") == "file_with_invalid_chars"
    assert sanitize_filename("  spaces  ") == "spaces"
    assert sanitize_filename("...") == "output"
    assert sanitize_filename("") == "output"


def test_unique_output_path(tmp_path):
    # First file should be the base name
    result = unique_output_path(tmp_path, "video", "mp4")
    assert result == tmp_path / "video.mp4"

    # Create the first file to simulate it existing
    result.with_suffix("").touch()  # creates "video" file
    result.touch()

    # Second file should get a counter
    result2 = unique_output_path(tmp_path, "video", "mp4")
    assert result2 == tmp_path / "video_1.mp4"

    # Create it too
    result2.touch()

    # Third should get _2
    result3 = unique_output_path(tmp_path, "video", "mp4")
    assert result3 == tmp_path / "video_2.mp4"
