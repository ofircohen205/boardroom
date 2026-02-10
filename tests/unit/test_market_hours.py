# tests/test_market_hours.py
"""Tests for market hours detection (Phase 4b - TASE support)."""
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch

from backend.jobs.alert_checker import (
    is_us_market_hours,
    is_tase_market_hours,
    is_market_hours
)


class TestUSMarketHours:
    """Test US market hours detection (9:30 AM - 4:00 PM ET, Mon-Fri)."""

    def test_us_market_open(self):
        """Market should be open at 10 AM ET on Monday."""
        et_tz = ZoneInfo("America/New_York")
        monday_10am = datetime(2026, 2, 9, 10, 0, 0, tzinfo=et_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_10am

            assert is_us_market_hours() is True

    def test_us_market_before_open(self):
        """Market should be closed at 9:00 AM ET."""
        et_tz = ZoneInfo("America/New_York")
        monday_9am = datetime(2026, 2, 9, 9, 0, 0, tzinfo=et_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_9am

            assert is_us_market_hours() is False

    def test_us_market_at_open(self):
        """Market should be open at exactly 9:30 AM ET."""
        et_tz = ZoneInfo("America/New_York")
        monday_930am = datetime(2026, 2, 9, 9, 30, 0, tzinfo=et_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_930am

            assert is_us_market_hours() is True

    def test_us_market_at_close(self):
        """Market should be closed at exactly 4:00 PM ET."""
        et_tz = ZoneInfo("America/New_York")
        monday_4pm = datetime(2026, 2, 9, 16, 0, 0, tzinfo=et_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_4pm

            assert is_us_market_hours() is False

    def test_us_market_after_close(self):
        """Market should be closed at 5:00 PM ET."""
        et_tz = ZoneInfo("America/New_York")
        monday_5pm = datetime(2026, 2, 9, 17, 0, 0, tzinfo=et_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_5pm

            assert is_us_market_hours() is False

    def test_us_market_saturday(self):
        """Market should be closed on Saturday."""
        et_tz = ZoneInfo("America/New_York")
        saturday_10am = datetime(2026, 2, 14, 10, 0, 0, tzinfo=et_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = saturday_10am

            assert is_us_market_hours() is False

    def test_us_market_sunday(self):
        """Market should be closed on Sunday."""
        et_tz = ZoneInfo("America/New_York")
        sunday_10am = datetime(2026, 2, 15, 10, 0, 0, tzinfo=et_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = sunday_10am

            assert is_us_market_hours() is False


class TestTASEMarketHours:
    """Test TASE market hours detection (10:00 AM - 4:45 PM IST, Sun-Thu)."""

    def test_tase_market_open_monday(self):
        """TASE should be open at 11 AM IST on Monday."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        monday_11am = datetime(2026, 2, 9, 11, 0, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_11am

            assert is_tase_market_hours() is True

    def test_tase_market_open_sunday(self):
        """TASE should be open on Sunday (Israeli trading day)."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        sunday_11am = datetime(2026, 2, 15, 11, 0, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = sunday_11am

            assert is_tase_market_hours() is True

    def test_tase_market_open_thursday(self):
        """TASE should be open on Thursday (last trading day)."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        thursday_11am = datetime(2026, 2, 12, 11, 0, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = thursday_11am

            assert is_tase_market_hours() is True

    def test_tase_market_closed_friday(self):
        """TASE should be closed on Friday."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        friday_11am = datetime(2026, 2, 13, 11, 0, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = friday_11am

            assert is_tase_market_hours() is False

    def test_tase_market_closed_saturday(self):
        """TASE should be closed on Saturday (Shabbat)."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        saturday_11am = datetime(2026, 2, 14, 11, 0, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = saturday_11am

            assert is_tase_market_hours() is False

    def test_tase_market_before_open(self):
        """TASE should be closed at 9:30 AM IST."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        monday_930am = datetime(2026, 2, 9, 9, 30, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_930am

            assert is_tase_market_hours() is False

    def test_tase_market_at_open(self):
        """TASE should be open at exactly 10:00 AM IST."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        monday_10am = datetime(2026, 2, 9, 10, 0, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_10am

            assert is_tase_market_hours() is True

    def test_tase_market_at_close(self):
        """TASE should be closed at exactly 4:45 PM IST."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        monday_445pm = datetime(2026, 2, 9, 16, 45, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_445pm

            assert is_tase_market_hours() is False

    def test_tase_market_after_close(self):
        """TASE should be closed at 5:00 PM IST."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        monday_5pm = datetime(2026, 2, 9, 17, 0, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_5pm

            assert is_tase_market_hours() is False


class TestMarketHoursDispatch:
    """Test market hours dispatch function."""

    def test_dispatch_us_market(self):
        """is_market_hours should dispatch to US for 'US' market."""
        et_tz = ZoneInfo("America/New_York")
        monday_10am = datetime(2026, 2, 9, 10, 0, 0, tzinfo=et_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_10am

            assert is_market_hours("US") is True

    def test_dispatch_tase_market(self):
        """is_market_hours should dispatch to TASE for 'TASE' market."""
        ist_tz = ZoneInfo("Asia/Jerusalem")
        monday_11am = datetime(2026, 2, 9, 11, 0, 0, tzinfo=ist_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_11am

            assert is_market_hours("TASE") is True

    def test_dispatch_default_to_us(self):
        """is_market_hours should default to US for unknown markets."""
        et_tz = ZoneInfo("America/New_York")
        monday_10am = datetime(2026, 2, 9, 10, 0, 0, tzinfo=et_tz)

        with patch('backend.jobs.alert_checker.datetime') as mock_datetime:
            mock_datetime.now.return_value = monday_10am

            assert is_market_hours("UNKNOWN") is True
