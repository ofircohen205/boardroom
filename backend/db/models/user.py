# backend/db/models/user.py
"""User and authentication models."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, LargeBinary, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.enums import LLMProvider

from .base import Base

if TYPE_CHECKING:
    from .alerts import Notification, PriceAlert, ScheduledAnalysis
    from .analysis import AnalysisSession
    from .backtesting import BacktestResult, PaperAccount, Strategy
    from .portfolio import Portfolio, Watchlist


class User(Base):
    """User account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    watchlists: Mapped[list["Watchlist"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    portfolios: Mapped[list["Portfolio"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    analysis_sessions: Mapped[list["AnalysisSession"]] = relationship(
        back_populates="user"
    )
    api_keys: Mapped[list["UserAPIKey"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    price_alerts: Mapped[list["PriceAlert"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    scheduled_analyses: Mapped[list["ScheduledAnalysis"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    strategies: Mapped[list["Strategy"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    paper_accounts: Mapped[list["PaperAccount"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    backtest_results: Mapped[list["BacktestResult"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserAPIKey(Base):
    """User's encrypted API keys for LLM providers."""

    __tablename__ = "user_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    provider: Mapped[LLMProvider] = mapped_column(SQLEnum(LLMProvider))
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="api_keys")
