# tests/unit/notifications/test_dao_alerts.py
"""Unit tests for PriceAlertDAO, NotificationDAO, and ScheduledAnalysisDAO."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.shared.ai.state.enums import Market
from backend.shared.dao.alerts import (
    NotificationDAO,
    PriceAlertDAO,
    ScheduledAnalysisDAO,
)
from backend.shared.db.models import (
    AlertCondition,
    AlertFrequency,
    Notification,
    NotificationType,
    PriceAlert,
    ScheduledAnalysis,
)

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def make_scalars_all(items):
    """Return a mock execute result where .scalars().all() returns items."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


def make_scalars_first(item):
    """Return a mock execute result where .scalars().first() returns item."""
    result = MagicMock()
    result.scalars.return_value.first.return_value = item
    return result


def make_scalar_one_or_none(item):
    """Return a mock execute result where .scalar_one_or_none() returns item."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = item
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def price_alert_dao(mock_session):
    return PriceAlertDAO(mock_session)


@pytest.fixture
def notification_dao(mock_session):
    return NotificationDAO(mock_session)


@pytest.fixture
def scheduled_analysis_dao(mock_session):
    return ScheduledAnalysisDAO(mock_session)


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def sample_alert(sample_user_id):
    alert = MagicMock(spec=PriceAlert)
    alert.id = uuid4()
    alert.user_id = sample_user_id
    alert.ticker = "AAPL"
    alert.market = Market.US
    alert.condition = AlertCondition.ABOVE
    alert.target_price = 200.0
    alert.active = True
    alert.triggered = False
    alert.triggered_at = None
    alert.cooldown_until = None
    return alert


@pytest.fixture
def sample_notification(sample_user_id):
    notif = MagicMock(spec=Notification)
    notif.id = uuid4()
    notif.user_id = sample_user_id
    notif.type = NotificationType.PRICE_ALERT
    notif.data = {"ticker": "AAPL", "price": 201.0}
    notif.read = False
    return notif


@pytest.fixture
def sample_schedule(sample_user_id):
    schedule = MagicMock(spec=ScheduledAnalysis)
    schedule.id = uuid4()
    schedule.user_id = sample_user_id
    schedule.ticker = "AAPL"
    schedule.market = Market.US
    schedule.frequency = AlertFrequency.DAILY
    schedule.active = True
    schedule.next_run = datetime.now() - timedelta(minutes=5)
    schedule.last_run = None
    return schedule


# ===========================================================================
# PriceAlertDAO tests
# ===========================================================================


class TestPriceAlertDAO:
    """Tests for PriceAlertDAO."""

    async def test_get_user_alerts_active_only_returns_active_alerts(
        self, price_alert_dao, mock_session, sample_user_id, sample_alert
    ):
        """get_user_alerts with active_only=True returns only active alerts."""
        mock_session.execute.return_value = make_scalars_all([sample_alert])

        result = await price_alert_dao.get_user_alerts(sample_user_id, active_only=True)

        assert result == [sample_alert]
        mock_session.execute.assert_awaited_once()

    async def test_get_user_alerts_all_alerts_when_active_only_false(
        self, price_alert_dao, mock_session, sample_user_id, sample_alert
    ):
        """get_user_alerts with active_only=False returns all alerts including inactive."""
        inactive_alert = MagicMock(spec=PriceAlert)
        inactive_alert.id = uuid4()
        inactive_alert.active = False
        mock_session.execute.return_value = make_scalars_all(
            [sample_alert, inactive_alert]
        )

        result = await price_alert_dao.get_user_alerts(
            sample_user_id, active_only=False
        )

        assert len(result) == 2
        assert sample_alert in result
        assert inactive_alert in result

    async def test_get_user_alerts_returns_empty_list_when_no_alerts(
        self, price_alert_dao, mock_session, sample_user_id
    ):
        """get_user_alerts returns empty list when user has no alerts."""
        mock_session.execute.return_value = make_scalars_all([])

        result = await price_alert_dao.get_user_alerts(sample_user_id)

        assert result == []

    async def test_get_active_alerts_for_ticker_returns_matching_alerts(
        self, price_alert_dao, mock_session, sample_alert
    ):
        """get_active_alerts_for_ticker returns alerts for the given ticker/market."""
        mock_session.execute.return_value = make_scalars_all([sample_alert])

        result = await price_alert_dao.get_active_alerts_for_ticker("AAPL", Market.US)

        assert result == [sample_alert]
        mock_session.execute.assert_awaited_once()

    async def test_get_active_alerts_for_ticker_returns_empty_when_none_match(
        self, price_alert_dao, mock_session
    ):
        """get_active_alerts_for_ticker returns empty list when no alerts match."""
        mock_session.execute.return_value = make_scalars_all([])

        result = await price_alert_dao.get_active_alerts_for_ticker("TSLA", Market.US)

        assert result == []

    async def test_get_all_active_tickers_returns_ticker_market_tuples(
        self, price_alert_dao, mock_session
    ):
        """get_all_active_tickers returns list of (ticker, market) tuples."""
        mock_result = MagicMock()
        mock_result.all.return_value = [("AAPL", Market.US), ("MSFT", Market.US)]
        mock_session.execute.return_value = mock_result

        result = await price_alert_dao.get_all_active_tickers()

        assert len(result) == 2
        assert ("AAPL", Market.US) in result
        assert ("MSFT", Market.US) in result

    async def test_get_all_active_tickers_returns_empty_list_when_none(
        self, price_alert_dao, mock_session
    ):
        """get_all_active_tickers returns empty list when no active alerts exist."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await price_alert_dao.get_all_active_tickers()

        assert result == []

    async def test_reset_alert_resets_triggered_state_and_returns_alert(
        self, price_alert_dao, mock_session, sample_alert
    ):
        """reset_alert clears triggered fields and returns the updated alert."""
        # get_by_id uses .scalars().first()
        mock_session.execute.return_value = make_scalars_first(sample_alert)

        result = await price_alert_dao.reset_alert(sample_alert.id)

        assert result is not None
        assert sample_alert.triggered is False
        assert sample_alert.triggered_at is None
        assert sample_alert.cooldown_until is None
        mock_session.add.assert_called_once_with(sample_alert)
        mock_session.commit.assert_awaited()

    async def test_reset_alert_returns_none_when_alert_not_found(
        self, price_alert_dao, mock_session
    ):
        """reset_alert returns None when the alert ID does not exist."""
        mock_session.execute.return_value = make_scalars_first(None)

        result = await price_alert_dao.reset_alert(uuid4())

        assert result is None

    async def test_count_user_alerts_returns_correct_count(
        self, price_alert_dao, mock_session, sample_user_id
    ):
        """count_user_alerts returns the integer count for the user."""
        count_result = MagicMock()
        count_result.scalar.return_value = 3
        mock_session.execute.return_value = count_result

        result = await price_alert_dao.count_user_alerts(sample_user_id)

        assert result == 3

    async def test_count_user_alerts_returns_zero_when_scalar_is_none(
        self, price_alert_dao, mock_session, sample_user_id
    ):
        """count_user_alerts returns 0 when scalar() returns None (no rows)."""
        count_result = MagicMock()
        count_result.scalar.return_value = None
        mock_session.execute.return_value = count_result

        result = await price_alert_dao.count_user_alerts(sample_user_id)

        assert result == 0


