"""Tests for time parsing utilities."""

import pytest
from mediaclipper.services.ffprobe_service import FFprobeService


def test_format_duration():
    service = FFprobeService()
    assert service.format_duration(0) == "00:00:00.000"
    assert service.format_duration(65.5) == "00:01:05.500"
    assert service.format_duration(3661.123) == "01:01:01.123"


def test_parse_time():
    service = FFprobeService()
    assert service.parse_time("00:00:00") == 0.0
    assert service.parse_time("00:01:05") == 65.0
    assert service.parse_time("01:01:01") == 3661.0
    assert service.parse_time("01:30:00") == 5400.0
    assert service.parse_time("65") == 65.0
    assert service.parse_time("  01:30  ") == 90.0
    # With milliseconds
    assert service.parse_time("00:01:05.500") == 65.5
    assert service.parse_time("01:00:00.00") == 3600.0


def test_parse_time_invalid():
    service = FFprobeService()
    assert service.parse_time("") is None
    assert service.parse_time("invalid") is None
