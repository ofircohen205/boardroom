# backend/db/models/portfolio.py
"""Portfolio and watchlist models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.ai.state.enums import Market

from .base import Base

if TYPE_CHECKING:
    from .user import User


class Watchlist(Base):
    """User's watchlist of stocks to monitor."""

    __tablename__ = "watchlists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    name: Mapped[str] = mapped_column(String(100), default="Default")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="watchlists")
    items: Mapped[list["WatchlistItem"]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan"
    )


class WatchlistItem(Base):
    """Individual stock in a watchlist."""

    __tablename__ = "watchlist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    watchlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("watchlists.id")
    )
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[Market] = mapped_column(SQLEnum(Market))
    added_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    watchlist: Mapped["Watchlist"] = relationship(back_populates="items")


class Portfolio(Base):
    """User's portfolio of actual positions."""

    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    name: Mapped[str] = mapped_column(String(100), default="My Portfolio")
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="portfolios")
    positions: Mapped[list["Position"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )


class Position(Base):
    """Individual position in a portfolio."""

    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolios.id")
    )
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[Market] = mapped_column(SQLEnum(Market))
    quantity: Mapped[float] = mapped_column(Float)
    avg_entry_price: Mapped[float] = mapped_column(Float)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(default=datetime.now)
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")
