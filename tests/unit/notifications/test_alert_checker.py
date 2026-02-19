# tests/unit/notifications/test_alert_checker.py
"""Unit tests for backend.shared.jobs.alert_checker."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.shared.db.models import AlertCondition
from backend.shared.jobs.alert_checker import (
    check_alert_condition,
    check_price_alerts,
    is_market_hours,
    is_tase_market_hours,
    is_us_market_hours,
)


def make_alert(condition, target_value, baseline_price=None):
    """Create a mock PriceAlert for check_alert_condition tests."""
    alert = MagicMock()
    alert.condition = condition
    alert.target_value = target_value
    alert.baseline_price = baseline_price
    alert.id = "test-alert-id"
    alert.ticker = "AAPL"
    return alert


@pytest.fixture
def mock_db():
    """Minimal async DB session mock."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


class TestCheckAlertConditionAbove:
    def test_above_price_above_target_returns_true(self):
        alert = make_alert(AlertCondition.ABOVE, 150.0)
        assert check_alert_condition(alert, 155.0) is True

    def test_above_price_below_target_returns_false(self):
        alert = make_alert(AlertCondition.ABOVE, 150.0)
        assert check_alert_condition(alert, 140.0) is False

    def test_above_price_equal_to_target_returns_false(self):
        alert = make_alert(AlertCondition.ABOVE, 150.0)
        assert check_alert_condition(alert, 150.0) is False


class TestCheckAlertConditionBelow:
    def test_below_price_below_target_returns_true(self):
        alert = make_alert(AlertCondition.BELOW, 100.0)
        assert check_alert_condition(alert, 95.0) is True

    def test_below_price_above_target_returns_false(self):
        alert = make_alert(AlertCondition.BELOW, 100.0)
        assert check_alert_condition(alert, 110.0) is False

    def test_below_price_equal_to_target_returns_false(self):
        alert = make_alert(AlertCondition.BELOW, 100.0)
        assert check_alert_condition(alert, 100.0) is False


class TestCheckAlertConditionChangePct:
    def test_change_pct_exceeds_threshold_returns_true(self):
        alert = make_alert(AlertCondition.CHANGE_PCT, 10.0, baseline_price=100.0)
        assert check_alert_condition(alert, 115.0) is True

    def test_change_pct_below_threshold_returns_false(self):
        alert = make_alert(AlertCondition.CHANGE_PCT, 5.0, baseline_price=100.0)
        assert check_alert_condition(alert, 103.0) is False

    def test_change_pct_baseline_is_none_returns_false(self):
        alert = make_alert(AlertCondition.CHANGE_PCT, 5.0, baseline_price=None)
        assert check_alert_condition(alert, 110.0) is False

    def test_change_pct_baseline_is_zero_returns_false(self):
        alert = make_alert(AlertCondition.CHANGE_PCT, 5.0, baseline_price=0)
        assert check_alert_condition(alert, 110.0) is False

    def test_change_pct_negative_movement_uses_abs(self):
        alert = make_alert(AlertCondition.CHANGE_PCT, 10.0, baseline_price=100.0)
        assert check_alert_condition(alert, 85.0) is True

    def test_change_pct_exactly_at_threshold_returns_true(self):
        alert = make_alert(AlertCondition.CHANGE_PCT, 10.0, baseline_price=100.0)
        assert check_alert_condition(alert, 110.0) is True


class TestCheckAlertConditionUnknown:
    def test_unknown_condition_returns_false(self):
        alert = make_alert("SOME_UNKNOWN_CONDITION", 100.0)
        assert check_alert_condition(alert, 200.0) is False


class TestMarketHoursReturnType:
    def test_is_us_market_hours_returns_bool(self):
        result = is_us_market_hours()
        assert isinstance(result, bool)

    def test_is_tase_market_hours_returns_bool(self):
        result = is_tase_market_hours()
        assert isinstance(result, bool)


class TestIsMarketHoursDelegation:
    def test_is_market_hours_us_delegates_to_us_function(self):
        with patch(
            "backend.shared.jobs.alert_checker.is_us_market_hours", return_value=True
        ) as mock_us:
            result = is_market_hours("US")
        assert result is True
        mock_us.assert_called_once()

    def test_is_market_hours_tase_delegates_to_tase_function(self):
        with patch(
            "backend.shared.jobs.alert_checker.is_tase_market_hours", return_value=False
        ) as mock_tase:
            result = is_market_hours("TASE")
        assert result is False
        mock_tase.assert_called_once()

    def test_is_market_hours_defaults_to_us_when_unknown_market(self):
        with patch(
            "backend.shared.jobs.alert_checker.is_us_market_hours", return_value=True
        ) as mock_us:
            result = is_market_hours("UNKNOWN")
        assert result is True
        mock_us.assert_called_once()


