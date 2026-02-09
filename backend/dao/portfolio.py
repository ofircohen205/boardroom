# backend/dao/portfolio.py
"""Portfolio and watchlist data access objects."""
from functools import lru_cache
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import Watchlist, WatchlistItem, Portfolio, Position
from backend.ai.state.enums import Market
from .base import BaseDAO


class WatchlistDAO(BaseDAO[Watchlist]):
    """Data access object for Watchlist operations."""

    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls, session: AsyncSession):
        """Get a singleton instance of the WatchlistDAO."""
        return super().get_instance(session, Watchlist)

    async def get_user_watchlists(self, user_id: UUID) -> List[Watchlist]:
        """Get all watchlists for a user with items loaded."""
        result = await self.session.execute(
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .options(selectinload(Watchlist.items))
        )
        return list(result.scalars().all())

    async def get_default_watchlist(self, user_id: UUID) -> Optional[Watchlist]:
        """Get or create the default watchlist for a user."""
        result = await self.session.execute(
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .where(Watchlist.name == 'Default')
            .options(selectinload(Watchlist.items))
        )
        watchlist = result.scalars().first()

        if not watchlist:
            # Create default watchlist
            watchlist = await self.create(user_id=user_id, name='Default')

        return watchlist

    async def add_item(
        self, watchlist_id: UUID, ticker: str, market: Market
    ) -> WatchlistItem:
        """Add an item to a watchlist."""
        # Check if item already exists
        result = await self.session.execute(
            select(WatchlistItem)
            .where(WatchlistItem.watchlist_id == watchlist_id)
            .where(WatchlistItem.ticker == ticker)
        )
        existing = result.scalars().first()

        if existing:
            return existing

        # Create new item
        item = WatchlistItem(
            watchlist_id=watchlist_id,
            ticker=ticker,
            market=market,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item


class PortfolioDAO(BaseDAO[Portfolio]):
    """Data access object for Portfolio operations."""

    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls, session: AsyncSession):
        """Get a singleton instance of the PortfolioDAO."""
        return super().get_instance(session, Portfolio)

    async def get_user_portfolios(self, user_id: UUID) -> List[Portfolio]:
        """Get all portfolios for a user with positions loaded."""
        result = await self.session.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user_id)
            .options(selectinload(Portfolio.positions))
        )
        return list(result.scalars().all())

    async def add_position(
        self,
        portfolio_id: UUID,
        ticker: str,
        market: Market,
        quantity: float,
        avg_entry_price: float,
        sector: Optional[str] = None,
    ) -> Position:
        """Add a position to a portfolio."""
        position = Position(
            portfolio_id=portfolio_id,
            ticker=ticker,
            market=market,
            quantity=quantity,
            avg_entry_price=avg_entry_price,
            sector=sector,
        )
        self.session.add(position)
        await self.session.flush()
        await self.session.refresh(position)
        return position
