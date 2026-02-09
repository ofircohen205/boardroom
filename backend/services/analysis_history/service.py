# backend/services/analysis_history/service.py
"""Analysis history service - manages analysis sessions and results."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.analysis import AnalysisDAO
from backend.db.models import AnalysisSession, AgentReport, FinalDecision
from backend.ai.state.enums import Market, AgentType, Action


async def create_analysis_session(
    ticker: str,
    market: Market,
    user_id: Optional[UUID],
    db: AsyncSession
) -> AnalysisSession:
    """Create a new analysis session."""
    dao = AnalysisDAO(db)
    session = await dao.create_session(ticker, market, user_id)
    await db.commit()
    await db.refresh(session)
    return session


async def save_agent_report(
    session_id: UUID,
    agent_type: AgentType,
    report_data: dict,
    db: AsyncSession
) -> AgentReport:
    """Save an agent's report to a session."""
    dao = AnalysisDAO(db)
    report = await dao.add_report(session_id, agent_type, report_data)
    await db.commit()
    await db.refresh(report)
    return report


async def save_final_decision(
    session_id: UUID,
    action: Action,
    confidence: float,
    rationale: str,
    vetoed: bool,
    veto_reason: Optional[str],
    db: AsyncSession
) -> FinalDecision:
    """Save the final trading decision for a session."""
    dao = AnalysisDAO(db)
    decision = await dao.add_decision(
        session_id=session_id,
        action=action,
        confidence=confidence,
        rationale=rationale,
        vetoed=vetoed,
        veto_reason=veto_reason,
    )
    await db.commit()
    await db.refresh(decision)
    return decision


async def get_user_analysis_history(
    user_id: UUID,
    limit: int,
    db: AsyncSession
) -> List[AnalysisSession]:
    """Get analysis history for a user."""
    dao = AnalysisDAO(db)
    return await dao.get_user_sessions(user_id, limit)
