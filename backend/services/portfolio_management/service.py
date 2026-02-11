# backend/services/portfolio_management/service.py
"""Portfolio and watchlist management service."""

from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Market
from backend.dao.portfolio import PortfolioDAO
from backend.db.models import Portfolio, Position
from backend.services.base import BaseService


class PortfolioService(BaseService):
    """Service for portfolio operations."""

    def __init__(self, portfolio_dao: PortfolioDAO):
        """
        Initialize PortfolioService.

        Args:
            portfolio_dao: DAO for portfolio operations
        """
        self.portfolio_dao = portfolio_dao

    async def get_user_portfolios(self, user_id: UUID) -> List[Portfolio]:
        """
        Get all portfolios for a user.

        Args:
            user_id: User ID

        Returns:
            List of Portfolio objects with positions loaded
        """
        return await self.portfolio_dao.get_user_portfolios(user_id)

    async def create_portfolio(
        self, user_id: UUID, name: str, db: AsyncSession
    ) -> Portfolio:
        """
        Create a new portfolio for a user.

        Args:
            user_id: User ID
            name: Portfolio name
            db: Database session

        Returns:
            Created Portfolio object
        """
        portfolio = await self.portfolio_dao.create(user_id=user_id, name=name)
        await db.commit()
        await db.refresh(portfolio)
        return portfolio

    async def add_position(
        self,
        portfolio_id: UUID,
        ticker: str,
        market: Market,
        quantity: float,
        avg_entry_price: float,
        sector: str | None,
        db: AsyncSession,
    ) -> Position:
        """
        Add a position to a portfolio.

        Args:
            portfolio_id: Portfolio ID
            ticker: Stock ticker symbol
            market: Market enum (US or TASE)
            quantity: Number of shares
            avg_entry_price: Average entry price
            sector: Optional sector name
            db: Database session

        Returns:
            Created Position object
        """
        position = await self.portfolio_dao.add_position(
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