# ===========================================================================
# NotificationDAO tests
# ===========================================================================


class TestNotificationDAO:
    """Tests for NotificationDAO."""

    async def test_get_user_notifications_returns_all_by_default(
        self, notification_dao, mock_session, sample_user_id, sample_notification
    ):
        """get_user_notifications returns all notifications for the user."""
        mock_session.execute.return_value = make_scalars_all([sample_notification])

        result = await notification_dao.get_user_notifications(sample_user_id)

        assert result == [sample_notification]
        mock_session.execute.assert_awaited_once()

    async def test_get_user_notifications_unread_only_filter(
        self, notification_dao, mock_session, sample_user_id, sample_notification
    ):
        """get_user_notifications with unread_only=True filters to unread only."""
        mock_session.execute.return_value = make_scalars_all([sample_notification])

        result = await notification_dao.get_user_notifications(
            sample_user_id, unread_only=True
        )

        assert result == [sample_notification]

    async def test_get_user_notifications_returns_empty_list_when_none(
        self, notification_dao, mock_session, sample_user_id
    ):
        """get_user_notifications returns empty list when user has no notifications."""
        mock_session.execute.return_value = make_scalars_all([])

        result = await notification_dao.get_user_notifications(sample_user_id)

        assert result == []

    async def test_get_unread_count_returns_correct_count(
        self, notification_dao, mock_session, sample_user_id
    ):
        """get_unread_count returns the correct integer count of unread notifications."""
        count_result = MagicMock()
        count_result.scalar.return_value = 5
        mock_session.execute.return_value = count_result

        result = await notification_dao.get_unread_count(sample_user_id)

        assert result == 5

    async def test_get_unread_count_returns_zero_when_scalar_is_none(
        self, notification_dao, mock_session, sample_user_id
    ):
        """get_unread_count returns 0 when scalar() returns None."""
        count_result = MagicMock()
        count_result.scalar.return_value = None
        mock_session.execute.return_value = count_result

        result = await notification_dao.get_unread_count(sample_user_id)

        assert result == 0

    async def test_mark_as_read_sets_read_true_and_returns_notification(
        self, notification_dao, mock_session, sample_notification
    ):
        """mark_as_read sets read=True on the notification and commits."""
        mock_session.execute.return_value = make_scalars_first(sample_notification)

        result = await notification_dao.mark_as_read(sample_notification.id)

        assert result is not None
        assert sample_notification.read is True
        mock_session.add.assert_called_once_with(sample_notification)
        mock_session.commit.assert_awaited()

    async def test_mark_as_read_returns_none_when_notification_not_found(
        self, notification_dao, mock_session
    ):
        """mark_as_read returns None when the notification ID does not exist."""
        mock_session.execute.return_value = make_scalars_first(None)

        result = await notification_dao.mark_as_read(uuid4())

        assert result is None

    async def test_mark_all_read_executes_update_and_returns_rowcount(
        self, notification_dao, mock_session, sample_user_id
    ):
        """mark_all_read issues a bulk UPDATE and returns the number of rows updated."""
        update_result = MagicMock()
        update_result.rowcount = 4
        mock_session.execute.return_value = update_result

        result = await notification_dao.mark_all_read(sample_user_id)

        assert result == 4
        mock_session.execute.assert_awaited_once()
        mock_session.flush.assert_awaited_once()

    async def test_find_recent_by_ticker_returns_matching_notification(
        self, notification_dao, mock_session, sample_user_id, sample_notification
    ):
        """find_recent_by_ticker returns the most recent matching notification."""
        mock_session.execute.return_value = make_scalar_one_or_none(sample_notification)

        result = await notification_dao.find_recent_by_ticker(
            sample_user_id, NotificationType.PRICE_ALERT, "AAPL"
        )

        assert result is sample_notification

    async def test_find_recent_by_ticker_returns_none_when_no_match(
        self, notification_dao, mock_session, sample_user_id
    ):
        """find_recent_by_ticker returns None when no recent notification exists."""
        mock_session.execute.return_value = make_scalar_one_or_none(None)

        result = await notification_dao.find_recent_by_ticker(
            sample_user_id, NotificationType.PRICE_ALERT, "TSLA"
        )

        assert result is None


