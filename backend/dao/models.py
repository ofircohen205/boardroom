import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Float, Boolean, Text, Enum as SQLEnum, LargeBinary
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.core.enums import LLMProvider
from backend.ai.state.enums import Market, AgentType, Action


class Base(DeclarativeBase):
    pass



class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[Market] = mapped_column(SQLEnum(Market))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    user: Mapped[Optional["User"]] = relationship(back_populates="analysis_sessions")
    agent_reports: Mapped[list["AgentReport"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    final_decision: Mapped[Optional["FinalDecision"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class AgentReport(Base):
    __tablename__ = "agent_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id"))
    agent_type: Mapped[AgentType] = mapped_column(SQLEnum(AgentType))
    report_data: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    session: Mapped["AnalysisSession"] = relationship(back_populates="agent_reports")


class FinalDecision(Base):
    __tablename__ = "final_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id"), unique=True)
    action: Mapped[Action] = mapped_column(SQLEnum(Action))
    confidence: Mapped[float] = mapped_column(Float)
    rationale: Mapped[str] = mapped_column(Text)
    vetoed: Mapped[bool] = mapped_column(Boolean, default=False)
    veto_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    session: Mapped["AnalysisSession"] = relationship(back_populates="final_decision")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    watchlists: Mapped[list["Watchlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    analysis_sessions: Mapped[list["AnalysisSession"]] = relationship(back_populates="user")
    api_keys: Mapped[list["UserAPIKey"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserAPIKey(Base):
    __tablename__ = "user_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    provider: Mapped[LLMProvider] = mapped_column(SQLEnum(LLMProvider))
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="api_keys")


class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100), default="Default")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="watchlists")
    items: Mapped[list["WatchlistItem"]] = relationship(back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watchlist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("watchlists.id"))
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[Market] = mapped_column(SQLEnum(Market))
    added_at: Mapped[datetime] = mapped_column(default=datetime.now)

    watchlist: Mapped["Watchlist"] = relationship(back_populates="items")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100), default="My Portfolio")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="portfolios")
    positions: Mapped[list["Position"]] = relationship(back_populates="portfolio", cascade="all, delete-orphan")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id"))
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[Market] = mapped_column(SQLEnum(Market))
    quantity: Mapped[float] = mapped_column(Float)
    avg_entry_price: Mapped[float] = mapped_column(Float)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(default=datetime.now)
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")


# Phase 2: Performance Tracking Models

class AnalysisOutcome(Base):
    """Tracks what actually happened after a recommendation was made."""
    __tablename__ = "analysis_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id"), unique=True)
    ticker: Mapped[str] = mapped_column(String(20))
    action_recommended: Mapped[Action] = mapped_column(SQLEnum(Action))
    price_at_recommendation: Mapped[float] = mapped_column(Float)
    price_after_1d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_after_7d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_after_30d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_after_90d: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    outcome_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    last_updated: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)


class AgentAccuracy(Base):
    """Tracks accuracy metrics for each agent type over different time periods."""
    __tablename__ = "agent_accuracy"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type: Mapped[AgentType] = mapped_column(SQLEnum(AgentType))
    period: Mapped[str] = mapped_column(String(10))  # "7d", "30d", "90d"
    total_signals: Mapped[int] = mapped_column(default=0)
    correct_signals: Mapped[int] = mapped_column(default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    last_calculated: Mapped[datetime] = mapped_column(default=datetime.now)
