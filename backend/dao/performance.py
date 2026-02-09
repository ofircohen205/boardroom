# backend/dao/performance.py
"""Performance tracking data access objects."""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import AnalysisOutcome, AgentAccuracy
from backend.ai.state.enums import AgentType, Action
from .base import BaseDAO


class PerformanceDAO(BaseDAO[AnalysisOutcome]):
    """Data access object for Performance tracking operations."""

    def __init__(self, session: AsyncSession):
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
    ) -> List[AnalysisOutcome]:
        """Get recent outcomes."""
        result = await self.session.execute(
            select(AnalysisOutcome)
            .order_by(desc(AnalysisOutcome.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

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
