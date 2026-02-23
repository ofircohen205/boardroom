# backend/dao/performance.py
"""Performance tracking data access objects."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.ai.state.enums import Action, AgentType
from backend.shared.db.models import (
    AgentAccuracy,
    AnalysisOutcome,
    AnalysisSession,
    FinalDecision,
)

from .base import BaseDAO


class PerformanceDAO(BaseDAO[AnalysisOutcome]):
    """Data access object for Performance tracking operations."""

    def __init__(self, session: AsyncSession):
        """Initialize PerformanceDAO with a database session."""
        super().__init__(session, AnalysisOutcome)

    async def create_outcome(
        self,
        session_id: UUID,
        ticker: str,
        action_recommended: Action,
        price_at_recommendation: float,
    ) -> AnalysisOutcome:
        """Create a new analysis outcome record."""
        return await self.create(
            session_id=session_id,
            ticker=ticker,
            action_recommended=action_recommended,
            price_at_recommendation=price_at_recommendation,
        )

    async def get_by_session_id(self, session_id: UUID) -> Optional[AnalysisOutcome]:
        """Get outcome by analysis session ID."""
        result = await self.session.execute(
            select(AnalysisOutcome).where(AnalysisOutcome.session_id == session_id)
        )
        return result.scalars().first()

    async def get_recent_outcomes(
        self,
        limit: int = 50,
        ticker: Optional[str] = None,
    ) -> List[tuple[AnalysisOutcome, FinalDecision, AnalysisSession]]:
        """Get recent outcomes with decision and session details."""
        from backend.shared.db.models import AnalysisSession, FinalDecision

        query = (
            select(AnalysisOutcome, FinalDecision, AnalysisSession)
            .join(AnalysisSession, AnalysisOutcome.session_id == AnalysisSession.id)
            .join(FinalDecision, AnalysisOutcome.session_id == FinalDecision.session_id)
            .order_by(desc(AnalysisOutcome.created_at))
            .limit(limit)
        )

        if ticker:
            query = query.where(AnalysisOutcome.ticker == ticker)

        result = await self.session.execute(query)
        return [tuple(row) for row in result.all()]

    async def get_agent_accuracy(
        self,
        agent_type: AgentType,
        period: str,
    ) -> Optional[AgentAccuracy]:
        """Get agent accuracy record for a specific period."""
        result = await self.session.execute(
            select(AgentAccuracy)
            .where(AgentAccuracy.agent_type == agent_type)
            .where(AgentAccuracy.period == period)
        )
        return result.scalars().first()

    async def get_analysis_session(self, session_id: UUID) -> Optional[AnalysisSession]:
        """Get an analysis session by ID."""
        result = await self.session.execute(
            select(AnalysisSession).where(AnalysisSession.id == session_id)
        )
        return result.scalars().first()

    async def get_final_decision(self, session_id: UUID) -> Optional[FinalDecision]:
        """Get the final decision for an analysis session."""
        result = await self.session.execute(
            select(FinalDecision).where(FinalDecision.session_id == session_id)
        )
        return result.scalars().first()

    async def get_timeline_outcomes(self, days: int) -> List[AnalysisOutcome]:
        """Get analysis outcomes from the last N days."""
        from datetime import datetime, timedelta

        start_date = datetime.now() - timedelta(days=days)
        result = await self.session.execute(
            select(AnalysisOutcome)
            .where(AnalysisOutcome.created_at >= start_date)
            .order_by(AnalysisOutcome.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_all_agent_accuracy(self) -> List[AgentAccuracy]:
        """Get all agent accuracy records."""
        result = await self.session.execute(select(AgentAccuracy))
        return list(result.scalars().all())

    async def get_agent_detailed_accuracy(
        self, agent_enum: AgentType
    ) -> List[AgentAccuracy]:
        """Get detailed accuracy records for a specific agent."""
        result = await self.session.execute(
            select(AgentAccuracy).where(AgentAccuracy.agent_type == agent_enum)
        )
        return list(result.scalars().all())

    async def get_ticker_history(self, ticker: str) -> List[AnalysisOutcome]:
        """Get history of outcomes for a specific ticker."""
        result = await self.session.execute(
            select(AnalysisOutcome)
            .where(AnalysisOutcome.ticker == ticker)
            .order_by(AnalysisOutcome.created_at.desc())
        )
        return list(result.scalars().all())
