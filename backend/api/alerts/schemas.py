# backend/api/alerts/schemas.py
"""Pydantic schemas for alerts API."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class PriceAlertCreate(BaseModel):
    """Schema for creating a price alert."""
    ticker: str = Field(..., min_length=1, max_length=20, description="Stock ticker symbol")
    market: str = Field(..., pattern="^(US|TASE)$", description="Market (US or TASE)")
    condition: str = Field(..., pattern="^(above|below|change_pct)$", description="Alert condition")
    target_value: float = Field(..., gt=0, description="Target price or percentage")

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        """Convert ticker to uppercase."""
        return v.upper()


class PriceAlertSchema(BaseModel):
    """Schema for price alert response."""
    id: UUID
    ticker: str
    market: str
    condition: str
    target_value: float
    triggered: bool
    triggered_at: datetime | None = None
    cooldown_until: datetime | None = None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PriceAlertToggle(BaseModel):
    """Schema for toggling alert active status."""
    active: bool
