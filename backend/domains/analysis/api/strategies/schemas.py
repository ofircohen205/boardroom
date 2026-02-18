"""Pydantic schemas for strategy API."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class StrategyWeights(BaseModel):
    """Agent weights configuration."""

    fundamental: float = Field(
        ..., ge=0.0, le=1.0, description="Weight for fundamental analysis (0-1)"
    )
    technical: float = Field(
        ..., ge=0.0, le=1.0, description="Weight for technical analysis (0-1)"
    )
    sentiment: float = Field(
        ..., ge=0.0, le=1.0, description="Weight for sentiment analysis (0-1)"
    )

    @field_validator("fundamental", "technical", "sentiment")
    @classmethod
    def validate_weight_range(cls, v: float) -> float:
        """Validate that weights are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Weight must be between 0.0 and 1.0")
        return v

    @classmethod
    def validate_sum(cls, weights: "StrategyWeights") -> None:
        """Validate that weights sum to 1.0."""
        total = weights.fundamental + weights.technical + weights.sentiment
        if not (0.99 <= total <= 1.01):  # Allow small floating point error
            raise ValueError(f"Weights must sum to 1.0, got {total}")


class StrategyThresholds(BaseModel):
    """Decision thresholds configuration."""

    buy: float = Field(
        70.0, ge=0.0, le=100.0, description="Minimum score to trigger BUY (0-100)"
    )
    sell: float = Field(
        30.0, ge=0.0, le=100.0, description="Maximum score to trigger SELL (0-100)"
    )

    @field_validator("buy", "sell")
    @classmethod
    def validate_threshold_range(cls, v: float) -> float:
        """Validate that thresholds are between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError("Threshold must be between 0.0 and 100.0")
        return v


class StrategyRiskParams(BaseModel):
    """Risk management parameters."""

    max_position_size: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Maximum position size as fraction of capital (0-1)",
    )
    stop_loss: float | None = Field(
        None, ge=0.0, le=1.0, description="Stop loss percentage (e.g., 0.1 = 10%)"
    )
    take_profit: float | None = Field(
        None, ge=0.0, description="Take profit percentage (e.g., 0.2 = 20%)"
    )


class StrategyConfig(BaseModel):
    """Complete strategy configuration."""

    weights: StrategyWeights
    thresholds: StrategyThresholds = Field(
        default_factory=lambda: StrategyThresholds(buy=70.0, sell=30.0)
    )
    risk_params: StrategyRiskParams = Field(
        default_factory=lambda: StrategyRiskParams(
            max_position_size=0.5, stop_loss=None, take_profit=None
        )
    )


class StrategyCreate(BaseModel):
    """Request schema for creating a strategy."""

    name: str = Field(..., min_length=1, max_length=100, description="Strategy name")
    description: str | None = Field(
        None, max_length=500, description="Optional description"
    )
    config: StrategyConfig

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: StrategyConfig) -> StrategyConfig:
        """Validate that weights sum to 1.0."""
        StrategyWeights.validate_sum(v.weights)
        return v


class StrategyUpdate(BaseModel):
    """Request schema for updating a strategy."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    config: StrategyConfig | None = None
    is_active: bool | None = None

    @field_validator("config")
    @classmethod
    def validate_config(cls, v: StrategyConfig | None) -> StrategyConfig | None:
        """Validate that weights sum to 1.0 if config is provided."""
        if v is not None:
            StrategyWeights.validate_sum(v.weights)
        return v


class StrategyResponse(BaseModel):
    """Response schema for strategy."""

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    config: dict[str, Any]  # Stored as JSON in DB
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
