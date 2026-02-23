"""
Services for backtesting, strategies, and paper trading.

This module provides high-level business logic for the analysis domain,
acting as an intermediary between API endpoints and DAOs.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.analysis.api.strategies.schemas import (
    StrategyCreate,
    StrategyUpdate,
)
from backend.shared.dao.backtesting import (
    BacktestResultDAO,
    PaperAccountDAO,
    PaperPositionDAO,
    PaperTradeDAO,
    StrategyDAO,
)
from backend.shared.db.models.backtesting import (
    BacktestResult,
    PaperAccount,
    PaperPosition,
    PaperTrade,
    Strategy,
)
from backend.shared.services.base import BaseService


class StrategyService(BaseService):
    """Service for managing trading strategies."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.strategy_dao = StrategyDAO(db)

    async def create_strategy(
        self, user_id: UUID, strategy_data: StrategyCreate
    ) -> Strategy:
        """Create a new strategy."""
        return await self.strategy_dao.create_strategy(user_id, strategy_data)

    async def get_user_strategies(
        self, user_id: UUID, active_only: bool = True
    ) -> list[Strategy]:
        """Get all strategies for a user."""
        return await self.strategy_dao.get_user_strategies(user_id, active_only)

    async def get_strategy(self, strategy_id: UUID, user_id: UUID) -> Strategy:
        """Get a specific strategy by ID and user ID."""
        strategy = await self.strategy_dao.get_by_id_and_user(strategy_id, user_id)
        if not strategy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy {strategy_id} not found",
            )
        return strategy

    async def update_strategy(
        self, strategy_id: UUID, user_id: UUID, strategy_data: StrategyUpdate
    ) -> Strategy:
        """Update an existing strategy."""
        strategy = await self.get_strategy(strategy_id, user_id)

        # Update fields
        if strategy_data.name is not None:
            strategy.name = strategy_data.name
        if strategy_data.description is not None:
            strategy.description = strategy_data.description
        if strategy_data.config is not None:
            strategy.config = strategy_data.config.model_dump()
        if strategy_data.is_active is not None:
            strategy.is_active = strategy_data.is_active

        await self.db.commit()
        await self.db.refresh(strategy)
        return strategy

    async def delete_strategy(self, strategy_id: UUID, user_id: UUID) -> None:
        """Delete a strategy."""
        strategy = await self.get_strategy(strategy_id, user_id)
        await self.strategy_dao.delete(strategy_id)
        await self.db.commit()


class BacktestService(BaseService):
    """Service for managing backtest results."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.backtest_dao = BacktestResultDAO(db)
        self.strategy_dao = StrategyDAO(db)

    async def get_user_results(
        self, user_id: UUID, limit: int = 50
    ) -> list[BacktestResult]:
        """Get backtest results for a user."""
        return await self.backtest_dao.get_user_results(user_id, limit)

    async def get_result(self, result_id: UUID, user_id: UUID) -> BacktestResult:
        """Get a specific backtest result."""
        result = await self.backtest_dao.get_by_id(result_id)
        if not result or result.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest result {result_id} not found",
            )
        return result

    async def delete_result(self, result_id: UUID, user_id: UUID) -> None:
        """Delete a backtest result."""
        result = await self.get_result(result_id, user_id)
        await self.backtest_dao.delete(result_id)
        await self.db.commit()


class PaperTradingService(BaseService):
    """Service for managing paper trading accounts."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.account_dao = PaperAccountDAO(db)
        self.trade_dao = PaperTradeDAO(db)
        self.position_dao = PaperPositionDAO(db)

    async def get_user_accounts(
        self, user_id: UUID, active_only: bool = True
    ) -> list[PaperAccount]:
        """Get all paper trading accounts for a user."""
        return await self.account_dao.get_user_accounts(user_id, active_only)

    async def get_account(self, account_id: UUID, user_id: UUID) -> PaperAccount:
        """Get a specific paper trading account."""
        account = await self.account_dao.get_by_id_and_user(account_id, user_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paper account {account_id} not found",
            )
        return account

    async def get_account_trades(
        self, account_id: UUID, user_id: UUID, limit: int = 100
    ) -> list[PaperTrade]:
        """Get trade history for an account."""
        await self.get_account(account_id, user_id)  # Validate ownership
        return await self.trade_dao.get_account_trades(account_id, limit)

    async def get_account_positions(
        self, account_id: UUID, user_id: UUID
    ) -> list[PaperPosition]:
        """Get all open positions for an account."""
        await self.get_account(account_id, user_id)  # Validate ownership
        return await self.position_dao.get_account_positions(account_id)
