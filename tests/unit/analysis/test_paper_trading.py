"""Unit tests for paper trading API endpoints."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from httpx import ASGITransport, AsyncClient

from backend.dependencies import get_paper_trading_service
from backend.main import app
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.database import get_db


@pytest.fixture
def mock_user():
    """A mock User that does not require a real database session."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "paper-test@example.com"
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
    db.add = MagicMock()
    return db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_account(user_id=None, account_id=None, strategy_id=None):
    """Build a minimal mock PaperAccount object."""
    account = MagicMock()
    account.id = account_id or uuid4()
    account.user_id = user_id or uuid4()
    account.strategy_id = strategy_id or uuid4()
    account.name = "Test Account"
    account.initial_balance = Decimal("10000.00")
    account.current_balance = Decimal("10000.00")
    account.is_active = True
    account.created_at = datetime(2026, 1, 1, 12, 0, 0)
    account.updated_at = datetime(2026, 1, 1, 12, 0, 0)
    return account


def _make_trade(account_id=None, trade_id=None):
    """Build a minimal mock PaperTrade object."""
    trade = MagicMock()
    trade.id = trade_id or uuid4()
    trade.account_id = account_id or uuid4()
    trade.ticker = "AAPL"
    trade.trade_type = "BUY"
    trade.quantity = 10
    trade.price = Decimal("150.00")
    trade.total_value = Decimal("1500.00")
    trade.analysis_session_id = None
    trade.executed_at = datetime(2026, 1, 1, 12, 0, 0)
    return trade


def _make_strategy(user_id=None, strategy_id=None):
    """Build a minimal mock Strategy object."""
    strategy = MagicMock()
    strategy.id = strategy_id or uuid4()
    strategy.user_id = user_id or uuid4()
    strategy.name = "Test Strategy"
    return strategy


def _make_mock_paper_service(mock_db=None):
    """Build a mock PaperTradingService with all attributes and methods as AsyncMock."""
    service = MagicMock()
    service.db = mock_db or MagicMock()
    service.db.commit = AsyncMock()
    service.db.refresh = AsyncMock()
    service.account_dao = MagicMock()
    service.account_dao.create_account = AsyncMock()
    service.account_dao.delete = AsyncMock()
    service.account_dao.execute_trade = AsyncMock()
    service.position_dao = MagicMock()
    service.position_dao.get_position = AsyncMock()
    service.trade_dao = MagicMock()
    service.get_user_accounts = AsyncMock()
    service.get_account = AsyncMock()
    service.get_account_positions = AsyncMock()
    service.get_account_trades = AsyncMock()
    return service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def paper_client(mock_user, mock_db):
    """AsyncClient with auth and DB dependencies overridden."""
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/paper/accounts - create paper account
# ---------------------------------------------------------------------------


