import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Float, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.state.enums import Market, AgentType, Action


class Base(DeclarativeBase):
    pass


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[Market] = mapped_column(SQLEnum(Market))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    agent_reports: Mapped[list["AgentReport"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    final_decision: Mapped[Optional["FinalDecision"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class AgentReport(Base):
    __tablename__ = "agent_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id"))
    agent_type: Mapped[AgentType] = mapped_column(SQLEnum(AgentType))
    report_data: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

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
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    session: Mapped["AnalysisSession"] = relationship(back_populates="final_decision")
