"""Unit tests for strategies API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from httpx import ASGITransport, AsyncClient

from backend.dependencies import get_strategy_service
from backend.main import app
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.database import get_db

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_user():
    """A mock User that does not require a real database session."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "strat-test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def mock_db():
    """A lightweight mock DB session (no real SQLite needed)."""
    db = MagicMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    return db


STRATEGY_CONFIG = {
    "weights": {"fundamental": 0.4, "technical": 0.4, "sentiment": 0.2},
    "thresholds": {"buy": 70.0, "sell": 30.0},
    "risk_params": {"max_position_size": 0.5, "stop_loss": None, "take_profit": None},
}

STRATEGY_CREATE_PAYLOAD = {
    "name": "Test Strategy",
    "description": "A test strategy",
    "config": STRATEGY_CONFIG,
}


def _make_strategy(user_id=None, strategy_id=None):
    """Build a minimal mock Strategy object."""
    strategy = MagicMock()
    strategy.id = strategy_id or uuid4()
    strategy.user_id = user_id or uuid4()
    strategy.name = "Test Strategy"
    strategy.description = "A test strategy"
    strategy.config = STRATEGY_CONFIG
    strategy.is_active = True
    strategy.created_at = datetime(2026, 1, 1, 12, 0, 0)
    strategy.updated_at = datetime(2026, 1, 1, 12, 0, 0)
    return strategy


def _make_mock_strategy_service():
    """Build a mock StrategyService with all methods as AsyncMock."""
    service = MagicMock()
    service.create_strategy = AsyncMock()
    service.get_user_strategies = AsyncMock()
    service.get_strategy = AsyncMock()
    service.update_strategy = AsyncMock()
    service.delete_strategy = AsyncMock()
    return service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def strategies_client(mock_user, mock_db):
    """AsyncClient with auth and DB dependencies overridden."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/strategies - create strategy
# ---------------------------------------------------------------------------


async def test_create_strategy_success(strategies_client, mock_user):
    """Creating a strategy returns 201 with the strategy data."""
    mock_strategy = _make_strategy(user_id=mock_user.id)
    mock_service = _make_mock_strategy_service()
    mock_service.create_strategy.return_value = mock_strategy

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.post(
        "/api/api/strategies", json=STRATEGY_CREATE_PAYLOAD
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Strategy"


async def test_create_strategy_missing_name(strategies_client):
    """Creating a strategy without required name field returns 422."""
    payload = {
        "config": STRATEGY_CONFIG,
    }
    response = await strategies_client.post("/api/api/strategies", json=payload)
    assert response.status_code == 422


async def test_create_strategy_invalid_weights_sum(strategies_client):
    """Creating a strategy with weights that do not sum to 1.0 returns 422."""
    payload = {
        "name": "Bad Weights",
        "config": {
            "weights": {"fundamental": 0.5, "technical": 0.5, "sentiment": 0.5},
            "thresholds": {"buy": 70.0, "sell": 30.0},
            "risk_params": {
                "max_position_size": 0.5,
                "stop_loss": None,
                "take_profit": None,
            },
        },
    }
    response = await strategies_client.post("/api/api/strategies", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/strategies - list strategies
# ---------------------------------------------------------------------------


async def test_list_strategies_returns_list(strategies_client, mock_user):
    """Listing strategies returns 200 with a list."""
    mock_strategy = _make_strategy(user_id=mock_user.id)
    mock_service = _make_mock_strategy_service()
    mock_service.get_user_strategies.return_value = [mock_strategy]

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.get("/api/api/strategies")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


async def test_list_strategies_empty(strategies_client):
    """Listing strategies when none exist returns 200 with empty list."""
    mock_service = _make_mock_strategy_service()
    mock_service.get_user_strategies.return_value = []

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.get("/api/api/strategies")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_strategies_active_only_param(strategies_client):
    """The active_only query param is forwarded to the service."""
    mock_service = _make_mock_strategy_service()
    mock_service.get_user_strategies.return_value = []

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.get("/api/api/strategies?active_only=false")

    assert response.status_code == 200
    mock_service.get_user_strategies.assert_awaited_once()
    _, kwargs = mock_service.get_user_strategies.call_args
    assert kwargs.get("active_only") is False


# ---------------------------------------------------------------------------
# GET /api/strategies/{strategy_id} - get single strategy
# ---------------------------------------------------------------------------


async def test_get_strategy_success(strategies_client, mock_user):
    """Getting an existing strategy returns 200."""
    strategy_id = uuid4()
    mock_strategy = _make_strategy(user_id=mock_user.id, strategy_id=strategy_id)
    mock_service = _make_mock_strategy_service()
    mock_service.get_strategy.return_value = mock_strategy

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.get(f"/api/api/strategies/{strategy_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Strategy"


async def test_get_strategy_not_found(strategies_client):
    """Getting a non-existent strategy returns 404."""
    strategy_id = uuid4()
    mock_service = _make_mock_strategy_service()
    mock_service.get_strategy.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
    )

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.get(f"/api/api/strategies/{strategy_id}")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/strategies/{strategy_id} - update strategy
# ---------------------------------------------------------------------------


async def test_update_strategy_success(strategies_client, mock_user):
    """Updating an existing strategy returns 200 with updated data."""
    strategy_id = uuid4()
    mock_strategy = _make_strategy(user_id=mock_user.id, strategy_id=strategy_id)
    mock_service = _make_mock_strategy_service()
    mock_service.update_strategy.return_value = mock_strategy

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.put(
        f"/api/api/strategies/{strategy_id}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 200


async def test_update_strategy_not_found(strategies_client):
    """Updating a non-existent strategy returns 404."""
    strategy_id = uuid4()
    mock_service = _make_mock_strategy_service()
    mock_service.update_strategy.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
    )

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.put(
        f"/api/api/strategies/{strategy_id}",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/strategies/{strategy_id} - delete strategy
# ---------------------------------------------------------------------------


async def test_delete_strategy_success(strategies_client, mock_user):
    """Deleting an existing strategy returns 204."""
    strategy_id = uuid4()
    mock_service = _make_mock_strategy_service()
    mock_service.delete_strategy.return_value = None

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.delete(f"/api/api/strategies/{strategy_id}")

    assert response.status_code == 204


async def test_delete_strategy_not_found(strategies_client):
    """Deleting a non-existent strategy returns 404."""
    strategy_id = uuid4()
    mock_service = _make_mock_strategy_service()
    mock_service.delete_strategy.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
    )

    app.dependency_overrides[get_strategy_service] = lambda: mock_service

    response = await strategies_client.delete(f"/api/api/strategies/{strategy_id}")

    assert response.status_code == 404
