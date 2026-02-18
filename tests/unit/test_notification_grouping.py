# tests/test_notification_grouping.py
"""Tests for notification grouping feature (Phase 4b)."""

from datetime import datetime, timedelta
from typing import ClassVar
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from backend.domains.notifications.services.alert_service import AlertService
from backend.shared.ai.state.enums import Market
from backend.shared.db.models import AlertCondition, NotificationType


@pytest.fixture
def mock_alert():
    """Create a mock price alert."""

    class MockAlert:
        id: ClassVar = uuid4()
        user_id: ClassVar = uuid4()
        ticker: ClassVar = "AAPL"
        market: ClassVar = Market.US
        condition: ClassVar = AlertCondition.ABOVE
        target_value: ClassVar = 200.0
        triggered: ClassVar = False
        triggered_at: ClassVar = None
        cooldown_until: ClassVar = None

    return MockAlert()


@pytest.fixture
def mock_notification():
    """Create a mock notification."""

    class MockNotification:
        id: ClassVar = uuid4()
        user_id: ClassVar = uuid4()
        type: ClassVar = NotificationType.PRICE_ALERT
        title: ClassVar = "AAPL Above $200"
        body: ClassVar = "AAPL has risen above $200.00. Current price: $205.00"
        data: ClassVar = {
            "ticker": "AAPL",
            "market": "US",
            "condition": "above",
            "target_value": 200.0,
            "current_price": 205.0,
            "alert_id": str(uuid4()),
            "grouped_count": 1,
        }
        read: ClassVar = False
        created_at: ClassVar = datetime.now() - timedelta(minutes=5)

    return MockNotification()


