# backend/dao/analysis.py
"""Analysis session data access objects."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Action, AgentType, Market
from backend.db.models import AgentReport, AnalysisSession, FinalDecision

from .base import BaseDAO


class AnalysisDAO(BaseDAO[AnalysisSession]):
    """Data access object for Analysis operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AnalysisSession)

    async def create_session(
        self,
        ticker: str,
        market: Market,
        user_id: Optional[UUID] = None,
    ) -> AnalysisSession:
        """Create a new analysis session."""
        return await self.create(
            ticker=ticker,
            market=market,
            user_id=user_id,
        )

    async def add_report(
        self,
        session_id: UUID,
        agent_type: AgentType,
        report_data: dict,
    ) -> AgentReport:
        """Add an agent report to a session."""
        report = AgentReport(
            session_id=session_id,
            agent_type=agent_type,
            report_data=report_data,
        )
        self.session.add(report)
        await self.session.flush()
        await self.session.refresh(report)
        return report

    async def add_decision(
        self,
        session_id: UUID,
        action: Action,
        confidence: float,
        rationale: str,
        vetoed: bool = False,
        veto_reason: Optional[str] = None,
    ) -> FinalDecision:
        """Add a final decision to a session."""
        decision = FinalDecision(
            session_id=session_id,
            action=action,
            confidence=confidence,
            rationale=rationale,
            vetoed=vetoed,
            veto_reason=veto_reason,
        )
        self.session.add(decision)
        await self.session.flush()
        await self.session.refresh(decision)
        return decision

    async def get_user_sessions(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> List[AnalysisSession]:
        """Get analysis sessions for a user, most recent first."""
        result = await self.session.execute(
            select(AnalysisSession)
            .where(AnalysisSession.user_id == user_id)
            .order_by(desc(AnalysisSession.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
