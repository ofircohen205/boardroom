"""Pydantic schemas for paper trading API."""

from datetime import datetime
from decimal import Decimal
from typing import ClassVar, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PaperAccountCreate(BaseModel):
    """Request schema for creating a paper trading account."""

    name: str = Field(..., min_length=1, max_length=100, description="Account name")
    strategy_id: UUID = Field(..., description="Strategy to use for trading")
    initial_balance: Decimal = Field(
        Decimal("10000.00"), gt=0, description="Initial cash balance (default: $10,000)"
    )

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "name": "My Paper Trading Account",
                "strategy_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "initial_balance": 10000.00,
            }
        }


class PaperAccountUpdate(BaseModel):
    """Request schema for updating a paper account."""

    name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None


class PaperPositionResponse(BaseModel):
    """Response schema for a paper trading position."""

    id: UUID
    ticker: str
    quantity: int
    average_entry_price: float
    current_price: float | None
    market_value: float | None = Field(
        None, description="Current market value of position"
    )
    unrealized_pnl: float | None = Field(None, description="Unrealized profit/loss")
    unrealized_pnl_pct: float | None = Field(
        None, description="Unrealized P&L as percentage"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "ticker": "AAPL",
                "quantity": 10,
                "average_entry_price": 150.00,
                "current_price": 155.00,
                "market_value": 1550.00,
                "unrealized_pnl": 50.00,
                "unrealized_pnl_pct": 0.033,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class PaperAccountResponse(BaseModel):
    """Response schema for a paper trading account."""

    id: UUID
    user_id: UUID
    strategy_id: UUID
    name: str
    initial_balance: float
    current_balance: float
    total_value: float | None = Field(
        None, description="Total account value (cash + positions)"
    )
    total_pnl: float | None = Field(None, description="Total profit/loss")
    total_pnl_pct: float | None = Field(None, description="Total P&L as percentage")
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Optional: Include positions and recent trades
    positions: list[PaperPositionResponse] | None = None

    class Config:
        from_attributes = True
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "strategy_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name": "My Paper Account",
                "initial_balance": 10000.00,
                "current_balance": 8500.00,
                "total_value": 10500.00,
                "total_pnl": 500.00,
                "total_pnl_pct": 0.05,
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class PaperTradeRequest(BaseModel):
    """Request schema for executing a paper trade."""

    ticker: str = Field(
        ..., min_length=1, max_length=10, description="Stock ticker symbol"
    )
    trade_type: Literal["BUY", "SELL"] = Field(..., description="Trade type")
    quantity: int = Field(..., gt=0, description="Number of shares to trade")
    price: Decimal | None = Field(
        None,
        gt=0,
        description="Price per share (optional, uses current market price if not provided)",
    )
    analysis_session_id: UUID | None = Field(
        None, description="Optional reference to analysis that triggered this trade"
    )

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "ticker": "AAPL",
                "trade_type": "BUY",
                "quantity": 10,
                "price": 150.25,
                "analysis_session_id": None,
            }
        }


class PaperTradeResponse(BaseModel):
    """Response schema for a paper trade."""

    id: UUID
    account_id: UUID
    ticker: str
    trade_type: Literal["BUY", "SELL"]
    quantity: int
    price: float
    total_value: float
    analysis_session_id: UUID | None
    executed_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "account_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "ticker": "AAPL",
                "trade_type": "BUY",
                "quantity": 10,
                "price": 150.25,
                "total_value": 1502.50,
                "analysis_session_id": None,
                "executed_at": "2024-01-15T10:30:00Z",
            }
        }


class PaperPerformanceResponse(BaseModel):
    """Response schema for paper account performance metrics."""

    account_id: UUID
    initial_balance: float
    current_value: float
    total_return: float = Field(
        ..., description="Total return as decimal (e.g., 0.25 = 25%)"
    )
    total_pnl: float = Field(..., description="Total profit/loss in dollars")
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float = Field(..., description="Win rate as decimal (e.g., 0.65 = 65%)")
    avg_win: float | None = Field(None, description="Average winning trade amount")
    avg_loss: float | None = Field(None, description="Average losing trade amount")
    largest_win: float | None = Field(None, description="Largest winning trade")
    largest_loss: float | None = Field(None, description="Largest losing trade")

    # Time series data for charting
    equity_curve: list[dict] | None = Field(
        None, description="Daily equity values for performance chart"
    )

    class Config:
        json_schema_extra: ClassVar[dict] = {
            "example": {
                "account_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "initial_balance": 10000.00,
                "current_value": 10500.00,
                "total_return": 0.05,
                "total_pnl": 500.00,
                "total_trades": 12,
                "winning_trades": 8,
                "losing_trades": 4,
                "win_rate": 0.67,
                "avg_win": 125.00,
                "avg_loss": -75.00,
                "largest_win": 250.00,
                "largest_loss": -150.00,
            }
        }
