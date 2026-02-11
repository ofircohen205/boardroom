"""
Database models for backtesting and paper trading.

This module contains all models related to:
- Historical price and fundamental data storage
- User-defined trading strategies
- Paper trading accounts and trades
- Backtest results and configuration
"""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.models.base import Base


class TradeType(str, enum.Enum):
    """Type of trade action."""

    BUY = "buy"
    SELL = "sell"


class BacktestFrequency(str, enum.Enum):
    """Frequency of backtest decision points."""

    DAILY = "daily"
    WEEKLY = "weekly"


class HistoricalPrice(Base):
    """Daily OHLCV price data for backtesting.

    Stores historical price data fetched from Yahoo Finance (or other providers).
    Uses adjusted_close to handle splits and dividends correctly.
    """

    __tablename__ = "historical_prices"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # OHLCV data
    open: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    adjusted_close: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False
    )  # Use this for backtest calculations
    volume: Mapped[int] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_historical_prices_ticker_date"),
        Index("ix_historical_prices_ticker_date", "ticker", "date"),
        CheckConstraint("open > 0", name="ck_historical_prices_open_positive"),
        CheckConstraint("high > 0", name="ck_historical_prices_high_positive"),
        CheckConstraint("low > 0", name="ck_historical_prices_low_positive"),
        CheckConstraint("close > 0", name="ck_historical_prices_close_positive"),
        CheckConstraint(
            "adjusted_close > 0", name="ck_historical_prices_adjusted_close_positive"
        ),
        CheckConstraint("volume >= 0", name="ck_historical_prices_volume_nonnegative"),
    )


class HistoricalFundamentals(Base):
    """Quarterly fundamental data snapshots for backtesting.

    Stores key fundamental metrics at quarterly intervals.
    Used for fundamental scoring in backtests.
    """

    __tablename__ = "historical_fundamentals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    quarter_end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Income statement metrics
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    net_income: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    earnings_per_share: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))

    # Valuation metrics
    pe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    price_to_book: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    price_to_sales: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))

    # Balance sheet metrics
    total_debt: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    total_equity: Mapped[Decimal | None] = mapped_column(Numeric(20, 2))
    debt_to_equity: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))

    # Growth metrics (YoY)
    revenue_growth: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 4)
    )  # e.g., 0.15 = 15% growth
    earnings_growth: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "ticker",
            "quarter_end_date",
            name="uq_historical_fundamentals_ticker_quarter",
        ),
        Index(
            "ix_historical_fundamentals_ticker_quarter", "ticker", "quarter_end_date"
        ),
    )


class Strategy(Base):
    """User-defined trading strategy with customizable agent weights.

    Stores configuration for agent weights and risk parameters.
    Can be applied to backtests or live paper trading.
    """

    __tablename__ = "strategies"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))

    # Strategy configuration stored as JSON
    # Example: {
    #   "weights": {"fundamental": 0.3, "technical": 0.4, "sentiment": 0.3},
    #   "thresholds": {"buy": 70, "sell": 30},
    #   "risk_params": {"max_position_size": 0.5, "stop_loss": 0.1}
    # }
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="strategies")
    paper_accounts: Mapped[list["PaperAccount"]] = relationship(
        back_populates="strategy", cascade="all, delete-orphan"
    )


class PaperAccount(Base):
    """Virtual trading account for paper trading simulation.

    Tracks cash balance, positions, and overall performance.
    Linked to a specific strategy that determines trade decisions.
    """

    __tablename__ = "paper_accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    strategy_id: Mapped[UUID] = mapped_column(
        ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    initial_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="paper_accounts")
    strategy: Mapped[Strategy] = relationship(back_populates="paper_accounts")
    trades: Mapped[list["PaperTrade"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
        order_by="PaperTrade.executed_at.desc()",
    )
    positions: Mapped[list["PaperPosition"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "initial_balance > 0", name="ck_paper_accounts_initial_balance_positive"
        ),
        CheckConstraint(
            "current_balance >= 0", name="ck_paper_accounts_current_balance_nonnegative"
        ),
    )


class PaperTrade(Base):
    """Record of a paper trade execution.

    Tracks all buy/sell transactions in a paper account.
    Used for trade history and P&L calculation.
    """

    __tablename__ = "paper_trades"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    trade_type: Mapped[TradeType] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )  # quantity * price

    # Optional reference to the analysis that triggered this trade
    analysis_session_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("analysis_sessions.id", ondelete="SET NULL"), index=True
    )

    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    account: Mapped[PaperAccount] = relationship(back_populates="trades")
    analysis_session: Mapped["AnalysisSession | None"] = relationship()

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_paper_trades_quantity_positive"),
        CheckConstraint("price > 0", name="ck_paper_trades_price_positive"),
        CheckConstraint("total_value > 0", name="ck_paper_trades_total_value_positive"),
        Index("ix_paper_trades_account_executed", "account_id", "executed_at"),
    )


class PaperPosition(Base):
    """Current open position in a paper account.

    Tracks quantity and average entry price for each ticker.
    Updated as trades are executed.
    """

    __tablename__ = "paper_positions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )

    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    average_entry_price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    # Cached current value (updated periodically from live prices)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    last_price_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    account: Mapped[PaperAccount] = relationship(back_populates="positions")

    __table_args__ = (
        UniqueConstraint(
            "account_id", "ticker", name="uq_paper_positions_account_ticker"
        ),
        CheckConstraint("quantity > 0", name="ck_paper_positions_quantity_positive"),
        CheckConstraint(
            "average_entry_price > 0", name="ck_paper_positions_entry_price_positive"
        ),
    )


class BacktestResult(Base):
    """Results from a completed backtest run.

    Stores backtest configuration, performance metrics, and equity curve.
    """

    __tablename__ = "backtest_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    strategy_id: Mapped[UUID] = mapped_column(
        ForeignKey("strategies.id", ondelete="SET NULL"), index=True
    )

    # Backtest configuration
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    initial_capital: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    check_frequency: Mapped[BacktestFrequency] = mapped_column(nullable=False)
    position_size_pct: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False
    )  # 0.500 = 50%

    # Optional risk parameters
    stop_loss_pct: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    take_profit_pct: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))

    # Performance metrics
    total_return: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False
    )  # e.g., 0.25 = 25%
    annualized_return: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    sharpe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    max_drawdown: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False
    )  # e.g., -0.15 = -15%
    win_rate: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False
    )  # 0.65 = 65%
    total_trades: Mapped[int] = mapped_column(nullable=False)

    # Benchmark comparison
    buy_and_hold_return: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)

    # Detailed results stored as JSON
    # equity_curve: [{date: "2024-01-15", equity: 10500.25}]
    # trades: [{date: "2024-01-15", type: "buy", quantity: 10, price: 150.0, total: 1500.0}]
    equity_curve: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    trades: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)

    # Execution metadata
    execution_time_seconds: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="backtest_results")
    strategy: Mapped[Strategy | None] = relationship()

    __table_args__ = (
        CheckConstraint(
            "initial_capital > 0", name="ck_backtest_results_initial_capital_positive"
        ),
        CheckConstraint(
            "position_size_pct > 0 AND position_size_pct <= 1",
            name="ck_backtest_results_position_size_valid",
        ),
        CheckConstraint("total_trades >= 0", name="ck_backtest_results_trades_valid"),
        CheckConstraint(
            "win_rate >= 0 AND win_rate <= 1", name="ck_backtest_results_win_rate_valid"
        ),
        Index("ix_backtest_results_user_created", "user_id", "created_at"),
    )
