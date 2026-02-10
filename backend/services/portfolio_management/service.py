# backend/services/portfolio_management/service.py
"""Portfolio and watchlist management service."""
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Market
from backend.dao.portfolio import PortfolioDAO, WatchlistDAO
from backend.db.models import Portfolio, Position, Watchlist, WatchlistItem


async def get_user_watchlists(user_id: UUID, db: AsyncSession) -> List[Watchlist]:
    """Get all watchlists for a user."""
    dao = WatchlistDAO.get_instance(db)
    return await dao.get_user_watchlists(user_id)


async def create_watchlist(user_id: UUID, name: str, db: AsyncSession) -> Watchlist:
    """Create a new watchlist for a user."""
    dao = WatchlistDAO.get_instance(db)
    watchlist = await dao.create(user_id=user_id, name=name)
    await db.commit()
    await db.refresh(watchlist)
    return watchlist


async def add_to_watchlist(
    watchlist_id: UUID, ticker: str, market: Market, db: AsyncSession
) -> WatchlistItem:
    """Add a stock to a watchlist."""
    dao = WatchlistDAO.get_instance(db)
    item = await dao.add_item(watchlist_id, ticker, market)
    await db.commit()
    await db.refresh(item)
    return item


async def remove_from_watchlist(
    watchlist_id: UUID, ticker: str, db: AsyncSession
) -> bool:
    """Remove a stock from a watchlist."""
    dao = WatchlistDAO.get_instance(db)

    # Find the item to remove
    result = await db.execute(
        select(WatchlistItem)
        .where(WatchlistItem.watchlist_id == watchlist_id)
        .where(WatchlistItem.ticker == ticker)
    )
    item_to_remove = result.scalars().first()

    if not item_to_remove:
        return False

    # Delete the item
    removed = await dao.delete(item_to_remove.id)
    await db.commit()
    return removed


async def get_user_portfolios(user_id: UUID, db: AsyncSession) -> List[Portfolio]:
    """Get all portfolios for a user."""
    dao = PortfolioDAO.get_instance(db)
    return await dao.get_user_portfolios(user_id)


async def create_portfolio(user_id: UUID, name: str, db: AsyncSession) -> Portfolio:
    """Create a new portfolio for a user."""
    dao = PortfolioDAO.get_instance(db)
    portfolio = await dao.create(user_id=user_id, name=name)
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
    db: AsyncSession,
) -> Position:
    """Add a position to a portfolio."""
    dao = PortfolioDAO.get_instance(db)
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
