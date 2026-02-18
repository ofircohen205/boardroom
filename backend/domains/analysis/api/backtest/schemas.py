"""Pydantic schemas for backtest API."""

from datetime import date
from decimal import Decimal
from typing import ClassVar, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BacktestConfigRequest(BaseModel):
    """Request schema for starting a backtest."""

    ticker: str = Field(
        ..., min_length=1, max_length=10, description="Stock ticker symbol"
    )
    strategy_id: UUID = Field(..., description="Strategy ID to use for backtesting")
    start_date: date = Field(..., description="Start date for backtest (YYYY-MM-DD)")
    end_date: date = Field(..., description="End date for backtest (YYYY-MM-DD)")
    initial_capital: Decimal = Field(
        Decimal("10000.00"),
        gt=0,
        description="Initial capital for backtest (default: $10,000)",
    )
    check_frequency: Literal["daily", "weekly"] = Field(
        "daily", description="Trading decision frequency (default: daily)"
    )
    position_size_pct: Decimal = Field(
        Decimal("0.5"),
        gt=0,
        le=1,
        description="Position size as fraction of capital (default: 0.5 = 50%)",
    )
    stop_loss_pct: Decimal | None = Field(
        None, ge=0, le=1, description="Optional stop loss percentage (e.g., 0.1 = 10%)"
    )
    take_profit_pct: Decimal | None = Field(
        None, ge=0, description="Optional take profit percentage (e.g., 0.2 = 20%)"
    )

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "ticker": "AAPL",
                "strategy_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 10000.00,
                "check_frequency": "daily",
                "position_size_pct": 0.5,
                "stop_loss_pct": 0.1,
                "take_profit_pct": 0.2,
            }
        }


class TradeResponse(BaseModel):
    """Response schema for a trade record."""

    date: str = Field(..., description="Trade date (ISO format)")
    type: Literal["BUY", "SELL"] = Field(..., description="Trade type")
    quantity: int = Field(..., description="Number of shares")
    price: float = Field(..., description="Price per share")
    total: float = Field(..., description="Total trade value")
    commission: float = Field(0.0, description="Commission paid (default: 0)")

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "date": "2023-03-15",
                "type": "BUY",
                "quantity": 10,
                "price": 150.25,
                "total": 1502.50,
                "commission": 0.0,
            }
        }


class EquityPointResponse(BaseModel):
    """Response schema for an equity curve point."""

    date: str = Field(..., description="Date (ISO format)")
    equity: float = Field(..., description="Total portfolio equity")
    cash: float = Field(..., description="Cash balance")
    position_value: float = Field(..., description="Value of open positions")

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "date": "2023-03-15",
                "equity": 10500.00,
                "cash": 5000.00,
                "position_value": 5500.00,
            }
        }


class BacktestResultResponse(BaseModel):
    """Response schema for backtest results."""

    id: UUID | None = Field(None, description="Backtest result ID (if saved)")
    ticker: str
    strategy_id: UUID
    start_date: str
    end_date: str
    initial_capital: float

    # Performance metrics
    total_return: float = Field(
        ..., description="Total return as decimal (e.g., 0.25 = 25%)"
    )
    annualized_return: float = Field(..., description="Annualized return")
    sharpe_ratio: float | None = Field(
        None, description="Sharpe ratio (risk-adjusted return)"
    )
    max_drawdown: float = Field(
        ..., description="Maximum drawdown as decimal (e.g., -0.15 = -15%)"
    )
    win_rate: float = Field(..., description="Win rate as decimal (e.g., 0.65 = 65%)")
    total_trades: int = Field(..., description="Total number of trades executed")

    # Benchmark comparison
    buy_and_hold_return: float = Field(..., description="Buy-and-hold benchmark return")

    # Detailed data
    equity_curve: list[EquityPointResponse] = Field(
        ..., description="Equity curve over time"
    )
    trades: list[TradeResponse] = Field(..., description="All trades executed")

    # Execution metadata
    execution_time_seconds: float | None = Field(
        None, description="Backtest execution time"
    )

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "ticker": "AAPL",
                "strategy_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 10000.00,
                "total_return": 0.35,
                "annualized_return": 0.35,
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.12,
                "win_rate": 0.67,
                "total_trades": 12,
                "buy_and_hold_return": 0.48,
                "equity_curve": [],
                "trades": [],
                "execution_time_seconds": 2.5,
            }
        }


class BacktestProgressMessage(BaseModel):
    """WebSocket message for backtest progress updates."""

    type: Literal[
        "backtest_started", "backtest_progress", "backtest_completed", "backtest_error"
    ]
    data: dict

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "examples": [
                {
                    "type": "backtest_started",
                    "data": {
                        "ticker": "AAPL",
                        "start_date": "2023-01-01",
                        "end_date": "2023-12-31",
                    },
                },
                {
                    "type": "backtest_progress",
                    "data": {
                        "current_date": "2023-06-15",
                        "progress_pct": 45.5,
                        "trades_executed": 5,
                        "current_equity": 10500.00,
                    },
                },
                {
                    "type": "backtest_completed",
                    "data": {
                        "total_return": 0.35,
                        "total_trades": 12,
                        "execution_time": 2.5,
                    },
                },
                {
                    "type": "backtest_error",
                    "data": {"error": "Insufficient historical data for INVALID"},
                },
            ]
        }
