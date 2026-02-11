# backend/api/schedules/schemas.py
"""Pydantic schemas for scheduled analysis API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ScheduledAnalysisCreate(BaseModel):
    """Schema for creating a scheduled analysis."""

    ticker: str = Field(
        ..., min_length=1, max_length=20, description="Stock ticker symbol"
    )
    market: str = Field(..., pattern="^(US|TASE)$", description="Market (US or TASE)")
    frequency: str = Field(
        ..., pattern="^(daily|weekly|on_change)$", description="Schedule frequency"
    )

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, v: str) -> str:
        """Convert ticker to uppercase."""
        return v.upper()


class ScheduledAnalysisSchema(BaseModel):
    """Schema for scheduled analysis response."""

    id: UUID
    ticker: str
    market: str
    frequency: str
    last_run: datetime | None = None
    next_run: datetime | None = None
    active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduledAnalysisToggle(BaseModel):
    """Schema for toggling schedule active status."""

    active: bool