# ===========================================================================
# ScheduledAnalysisDAO tests
# ===========================================================================


class TestScheduledAnalysisDAO:
    """Tests for ScheduledAnalysisDAO."""

    async def test_get_user_schedules_returns_schedules_for_user(
        self, scheduled_analysis_dao, mock_session, sample_user_id, sample_schedule
    ):
        """get_user_schedules returns all schedules belonging to the user."""
        mock_session.execute.return_value = make_scalars_all([sample_schedule])

        result = await scheduled_analysis_dao.get_user_schedules(sample_user_id)

        assert result == [sample_schedule]
        mock_session.execute.assert_awaited_once()

    async def test_get_user_schedules_returns_empty_list_when_none(
        self, scheduled_analysis_dao, mock_session, sample_user_id
    ):
        """get_user_schedules returns empty list when user has no schedules."""
        mock_session.execute.return_value = make_scalars_all([])

        result = await scheduled_analysis_dao.get_user_schedules(sample_user_id)

        assert result == []

    async def test_get_due_schedules_returns_overdue_schedules(
        self, scheduled_analysis_dao, mock_session, sample_schedule
    ):
        """get_due_schedules returns active schedules where next_run <= now."""
        mock_session.execute.return_value = make_scalars_all([sample_schedule])

        result = await scheduled_analysis_dao.get_due_schedules()

        assert result == [sample_schedule]
        mock_session.execute.assert_awaited_once()

    async def test_get_due_schedules_returns_empty_when_none_due(
        self, scheduled_analysis_dao, mock_session
    ):
        """get_due_schedules returns empty list when no schedules are currently due."""
        mock_session.execute.return_value = make_scalars_all([])

        result = await scheduled_analysis_dao.get_due_schedules()

        assert result == []

    async def test_update_run_times_updates_timestamps_and_returns_schedule(
        self, scheduled_analysis_dao, mock_session, sample_schedule
    ):
        """update_run_times persists last_run and next_run on the found schedule."""
        mock_session.execute.return_value = make_scalars_first(sample_schedule)

        last_run = datetime.now()
        next_run = last_run + timedelta(days=1)

        result = await scheduled_analysis_dao.update_run_times(
            sample_schedule.id, last_run, next_run
        )

        assert result is not None
        assert sample_schedule.last_run == last_run
        assert sample_schedule.next_run == next_run
        mock_session.add.assert_called_once_with(sample_schedule)
        mock_session.commit.assert_awaited()

    async def test_update_run_times_returns_none_when_schedule_not_found(
        self, scheduled_analysis_dao, mock_session
    ):
        """update_run_times returns None when the schedule ID does not exist."""
        mock_session.execute.return_value = make_scalars_first(None)

        result = await scheduled_analysis_dao.update_run_times(
            uuid4(), datetime.now(), datetime.now() + timedelta(days=1)
        )

        assert result is None

    async def test_count_user_schedules_returns_correct_count(
        self, scheduled_analysis_dao, mock_session, sample_user_id
    ):
        """count_user_schedules returns the integer count for the user."""
        count_result = MagicMock()
        count_result.scalar.return_value = 2
        mock_session.execute.return_value = count_result

        result = await scheduled_analysis_dao.count_user_schedules(sample_user_id)

        assert result == 2

    async def test_count_user_schedules_returns_zero_when_scalar_is_none(
        self, scheduled_analysis_dao, mock_session, sample_user_id
    ):
        """count_user_schedules returns 0 when scalar() returns None."""
        count_result = MagicMock()
        count_result.scalar.return_value = None
        mock_session.execute.return_value = count_result

        result = await scheduled_analysis_dao.count_user_schedules(sample_user_id)

        assert result == 0

    async def test_get_by_ticker_market_frequency_returns_existing_schedule(
        self, scheduled_analysis_dao, mock_session, sample_user_id, sample_schedule
    ):
        """get_by_ticker_market_frequency returns a schedule when a match exists."""
        mock_session.execute.return_value = make_scalar_one_or_none(sample_schedule)

        result = await scheduled_analysis_dao.get_by_ticker_market_frequency(
            sample_user_id, "AAPL", Market.US, AlertFrequency.DAILY
        )

        assert result is sample_schedule

    async def test_get_by_ticker_market_frequency_returns_none_when_not_found(
        self, scheduled_analysis_dao, mock_session, sample_user_id
    ):
        """get_by_ticker_market_frequency returns None when no duplicate exists."""
        mock_session.execute.return_value = make_scalar_one_or_none(None)

        result = await scheduled_analysis_dao.get_by_ticker_market_frequency(
            sample_user_id, "TSLA", Market.US, AlertFrequency.WEEKLY
        )

        assert result is None
