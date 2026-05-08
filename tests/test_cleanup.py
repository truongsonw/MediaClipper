"""Tests for cleanup logic."""

import pytest
import time
import tempfile
import os
from pathlib import Path
from mediaclipper.infra.temp_manager import TempManager


def test_create_and_cleanup_current(tmp_path, monkeypatch):
    # Patch temp_root to use our temp dir
    import mediaclipper.infra.temp_manager as tm
    monkeypatch.setattr(tm, "temp_root", lambda: tmp_path)

    mgr = TempManager()
    task_dir = mgr.create_task_dir()
    assert task_dir.exists()
    assert task_dir.is_dir()

    mgr.cleanup_current()
    assert not task_dir.exists()


def test_cleanup_old(tmp_path, monkeypatch):
    import mediaclipper.infra.temp_manager as tm
    monkeypatch.setattr(tm, "temp_root", lambda: tmp_path)

    mgr = TempManager()

    # Create an old dir
    old_dir = tmp_path / "task_old"
    old_dir.mkdir()
    old_time = time.time() - (25 * 3600)  # 25 hours ago
    os.utime(old_dir, (old_time, old_time))

    # Create a recent dir
    recent_dir = tmp_path / "task_recent"
    recent_dir.mkdir()

    removed = mgr.cleanup_old(max_age_hours=24)
    assert removed == 1
    assert not old_dir.exists()
    assert recent_dir.exists()