async def test_create_paper_account_success(paper_client, mock_user, mock_db):
    """Creating a paper account with valid strategy returns 201."""
    strategy_id = uuid4()
    mock_strategy = _make_strategy(user_id=mock_user.id, strategy_id=strategy_id)
    mock_account = _make_account(user_id=mock_user.id, strategy_id=strategy_id)

    mock_service = _make_mock_paper_service(mock_db)
    mock_service.account_dao.create_account.return_value = mock_account

    mock_strategy_dao = MagicMock()
    mock_strategy_dao.get_by_id_and_user = AsyncMock(return_value=mock_strategy)

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    with patch(
        "backend.shared.dao.backtesting.StrategyDAO",
        return_value=mock_strategy_dao,
    ):
        response = await paper_client.post(
            "/api/api/paper/accounts",
            json={
                "name": "Test Account",
                "strategy_id": str(strategy_id),
                "initial_balance": 10000.0,
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Account"


async def test_create_paper_account_strategy_not_found(paper_client, mock_db):
    """Creating a paper account with a missing strategy returns 404."""
    mock_service = _make_mock_paper_service(mock_db)

    mock_strategy_dao = MagicMock()
    mock_strategy_dao.get_by_id_and_user = AsyncMock(return_value=None)

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    with patch(
        "backend.shared.dao.backtesting.StrategyDAO",
        return_value=mock_strategy_dao,
    ):
        response = await paper_client.post(
            "/api/api/paper/accounts",
            json={
                "name": "Test Account",
                "strategy_id": str(uuid4()),
                "initial_balance": 10000.0,
            },
        )

    assert response.status_code == 404


async def test_create_paper_account_missing_name(paper_client):
    """Creating a paper account without required name returns 422."""
    response = await paper_client.post(
        "/api/api/paper/accounts",
        json={"strategy_id": str(uuid4()), "initial_balance": 10000.0},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/paper/accounts - list accounts
# ---------------------------------------------------------------------------


async def test_list_paper_accounts_returns_list(paper_client, mock_user, mock_db):
    """Listing accounts returns 200 with a list."""
    mock_account = _make_account(user_id=mock_user.id)
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_user_accounts.return_value = [mock_account]

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get("/api/api/paper/accounts")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


async def test_list_paper_accounts_empty(paper_client, mock_db):
    """Listing accounts when none exist returns 200 with empty list."""
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_user_accounts.return_value = []

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get("/api/api/paper/accounts")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /api/paper/accounts/{account_id} - get account details
# ---------------------------------------------------------------------------


async def test_get_paper_account_not_found(paper_client, mock_db):
    """Getting a non-existent account returns 404."""
    account_id = uuid4()
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Paper account not found"
    )

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get(f"/api/api/paper/accounts/{account_id}")

    assert response.status_code == 404


async def test_get_paper_account_success(paper_client, mock_user, mock_db):
    """Getting an existing account returns 200 with account data."""
    account_id = uuid4()
    mock_account = _make_account(user_id=mock_user.id, account_id=account_id)
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.return_value = mock_account
    mock_service.get_account_positions.return_value = []

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get(
        f"/api/api/paper/accounts/{account_id}?include_positions=true"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Account"


# ---------------------------------------------------------------------------
# PUT /api/paper/accounts/{account_id} - update account
# ---------------------------------------------------------------------------


async def test_update_paper_account_success(paper_client, mock_user, mock_db):
    """Updating an existing account returns 200."""
    account_id = uuid4()
    mock_account = _make_account(user_id=mock_user.id, account_id=account_id)
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.return_value = mock_account

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.put(
        f"/api/api/paper/accounts/{account_id}",
        json={"name": "Updated Account"},
    )

    assert response.status_code == 200


async def test_update_paper_account_not_found(paper_client, mock_db):
    """Updating a non-existent account returns 404."""
    account_id = uuid4()
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Paper account not found"
    )

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.put(
        f"/api/api/paper/accounts/{account_id}",
        json={"name": "Updated Account"},
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/paper/accounts/{account_id} - delete account
# ---------------------------------------------------------------------------


async def test_delete_paper_account_success(paper_client, mock_user, mock_db):
    """Deleting an existing account returns 204."""
    account_id = uuid4()
    mock_account = _make_account(user_id=mock_user.id, account_id=account_id)
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.return_value = mock_account

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.delete(f"/api/api/paper/accounts/{account_id}")

    assert response.status_code == 204


async def test_delete_paper_account_not_found(paper_client, mock_db):
    """Deleting a non-existent account returns 404."""
    account_id = uuid4()
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Paper account not found"
    )

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.delete(f"/api/api/paper/accounts/{account_id}")

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/paper/accounts/{account_id}/trades - execute trade
# ---------------------------------------------------------------------------


async def test_execute_trade_account_not_found(paper_client, mock_db):
    """Executing a trade on a missing account returns 404."""
    account_id = uuid4()
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Paper account not found"
    )

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.post(
        f"/api/api/paper/accounts/{account_id}/trades",
        json={"ticker": "AAPL", "trade_type": "BUY", "quantity": 10},
    )

    assert response.status_code == 404


async def test_execute_trade_insufficient_funds(paper_client, mock_user, mock_db):
    """Executing a BUY trade with insufficient funds returns 400."""
    account_id = uuid4()
    mock_account = _make_account(user_id=mock_user.id, account_id=account_id)
    mock_account.current_balance = Decimal("100.00")  # Too little for 10 shares

    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.return_value = mock_account

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    with patch(
        "backend.domains.analysis.api.paper.router.get_latest_price",
        new=AsyncMock(return_value=Decimal("150.00")),
    ):
        response = await paper_client.post(
            f"/api/api/paper/accounts/{account_id}/trades",
            json={"ticker": "AAPL", "trade_type": "BUY", "quantity": 10},
        )

    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]