class TestCheckPriceAlertsNoTickers:
    async def test_returns_success_with_zero_counts_when_no_tickers(self, mock_db):
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService"),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(return_value=[])
            mock_dao_cls.return_value = mock_dao
            result = await check_price_alerts(mock_db)
        assert result["success"] is True
        assert result["alerts_checked"] == 0
        assert result["alerts_triggered"] == 0


class TestCheckPriceAlertsAllMarketsClosed:
    async def test_returns_skipped_all_markets_closed(self, mock_db):
        market_mock = MagicMock()
        market_mock.value = "US"
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService"),
            patch(
                "backend.shared.jobs.alert_checker.is_us_market_hours",
                return_value=False,
            ),
            patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(
                return_value=[("AAPL", market_mock)]
            )
            mock_dao_cls.return_value = mock_dao
            result = await check_price_alerts(mock_db)
        assert result["success"] is True
        assert result["alerts_checked"] == 0
        assert result["alerts_triggered"] == 0
        assert result.get("skipped") == "all_markets_closed"


class TestCheckPriceAlertsAlertTriggered:
    async def test_triggered_alert_increments_counter(self, mock_db):
        market_mock = MagicMock()
        market_mock.value = "US"
        alert = make_alert(AlertCondition.ABOVE, 100.0)
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService") as mock_svc_cls,
            patch(
                "backend.shared.jobs.alert_checker.get_market_data_client"
            ) as mock_mdc,
            patch(
                "backend.shared.jobs.alert_checker.is_us_market_hours",
                return_value=True,
            ),
            patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(
                return_value=[("AAPL", market_mock)]
            )
            mock_dao.get_active_alerts_for_ticker = AsyncMock(return_value=[alert])
            mock_dao_cls.return_value = mock_dao
            mock_svc = MagicMock()
            mock_svc.trigger_alert = AsyncMock()
            mock_svc_cls.return_value = mock_svc
            market_client = MagicMock()
            market_client.get_stock_data = AsyncMock(
                return_value={"current_price": 150.0}
            )
            mock_mdc.return_value = market_client
            result = await check_price_alerts(mock_db)
        assert result["success"] is True
        assert result["alerts_checked"] == 1
        assert result["alerts_triggered"] == 1
        mock_db.commit.assert_called_once()


class TestCheckPriceAlertsNoAlertsFire:
    async def test_no_alerts_triggered_when_condition_not_met(self, mock_db):
        market_mock = MagicMock()
        market_mock.value = "US"
        alert = make_alert(AlertCondition.ABOVE, 100.0)
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService") as mock_svc_cls,
            patch(
                "backend.shared.jobs.alert_checker.get_market_data_client"
            ) as mock_mdc,
            patch(
                "backend.shared.jobs.alert_checker.is_us_market_hours",
                return_value=True,
            ),
            patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(
                return_value=[("AAPL", market_mock)]
            )
            mock_dao.get_active_alerts_for_ticker = AsyncMock(return_value=[alert])
            mock_dao_cls.return_value = mock_dao
            mock_svc_cls.return_value = MagicMock()
            market_client = MagicMock()
            market_client.get_stock_data = AsyncMock(
                return_value={"current_price": 90.0}
            )
            mock_mdc.return_value = market_client
            result = await check_price_alerts(mock_db)
        assert result["success"] is True
        assert result["alerts_checked"] == 1
        assert result["alerts_triggered"] == 0


