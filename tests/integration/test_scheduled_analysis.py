# tests/test_scheduled_analysis.py
"""Tests for scheduled analysis features (Phase 4b)."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.shared.db.models import AlertFrequency
from backend.shared.jobs.scheduled_analyzer import calculate_next_run


class TestCalculateNextRun:
    """Test next run time calculation for different frequencies."""

    def test_daily_before_8am(self):
        """Daily schedule before 8 AM should schedule for today at 8 AM."""
        # Mock current time: Monday 6 AM ET
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 9, 6, 0, 0, tzinfo=et_tz)  # Monday 6 AM

        # Patch datetime.now to return our mock time
        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.DAILY)

            # Should schedule for today at 8 AM
            assert next_run.hour == 8
            assert next_run.minute == 0
            assert next_run.date() == now.date()

    def test_daily_after_8am(self):
        """Daily schedule after 8 AM should schedule for tomorrow at 8 AM."""
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 9, 10, 0, 0, tzinfo=et_tz)  # Monday 10 AM

        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.DAILY)

            # Should schedule for tomorrow at 8 AM
            assert next_run.hour == 8
            assert next_run.minute == 0
            assert next_run.date() == (now + timedelta(days=1)).date()

    def test_daily_skips_weekends(self):
        """Daily schedule on Friday after 8 AM should skip to Monday."""
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 13, 10, 0, 0, tzinfo=et_tz)  # Friday 10 AM

        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.DAILY)

            # Should skip Saturday and Sunday, schedule for Monday
            assert next_run.weekday() == 0  # Monday
            assert next_run.hour == 8

    def test_weekly_same_monday_before_8am(self):
        """Weekly on Monday before 8 AM should schedule for today."""
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 9, 6, 0, 0, tzinfo=et_tz)  # Monday 6 AM

        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.WEEKLY)

            # Should schedule for today (Monday) at 8 AM
            assert next_run.weekday() == 0  # Monday
            assert next_run.date() == now.date()
            assert next_run.hour == 8

    def test_weekly_same_monday_after_8am(self):
        """Weekly on Monday after 8 AM should schedule for next Monday."""
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 9, 10, 0, 0, tzinfo=et_tz)  # Monday 10 AM

        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.WEEKLY)

            # Should schedule for next Monday
            assert next_run.weekday() == 0  # Monday
            assert next_run.date() == (now + timedelta(days=7)).date()

    def test_weekly_on_wednesday(self):
        """Weekly on Wednesday should schedule for next Monday."""
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 11, 10, 0, 0, tzinfo=et_tz)  # Wednesday

        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.WEEKLY)

            # Should schedule for next Monday
            assert next_run.weekday() == 0  # Monday
            assert next_run > now
            assert next_run.hour == 8

    def test_on_change_during_market_hours(self):
        """On-change during market hours should schedule for next hour."""
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 9, 11, 30, 0, tzinfo=et_tz)  # Monday 11:30 AM

        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.ON_CHANGE)

            # Should schedule for 12:00 PM (next hour)
            assert next_run.hour == 12
            assert next_run.minute == 0
            assert next_run.date() == now.date()

    def test_on_change_before_market_hours(self):
        """On-change before market hours should schedule for 10 AM today."""
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 9, 8, 0, 0, tzinfo=et_tz)  # Monday 8 AM

        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.ON_CHANGE)

            # Should schedule for 10 AM today
            assert next_run.hour == 10
            assert next_run.minute == 0
            assert next_run.date() == now.date()

    def test_on_change_after_market_hours(self):
        """On-change after market hours should schedule for 10 AM next day."""
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 9, 18, 0, 0, tzinfo=et_tz)  # Monday 6 PM

        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.ON_CHANGE)

            # Should schedule for 10 AM tomorrow
            assert next_run.hour == 10
            assert next_run.minute == 0
            assert next_run.date() == (now + timedelta(days=1)).date()

    def test_on_change_friday_evening(self):
        """On-change on Friday evening should skip weekend to Monday."""
        et_tz = ZoneInfo("America/New_York")
        now = datetime(2026, 2, 13, 18, 0, 0, tzinfo=et_tz)  # Friday 6 PM

        from unittest.mock import patch

        with patch("backend.shared.jobs.scheduled_analyzer.datetime") as mock_datetime:
            mock_datetime.now.return_value = now

            next_run = calculate_next_run(AlertFrequency.ON_CHANGE)

            # Should skip weekend, schedule for Monday 10 AM
            assert next_run.weekday() == 0  # Monday
            assert next_run.hour == 10