async def test_execute_trade_sell_insufficient_shares(paper_client, mock_user, mock_db):
    """Executing a SELL trade with no position returns 400."""
    account_id = uuid4()
    mock_account = _make_account(user_id=mock_user.id, account_id=account_id)
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.return_value = mock_account
    mock_service.position_dao.get_position.return_value = None

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    with patch(
        "backend.domains.analysis.api.paper.router.get_latest_price",
        new=AsyncMock(return_value=Decimal("150.00")),
    ):
        response = await paper_client.post(
            f"/api/api/paper/accounts/{account_id}/trades",
            json={"ticker": "AAPL", "trade_type": "SELL", "quantity": 10},
        )

    assert response.status_code == 400
    assert "Insufficient shares" in response.json()["detail"]


async def test_execute_trade_no_price_available(paper_client, mock_user, mock_db):
    """Executing a trade when price cannot be fetched returns 400."""
    account_id = uuid4()
    mock_account = _make_account(user_id=mock_user.id, account_id=account_id)
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.return_value = mock_account

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    with patch(
        "backend.domains.analysis.api.paper.router.get_latest_price",
        new=AsyncMock(return_value=None),
    ):
        response = await paper_client.post(
            f"/api/api/paper/accounts/{account_id}/trades",
            json={"ticker": "INVALID", "trade_type": "BUY", "quantity": 1},
        )

    assert response.status_code == 400


async def test_execute_buy_trade_success(paper_client, mock_user, mock_db):
    """Executing a valid BUY trade returns 201."""
    account_id = uuid4()
    mock_account = _make_account(user_id=mock_user.id, account_id=account_id)
    mock_trade = _make_trade(account_id=account_id)

    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.return_value = mock_account
    mock_service.account_dao.execute_trade.return_value = mock_trade

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    with patch(
        "backend.domains.analysis.api.paper.router.get_latest_price",
        new=AsyncMock(return_value=Decimal("150.00")),
    ):
        response = await paper_client.post(
            f"/api/api/paper/accounts/{account_id}/trades",
            json={"ticker": "AAPL", "trade_type": "BUY", "quantity": 10},
        )

    assert response.status_code == 201


# ---------------------------------------------------------------------------
# GET /api/paper/accounts/{account_id}/trades - trade history
# ---------------------------------------------------------------------------


async def test_get_trade_history_account_not_found(paper_client, mock_db):
    """Getting trade history for a missing account returns 404."""
    account_id = uuid4()
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account_trades.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Paper account not found"
    )

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get(f"/api/api/paper/accounts/{account_id}/trades")

    assert response.status_code == 404


async def test_get_trade_history_success(paper_client, mock_user, mock_db):
    """Getting trade history returns 200 with list of trades."""
    account_id = uuid4()
    mock_trade = _make_trade(account_id=account_id)
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account_trades.return_value = [mock_trade]

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get(f"/api/api/paper/accounts/{account_id}/trades")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ---------------------------------------------------------------------------
# GET /api/paper/accounts/{account_id}/positions - get positions
# ---------------------------------------------------------------------------


async def test_get_positions_account_not_found(paper_client, mock_db):
    """Getting positions for a missing account returns 404."""
    account_id = uuid4()
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account_positions.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Paper account not found"
    )

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get(f"/api/api/paper/accounts/{account_id}/positions")

    assert response.status_code == 404


async def test_get_positions_success(paper_client, mock_user, mock_db):
    """Getting positions returns 200 with empty list when no positions."""
    account_id = uuid4()
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account_positions.return_value = []

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get(f"/api/api/paper/accounts/{account_id}/positions")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /api/paper/accounts/{account_id}/performance - performance metrics
# ---------------------------------------------------------------------------


async def test_get_performance_account_not_found(paper_client, mock_db):
    """Getting performance for a missing account returns 404."""
    account_id = uuid4()
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Paper account not found"
    )

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get(
        f"/api/api/paper/accounts/{account_id}/performance"
    )

    assert response.status_code == 404


async def test_get_performance_success(paper_client, mock_user, mock_db):
    """Getting performance for an existing account returns 200 with metrics."""
    account_id = uuid4()
    mock_account = _make_account(user_id=mock_user.id, account_id=account_id)
    mock_service = _make_mock_paper_service(mock_db)
    mock_service.get_account.return_value = mock_account
    mock_service.get_account_trades.return_value = []
    mock_service.get_account_positions.return_value = []

    app.dependency_overrides[get_paper_trading_service] = lambda: mock_service

    response = await paper_client.get(
        f"/api/api/paper/accounts/{account_id}/performance"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["account_id"] == str(account_id)
    assert data["initial_balance"] == 10000.0
    assert data["total_trades"] == 0
    assert data["win_rate"] == 0.0
