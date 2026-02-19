# tests/unit/test_services_alert.py
"""Unit tests for AlertService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.domains.notifications.services.alert_service import (
    MAX_ALERTS_PER_USER,
    AlertService,
    AlertValidationError,
)
from backend.shared.ai.state.enums import Market
from backend.shared.db.models import (
    AlertCondition,
    Notification,
    NotificationType,
    PriceAlert,
)
from backend.shared.services.base import BaseService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_price_alert_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.count_user_alerts = AsyncMock(return_value=0)
    dao.create = AsyncMock()
    dao.get_user_alerts = AsyncMock()
    dao.get_by_id = AsyncMock()
    dao.update = AsyncMock()
    dao.delete = AsyncMock()
    return dao


@pytest.fixture
def mock_notification_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.create = AsyncMock()
    dao.get_user_notifications = AsyncMock()
    dao.get_by_id = AsyncMock()
    dao.update = AsyncMock()
    dao.find_recent_by_ticker = AsyncMock(return_value=None)
    return dao


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def alert_service(mock_price_alert_dao, mock_notification_dao):
    return AlertService(mock_price_alert_dao, mock_notification_dao)


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
    alert.target_value = 200.0
    alert.triggered = False
    alert.active = True
    alert.data = {}
    return alert


@pytest.fixture
def sample_notification(sample_user_id):
    notification = MagicMock(spec=Notification)
    notification.id = uuid4()
    notification.user_id = sample_user_id
    notification.type = NotificationType.PRICE_ALERT
    notification.title = "AAPL Above $200.0"
    notification.body = "AAPL has risen above $200.00. Current price: $205.00"
    notification.data = {
        "ticker": "AAPL",
        "market": "us",
        "condition": "above",
        "target_value": 200.0,
        "current_price": 205.0,
        "alert_id": str(uuid4()),
        "grouped_count": 1,
    }
    notification.read = False
    notification.created_at = datetime.now()
    return notification


# ---------------------------------------------------------------------------
# Service initialisation
# ---------------------------------------------------------------------------


def test_daos_stored_on_service(mock_price_alert_dao, mock_notification_dao):
    """Constructor stores both DAOs on the service instance."""
    service = AlertService(mock_price_alert_dao, mock_notification_dao)
    assert service.price_alert_dao is mock_price_alert_dao
    assert service.notification_dao is mock_notification_dao


def test_inherits_from_base_service(mock_price_alert_dao, mock_notification_dao):
    """AlertService inherits from BaseService."""
    service = AlertService(mock_price_alert_dao, mock_notification_dao)
    assert isinstance(service, BaseService)


# ---------------------------------------------------------------------------
# create_price_alert - success path
# ---------------------------------------------------------------------------


async def test_create_price_alert_success(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id, sample_alert
):
    """Happy path: alert is created when user is under the rate limit."""
    mock_price_alert_dao.count_user_alerts.return_value = 0
    mock_price_alert_dao.create.return_value = sample_alert

    result = await alert_service.create_price_alert(
        db=mock_db,
        user_id=sample_user_id,
        ticker="aapl",
        market=Market.US,
        condition=AlertCondition.ABOVE,
        target_value=200.0,
    )

    assert result is sample_alert
    mock_price_alert_dao.count_user_alerts.assert_awaited_once_with(sample_user_id)
    mock_price_alert_dao.create.assert_awaited_once_with(
        user_id=sample_user_id,
        ticker="AAPL",  # should be uppercased
        market=Market.US,
        condition=AlertCondition.ABOVE,
        target_value=200.0,
        baseline_price=None,
        triggered=False,
        active=True,
    )


async def test_create_price_alert_ticker_uppercased(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id, sample_alert
):
    """Ticker is converted to uppercase before creating the alert."""
    mock_price_alert_dao.count_user_alerts.return_value = 5
    mock_price_alert_dao.create.return_value = sample_alert

    await alert_service.create_price_alert(
        db=mock_db,
        user_id=sample_user_id,
        ticker="tsla",
        market=Market.US,
        condition=AlertCondition.BELOW,
        target_value=150.0,
    )

    call_kwargs = mock_price_alert_dao.create.call_args.kwargs
    assert call_kwargs["ticker"] == "TSLA"


async def test_create_price_alert_below_condition(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id, sample_alert
):
    """BELOW condition alert is created successfully."""
    mock_price_alert_dao.count_user_alerts.return_value = 0
    mock_price_alert_dao.create.return_value = sample_alert

    result = await alert_service.create_price_alert(
        db=mock_db,
        user_id=sample_user_id,
        ticker="MSFT",
        market=Market.US,
        condition=AlertCondition.BELOW,
        target_value=300.0,
    )

    assert result is sample_alert


async def test_create_price_alert_at_limit_minus_one_succeeds(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id, sample_alert
):
    """Alert creation succeeds when count is one below the limit (49)."""
    mock_price_alert_dao.count_user_alerts.return_value = MAX_ALERTS_PER_USER - 1
    mock_price_alert_dao.create.return_value = sample_alert

    result = await alert_service.create_price_alert(
        db=mock_db,
        user_id=sample_user_id,
        ticker="AAPL",
        market=Market.US,
        condition=AlertCondition.ABOVE,
        target_value=200.0,
    )

    assert result is sample_alert


# ---------------------------------------------------------------------------
# create_price_alert - rate limit (count >= 50)
# ---------------------------------------------------------------------------


async def test_create_price_alert_rate_limit_exact(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id
):
    """AlertValidationError raised when count == MAX_ALERTS_PER_USER (50)."""
    mock_price_alert_dao.count_user_alerts.return_value = MAX_ALERTS_PER_USER

    with pytest.raises(AlertValidationError, match="50"):
        await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=200.0,
        )

    mock_price_alert_dao.create.assert_not_awaited()


async def test_create_price_alert_rate_limit_exceeded(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id
):
    """AlertValidationError raised when count > MAX_ALERTS_PER_USER."""
    mock_price_alert_dao.count_user_alerts.return_value = MAX_ALERTS_PER_USER + 5

    with pytest.raises(AlertValidationError):
        await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=200.0,
        )

    mock_price_alert_dao.create.assert_not_awaited()


# ---------------------------------------------------------------------------
# create_price_alert - invalid target value (<= 0)
# ---------------------------------------------------------------------------


async def test_create_price_alert_zero_target_value(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id
):
    """AlertValidationError raised when target_value is 0."""
    mock_price_alert_dao.count_user_alerts.return_value = 0

    with pytest.raises(AlertValidationError, match="greater than 0"):
        await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.ABOVE,
            target_value=0,
        )

    mock_price_alert_dao.create.assert_not_awaited()


async def test_create_price_alert_negative_target_value(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id
):
    """AlertValidationError raised when target_value is negative."""
    mock_price_alert_dao.count_user_alerts.return_value = 0

    with pytest.raises(AlertValidationError, match="greater than 0"):
        await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.BELOW,
            target_value=-50.0,
        )

    mock_price_alert_dao.create.assert_not_awaited()


# ---------------------------------------------------------------------------
# create_price_alert - CHANGE_PCT condition validation
# ---------------------------------------------------------------------------


async def test_create_price_alert_change_pct_below_min(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id
):
    """AlertValidationError raised when CHANGE_PCT target is below 0.1."""
    mock_price_alert_dao.count_user_alerts.return_value = 0

    with pytest.raises(AlertValidationError, match=r"0\.1 and 100"):
        await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.CHANGE_PCT,
            target_value=0.05,
        )

    mock_price_alert_dao.create.assert_not_awaited()


async def test_create_price_alert_change_pct_above_max(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id
):
    """AlertValidationError raised when CHANGE_PCT target exceeds 100."""
    mock_price_alert_dao.count_user_alerts.return_value = 0

    with pytest.raises(AlertValidationError, match=r"0\.1 and 100"):
        await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.CHANGE_PCT,
            target_value=101.0,
        )

    mock_price_alert_dao.create.assert_not_awaited()


async def test_create_price_alert_change_pct_valid(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id, sample_alert
):
    """CHANGE_PCT alert with valid percentage (0.1-100) proceeds to fetch baseline."""
    mock_price_alert_dao.count_user_alerts.return_value = 0
    mock_price_alert_dao.create.return_value = sample_alert

    mock_market_client = MagicMock()
    mock_market_client.get_stock_data = AsyncMock(return_value={"current_price": 180.0})

    with patch(
        "backend.shared.ai.tools.market_data.get_market_data_client",
        return_value=mock_market_client,
    ):
        result = await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.CHANGE_PCT,
            target_value=5.0,
        )

    assert result is sample_alert
    call_kwargs = mock_price_alert_dao.create.call_args.kwargs
    assert call_kwargs["baseline_price"] == 180.0


async def test_create_price_alert_change_pct_baseline_fetch_fails(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id, sample_alert
):
    """When baseline price fetch fails, alert is still created with baseline_price=None."""
    mock_price_alert_dao.count_user_alerts.return_value = 0
    mock_price_alert_dao.create.return_value = sample_alert

    mock_market_client = MagicMock()
    mock_market_client.get_stock_data = AsyncMock(
        side_effect=Exception("API unavailable")
    )

    with patch(
        "backend.shared.ai.tools.market_data.get_market_data_client",
        return_value=mock_market_client,
    ):
        result = await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.CHANGE_PCT,
            target_value=5.0,
        )

    assert result is sample_alert
    call_kwargs = mock_price_alert_dao.create.call_args.kwargs
    assert call_kwargs["baseline_price"] is None


async def test_create_price_alert_change_pct_min_boundary(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id, sample_alert
):
    """CHANGE_PCT at exact minimum boundary (0.1) is valid."""
    mock_price_alert_dao.count_user_alerts.return_value = 0
    mock_price_alert_dao.create.return_value = sample_alert

    mock_market_client = MagicMock()
    mock_market_client.get_stock_data = AsyncMock(return_value={"current_price": 100.0})

    with patch(
        "backend.shared.ai.tools.market_data.get_market_data_client",
        return_value=mock_market_client,
    ):
        result = await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.CHANGE_PCT,
            target_value=0.1,
        )

    assert result is sample_alert


async def test_create_price_alert_change_pct_max_boundary(
    alert_service, mock_price_alert_dao, mock_db, sample_user_id, sample_alert
):
    """CHANGE_PCT at exact maximum boundary (100) is valid."""
    mock_price_alert_dao.count_user_alerts.return_value = 0
    mock_price_alert_dao.create.return_value = sample_alert

    mock_market_client = MagicMock()
    mock_market_client.get_stock_data = AsyncMock(return_value={"current_price": 100.0})

    with patch(
        "backend.shared.ai.tools.market_data.get_market_data_client",
        return_value=mock_market_client,
    ):
        result = await alert_service.create_price_alert(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            market=Market.US,
            condition=AlertCondition.CHANGE_PCT,
            target_value=100.0,
        )

    assert result is sample_alert


# ---------------------------------------------------------------------------
# trigger_alert - success with new notification (no grouping)
# ---------------------------------------------------------------------------


async def test_trigger_alert_creates_notification_above(
    alert_service,
    mock_price_alert_dao,
    mock_notification_dao,
    mock_db,
    sample_alert,
    sample_notification,
):
    """ABOVE condition: new notification is created and alert is updated."""
    sample_alert.condition = AlertCondition.ABOVE
    sample_alert.target_value = 200.0
    mock_notification_dao.find_recent_by_ticker.return_value = None
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        result = await alert_service.trigger_alert(
            db=mock_db, alert=sample_alert, current_price=205.0
        )

    assert result is sample_notification
    mock_price_alert_dao.update.assert_awaited_once_with(sample_alert)
    assert sample_alert.triggered is True
    mock_notification_dao.create.assert_awaited_once()
    create_kwargs = mock_notification_dao.create.call_args.kwargs
    assert create_kwargs["user_id"] == sample_alert.user_id
    assert create_kwargs["type"] == NotificationType.PRICE_ALERT
    assert "AAPL" in create_kwargs["title"]
    assert create_kwargs["data"]["grouped_count"] == 1


async def test_trigger_alert_creates_notification_below(
    alert_service,
    mock_price_alert_dao,
    mock_notification_dao,
    mock_db,
    sample_alert,
    sample_notification,
):
    """BELOW condition: notification title and body reflect below condition."""
    sample_alert.condition = AlertCondition.BELOW
    sample_alert.target_value = 150.0
    mock_notification_dao.find_recent_by_ticker.return_value = None
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.trigger_alert(
            db=mock_db, alert=sample_alert, current_price=145.0
        )

    create_kwargs = mock_notification_dao.create.call_args.kwargs
    assert "Below" in create_kwargs["title"]


async def test_trigger_alert_creates_notification_change_pct(
    alert_service,
    mock_price_alert_dao,
    mock_notification_dao,
    mock_db,
    sample_alert,
    sample_notification,
):
    """CHANGE_PCT condition: notification title includes percentage."""
    sample_alert.condition = AlertCondition.CHANGE_PCT
    sample_alert.target_value = 5.0
    mock_notification_dao.find_recent_by_ticker.return_value = None
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.trigger_alert(
            db=mock_db, alert=sample_alert, current_price=189.0
        )

    create_kwargs = mock_notification_dao.create.call_args.kwargs
    assert "Changed" in create_kwargs["title"]


async def test_trigger_alert_sends_websocket_notification(
    alert_service,
    mock_price_alert_dao,
    mock_notification_dao,
    mock_db,
    sample_alert,
    sample_notification,
):
    """WebSocket notification is sent after creating/updating the notification."""
    mock_notification_dao.find_recent_by_ticker.return_value = None
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.trigger_alert(
            db=mock_db, alert=sample_alert, current_price=205.0
        )

    mock_connection_manager.send_notification.assert_awaited_once()
    ws_call_kwargs = mock_connection_manager.send_notification.call_args.kwargs
    assert ws_call_kwargs["user_id"] == sample_alert.user_id


async def test_trigger_alert_websocket_failure_does_not_propagate(
    alert_service,
    mock_price_alert_dao,
    mock_notification_dao,
    mock_db,
    sample_alert,
    sample_notification,
):
    """WebSocket send failure does not raise — the notification is still returned."""
    mock_notification_dao.find_recent_by_ticker.return_value = None
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock(
        side_effect=Exception("WebSocket disconnected")
    )

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        result = await alert_service.trigger_alert(
            db=mock_db, alert=sample_alert, current_price=205.0
        )

    assert result is sample_notification


# ---------------------------------------------------------------------------
# trigger_alert - grouped notification (recent notification exists)
# ---------------------------------------------------------------------------


async def test_trigger_alert_groups_with_recent_notification(
    alert_service,
    mock_price_alert_dao,
    mock_notification_dao,
    mock_db,
    sample_alert,
    sample_notification,
):
    """When a recent notification exists, it is updated instead of creating new one."""
    existing_notification = MagicMock(spec=Notification)
    existing_notification.id = uuid4()
    existing_notification.data = {"grouped_count": 2}
    existing_notification.condition = AlertCondition.ABOVE
    mock_notification_dao.find_recent_by_ticker.return_value = existing_notification
    mock_notification_dao.update.return_value = existing_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        result = await alert_service.trigger_alert(
            db=mock_db, alert=sample_alert, current_price=210.0
        )

    assert result is existing_notification
    mock_notification_dao.update.assert_awaited_once_with(existing_notification)
    mock_notification_dao.create.assert_not_awaited()
    # grouped_count incremented to 3
    assert existing_notification.data["grouped_count"] == 3


async def test_trigger_alert_grouped_below_condition(
    alert_service,
    mock_price_alert_dao,
    mock_notification_dao,
    mock_db,
    sample_alert,
):
    """Grouped notification for BELOW condition has correct title format."""
    sample_alert.condition = AlertCondition.BELOW
    existing_notification = MagicMock(spec=Notification)
    existing_notification.id = uuid4()
    existing_notification.data = {"grouped_count": 1}
    mock_notification_dao.find_recent_by_ticker.return_value = existing_notification
    mock_notification_dao.update.return_value = existing_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.trigger_alert(
            db=mock_db, alert=sample_alert, current_price=140.0
        )

    assert "Below" in existing_notification.title


async def test_trigger_alert_grouped_change_pct_condition(
    alert_service,
    mock_price_alert_dao,
    mock_notification_dao,
    mock_db,
    sample_alert,
):
    """Grouped notification for CHANGE_PCT condition has correct title format."""
    sample_alert.condition = AlertCondition.CHANGE_PCT
    sample_alert.target_value = 5.0
    existing_notification = MagicMock(spec=Notification)
    existing_notification.id = uuid4()
    existing_notification.data = {"grouped_count": 1}
    mock_notification_dao.find_recent_by_ticker.return_value = existing_notification
    mock_notification_dao.update.return_value = existing_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.trigger_alert(
            db=mock_db, alert=sample_alert, current_price=189.0
        )

    assert "Changed" in existing_notification.title


async def test_trigger_alert_marks_grouped_notification_unread(
    alert_service,
    mock_price_alert_dao,
    mock_notification_dao,
    mock_db,
    sample_alert,
):
    """When grouping, the existing notification is marked as unread again."""
    existing_notification = MagicMock(spec=Notification)
    existing_notification.id = uuid4()
    existing_notification.data = {"grouped_count": 1}
    existing_notification.read = True
    mock_notification_dao.find_recent_by_ticker.return_value = existing_notification
    mock_notification_dao.update.return_value = existing_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.trigger_alert(
            db=mock_db, alert=sample_alert, current_price=210.0
        )

    assert existing_notification.read is False


# ---------------------------------------------------------------------------
# create_analysis_notification
# ---------------------------------------------------------------------------


async def test_create_analysis_notification_buy(
    alert_service, mock_notification_dao, mock_db, sample_user_id, sample_notification
):
    """BUY action creates ANALYSIS_COMPLETE notification with correct content."""
    sample_notification.type = NotificationType.ANALYSIS_COMPLETE
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        result = await alert_service.create_analysis_notification(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            action="BUY",
            confidence=0.85,
        )

    assert result is sample_notification
    create_kwargs = mock_notification_dao.create.call_args.kwargs
    assert create_kwargs["type"] == NotificationType.ANALYSIS_COMPLETE
    assert "BUY" in create_kwargs["title"]
    assert "AAPL" in create_kwargs["title"]
    assert create_kwargs["data"]["action"] == "BUY"
    assert create_kwargs["data"]["confidence"] == 0.85
    assert create_kwargs["data"]["vetoed"] is False


async def test_create_analysis_notification_vetoed(
    alert_service, mock_notification_dao, mock_db, sample_user_id, sample_notification
):
    """Vetoed decision creates VETO_ALERT notification type."""
    sample_notification.type = NotificationType.VETO_ALERT
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        result = await alert_service.create_analysis_notification(
            db=mock_db,
            user_id=sample_user_id,
            ticker="TSLA",
            action="HOLD",
            confidence=0.6,
            vetoed=True,
            veto_reason="Sector concentration exceeded 30%",
        )

    assert result is sample_notification
    create_kwargs = mock_notification_dao.create.call_args.kwargs
    assert create_kwargs["type"] == NotificationType.VETO_ALERT
    assert "VETOED" in create_kwargs["title"]
    assert "Sector concentration exceeded 30%" in create_kwargs["body"]
    assert create_kwargs["data"]["vetoed"] is True
    assert create_kwargs["data"]["veto_reason"] == "Sector concentration exceeded 30%"


async def test_create_analysis_notification_sell(
    alert_service, mock_notification_dao, mock_db, sample_user_id, sample_notification
):
    """SELL action creates ANALYSIS_COMPLETE notification."""
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.create_analysis_notification(
            db=mock_db,
            user_id=sample_user_id,
            ticker="MSFT",
            action="SELL",
            confidence=0.72,
        )

    create_kwargs = mock_notification_dao.create.call_args.kwargs
    assert create_kwargs["type"] == NotificationType.ANALYSIS_COMPLETE
    assert "SELL" in create_kwargs["title"]


async def test_create_analysis_notification_confidence_formatted(
    alert_service, mock_notification_dao, mock_db, sample_user_id, sample_notification
):
    """Confidence is formatted as percentage in the notification body."""
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.create_analysis_notification(
            db=mock_db,
            user_id=sample_user_id,
            ticker="NVDA",
            action="BUY",
            confidence=0.90,
        )

    create_kwargs = mock_notification_dao.create.call_args.kwargs
    assert "90%" in create_kwargs["body"]


async def test_create_analysis_notification_websocket_failure_does_not_propagate(
    alert_service, mock_notification_dao, mock_db, sample_user_id, sample_notification
):
    """WebSocket failure during analysis notification does not raise."""
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock(
        side_effect=Exception("connection reset")
    )

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        result = await alert_service.create_analysis_notification(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            action="HOLD",
            confidence=0.55,
        )

    assert result is sample_notification


async def test_create_analysis_notification_default_vetoed_false(
    alert_service, mock_notification_dao, mock_db, sample_user_id, sample_notification
):
    """vetoed defaults to False when not provided."""
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.create_analysis_notification(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            action="BUY",
            confidence=0.88,
        )

    create_kwargs = mock_notification_dao.create.call_args.kwargs
    assert create_kwargs["data"]["vetoed"] is False
    assert create_kwargs["data"]["veto_reason"] is None


async def test_create_analysis_notification_sends_websocket(
    alert_service, mock_notification_dao, mock_db, sample_user_id, sample_notification
):
    """WebSocket notification is sent after creating the analysis notification."""
    mock_notification_dao.create.return_value = sample_notification

    mock_connection_manager = MagicMock()
    mock_connection_manager.send_notification = AsyncMock()

    with patch(
        "backend.domains.analysis.api.connection_manager.connection_manager",
        mock_connection_manager,
    ):
        await alert_service.create_analysis_notification(
            db=mock_db,
            user_id=sample_user_id,
            ticker="AAPL",
            action="BUY",
            confidence=0.88,
        )

    mock_connection_manager.send_notification.assert_awaited_once()
    ws_kwargs = mock_connection_manager.send_notification.call_args.kwargs
    assert ws_kwargs["user_id"] == sample_user_id


# ---------------------------------------------------------------------------
# MAX_ALERTS_PER_USER constant
# ---------------------------------------------------------------------------


def test_max_alerts_per_user_constant():
    """MAX_ALERTS_PER_USER is 50 as specified in business rules."""
    assert MAX_ALERTS_PER_USER == 50


# ---------------------------------------------------------------------------
# AlertValidationError
# ---------------------------------------------------------------------------


def test_alert_validation_error_is_exception():
    """AlertValidationError is a standard Exception subclass."""
    err = AlertValidationError("test error")
    assert isinstance(err, Exception)
    assert str(err) == "test error"
