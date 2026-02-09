# backend/db/models/user.py
"""User and authentication models."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, LargeBinary, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.enums import LLMProvider
from .base import Base

if TYPE_CHECKING:
    from .portfolio import Watchlist, Portfolio
    from .analysis import AnalysisSession


class User(Base):
    """User account."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    watchlists: Mapped[list["Watchlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    portfolios: Mapped[list["Portfolio"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    analysis_sessions: Mapped[list["AnalysisSession"]] = relationship(back_populates="user")
    api_keys: Mapped[list["UserAPIKey"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserAPIKey(Base):
    """User's encrypted API keys for LLM providers."""
    __tablename__ = "user_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    provider: Mapped[LLMProvider] = mapped_column(SQLEnum(LLMProvider))
    encrypted_key: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="api_keys")
