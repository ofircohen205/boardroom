# tests/unit/test_websocket_handlers.py
"""Unit tests for WebSocket helper functions in the analysis domain."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.domains.analysis.api.websocket import (
    _calculate_portfolio_sector_weight,
    _serialize,
    get_current_user_ws,
)
from backend.shared.ai.state.enums import Market
from backend.shared.core.security import create_access_token

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """A mock AsyncSession with async execute support."""
    db = MagicMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """A mock User that does not require a real database session."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "ws-test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def valid_token(mock_user):
    """A valid JWT token for the mock user."""
    return create_access_token({"sub": mock_user.email})


# ---------------------------------------------------------------------------
# get_current_user_ws -- authentication helper
# ---------------------------------------------------------------------------


async def test_get_current_user_ws_empty_token(mock_db):
    """Empty token should return None without touching the database."""
    result = await get_current_user_ws("", mock_db)
    assert result is None
    mock_db.execute.assert_not_called()


async def test_get_current_user_ws_invalid_token(mock_db):
    """A malformed JWT should return None (JWTError handled internally)."""
    result = await get_current_user_ws("not.a.valid.jwt", mock_db)
    assert result is None


async def test_get_current_user_ws_valid_token_user_found(
    mock_user, mock_db, valid_token
):
    """A valid token whose email maps to an existing user returns that user."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    user = await get_current_user_ws(valid_token, mock_db)
    assert user == mock_user


async def test_get_current_user_ws_valid_token_user_not_found(mock_db, valid_token):
    """A valid token with an email not in the database should return None."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    result = await get_current_user_ws(valid_token, mock_db)
    assert result is None


async def test_get_current_user_ws_token_missing_sub(mock_db):
    """A JWT that has no 'sub' claim should return None.

    The implementation converts None → 'None' (str), queries the DB,
    and returns None when no user is found with email 'None'.
    """
    token_without_sub = create_access_token({"role": "admin"})
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    result = await get_current_user_ws(token_without_sub, mock_db)
    assert result is None


# ---------------------------------------------------------------------------
# _calculate_portfolio_sector_weight
# ---------------------------------------------------------------------------


async def test_calculate_portfolio_sector_weight_no_sector(mock_user, mock_db):
    """When the market data client cannot determine a sector, return 0.0."""
    mock_client = AsyncMock()
    mock_client.get_stock_data = AsyncMock(return_value={})  # no "sector" key

    with patch(
        "backend.domains.analysis.api.websocket.get_market_data_client",
        return_value=mock_client,
    ):
        weight = await _calculate_portfolio_sector_weight(
            mock_db, mock_user, "AAPL", Market.US
        )

    assert weight == 0.0


async def test_calculate_portfolio_sector_weight_no_portfolio(mock_user, mock_db):
    """When the user has no portfolio, return 0.0."""
    mock_client = AsyncMock()
    mock_client.get_stock_data = AsyncMock(return_value={"sector": "Technology"})

    portfolio_result = MagicMock()
    portfolio_result.scalars.return_value.first.return_value = None
    mock_db.execute = AsyncMock(return_value=portfolio_result)

    with patch(
        "backend.domains.analysis.api.websocket.get_market_data_client",
        return_value=mock_client,
    ):
        weight = await _calculate_portfolio_sector_weight(
            mock_db, mock_user, "AAPL", Market.US
        )

    assert weight == 0.0


async def test_calculate_portfolio_sector_weight_empty_portfolio(mock_user, mock_db):
    """When the portfolio has no positions, return 0.0."""
    mock_client = AsyncMock()
    mock_client.get_stock_data = AsyncMock(return_value={"sector": "Technology"})

    portfolio = MagicMock()
    portfolio.positions = []
    portfolio_result = MagicMock()
    portfolio_result.scalars.return_value.first.return_value = portfolio
    mock_db.execute = AsyncMock(return_value=portfolio_result)

    with patch(
        "backend.domains.analysis.api.websocket.get_market_data_client",
        return_value=mock_client,
    ):
        weight = await _calculate_portfolio_sector_weight(
            mock_db, mock_user, "AAPL", Market.US
        )

    assert weight == 0.0


async def test_calculate_portfolio_sector_weight_single_matching_position(
    mock_user, mock_db
):
    """Single position in the same sector gives weight of 1.0 (100%)."""
    position = MagicMock()
    position.ticker = "MSFT"
    position.market = Market.US
    position.quantity = 10

    portfolio = MagicMock()
    portfolio.positions = [position]
    portfolio_result = MagicMock()
    portfolio_result.scalars.return_value.first.return_value = portfolio
    mock_db.execute = AsyncMock(return_value=portfolio_result)

    async def fake_get_stock_data(ticker, market):
        return {"sector": "Technology", "current_price": 100.0}

    mock_client = AsyncMock()
    mock_client.get_stock_data = AsyncMock(side_effect=fake_get_stock_data)

    with patch(
        "backend.domains.analysis.api.websocket.get_market_data_client",
        return_value=mock_client,
    ):
        weight = await _calculate_portfolio_sector_weight(
            mock_db, mock_user, "AAPL", Market.US
        )

    assert weight == pytest.approx(1.0)