class TestNotificationGrouping:
    """Test notification grouping to prevent spam."""

    @pytest.mark.asyncio
    async def test_first_alert_creates_new_notification(self, mock_alert):
        """First alert should create a new notification (no grouping)."""
        mock_db = AsyncMock()
        mock_price_alert_dao = AsyncMock()
        mock_notification_dao = AsyncMock()

        # No recent notification exists
        mock_notification_dao.find_recent_by_ticker.return_value = None
        mock_notification_dao.create.return_value = AsyncMock(
            id=uuid4(), title="AAPL Above $200", data={"grouped_count": 1}
        )

        alert_service = AlertService(mock_price_alert_dao, mock_notification_dao)

        with patch(
            "backend.domains.analysis.api.connection_manager.connection_manager"
        ):
            await alert_service.trigger_alert(mock_db, mock_alert, 205.0)

            # Should create new notification
            mock_notification_dao.create.assert_called_once()
            # Should NOT update existing notification
            mock_notification_dao.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_second_alert_groups_with_recent(self, mock_alert, mock_notification):
        """Second alert within 15 minutes should group with first."""
        mock_db = AsyncMock()
        mock_price_alert_dao = AsyncMock()
        mock_notification_dao = AsyncMock()

        # Recent notification exists
        mock_notification_dao.find_recent_by_ticker.return_value = mock_notification
        mock_notification_dao.update.return_value = mock_notification

        alert_service = AlertService(mock_price_alert_dao, mock_notification_dao)

        with patch(
            "backend.domains.analysis.api.connection_manager.connection_manager"
        ):
            await alert_service.trigger_alert(mock_db, mock_alert, 210.0)

            # Should update existing notification
            mock_notification_dao.update.assert_called_once()
            # Should NOT create new notification
            mock_notification_dao.create.assert_not_called()

            # Verify grouped count incremented
            updated_notification = mock_notification_dao.update.call_args[0][0]
            assert updated_notification.data["grouped_count"] == 2

    @pytest.mark.asyncio
    async def test_grouped_notification_shows_count(
        self, mock_alert, mock_notification
    ):
        """Grouped notification should show count in title."""
        mock_db = AsyncMock()
        mock_price_alert_dao = AsyncMock()
        mock_notification_dao = AsyncMock()

        mock_notification_dao.find_recent_by_ticker.return_value = mock_notification
        mock_notification_dao.update.return_value = mock_notification

        alert_service = AlertService(mock_price_alert_dao, mock_notification_dao)

        with patch(
            "backend.domains.analysis.api.connection_manager.connection_manager"
        ):
            await alert_service.trigger_alert(mock_db, mock_alert, 210.0)

            updated_notification = mock_notification_dao.update.call_args[0][0]
            # Title should include count: "AAPL Above $200 (2x)"
            assert "(2x)" in updated_notification.title

    @pytest.mark.asyncio
    async def test_different_ticker_creates_separate_notification(self, mock_alert):
        """Alert for different ticker should create separate notification."""
        mock_db = AsyncMock()
        mock_price_alert_dao = AsyncMock()
        mock_notification_dao = AsyncMock()

        # Recent notification exists but for different ticker
        mock_notification_dao.find_recent_by_ticker.return_value = None
        mock_notification_dao.create.return_value = AsyncMock(id=uuid4())

        # Change ticker to MSFT
        mock_alert.ticker = "MSFT"

        alert_service = AlertService(mock_price_alert_dao, mock_notification_dao)

        with patch(
            "backend.domains.analysis.api.connection_manager.connection_manager"
        ):
            await alert_service.trigger_alert(mock_db, mock_alert, 350.0)

            # Should create new notification (different ticker)
            mock_notification_dao.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_old_notification_not_grouped(self, mock_alert, mock_notification):
        """Alert after 15 minute window should create new notification."""
        mock_db = AsyncMock()
        mock_price_alert_dao = AsyncMock()
        mock_notification_dao = AsyncMock()

        # Notification is too old (20 minutes)
        mock_notification.created_at = datetime.now() - timedelta(minutes=20)

        # find_recent_by_ticker uses 15-minute window, so returns None
        mock_notification_dao.find_recent_by_ticker.return_value = None
        mock_notification_dao.create.return_value = AsyncMock(id=uuid4())

        alert_service = AlertService(mock_price_alert_dao, mock_notification_dao)

        with patch(
            "backend.domains.analysis.api.connection_manager.connection_manager"
        ):
            await alert_service.trigger_alert(mock_db, mock_alert, 210.0)

            # Should create new notification (old one expired)
            mock_notification_dao.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_grouped_notification_marks_unread(
        self, mock_alert, mock_notification
    ):
        """Grouped notification should be marked as unread."""
        mock_db = AsyncMock()
        mock_price_alert_dao = AsyncMock()
        mock_notification_dao = AsyncMock()

        # Mark existing notification as read
        mock_notification.read = True

        mock_notification_dao.find_recent_by_ticker.return_value = mock_notification
        mock_notification_dao.update.return_value = mock_notification

        alert_service = AlertService(mock_price_alert_dao, mock_notification_dao)

        with patch(
            "backend.domains.analysis.api.connection_manager.connection_manager"
        ):
            await alert_service.trigger_alert(mock_db, mock_alert, 210.0)

            updated_notification = mock_notification_dao.update.call_args[0][0]
            # Should mark as unread again
            assert updated_notification.read is False

    @pytest.mark.asyncio
    async def test_grouped_notification_updates_timestamp(
        self, mock_alert, mock_notification
    ):
        """Grouped notification should update created_at timestamp."""
        mock_db = AsyncMock()
        mock_price_alert_dao = AsyncMock()
        mock_notification_dao = AsyncMock()

        old_timestamp = datetime.now() - timedelta(minutes=10)
        mock_notification.created_at = old_timestamp

        mock_notification_dao.find_recent_by_ticker.return_value = mock_notification
        mock_notification_dao.update.return_value = mock_notification

        alert_service = AlertService(mock_price_alert_dao, mock_notification_dao)

        with patch(
            "backend.domains.analysis.api.connection_manager.connection_manager"
        ):
            await alert_service.trigger_alert(mock_db, mock_alert, 210.0)

            updated_notification = mock_notification_dao.update.call_args[0][0]
            # Should update timestamp to now
            assert updated_notification.created_at > old_timestamp
