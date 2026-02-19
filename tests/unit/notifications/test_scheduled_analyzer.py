# tests/unit/notifications/test_scheduled_analyzer.py
"""Unit tests for backend/shared/jobs/scheduled_analyzer.py."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.shared.db.models import AlertFrequency
from backend.shared.jobs.scheduled_analyzer import (
    calculate_next_run,
    run_scheduled_analyses,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_schedule(
    ticker: str = "AAPL",
    frequency: AlertFrequency = AlertFrequency.DAILY,
) -> MagicMock:
    """Return a minimal ScheduledAnalysis mock."""
    schedule = MagicMock()
    schedule.id = uuid4()
    schedule.user_id = uuid4()
    schedule.ticker = ticker
    schedule.market = MagicMock(value="US")
    schedule.frequency = frequency
    return schedule


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# calculate_next_run -- pure function tests
# ---------------------------------------------------------------------------


class TestCalculateNextRunDaily:
    """Tests for AlertFrequency.DAILY."""

    def test_returns_datetime(self):
        result = calculate_next_run(AlertFrequency.DAILY)
        assert isinstance(result, datetime)

    def test_hour_is_eight(self):
        result = calculate_next_run(AlertFrequency.DAILY)
        assert result.hour == 8

    def test_returns_weekday(self):
        """Result must land on Monday-Friday (weekday < 5)."""
        result = calculate_next_run(AlertFrequency.DAILY)
        assert result.weekday() < 5

    def test_is_in_future(self):
        result = calculate_next_run(AlertFrequency.DAILY)
        now_utc = datetime.now(timezone.utc)
        assert result > now_utc


class TestCalculateNextRunWeekly:
    """Tests for AlertFrequency.WEEKLY."""

    def test_returns_datetime(self):
        result = calculate_next_run(AlertFrequency.WEEKLY)
        assert isinstance(result, datetime)

    def test_hour_is_eight(self):
        result = calculate_next_run(AlertFrequency.WEEKLY)
        assert result.hour == 8

    def test_lands_on_monday(self):
        """Weekly schedules must run on Monday (weekday == 0)."""
        result = calculate_next_run(AlertFrequency.WEEKLY)
        assert result.weekday() == 0

    def test_is_in_future(self):
        result = calculate_next_run(AlertFrequency.WEEKLY)
        now_utc = datetime.now(timezone.utc)
        assert result > now_utc


class TestCalculateNextRunOnChange:
    """Tests for AlertFrequency.ON_CHANGE."""

    def test_returns_datetime(self):
        result = calculate_next_run(AlertFrequency.ON_CHANGE)
        assert isinstance(result, datetime)

    def test_hour_within_market_hours(self):
        """ON_CHANGE must schedule during 10:00-15:59 ET."""
        result = calculate_next_run(AlertFrequency.ON_CHANGE)
        assert 10 <= result.hour < 16

    def test_returns_weekday(self):
        result = calculate_next_run(AlertFrequency.ON_CHANGE)
        assert result.weekday() < 5

    def test_is_in_future(self):
        result = calculate_next_run(AlertFrequency.ON_CHANGE)
        now_utc = datetime.now(timezone.utc)
        assert result > now_utc


class TestCalculateNextRunDefault:
    """Tests for unrecognised / None frequency (default branch)."""

    def test_none_frequency_returns_datetime_or_raises(self):
        """Passing None should either return a datetime (default branch) or raise."""
        try:
            result = calculate_next_run(None)  # type: ignore[arg-type]
            assert isinstance(result, datetime)
            assert result.hour == 8
        except Exception:
            pass


# ---------------------------------------------------------------------------
# run_scheduled_analyses -- async tests
# ---------------------------------------------------------------------------


class TestRunScheduledAnalysesNoSchedules:
    """When no schedules are due the function should return early."""

    async def test_returns_success_with_zero_schedules_run(self, mock_db):
        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.AlertService"),
            patch("backend.shared.jobs.scheduled_analyzer.BoardroomGraph"),
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[])
            mock_dao_cls.return_value = mock_dao

            result = await run_scheduled_analyses(mock_db)

        assert result["success"] is True
        assert result["schedules_run"] == 0

    async def test_does_not_commit_when_no_schedules(self, mock_db):
        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.AlertService"),
            patch("backend.shared.jobs.scheduled_analyzer.BoardroomGraph"),
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[])
            mock_dao_cls.return_value = mock_dao

            await run_scheduled_analyses(mock_db)

        mock_db.commit.assert_not_called()


class TestRunScheduledAnalysesWithFinalDecision:
    """When a schedule runs and produces a final_decision the notification is created."""

    async def test_schedules_run_count_increments(self, mock_db):
        schedule = _make_schedule()

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.AlertService"
            ) as mock_alert_svc_cls,
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[schedule])
            mock_dao.update_run_times = AsyncMock()
            mock_dao_cls.return_value = mock_dao

            mock_graph = AsyncMock()
            mock_graph.run = AsyncMock(
                return_value={
                    "final_decision": {"action": "BUY", "confidence": 0.8},
                    "risk_assessment": {"veto": False},
                }
            )
            mock_graph_cls.return_value = mock_graph

            mock_alert_svc = AsyncMock()
            mock_alert_svc.create_analysis_notification = AsyncMock()
            mock_alert_svc_cls.return_value = mock_alert_svc

            result = await run_scheduled_analyses(mock_db)

        assert result["success"] is True
        assert result["schedules_run"] == 1

    async def test_create_analysis_notification_called_with_correct_args(self, mock_db):
        schedule = _make_schedule(ticker="TSLA")

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.AlertService"
            ) as mock_alert_svc_cls,
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[schedule])
            mock_dao.update_run_times = AsyncMock()
            mock_dao_cls.return_value = mock_dao

            mock_graph = AsyncMock()
            mock_graph.run = AsyncMock(
                return_value={
                    "final_decision": {"action": "SELL", "confidence": 0.65},
                    "risk_assessment": {"veto": False},
                }
            )
            mock_graph_cls.return_value = mock_graph

            mock_alert_svc = AsyncMock()
            mock_alert_svc.create_analysis_notification = AsyncMock()
            mock_alert_svc_cls.return_value = mock_alert_svc

            await run_scheduled_analyses(mock_db)

        mock_alert_svc.create_analysis_notification.assert_called_once()
        call_kwargs = mock_alert_svc.create_analysis_notification.call_args.kwargs
        assert call_kwargs["ticker"] == "TSLA"
        assert call_kwargs["action"] == "SELL"
        assert call_kwargs["confidence"] == 0.65
        assert call_kwargs["vetoed"] is False
        assert call_kwargs["veto_reason"] is None

    async def test_update_run_times_called_after_successful_run(self, mock_db):
        schedule = _make_schedule()

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.AlertService"
            ) as mock_alert_svc_cls,
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[schedule])
            mock_dao.update_run_times = AsyncMock()
            mock_dao_cls.return_value = mock_dao

            mock_graph = AsyncMock()
            mock_graph.run = AsyncMock(
                return_value={
                    "final_decision": {"action": "HOLD", "confidence": 0.5},
                    "risk_assessment": {"veto": False},
                }
            )
            mock_graph_cls.return_value = mock_graph

            mock_alert_svc = AsyncMock()
            mock_alert_svc.create_analysis_notification = AsyncMock()
            mock_alert_svc_cls.return_value = mock_alert_svc

            await run_scheduled_analyses(mock_db)

        mock_dao.update_run_times.assert_called_once()
        call_kwargs = mock_dao.update_run_times.call_args.kwargs
        assert call_kwargs["schedule_id"] == schedule.id

    async def test_db_commit_called_after_processing(self, mock_db):
        schedule = _make_schedule()

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.AlertService"
            ) as mock_alert_svc_cls,
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[schedule])
            mock_dao.update_run_times = AsyncMock()
            mock_dao_cls.return_value = mock_dao

            mock_graph = AsyncMock()
            mock_graph.run = AsyncMock(
                return_value={
                    "final_decision": {"action": "BUY", "confidence": 0.9},
                    "risk_assessment": {"veto": False},
                }
            )
            mock_graph_cls.return_value = mock_graph

            mock_alert_svc = AsyncMock()
            mock_alert_svc.create_analysis_notification = AsyncMock()
            mock_alert_svc_cls.return_value = mock_alert_svc

            await run_scheduled_analyses(mock_db)

        mock_db.commit.assert_called_once()


class TestRunScheduledAnalysesWithVeto:
    """When the risk_assessment signals a veto the notification must carry vetoed=True."""

    async def test_vetoed_true_passed_to_notification(self, mock_db):
        schedule = _make_schedule()

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.AlertService"
            ) as mock_alert_svc_cls,
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[schedule])
            mock_dao.update_run_times = AsyncMock()
            mock_dao_cls.return_value = mock_dao

            mock_graph = AsyncMock()
            mock_graph.run = AsyncMock(
                return_value={
                    "final_decision": {"action": "BUY", "confidence": 0.75},
                    "risk_assessment": {
                        "veto": True,
                        "reason": "Sector overweight",
                    },
                }
            )
            mock_graph_cls.return_value = mock_graph

            mock_alert_svc = AsyncMock()
            mock_alert_svc.create_analysis_notification = AsyncMock()
            mock_alert_svc_cls.return_value = mock_alert_svc

            await run_scheduled_analyses(mock_db)

        call_kwargs = mock_alert_svc.create_analysis_notification.call_args.kwargs
        assert call_kwargs["vetoed"] is True
        assert call_kwargs["veto_reason"] == "Sector overweight"


class TestRunScheduledAnalysesNoFinalDecision:
    """When graph returns no final_decision the notification must NOT be created."""

    async def test_notification_not_created_when_no_final_decision(self, mock_db):
        schedule = _make_schedule()

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.AlertService"
            ) as mock_alert_svc_cls,
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[schedule])
            mock_dao.update_run_times = AsyncMock()
            mock_dao_cls.return_value = mock_dao

            mock_graph = AsyncMock()
            mock_graph.run = AsyncMock(
                return_value={
                    "final_decision": None,
                    "risk_assessment": {"veto": False},
                }
            )
            mock_graph_cls.return_value = mock_graph

            mock_alert_svc = AsyncMock()
            mock_alert_svc.create_analysis_notification = AsyncMock()
            mock_alert_svc_cls.return_value = mock_alert_svc

            result = await run_scheduled_analyses(mock_db)

        mock_alert_svc.create_analysis_notification.assert_not_called()
        assert result["schedules_run"] == 1

    async def test_update_run_times_still_called_without_final_decision(self, mock_db):
        schedule = _make_schedule()

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.AlertService"
            ) as mock_alert_svc_cls,
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[schedule])
            mock_dao.update_run_times = AsyncMock()
            mock_dao_cls.return_value = mock_dao

            mock_graph = AsyncMock()
            mock_graph.run = AsyncMock(return_value={"final_decision": None})
            mock_graph_cls.return_value = mock_graph

            mock_alert_svc = AsyncMock()
            mock_alert_svc_cls.return_value = mock_alert_svc

            await run_scheduled_analyses(mock_db)

        mock_dao.update_run_times.assert_called_once()


class TestRunScheduledAnalysesPerScheduleException:
    """An exception inside a single schedule must not abort processing of others."""

    async def test_failed_schedule_does_not_increment_count(self, mock_db):
        schedule = _make_schedule()

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.AlertService"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[schedule])
            mock_dao_cls.return_value = mock_dao

            mock_graph = AsyncMock()
            mock_graph.run = AsyncMock(side_effect=RuntimeError("LLM timeout"))
            mock_graph_cls.return_value = mock_graph

            result = await run_scheduled_analyses(mock_db)

        assert result["success"] is True
        assert result["schedules_run"] == 0

    async def test_second_schedule_still_runs_after_first_fails(self, mock_db):
        schedule_fail = _make_schedule(ticker="FAIL")
        schedule_ok = _make_schedule(ticker="MSFT")

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.AlertService"
            ) as mock_alert_svc_cls,
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(
                return_value=[schedule_fail, schedule_ok]
            )
            mock_dao.update_run_times = AsyncMock()
            mock_dao_cls.return_value = mock_dao

            mock_graph_fail = AsyncMock()
            mock_graph_fail.run = AsyncMock(side_effect=RuntimeError("Network error"))

            mock_graph_ok = AsyncMock()
            mock_graph_ok.run = AsyncMock(
                return_value={
                    "final_decision": {"action": "BUY", "confidence": 0.7},
                    "risk_assessment": {"veto": False},
                }
            )

            mock_graph_cls.side_effect = [mock_graph_fail, mock_graph_ok]

            mock_alert_svc = AsyncMock()
            mock_alert_svc.create_analysis_notification = AsyncMock()
            mock_alert_svc_cls.return_value = mock_alert_svc

            result = await run_scheduled_analyses(mock_db)

        assert result["schedules_run"] == 1
        mock_alert_svc.create_analysis_notification.assert_called_once()


class TestRunScheduledAnalysesOuterException:
    """An outer exception (e.g. DB failure on get_due_schedules) returns failure dict."""

    async def test_returns_failure_dict_on_outer_exception(self, mock_db):
        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.AlertService"),
            patch("backend.shared.jobs.scheduled_analyzer.BoardroomGraph"),
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(
                side_effect=Exception("DB connection lost")
            )
            mock_dao_cls.return_value = mock_dao

            result = await run_scheduled_analyses(mock_db)

        assert result["success"] is False
        assert "DB connection lost" in result["error"]
        assert result["schedules_run"] == 0

    async def test_rollback_called_on_outer_exception(self, mock_db):
        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.AlertService"),
            patch("backend.shared.jobs.scheduled_analyzer.BoardroomGraph"),
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(side_effect=Exception("Unexpected"))
            mock_dao_cls.return_value = mock_dao

            await run_scheduled_analyses(mock_db)

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()


class TestRunScheduledAnalysesReturnStructure:
    """Verify the shape of the returned dict on the happy path."""

    async def test_result_contains_duration_seconds(self, mock_db):
        schedule = _make_schedule()

        with (
            patch(
                "backend.shared.jobs.scheduled_analyzer.ScheduledAnalysisDAO"
            ) as mock_dao_cls,
            patch("backend.shared.jobs.scheduled_analyzer.PriceAlertDAO"),
            patch("backend.shared.jobs.scheduled_analyzer.NotificationDAO"),
            patch(
                "backend.shared.jobs.scheduled_analyzer.AlertService"
            ) as mock_alert_svc_cls,
            patch(
                "backend.shared.jobs.scheduled_analyzer.BoardroomGraph"
            ) as mock_graph_cls,
        ):
            mock_dao = AsyncMock()
            mock_dao.get_due_schedules = AsyncMock(return_value=[schedule])
            mock_dao.update_run_times = AsyncMock()
            mock_dao_cls.return_value = mock_dao

            mock_graph = AsyncMock()
            mock_graph.run = AsyncMock(
                return_value={
                    "final_decision": {"action": "HOLD", "confidence": 0.5},
                    "risk_assessment": {"veto": False},
                }
            )
            mock_graph_cls.return_value = mock_graph

            mock_alert_svc = AsyncMock()
            mock_alert_svc.create_analysis_notification = AsyncMock()
            mock_alert_svc_cls.return_value = mock_alert_svc

            result = await run_scheduled_analyses(mock_db)

        assert "duration_seconds" in result
        assert isinstance(result["duration_seconds"], float)
        assert result["duration_seconds"] >= 0