async def test_calculate_portfolio_sector_weight_mixed_sectors(mock_user, mock_db):
    """Two equal-value positions in different sectors: target sector is ~50%."""
    tech_position = MagicMock()
    tech_position.ticker = "MSFT"
    tech_position.market = Market.US
    tech_position.quantity = 10  # 10 x  =

    health_position = MagicMock()
    health_position.ticker = "JNJ"
    health_position.market = Market.US
    health_position.quantity = 10  # 10 x  =

    portfolio = MagicMock()
    portfolio.positions = [tech_position, health_position]
    portfolio_result = MagicMock()
    portfolio_result.scalars.return_value.first.return_value = portfolio
    mock_db.execute = AsyncMock(return_value=portfolio_result)

    async def fake_get_stock_data(ticker, market):
        if ticker in ("AAPL", "MSFT"):
            return {"sector": "Technology", "current_price": 100.0}
        return {"sector": "Healthcare", "current_price": 100.0}

    mock_client = AsyncMock()
    mock_client.get_stock_data = AsyncMock(side_effect=fake_get_stock_data)

    with patch(
        "backend.domains.analysis.api.websocket.get_market_data_client",
        return_value=mock_client,
    ):
        weight = await _calculate_portfolio_sector_weight(
            mock_db, mock_user, "AAPL", Market.US
        )

    assert weight == pytest.approx(0.5)


async def test_calculate_portfolio_sector_weight_position_data_error(
    mock_user, mock_db
):
    """Position whose market data fetch fails is skipped; returns 0.0 when all fail."""
    position = MagicMock()
    position.ticker = "FAIL"
    position.market = Market.US
    position.quantity = 10

    portfolio = MagicMock()
    portfolio.positions = [position]
    portfolio_result = MagicMock()
    portfolio_result.scalars.return_value.first.return_value = portfolio
    mock_db.execute = AsyncMock(return_value=portfolio_result)

    async def fake_get_stock_data(ticker, market):
        if ticker == "ANALYZED":
            return {"sector": "Technology", "current_price": 100.0}
        raise RuntimeError("API error")

    mock_client = AsyncMock()
    mock_client.get_stock_data = AsyncMock(side_effect=fake_get_stock_data)

    with patch(
        "backend.domains.analysis.api.websocket.get_market_data_client",
        return_value=mock_client,
    ):
        weight = await _calculate_portfolio_sector_weight(
            mock_db, mock_user, "ANALYZED", Market.US
        )

    # All positions were skipped, total_portfolio_value == 0, so weight is 0.0
    assert weight == 0.0


async def test_calculate_portfolio_sector_weight_outer_exception(mock_user, mock_db):
    """If get_market_data_client raises, return 0.0 via outer except clause."""
    with patch(
        "backend.domains.analysis.api.websocket.get_market_data_client",
        side_effect=RuntimeError("client init failed"),
    ):
        weight = await _calculate_portfolio_sector_weight(
            mock_db, mock_user, "AAPL", Market.US
        )

    assert weight == 0.0


# ---------------------------------------------------------------------------
# _serialize -- JSON serialisation utility
# ---------------------------------------------------------------------------


def test_serialize_plain_dict():
    """Plain dict passes through unchanged."""
    data = {"key": "value", "num": 42}
    assert _serialize(data) == data


def test_serialize_nested_dict():
    """Nested dicts are recursively serialised."""
    data = {"outer": {"inner": "value"}}
    assert _serialize(data) == {"outer": {"inner": "value"}}


def test_serialize_list():
    """Lists are recursively serialised."""
    data = [1, "two", {"three": 3}]
    assert _serialize(data) == [1, "two", {"three": 3}]


def test_serialize_enum():
    """Enum values are converted to their .value representation."""
    result = _serialize(Market.US)
    assert result == Market.US.value


def test_serialize_uuid():
    """UUID objects are converted to strings."""
    uid = uuid.uuid4()
    result = _serialize(uid)
    assert result == str(uid)


def test_serialize_datetime():
    """datetime objects are serialised via isoformat()."""
    from datetime import datetime

    dt = datetime(2025, 1, 15, 12, 0, 0)
    result = _serialize(dt)
    assert result == "2025-01-15T12:00:00"


def test_serialize_plain_scalar():
    """Plain scalars (int, str, None) pass through unchanged."""
    assert _serialize(42) == 42
    assert _serialize("hello") == "hello"
    assert _serialize(None) is None


def test_serialize_mixed_list_with_enums():
    """List containing enums and UUIDs are each serialised correctly."""
    uid = uuid.uuid4()
    data = [Market.US, uid, "plain"]
    result = _serialize(data)
    assert result == [Market.US.value, str(uid), "plain"]
