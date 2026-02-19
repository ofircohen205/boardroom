# tests/unit/portfolio/test_dao_portfolio.py
"""Unit tests for WatchlistDAO and PortfolioDAO (backend/shared/dao/portfolio.py).

All database interactions are replaced with AsyncMock so no real database
connection is required.  asyncio_mode = "auto" in pyproject.toml means
@pytest.mark.asyncio is not needed on individual test functions.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.shared.ai.state.enums import Market
from backend.shared.dao.portfolio import PortfolioDAO, WatchlistDAO
from backend.shared.db.models.portfolio import (
    Portfolio,
    Position,
    Watchlist,
    WatchlistItem,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_first_result(item):
    """Return a mock execute() result whose scalars().first() yields *item*."""
    result = MagicMock()
    result.scalars.return_value.first.return_value = item
    return result


def make_scalars_all(items):
    """Return a mock execute() result whose scalars().all() yields *items*."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


# ---------------------------------------------------------------------------
# Shared session fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """AsyncSession mock with all required async methods."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


# ===========================================================================
# WatchlistDAO tests
# ===========================================================================


@pytest.fixture
def watchlist_dao(mock_session):
    return WatchlistDAO(mock_session)


async def test_watchlist_dao_get_user_watchlists_returns_list(
    watchlist_dao, mock_session
):
    """get_user_watchlists() should return all watchlists owned by the user."""
    wl1 = MagicMock(spec=Watchlist)
    wl2 = MagicMock(spec=Watchlist)
    mock_session.execute.return_value = make_scalars_all([wl1, wl2])

    result = await watchlist_dao.get_user_watchlists(uuid4())

    assert result == [wl1, wl2]
    assert isinstance(result, list)
    mock_session.execute.assert_awaited_once()


async def test_watchlist_dao_get_default_watchlist_returns_existing(
    watchlist_dao, mock_session
):
    """get_default_watchlist() should return the existing watchlist when found."""
    existing_wl = MagicMock(spec=Watchlist)
    mock_session.execute.return_value = make_first_result(existing_wl)

    result = await watchlist_dao.get_default_watchlist(uuid4())

    assert result is existing_wl
    mock_session.execute.assert_awaited_once()


async def test_watchlist_dao_get_default_watchlist_creates_when_missing(
    watchlist_dao, mock_session
):
    """get_default_watchlist() should create and return a new watchlist when none exists."""
    none_result = make_first_result(None)
    mock_session.execute.return_value = none_result

    new_wl = MagicMock(spec=Watchlist)

    with patch.object(
        watchlist_dao, "create", new_callable=AsyncMock, return_value=new_wl
    ):
        result = await watchlist_dao.get_default_watchlist(uuid4())

    assert result is new_wl
    # execute was called once for the SELECT; create() handles its own persistence
    mock_session.execute.assert_awaited_once()


async def test_watchlist_dao_add_item_returns_existing_when_duplicate(
    watchlist_dao, mock_session
):
    """add_item() should return the existing item without creating a duplicate."""
    existing_item = MagicMock(spec=WatchlistItem)
    mock_session.execute.return_value = make_first_result(existing_item)

    result = await watchlist_dao.add_item(uuid4(), "AAPL", Market.US)

    assert result is existing_item
    # No add/flush/refresh should have been called
    mock_session.add.assert_not_called()
    mock_session.flush.assert_not_awaited()


async def test_watchlist_dao_add_item_creates_new_item_when_not_existing(
    watchlist_dao, mock_session
):
    """add_item() should create, flush, and refresh a new WatchlistItem when none exists."""
    mock_session.execute.return_value = make_first_result(None)

    # refresh() will be awaited with the newly created item; capture it via side_effect
    created_item = None

    async def capture_refresh(instance):
        nonlocal created_item
        created_item = instance

    mock_session.refresh.side_effect = capture_refresh

    watchlist_id = uuid4()
    result = await watchlist_dao.add_item(watchlist_id, "TSLA", Market.US)

    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    # result should be the WatchlistItem that was added (refresh returns None; result is the instance)
    assert isinstance(result, WatchlistItem)
    assert result.ticker == "TSLA"
    assert result.watchlist_id == watchlist_id
    assert result.market == Market.US


# ===========================================================================
# PortfolioDAO tests
# ===========================================================================


@pytest.fixture
def portfolio_dao(mock_session):
    return PortfolioDAO(mock_session)


async def test_portfolio_dao_get_user_portfolios_returns_list(
    portfolio_dao, mock_session
):
    """get_user_portfolios() should return all portfolios owned by the user."""
    p1 = MagicMock(spec=Portfolio)
    p2 = MagicMock(spec=Portfolio)
    mock_session.execute.return_value = make_scalars_all([p1, p2])

    result = await portfolio_dao.get_user_portfolios(uuid4())

    assert result == [p1, p2]
    assert isinstance(result, list)
    mock_session.execute.assert_awaited_once()


async def test_portfolio_dao_add_position_creates_and_returns_position(
    portfolio_dao, mock_session
):
    """add_position() should flush, refresh, and return the new Position."""
    portfolio_id = uuid4()

    result = await portfolio_dao.add_position(
        portfolio_id=portfolio_id,
        ticker="NVDA",
        market=Market.US,
        quantity=10.0,
        avg_entry_price=500.0,
        sector="Technology",
    )

    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
    assert isinstance(result, Position)
    assert result.ticker == "NVDA"
    assert result.portfolio_id == portfolio_id
    assert result.quantity == 10.0
    assert result.avg_entry_price == 500.0
    assert result.sector == "Technology"


async def test_portfolio_dao_add_position_without_sector(portfolio_dao, mock_session):
    """add_position() should work correctly when sector is omitted (defaults to None)."""
    portfolio_id = uuid4()

    result = await portfolio_dao.add_position(
        portfolio_id=portfolio_id,
        ticker="GOOG",
        market=Market.US,
        quantity=5.0,
        avg_entry_price=175.0,
    )

    assert isinstance(result, Position)
    assert result.sector is None
    mock_session.add.assert_called_once()
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()
