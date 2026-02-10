# backend/db/models/performance.py
"""Performance tracking models."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.ai.state.enums import Action, AgentType

from .base import Base


class AnalysisOutcome(Base):
    """Tracks what actually happened after a recommendation was made."""

    __tablename__ = "analysis_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("analysis_sessions.id"), unique=True
    )
    ticker: Mapped[str] = mapped_column(String(20))
    action_recommended: Mapped[Action] = mapped_column(SQLEnum(Action))
    price_at_recommendation: Mapped[float] = mapped_column(Float)
    price_after_1d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_after_7d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_after_30d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_after_90d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    outcome_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    last_updated: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )


class AgentAccuracy(Base):
    """Tracks accuracy metrics for each agent type over different time periods."""

    __tablename__ = "agent_accuracy"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_type: Mapped[AgentType] = mapped_column(SQLEnum(AgentType))
    period: Mapped[str] = mapped_column(String(10))  # "7d", "30d", "90d"
    total_signals: Mapped[int] = mapped_column(default=0)
    correct_signals: Mapped[int] = mapped_column(default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    last_calculated: Mapped[datetime] = mapped_column(default=datetime.now)