class TestCheckPriceAlertsExceptionHandling:
    async def test_returns_failure_when_dao_raises(self, mock_db):
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService"),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(
                side_effect=RuntimeError("DB connection lost")
            )
            mock_dao_cls.return_value = mock_dao
            result = await check_price_alerts(mock_db)
        assert result["success"] is False
        assert "DB connection lost" in result["error"]
        assert result["alerts_checked"] == 0
        assert result["alerts_triggered"] == 0
        mock_db.rollback.assert_called_once()

    async def test_skips_ticker_when_price_fetch_fails(self, mock_db):
        market_mock = MagicMock()
        market_mock.value = "US"
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService") as mock_svc_cls,
            patch(
                "backend.shared.jobs.alert_checker.get_market_data_client"
            ) as mock_mdc,
            patch(
                "backend.shared.jobs.alert_checker.is_us_market_hours",
                return_value=True,
            ),
            patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(
                return_value=[("AAPL", market_mock)]
            )
            mock_dao.get_active_alerts_for_ticker = AsyncMock(return_value=[])
            mock_dao_cls.return_value = mock_dao
            mock_svc_cls.return_value = MagicMock()
            market_client = MagicMock()
            market_client.get_stock_data = AsyncMock(
                side_effect=Exception("Network error")
            )
            mock_mdc.return_value = market_client
            result = await check_price_alerts(mock_db)
        assert result["success"] is True
        assert result["alerts_triggered"] == 0

    async def test_continues_when_trigger_alert_raises(self, mock_db):
        market_mock = MagicMock()
        market_mock.value = "US"
        alert = make_alert(AlertCondition.ABOVE, 100.0)
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService") as mock_svc_cls,
            patch(
                "backend.shared.jobs.alert_checker.get_market_data_client"
            ) as mock_mdc,
            patch(
                "backend.shared.jobs.alert_checker.is_us_market_hours",
                return_value=True,
            ),
            patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(
                return_value=[("AAPL", market_mock)]
            )
            mock_dao.get_active_alerts_for_ticker = AsyncMock(return_value=[alert])
            mock_dao_cls.return_value = mock_dao
            mock_svc = MagicMock()
            mock_svc.trigger_alert = AsyncMock(
                side_effect=Exception("Notification service unavailable")
            )
            mock_svc_cls.return_value = mock_svc
            market_client = MagicMock()
            market_client.get_stock_data = AsyncMock(
                return_value={"current_price": 150.0}
            )
            mock_mdc.return_value = market_client
            result = await check_price_alerts(mock_db)
        assert result["success"] is True
        assert result["alerts_checked"] == 1
        assert result["alerts_triggered"] == 0


class TestCheckPriceAlertsTaseMarket:
    async def test_tase_ticker_included_when_tase_is_open(self, mock_db):
        market_mock = MagicMock()
        market_mock.value = "TASE"
        alert = make_alert(AlertCondition.BELOW, 200.0)
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService") as mock_svc_cls,
            patch(
                "backend.shared.jobs.alert_checker.get_market_data_client"
            ) as mock_mdc,
            patch(
                "backend.shared.jobs.alert_checker.is_us_market_hours",
                return_value=False,
            ),
            patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=True,
            ),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(
                return_value=[("TEVA", market_mock)]
            )
            mock_dao.get_active_alerts_for_ticker = AsyncMock(return_value=[alert])
            mock_dao_cls.return_value = mock_dao
            mock_svc = MagicMock()
            mock_svc.trigger_alert = AsyncMock()
            mock_svc_cls.return_value = mock_svc
            market_client = MagicMock()
            market_client.get_stock_data = AsyncMock(
                return_value={"current_price": 150.0}
            )
            mock_mdc.return_value = market_client
            result = await check_price_alerts(mock_db)
        assert result["success"] is True
        assert result["alerts_checked"] == 1
        assert result["alerts_triggered"] == 1

    async def test_tase_ticker_skipped_when_tase_is_closed(self, mock_db):
        market_mock = MagicMock()
        market_mock.value = "TASE"
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService"),
            patch(
                "backend.shared.jobs.alert_checker.is_us_market_hours",
                return_value=False,
            ),
            patch(
                "backend.shared.jobs.alert_checker.is_tase_market_hours",
                return_value=False,
            ),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(
                return_value=[("TEVA", market_mock)]
            )
            mock_dao_cls.return_value = mock_dao
            result = await check_price_alerts(mock_db)
        assert result["success"] is True
        assert result.get("skipped") == "all_markets_closed"


class TestCheckPriceAlertsReturnShape:
    async def test_success_result_has_required_keys(self, mock_db):
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService"),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(return_value=[])
            mock_dao_cls.return_value = mock_dao
            result = await check_price_alerts(mock_db)
        assert "success" in result
        assert "alerts_checked" in result
        assert "alerts_triggered" in result
        assert "duration_seconds" in result

    async def test_failure_result_has_required_keys(self, mock_db):
        with (
            patch("backend.shared.jobs.alert_checker.PriceAlertDAO") as mock_dao_cls,
            patch("backend.shared.jobs.alert_checker.NotificationDAO"),
            patch("backend.shared.jobs.alert_checker.AlertService"),
        ):
            mock_dao = MagicMock()
            mock_dao.get_all_active_tickers = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_dao_cls.return_value = mock_dao
            result = await check_price_alerts(mock_db)
        assert result["success"] is False
        assert "error" in result
        assert "alerts_checked" in result
        assert "alerts_triggered" in result
