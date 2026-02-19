# tests/unit/test_api_notifications.py
"""Unit tests for notifications domain API endpoints.

Covers:
- backend/domains/notifications/api/alerts.py
- backend/domains/notifications/api/schedules.py
- backend/domains/notifications/api/endpoints.py
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def mock_user():
    """A mock User that does not require a real database session."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "notif-test@example.com"
    user.is_active = True
    return user


from backend.dependencies import get_alert_service, get_schedule_service
from backend.domains.notifications.services.alert_service import (
    AlertService,
    AlertValidationError,
)
from backend.domains.notifications.services.schedule_exceptions import (
    ScheduleError,
    ScheduleNotFoundError,
    ScheduleRateLimitError,
)
from backend.domains.notifications.services.schedule_service import ScheduleService
from backend.main import app
from backend.shared.ai.state.enums import Market
from backend.shared.auth.dependencies import get_current_user

BASE_ALERTS = "/api/alerts"
BASE_SCHEDULES = "/api/schedules"


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------


def _make_alert(user_id=None):
    alert = MagicMock()
    alert.id = uuid4()
    alert.user_id = user_id or uuid4()
    alert.ticker = "AAPL"
    alert.market = "US"
    alert.condition = "above"
    alert.target_value = 200.0
    alert.triggered = False
    alert.triggered_at = None
    alert.cooldown_until = None
    alert.active = True
    alert.created_at = datetime(2026, 1, 1, 12, 0, 0)
    return alert


def _make_schedule(user_id=None):
    schedule = MagicMock()
    schedule.id = uuid4()
    schedule.user_id = user_id or uuid4()
    schedule.ticker = "AAPL"
    schedule.market = Market.US
    schedule.frequency = "daily"
    schedule.last_run = None
    schedule.next_run = datetime(2026, 1, 2, 8, 0, 0)
    schedule.active = True
    schedule.created_at = datetime(2026, 1, 1, 12, 0, 0)
    return schedule


def _make_alert_service():
    svc = MagicMock(spec=AlertService)

    price_alert_dao = MagicMock()
    price_alert_dao.session = MagicMock()
    price_alert_dao.session.commit = AsyncMock()
    price_alert_dao.session.rollback = AsyncMock()
    price_alert_dao.get_user_alerts = AsyncMock(return_value=[])
    price_alert_dao.get_by_id = AsyncMock(return_value=None)
    price_alert_dao.update = AsyncMock()
    price_alert_dao.delete = AsyncMock()
    price_alert_dao.reset_alert = AsyncMock()
    svc.price_alert_dao = price_alert_dao

    notification_dao = MagicMock()
    notification_dao.session = MagicMock()
    svc.notification_dao = notification_dao

    svc.create_price_alert = AsyncMock()
    return svc


def _make_schedule_service():
    svc = MagicMock(spec=ScheduleService)

    schedule_dao = MagicMock()
    schedule_dao.session = MagicMock()
    schedule_dao.session.commit = AsyncMock()
    schedule_dao.session.rollback = AsyncMock()
    svc.schedule_dao = schedule_dao

    svc.create_scheduled_analysis = AsyncMock()
    svc.get_user_schedules = AsyncMock(return_value=[])
    svc.delete_schedule = AsyncMock(return_value=True)
    svc.toggle_schedule = AsyncMock()
    return svc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_alert_svc():
    return _make_alert_service()


@pytest.fixture
def mock_schedule_svc():
    return _make_schedule_service()


@pytest.fixture
async def alerts_client(mock_user, mock_alert_svc):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_alert_service] = lambda: mock_alert_svc
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def schedules_client(mock_user, mock_schedule_svc):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_schedule_service] = lambda: mock_schedule_svc
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


# ===========================================================================
# Alert API  (alerts.py)
# ===========================================================================


