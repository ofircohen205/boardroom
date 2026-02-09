# backend/services/portfolio_management/service.py
"""Portfolio and watchlist management service."""
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.portfolio import WatchlistDAO, PortfolioDAO
from backend.db.models import Watchlist, WatchlistItem, Portfolio, Position
from backend.ai.state.enums import Market


async def get_user_watchlists(user_id: UUID, db: AsyncSession) -> List[Watchlist]:
    """Get all watchlists for a user."""
    dao = WatchlistDAO(db)
    return await dao.get_user_watchlists(user_id)


async def create_watchlist(user_id: UUID, name: str, db: AsyncSession) -> Watchlist:
    """Create a new watchlist for a user."""
    dao = WatchlistDAO(db)
    watchlist = await dao.create_watchlist(user_id, name)
    await db.commit()
    await db.refresh(watchlist)
    return watchlist


async def add_to_watchlist(
    watchlist_id: UUID,
    ticker: str,
    market: Market,
    db: AsyncSession
) -> WatchlistItem:
    """Add a stock to a watchlist."""
    dao = WatchlistDAO(db)
    item = await dao.add_item(watchlist_id, ticker, market)
    await db.commit()
    await db.refresh(item)
    return item


async def remove_from_watchlist(
    watchlist_id: UUID,
    ticker: str,
    db: AsyncSession
) -> bool:
    """Remove a stock from a watchlist."""
    dao = WatchlistDAO(db)
    removed = await dao.remove_item(watchlist_id, ticker)
    await db.commit()
    return removed


async def get_user_portfolios(user_id: UUID, db: AsyncSession) -> List[Portfolio]:
    """Get all portfolios for a user."""
    dao = PortfolioDAO(db)
    return await dao.get_user_portfolios(user_id)


async def create_portfolio(user_id: UUID, name: str, db: AsyncSession) -> Portfolio:
    """Create a new portfolio for a user."""
    dao = PortfolioDAO(db)
    portfolio = await dao.create_portfolio(user_id, name)
    await db.commit()
    await db.refresh(portfolio)
    return portfolio


async def add_position(
    portfolio_id: UUID,
    ticker: str,
    market: Market,
    quantity: float,
    avg_entry_price: float,
    sector: str | None,
    db: AsyncSession
) -> Position:
    """Add a position to a portfolio."""
    dao = PortfolioDAO(db)
    position = await dao.add_position(
        portfolio_id=portfolio_id,
        ticker=ticker,
        market=market,
        quantity=quantity,
        avg_entry_price=avg_entry_price,
        sector=sector,
    )
    await db.commit()
    await db.refresh(position)
    return position
