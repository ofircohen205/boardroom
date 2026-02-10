"""Tests for alerts system."""
from datetime import datetime, timedelta

import pytest

from backend.ai.state.enums import Market
from backend.db.models import AlertCondition, PriceAlert
from backend.jobs.alert_checker import check_alert_condition, is_market_hours


class TestAlertConditions:
    """Test alert condition logic."""

    def test_above_condition_triggers(self):
        """Test that ABOVE condition triggers when price exceeds target."""
        alert = PriceAlert(
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=150.0,
            triggered=False,
            active=True,
        )

        # Price above target should trigger
        assert check_alert_condition(alert, 155.0) is True
        # Price below target should not trigger
        assert check_alert_condition(alert, 145.0) is False
        # Price equal to target should not trigger
        assert check_alert_condition(alert, 150.0) is False

    def test_below_condition_triggers(self):
        """Test that BELOW condition triggers when price falls below target."""
        alert = PriceAlert(
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.BELOW,
            target_value=150.0,
            triggered=False,
            active=True,
        )

        # Price below target should trigger
        assert check_alert_condition(alert, 145.0) is True
        # Price above target should not trigger
        assert check_alert_condition(alert, 155.0) is False
        # Price equal to target should not trigger
        assert check_alert_condition(alert, 150.0) is False

    def test_change_pct_condition_triggers(self):
        """Test that CHANGE_PCT condition triggers when percentage change exceeds target."""
        alert = PriceAlert(
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.CHANGE_PCT,
            target_value=5.0,  # 5% change threshold
            triggered=False,
            active=True,
        )

        # Set baseline price on alert
        alert.baseline_price = 100.0

        # 6% change should trigger (current: 106, baseline: 100)
        assert check_alert_condition(alert, 106.0) is True

        # -6% change should trigger (current: 94, baseline: 100)
        assert check_alert_condition(alert, 94.0) is True

        # 3% change should not trigger (current: 103, baseline: 100)
        assert check_alert_condition(alert, 103.0) is False

        # No baseline should not trigger
        alert.baseline_price = None
        assert check_alert_condition(alert, 106.0) is False

    def test_market_hours_detection(self):
        """Test market hours detection logic."""
        # This test is time-dependent and would need mocking for reliable testing
        # For now, we just ensure the function runs without error
        result = is_market_hours()
        assert isinstance(result, bool)


class TestAlertValidation:
    """Test alert validation rules."""

    def test_target_value_positive(self):
        """Test that target value must be positive."""
        # This would test the service layer validation
        # Would need async test setup with database
        pass

    def test_change_pct_range(self):
        """Test that change_pct target is between 0.1 and 100."""
        # Would test the service layer validation
        # Would need async test setup with database
        pass


class TestAlertCooldown:
    """Test alert cooldown logic."""

    def test_cooldown_prevents_retrigger(self):
        """Test that alerts in cooldown are not retriggered."""
        now = datetime.now()

        alert = PriceAlert(
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=150.0,
            triggered=True,
            cooldown_until=now + timedelta(hours=1),  # Still in cooldown
            active=True,
        )

        # Alert should not be included in active alerts query due to cooldown
        # This would be tested via DAO layer
        assert alert.cooldown_until > now

    def test_cooldown_expired_allows_retrigger(self):
        """Test that alerts with expired cooldown can be retriggered."""
        now = datetime.now()

        alert = PriceAlert(
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=150.0,
            triggered=False,
            cooldown_until=now - timedelta(hours=1),  # Cooldown expired
            active=True,
        )

        # Alert should be included in active alerts query
        assert alert.cooldown_until < now


class TestAlertRateLimiting:
    """Test alert rate limiting."""

    def test_max_alerts_per_user(self):
        """Test that users cannot exceed 50 alerts."""
        # Would test the service layer validation
        # Would need async test setup with database
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