class TestCreateAlert:
    async def test_create_alert_success(self, alerts_client, mock_alert_svc, mock_user):
        alert = _make_alert(user_id=mock_user.id)
        mock_alert_svc.create_price_alert.return_value = alert

        resp = await alerts_client.post(
            BASE_ALERTS,
            json={
                "ticker": "AAPL",
                "market": "US",
                "condition": "above",
                "target_value": 200.0,
            },
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["condition"] == "above"
        assert data["target_value"] == 200.0
        mock_alert_svc.create_price_alert.assert_awaited_once()

    async def test_create_alert_validation_error_returns_400(
        self, alerts_client, mock_alert_svc
    ):
        mock_alert_svc.create_price_alert.side_effect = AlertValidationError(
            "Maximum alerts exceeded"
        )

        resp = await alerts_client.post(
            BASE_ALERTS,
            json={
                "ticker": "AAPL",
                "market": "US",
                "condition": "above",
                "target_value": 200.0,
            },
        )

        assert resp.status_code == 400
        assert "Maximum alerts exceeded" in resp.json()["detail"]

    async def test_create_alert_server_error_returns_500(
        self, alerts_client, mock_alert_svc
    ):
        mock_alert_svc.create_price_alert.side_effect = RuntimeError("DB failure")

        resp = await alerts_client.post(
            BASE_ALERTS,
            json={
                "ticker": "AAPL",
                "market": "US",
                "condition": "above",
                "target_value": 200.0,
            },
        )

        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to create alert"

    async def test_create_alert_invalid_market_returns_422(self, alerts_client):
        resp = await alerts_client.post(
            BASE_ALERTS,
            json={
                "ticker": "AAPL",
                "market": "INVALID",
                "condition": "above",
                "target_value": 200.0,
            },
        )

        assert resp.status_code == 422

    async def test_create_alert_invalid_condition_returns_422(self, alerts_client):
        resp = await alerts_client.post(
            BASE_ALERTS,
            json={
                "ticker": "AAPL",
                "market": "US",
                "condition": "invalid_cond",
                "target_value": 200.0,
            },
        )

        assert resp.status_code == 422

    async def test_create_alert_zero_target_value_returns_422(self, alerts_client):
        resp = await alerts_client.post(
            BASE_ALERTS,
            json={
                "ticker": "AAPL",
                "market": "US",
                "condition": "above",
                "target_value": 0,
            },
        )

        assert resp.status_code == 422


class TestListAlerts:
    async def test_list_alerts_empty(self, alerts_client, mock_alert_svc, mock_user):
        mock_alert_svc.price_alert_dao.get_user_alerts.return_value = []

        resp = await alerts_client.get(BASE_ALERTS)

        assert resp.status_code == 200
        assert resp.json() == []
        mock_alert_svc.price_alert_dao.get_user_alerts.assert_awaited_once_with(
            mock_user.id, active_only=True
        )

    async def test_list_alerts_returns_alerts(
        self, alerts_client, mock_alert_svc, mock_user
    ):
        alert = _make_alert(user_id=mock_user.id)
        mock_alert_svc.price_alert_dao.get_user_alerts.return_value = [alert]

        resp = await alerts_client.get(BASE_ALERTS)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["ticker"] == "AAPL"

    async def test_list_alerts_active_only_false(
        self, alerts_client, mock_alert_svc, mock_user
    ):
        mock_alert_svc.price_alert_dao.get_user_alerts.return_value = []

        resp = await alerts_client.get(BASE_ALERTS, params={"active_only": False})

        assert resp.status_code == 200
        mock_alert_svc.price_alert_dao.get_user_alerts.assert_awaited_once_with(
            mock_user.id, active_only=False
        )


class TestDeleteAlert:
    async def test_delete_alert_success(self, alerts_client, mock_alert_svc, mock_user):
        alert = _make_alert(user_id=mock_user.id)
        mock_alert_svc.price_alert_dao.get_by_id.return_value = alert

        resp = await alerts_client.delete(f"{BASE_ALERTS}/{alert.id}")

        assert resp.status_code == 204
        mock_alert_svc.price_alert_dao.delete.assert_awaited_once_with(alert.id)

    async def test_delete_alert_not_found_returns_404(
        self, alerts_client, mock_alert_svc
    ):
        mock_alert_svc.price_alert_dao.get_by_id.return_value = None

        resp = await alerts_client.delete(f"{BASE_ALERTS}/{uuid4()}")

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Alert not found"

    async def test_delete_alert_forbidden_returns_403(
        self, alerts_client, mock_alert_svc, mock_user
    ):
        other_user_alert = _make_alert(user_id=uuid4())
        mock_alert_svc.price_alert_dao.get_by_id.return_value = other_user_alert

        resp = await alerts_client.delete(f"{BASE_ALERTS}/{other_user_alert.id}")

        assert resp.status_code == 403
        assert "Not authorized" in resp.json()["detail"]


class TestResetAlert:
    async def test_reset_alert_success(self, alerts_client, mock_alert_svc, mock_user):
        alert = _make_alert(user_id=mock_user.id)
        alert.triggered = True
        mock_alert_svc.price_alert_dao.get_by_id.return_value = alert

        reset_alert = _make_alert(user_id=mock_user.id)
        reset_alert.triggered = False
        mock_alert_svc.price_alert_dao.reset_alert.return_value = reset_alert

        resp = await alerts_client.patch(f"{BASE_ALERTS}/{alert.id}/reset")

        assert resp.status_code == 200
        mock_alert_svc.price_alert_dao.reset_alert.assert_awaited_once_with(alert.id)

    async def test_reset_alert_not_found_returns_404(
        self, alerts_client, mock_alert_svc
    ):
        mock_alert_svc.price_alert_dao.get_by_id.return_value = None

        resp = await alerts_client.patch(f"{BASE_ALERTS}/{uuid4()}/reset")

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Alert not found"

    async def test_reset_alert_forbidden_returns_403(
        self, alerts_client, mock_alert_svc, mock_user
    ):
        other_user_alert = _make_alert(user_id=uuid4())
        mock_alert_svc.price_alert_dao.get_by_id.return_value = other_user_alert

        resp = await alerts_client.patch(f"{BASE_ALERTS}/{other_user_alert.id}/reset")

        assert resp.status_code == 403
        assert "Not authorized" in resp.json()["detail"]


class TestToggleAlert:
    async def test_toggle_alert_success(self, alerts_client, mock_alert_svc, mock_user):
        alert = _make_alert(user_id=mock_user.id)
        mock_alert_svc.price_alert_dao.get_by_id.return_value = alert

        updated = _make_alert(user_id=mock_user.id)
        updated.active = False
        mock_alert_svc.price_alert_dao.update.return_value = updated

        resp = await alerts_client.patch(
            f"{BASE_ALERTS}/{alert.id}/toggle", json={"active": False}
        )

        assert resp.status_code == 200
        mock_alert_svc.price_alert_dao.update.assert_awaited_once()

    async def test_toggle_alert_not_found_returns_404(
        self, alerts_client, mock_alert_svc
    ):
        mock_alert_svc.price_alert_dao.get_by_id.return_value = None

        resp = await alerts_client.patch(
            f"{BASE_ALERTS}/{uuid4()}/toggle", json={"active": False}
        )

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Alert not found"

    async def test_toggle_alert_forbidden_returns_403(
        self, alerts_client, mock_alert_svc, mock_user
    ):
        other_user_alert = _make_alert(user_id=uuid4())
        mock_alert_svc.price_alert_dao.get_by_id.return_value = other_user_alert

        resp = await alerts_client.patch(
            f"{BASE_ALERTS}/{other_user_alert.id}/toggle", json={"active": False}
        )

        assert resp.status_code == 403

    async def test_toggle_alert_missing_body_returns_422(
        self, alerts_client, mock_alert_svc, mock_user
    ):
        alert = _make_alert(user_id=mock_user.id)
        mock_alert_svc.price_alert_dao.get_by_id.return_value = alert

        resp = await alerts_client.patch(f"{BASE_ALERTS}/{alert.id}/toggle")

        assert resp.status_code == 422


# ===========================================================================
# Schedules API  (schedules.py)
# ===========================================================================


class TestCreateSchedule:
    async def test_create_schedule_success(
        self, schedules_client, mock_schedule_svc, mock_user
    ):
        schedule = _make_schedule(user_id=mock_user.id)
        mock_schedule_svc.create_scheduled_analysis.return_value = schedule

        resp = await schedules_client.post(
            BASE_SCHEDULES,
            json={"ticker": "AAPL", "market": "US", "frequency": "daily"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["frequency"] == "daily"
        mock_schedule_svc.create_scheduled_analysis.assert_awaited_once()

    async def test_create_schedule_rate_limit_returns_400(
        self, schedules_client, mock_schedule_svc
    ):
        mock_schedule_svc.create_scheduled_analysis.side_effect = (
            ScheduleRateLimitError("Max schedules reached")
        )

        resp = await schedules_client.post(
            BASE_SCHEDULES,
            json={"ticker": "AAPL", "market": "US", "frequency": "daily"},
        )

        assert resp.status_code == 400
        assert "Max schedules reached" in resp.json()["detail"]

    async def test_create_schedule_generic_error_returns_500(
        self, schedules_client, mock_schedule_svc
    ):
        mock_schedule_svc.create_scheduled_analysis.side_effect = ScheduleError(
            "DB error"
        )

        resp = await schedules_client.post(
            BASE_SCHEDULES,
            json={"ticker": "AAPL", "market": "US", "frequency": "daily"},
        )

        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to create schedule"

    async def test_create_schedule_invalid_market_returns_422(self, schedules_client):
        resp = await schedules_client.post(
            BASE_SCHEDULES,
            json={"ticker": "AAPL", "market": "INVALID", "frequency": "daily"},
        )

        assert resp.status_code == 422

    async def test_create_schedule_invalid_frequency_returns_422(
        self, schedules_client
    ):
        resp = await schedules_client.post(
            BASE_SCHEDULES,
            json={"ticker": "AAPL", "market": "US", "frequency": "hourly"},
        )

        assert resp.status_code == 422

    async def test_create_schedule_ticker_uppercased(
        self, schedules_client, mock_schedule_svc, mock_user
    ):
        schedule = _make_schedule(user_id=mock_user.id)
        mock_schedule_svc.create_scheduled_analysis.return_value = schedule

        resp = await schedules_client.post(
            BASE_SCHEDULES,
            json={"ticker": "aapl", "market": "US", "frequency": "daily"},
        )

        assert resp.status_code == 201
        call_kwargs = mock_schedule_svc.create_scheduled_analysis.call_args
        assert call_kwargs.kwargs["ticker"] == "AAPL"

    async def test_create_schedule_weekly_frequency(
        self, schedules_client, mock_schedule_svc, mock_user
    ):
        schedule = _make_schedule(user_id=mock_user.id)
        schedule.frequency = "weekly"
        mock_schedule_svc.create_scheduled_analysis.return_value = schedule

        resp = await schedules_client.post(
            BASE_SCHEDULES,
            json={"ticker": "MSFT", "market": "US", "frequency": "weekly"},
        )

        assert resp.status_code == 201
        assert resp.json()["frequency"] == "weekly"

    async def test_create_schedule_on_change_frequency(
        self, schedules_client, mock_schedule_svc, mock_user
    ):
        schedule = _make_schedule(user_id=mock_user.id)
        schedule.frequency = "on_change"
        mock_schedule_svc.create_scheduled_analysis.return_value = schedule

        resp = await schedules_client.post(
            BASE_SCHEDULES,
            json={"ticker": "TSLA", "market": "US", "frequency": "on_change"},
        )

        assert resp.status_code == 201


class TestListSchedules:
    async def test_list_schedules_empty(
        self, schedules_client, mock_schedule_svc, mock_user
    ):
        mock_schedule_svc.get_user_schedules.return_value = []

        resp = await schedules_client.get(BASE_SCHEDULES)

        assert resp.status_code == 200
        assert resp.json() == []
        mock_schedule_svc.get_user_schedules.assert_awaited_once_with(mock_user.id)

    async def test_list_schedules_returns_schedules(
        self, schedules_client, mock_schedule_svc, mock_user
    ):
        schedule = _make_schedule(user_id=mock_user.id)
        mock_schedule_svc.get_user_schedules.return_value = [schedule]

        resp = await schedules_client.get(BASE_SCHEDULES)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["ticker"] == "AAPL"
        assert data[0]["frequency"] == "daily"
        assert data[0]["active"] is True


class TestDeleteSchedule:
    async def test_delete_schedule_success(self, schedules_client, mock_schedule_svc):
        schedule_id = uuid4()
        mock_schedule_svc.delete_schedule.return_value = True

        resp = await schedules_client.delete(f"{BASE_SCHEDULES}/{schedule_id}")

        assert resp.status_code == 204
        mock_schedule_svc.delete_schedule.assert_awaited_once()

    async def test_delete_schedule_not_found_returns_404(
        self, schedules_client, mock_schedule_svc
    ):
        mock_schedule_svc.delete_schedule.side_effect = ScheduleNotFoundError(
            "Schedule not found"
        )

        resp = await schedules_client.delete(f"{BASE_SCHEDULES}/{uuid4()}")

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Schedule not found"

    async def test_delete_schedule_generic_error_returns_500(
        self, schedules_client, mock_schedule_svc
    ):
        mock_schedule_svc.delete_schedule.side_effect = ScheduleError("DB error")

        resp = await schedules_client.delete(f"{BASE_SCHEDULES}/{uuid4()}")

        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to delete schedule"


class TestToggleSchedule:
    async def test_toggle_schedule_success(
        self, schedules_client, mock_schedule_svc, mock_user
    ):
        schedule = _make_schedule(user_id=mock_user.id)
        mock_schedule_svc.toggle_schedule.return_value = schedule

        resp = await schedules_client.patch(
            f"{BASE_SCHEDULES}/{schedule.id}/toggle", json={"active": False}
        )

        assert resp.status_code == 200
        mock_schedule_svc.toggle_schedule.assert_awaited_once()

    async def test_toggle_schedule_not_found_returns_404(
        self, schedules_client, mock_schedule_svc
    ):
        mock_schedule_svc.toggle_schedule.side_effect = ScheduleNotFoundError(
            "Schedule not found"
        )

        resp = await schedules_client.patch(
            f"{BASE_SCHEDULES}/{uuid4()}/toggle", json={"active": False}
        )

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Schedule not found"

    async def test_toggle_schedule_generic_error_returns_500(
        self, schedules_client, mock_schedule_svc
    ):
        mock_schedule_svc.toggle_schedule.side_effect = ScheduleError("DB error")

        resp = await schedules_client.patch(
            f"{BASE_SCHEDULES}/{uuid4()}/toggle", json={"active": False}
        )

        assert resp.status_code == 500
        assert resp.json()["detail"] == "Failed to toggle schedule"

    async def test_toggle_schedule_missing_body_returns_422(self, schedules_client):
        resp = await schedules_client.patch(f"{BASE_SCHEDULES}/{uuid4()}/toggle")

        assert resp.status_code == 422

    async def test_toggle_schedule_reactivate(
        self, schedules_client, mock_schedule_svc, mock_user
    ):
        schedule = _make_schedule(user_id=mock_user.id)
        schedule.active = True
        mock_schedule_svc.toggle_schedule.return_value = schedule

        resp = await schedules_client.patch(
            f"{BASE_SCHEDULES}/{schedule.id}/toggle", json={"active": True}
        )

        assert resp.status_code == 200
        assert resp.json()["active"] is True
