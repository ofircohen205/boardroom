"""Integration tests for alert checker job."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from backend.shared.ai.state.enums import Market
from backend.shared.dao.alerts import NotificationDAO, PriceAlertDAO
from backend.shared.db.models import AlertCondition, NotificationType, User
from backend.shared.jobs.alert_checker import check_price_alerts


@pytest.mark.asyncio
class TestAlertCheckerJob:
    """Test the alert checker background job."""

    @pytest_asyncio.fixture
    async def test_user(self, test_db_session):
        """Create a test user."""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            password_hash="hashed",  # pragma: allowlist secret
            is_active=True,
        )
        test_db_session.add(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)
        return user

    async def test_alert_checker_skips_when_market_closed(self, test_db_session):
        """Test that alert checker skips execution when market is closed."""
        with patch(
            "backend.shared.jobs.alert_checker.is_us_market_hours", return_value=False
        ):
            with patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ):
                result = await check_price_alerts(test_db_session)

                assert result["success"] is True
                # When both markets are closed and no alerts exist, function returns early
                assert result["alerts_checked"] == 0
                assert result["alerts_triggered"] == 0

    async def test_alert_checker_no_active_alerts(self, test_db_session):
        """Test alert checker with no active alerts."""
        with patch(
            "backend.shared.jobs.alert_checker.is_us_market_hours", return_value=True
        ):
            with patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ):
                result = await check_price_alerts(test_db_session)

                assert result["success"] is True
                assert result["alerts_checked"] == 0
                assert result["alerts_triggered"] == 0

    async def test_alert_checker_triggers_above_alert(self, test_db_session, test_user):
        """Test that ABOVE alert triggers when price exceeds target."""
        alert_dao = PriceAlertDAO(test_db_session)

        # Create an alert that should trigger (target: $150, current: $160)
        alert = await alert_dao.create(
            user_id=test_user.id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=150.0,
            triggered=False,
            active=True,
        )

        # Mock market hours and price data
        with patch(
            "backend.shared.jobs.alert_checker.is_us_market_hours", return_value=True
        ):
            with patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ):
                with patch(
                    "backend.shared.jobs.alert_checker.get_market_data_client"
                ) as mock_client:
                    # Mock the market data client to return a price above the target
                    mock_instance = AsyncMock()
                    mock_instance.get_stock_data.return_value = {"current_price": 160.0}
                    mock_client.return_value = mock_instance

                    result = await check_price_alerts(test_db_session)

                    assert result["success"] is True
                    assert result["alerts_checked"] == 1
                    assert result["alerts_triggered"] == 1

                    # Verify alert was triggered
                    await test_db_session.refresh(alert)
                    assert alert.triggered is True
                    assert alert.triggered_at is not None
                    assert alert.cooldown_until is not None

                    # Verify notification was created
                    notification_dao = NotificationDAO(test_db_session)
                    notifications = await notification_dao.get_user_notifications(
                        test_user.id, limit=10
                    )
                    assert len(notifications) == 1
                    assert notifications[0].type == NotificationType.PRICE_ALERT
                    assert "AAPL" in notifications[0].title
                    assert "150" in notifications[0].body

    async def test_alert_checker_does_not_trigger_below_alert(
        self, test_db_session, test_user
    ):
        """Test that ABOVE alert does not trigger when price is below target."""
        alert_dao = PriceAlertDAO(test_db_session)

        # Create an alert that should NOT trigger (target: $150, current: $140)
        alert = await alert_dao.create(
            user_id=test_user.id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=150.0,
            triggered=False,
            active=True,
        )

        with patch(
            "backend.shared.jobs.alert_checker.is_us_market_hours", return_value=True
        ):
            with patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ):
                with patch(
                    "backend.shared.jobs.alert_checker.get_market_data_client"
                ) as mock_client:
                    mock_instance = AsyncMock()
                    mock_instance.get_stock_data.return_value = {"current_price": 140.0}
                    mock_client.return_value = mock_instance

                    result = await check_price_alerts(test_db_session)

                    assert result["success"] is True
                    assert result["alerts_checked"] == 1
                    assert result["alerts_triggered"] == 0

                    # Verify alert was not triggered
                    await test_db_session.refresh(alert)
                    assert alert.triggered is False

    async def test_alert_checker_respects_cooldown(self, test_db_session, test_user):
        """Test that alerts in cooldown are not checked."""
        alert_dao = PriceAlertDAO(test_db_session)

        # Create an alert that is in cooldown
        await alert_dao.create(
            user_id=test_user.id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=150.0,
            triggered=True,
            cooldown_until=datetime.now().replace(hour=23, minute=59),  # Future time
            active=True,
        )

        with patch(
            "backend.shared.jobs.alert_checker.is_us_market_hours", return_value=True
        ):
            with patch(
                "backend.shared.jobs.alert_checker.get_market_data_client"
            ) as mock_client:
                mock_instance = AsyncMock()
                mock_instance.get_stock_data.return_value = {"current_price": 160.0}
                mock_client.return_value = mock_instance

                result = await check_price_alerts(test_db_session)

                # Alert should not be checked because it's in cooldown
                assert result["success"] is True
                assert result["alerts_checked"] == 0
                assert result["alerts_triggered"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
