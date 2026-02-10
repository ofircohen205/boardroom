# backend/db/models/alerts.py
"""Alert and notification models."""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Float, Boolean, Index, Enum as SQLEnum, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.ai.state.enums import Market
from .base import Base

if TYPE_CHECKING:
    from .user import User


class AlertCondition(str, Enum):
    """Condition type for price alerts."""
    ABOVE = "above"  # Trigger when price goes above target
    BELOW = "below"  # Trigger when price goes below target
    CHANGE_PCT = "change_pct"  # Trigger when price changes by target percentage


class NotificationType(str, Enum):
    """Type of notification."""
    PRICE_ALERT = "price_alert"
    ANALYSIS_COMPLETE = "analysis_complete"
    RECOMMENDATION_CHANGE = "recommendation_change"
    VETO_ALERT = "veto_alert"


class AlertFrequency(str, Enum):
    """Frequency for scheduled analysis."""
    DAILY = "daily"  # Run daily at 8 AM ET before market open
    WEEKLY = "weekly"  # Run weekly on Monday at 8 AM ET
    ON_CHANGE = "on_change"  # Run every hour during market hours


class PriceAlert(Base):
    """Price alert for a stock ticker."""
    __tablename__ = "price_alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    market: Mapped[Market] = mapped_column(SQLEnum(Market))
    condition: Mapped[AlertCondition] = mapped_column(SQLEnum(AlertCondition))
    target_value: Mapped[float] = mapped_column(Float)
    baseline_price: Mapped[float | None] = mapped_column(Float, default=None)  # For change_pct alerts
    triggered: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    triggered_at: Mapped[datetime | None] = mapped_column(default=None)
    cooldown_until: Mapped[datetime | None] = mapped_column(default=None)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="price_alerts")

    # Composite index for efficient job queries
    __table_args__ = (
        Index('ix_price_alerts_ticker_active', 'ticker', 'active'),
        Index('ix_price_alerts_triggered_active', 'triggered', 'active'),
    )


class Notification(Base):
    """User notification."""
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    type: Mapped[NotificationType] = mapped_column(SQLEnum(NotificationType))
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON, default=dict)  # Ticker, price, action, etc.
    read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, index=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications")

    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_notifications_user_read', 'user_id', 'read'),
        Index('ix_notifications_user_created', 'user_id', 'created_at'),
    )


class ScheduledAnalysis(Base):
    """Scheduled analysis for automatic stock analysis."""
    __tablename__ = "scheduled_analyses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[Market] = mapped_column(SQLEnum(Market))
    frequency: Mapped[AlertFrequency] = mapped_column(SQLEnum(AlertFrequency))
    last_run: Mapped[datetime | None] = mapped_column(default=None)
    next_run: Mapped[datetime | None] = mapped_column(default=None, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="scheduled_analyses")

    # Index for efficient job queries
    __table_args__ = (
        Index('ix_scheduled_analyses_next_run_active', 'next_run', 'active'),
    )
