"""
Data Access Objects for backtesting and paper trading.

Provides database operations for:
- Historical price and fundamental data
- User-defined trading strategies
- Paper trading accounts, trades, and positions
- Backtest results
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.dao.base import BaseDAO
from backend.shared.db.models.backtesting import (
    BacktestResult,
    HistoricalFundamentals,
    HistoricalPrice,
    PaperAccount,
    PaperPosition,
    PaperTrade,
    Strategy,
    TradeType,
)


class HistoricalPriceDAO(BaseDAO[HistoricalPrice]):
    """DAO for historical price data."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, HistoricalPrice)

    async def get_price_at_date(
        self, ticker: str, target_date: date
    ) -> HistoricalPrice | None:
        """Get price data for a specific ticker on a specific date.

        Args:
            ticker: Stock ticker symbol
            target_date: Date to get price for

        Returns:
            HistoricalPrice record or None if not found
        """
        stmt = select(HistoricalPrice).where(
            and_(
                HistoricalPrice.ticker == ticker.upper(),
                HistoricalPrice.date == target_date,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_price_range(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[HistoricalPrice]:
        """Get price data for a ticker within a date range.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of HistoricalPrice records ordered by date ascending
        """
        stmt = (
            select(HistoricalPrice)
            .where(
                and_(
                    HistoricalPrice.ticker == ticker.upper(),
                    HistoricalPrice.date >= start_date,
                    HistoricalPrice.date <= end_date,
                )
            )
            .order_by(HistoricalPrice.date.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_price(self, ticker: str) -> HistoricalPrice | None:
        """Get the most recent price data for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Most recent HistoricalPrice record or None
        """
        stmt = (
            select(HistoricalPrice)
            .where(HistoricalPrice.ticker == ticker.upper())
            .order_by(HistoricalPrice.date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def bulk_create(self, prices: list[HistoricalPrice]) -> list[HistoricalPrice]:
        """Bulk insert price records, skipping duplicates.

        Args:
            prices: List of HistoricalPrice records to insert

        Returns:
            List of successfully inserted records
        """
        self.session.add_all(prices)
        await self.session.flush()
        return prices


class HistoricalFundamentalsDAO(BaseDAO[HistoricalFundamentals]):
    """DAO for historical fundamental data."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, HistoricalFundamentals)

    async def get_fundamentals_at_date(
        self, ticker: str, target_date: date
    ) -> HistoricalFundamentals | None:
        """Get fundamentals for a ticker at or before a specific date.

        Uses forward-fill: returns the most recent fundamentals as of target_date.

        Args:
            ticker: Stock ticker symbol
            target_date: Date to get fundamentals for

        Returns:
            Most recent HistoricalFundamentals record on or before target_date
        """
        stmt = (
            select(HistoricalFundamentals)
            .where(
                and_(
                    HistoricalFundamentals.ticker == ticker.upper(),
                    HistoricalFundamentals.quarter_end_date <= target_date,
                )
            )
            .order_by(HistoricalFundamentals.quarter_end_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_fundamentals_range(
        self, ticker: str, start_date: date, end_date: date
    ) -> list[HistoricalFundamentals]:
        """Get all fundamental snapshots within a date range.

        Args:
            ticker: Stock ticker symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of HistoricalFundamentals ordered by quarter_end_date
        """
        stmt = (
            select(HistoricalFundamentals)
            .where(
                and_(
                    HistoricalFundamentals.ticker == ticker.upper(),
                    HistoricalFundamentals.quarter_end_date >= start_date,
                    HistoricalFundamentals.quarter_end_date <= end_date,
                )
            )
            .order_by(HistoricalFundamentals.quarter_end_date.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class StrategyDAO(BaseDAO[Strategy]):
    """DAO for user trading strategies."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Strategy)

    async def get_user_strategies(
        self, user_id: UUID, active_only: bool = True
    ) -> list[Strategy]:
        """Get all strategies for a user.

        Args:
            user_id: User ID
            active_only: If True, only return active strategies

        Returns:
            List of Strategy records ordered by created_at desc
        """
        stmt = select(Strategy).where(Strategy.user_id == user_id)

        if active_only:
            stmt = stmt.where(Strategy.is_active)

        stmt = stmt.order_by(Strategy.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_user(
        self, strategy_id: UUID, user_id: UUID
    ) -> Strategy | None:
        """Get a strategy by ID, ensuring it belongs to the user.

        Args:
            strategy_id: Strategy ID
            user_id: User ID

        Returns:
            Strategy record or None
        """
        stmt = select(Strategy).where(
            and_(Strategy.id == strategy_id, Strategy.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_strategy(self, user_id: UUID, strategy_data: Any) -> Strategy:
        """Create a new strategy.

        Args:
            user_id: User ID
            strategy_data: StrategyCreate schema

        Returns:
            Created Strategy
        """
        # Handle config serialization
        if hasattr(strategy_data.config, "model_dump"):
            config_dict = strategy_data.config.model_dump()
        elif hasattr(strategy_data.config, "dict"):
            config_dict = strategy_data.config.dict()
        else:
            config_dict = strategy_data.config

        strategy = Strategy(
            user_id=user_id,
            name=strategy_data.name,
            description=strategy_data.description,
            config=config_dict,
            is_active=True,
        )
        self.session.add(strategy)
        await self.session.commit()
        await self.session.refresh(strategy)
        return strategy


class PaperAccountDAO(BaseDAO[PaperAccount]):
    """DAO for paper trading accounts."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PaperAccount)

    async def get_user_accounts(
        self, user_id: UUID, active_only: bool = True
    ) -> list[PaperAccount]:
        """Get all paper accounts for a user.

        Args:
            user_id: User ID
            active_only: If True, only return active accounts

        Returns:
            List of PaperAccount records with strategy loaded
        """
        stmt = select(PaperAccount).where(PaperAccount.user_id == user_id)

        if active_only:
            stmt = stmt.where(PaperAccount.is_active)

        stmt = stmt.order_by(PaperAccount.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_and_user(
        self, account_id: UUID, user_id: UUID
    ) -> PaperAccount | None:
        """Get an account by ID, ensuring it belongs to the user.

        Args:
            account_id: Account ID
            user_id: User ID

        Returns:
            PaperAccount record or None
        """
        stmt = select(PaperAccount).where(
            and_(PaperAccount.id == account_id, PaperAccount.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_balance(
        self, account_id: UUID, new_balance: Decimal
    ) -> PaperAccount:
        """Update account balance.

        Args:
            account_id: Account ID
            new_balance: New balance value

        Returns:
            Updated PaperAccount record
        """
        account = await self.get(account_id)
        if not account:
            raise ValueError(f"Paper account {account_id} not found")

        account.current_balance = new_balance
        account.updated_at = datetime.utcnow()
        await self.session.flush()
        return account

    async def create_account(
        self,
        user_id: UUID,
        name: str,
        initial_balance: Decimal,
        strategy_id: UUID,
    ) -> PaperAccount:
        """Create a new paper trading account.

        Args:
            user_id: User ID
            name: Account name
            initial_balance: Initial cash balance
            strategy_id: Associated strategy ID

        Returns:
            Created PaperAccount
        """
        account = PaperAccount(
            user_id=user_id,
            name=name,
            initial_balance=initial_balance,
            current_balance=initial_balance,
            strategy_id=strategy_id,
            is_active=True,
        )
        self.session.add(account)
        await self.session.flush()
        await self.session.refresh(account)
        return account

    async def execute_trade(
        self,
        account_id: UUID,
        ticker: str,
        action: str,
        quantity: int,
        price: Decimal,
        analysis_session_id: UUID | None = None,
    ) -> PaperTrade:
        """Execute a trade, updating account balance and positions.

        Args:
            account_id: Account ID
            ticker: Stock ticker
            action: "BUY" or "SELL"
            quantity: Number of shares
            price: Execution price
            analysis_session_id: Optional analysis session ID

        Returns:
            Created PaperTrade record

        Raises:
            ValueError: If insufficient funds or invalid sell
        """
        # Get account
        account = await self.get_by_id(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        total_value = price * quantity
        trade_type = TradeType(action.lower())

        # Check funds for BUY
        if trade_type == TradeType.BUY:
            if account.current_balance < total_value:
                raise ValueError(
                    f"Insufficient funds: {account.current_balance} < {total_value}"
                )
            account.current_balance -= total_value
        elif trade_type == TradeType.SELL:
            # For SELL, funds increase by total value
            account.current_balance += total_value

        # Create trade record
        trade = PaperTrade(
            account_id=account_id,
            ticker=ticker.upper(),
            trade_type=trade_type,
            quantity=quantity,
            price=price,
            total_value=total_value,
            analysis_session_id=analysis_session_id,
        )
        self.session.add(trade)

        # Update position
        position_dao = PaperPositionDAO(self.session)
        # For SELL, quantity change is negative
        qty_delta = quantity if trade_type == TradeType.BUY else -quantity

        await position_dao.update_position(
            account_id=account_id,
            ticker=ticker,
            quantity_delta=qty_delta,
            price=price,
            trade_type=trade_type,
        )

        account.updated_at = datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(trade)
        return trade


class PaperTradeDAO(BaseDAO[PaperTrade]):
    """DAO for paper trade records."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PaperTrade)

    async def get_account_trades(
        self, account_id: UUID, limit: int = 100
    ) -> list[PaperTrade]:
        """Get trade history for an account.

        Args:
            account_id: Account ID
            limit: Maximum number of trades to return

        Returns:
            List of PaperTrade records ordered by executed_at desc
        """
        stmt = (
            select(PaperTrade)
            .where(PaperTrade.account_id == account_id)
            .order_by(PaperTrade.executed_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_trades_for_ticker(
        self, account_id: UUID, ticker: str
    ) -> list[PaperTrade]:
        """Get all trades for a specific ticker in an account.

        Args:
            account_id: Account ID
            ticker: Stock ticker symbol

        Returns:
            List of PaperTrade records ordered by executed_at
        """
        stmt = (
            select(PaperTrade)
            .where(
                and_(
                    PaperTrade.account_id == account_id,
                    PaperTrade.ticker == ticker.upper(),
                )
            )
            .order_by(PaperTrade.executed_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class PaperPositionDAO(BaseDAO[PaperPosition]):
    """DAO for paper trading positions."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, PaperPosition)

    async def get_account_positions(self, account_id: UUID) -> list[PaperPosition]:
        """Get all open positions for an account.

        Args:
            account_id: Account ID

        Returns:
            List of PaperPosition records
        """
        stmt = select(PaperPosition).where(PaperPosition.account_id == account_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_position(self, account_id: UUID, ticker: str) -> PaperPosition | None:
        """Get a specific position for an account and ticker.

        Args:
            account_id: Account ID
            ticker: Stock ticker symbol

        Returns:
            PaperPosition record or None
        """
        stmt = select(PaperPosition).where(
            and_(
                PaperPosition.account_id == account_id,
                PaperPosition.ticker == ticker.upper(),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_position(
        self,
        account_id: UUID,
        ticker: str,
        quantity_delta: int,
        price: Decimal,
        trade_type: TradeType,
    ) -> PaperPosition | None:
        """Update or create a position based on a trade.

        Args:
            account_id: Account ID
            ticker: Stock ticker symbol
            quantity_delta: Change in quantity (positive for buys, negative for sells)
            price: Trade price
            trade_type: BUY or SELL

        Returns:
            Updated/created PaperPosition or None if position was closed
        """
        position = await self.get_position(account_id, ticker)

        if trade_type == TradeType.BUY:
            if position:
                # Update average entry price using weighted average
                total_cost = (
                    position.average_entry_price * position.quantity
                    + price * quantity_delta
                )
                new_quantity = position.quantity + quantity_delta
                position.average_entry_price = total_cost / new_quantity
                position.quantity = new_quantity
                position.updated_at = datetime.utcnow()
            else:
                # Create new position
                position = PaperPosition(
                    account_id=account_id,
                    ticker=ticker.upper(),
                    quantity=quantity_delta,
                    average_entry_price=price,
                )
                self.session.add(position)

        elif trade_type == TradeType.SELL:
            if not position:
                raise ValueError(f"Cannot sell {ticker}: no open position")

            if quantity_delta > position.quantity:
                raise ValueError(
                    f"Cannot sell {quantity_delta} shares: only {position.quantity} available"
                )

            position.quantity -= quantity_delta
            position.updated_at = datetime.utcnow()

            # Close position if fully sold
            if position.quantity == 0:
                await self.session.delete(position)
                return None

        await self.session.flush()
        return position


class BacktestResultDAO(BaseDAO[BacktestResult]):
    """DAO for backtest results."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, BacktestResult)

    async def get_user_results(
        self, user_id: UUID, limit: int = 50
    ) -> list[BacktestResult]:
        """Get backtest results for a user.

        Args:
            user_id: User ID
            limit: Maximum number of results to return

        Returns:
            List of BacktestResult records ordered by created_at desc
        """
        stmt = (
            select(BacktestResult)
            .where(BacktestResult.user_id == user_id)
            .order_by(BacktestResult.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_results_by_ticker(
        self, user_id: UUID, ticker: str, limit: int = 20
    ) -> list[BacktestResult]:
        """Get backtest results for a specific ticker.

        Args:
            user_id: User ID
            ticker: Stock ticker symbol
            limit: Maximum number of results to return

        Returns:
            List of BacktestResult records ordered by created_at desc
        """
        stmt = (
            select(BacktestResult)
            .where(
                and_(
                    BacktestResult.user_id == user_id,
                    BacktestResult.ticker == ticker.upper(),
                )
            )
            .order_by(BacktestResult.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_results_by_strategy(
        self, user_id: UUID, strategy_id: UUID, limit: int = 20
    ) -> list[BacktestResult]:
        """Get backtest results for a specific strategy.

        Args:
            user_id: User ID
            strategy_id: Strategy ID
            limit: Maximum number of results to return

        Returns:
            List of BacktestResult records ordered by created_at desc
        """
        stmt = (
            select(BacktestResult)
            .where(
                and_(
                    BacktestResult.user_id == user_id,
                    BacktestResult.strategy_id == strategy_id,
                )
            )
            .order_by(BacktestResult.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
