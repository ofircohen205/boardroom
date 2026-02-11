# backend/services/analysis_history/service.py
"""Analysis history service - manages analysis sessions and results."""
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Action, AgentType, Market
from backend.dao.analysis import AnalysisDAO
from backend.db.models import AgentReport, AnalysisSession, FinalDecision
from backend.services.analysis.service import AnalysisService


# For backward compatibility, keep module-level functions using AnalysisService
async def create_analysis_session(
    ticker: str, market: Market, user_id: Optional[UUID], db: AsyncSession
) -> AnalysisSession:
    """Create a new analysis session. Deprecated: Use AnalysisService directly."""
    service = AnalysisService(AnalysisDAO(db))
    return await service.create_analysis_session(ticker, market, user_id, db)


async def save_agent_report(
    session_id: UUID, agent_type: AgentType, report_data: dict, db: AsyncSession
) -> AgentReport:
    """Save an agent's report to a session. Deprecated: Use AnalysisService directly."""
    service = AnalysisService(AnalysisDAO(db))
    return await service.save_agent_report(session_id, agent_type, report_data, db)


async def save_final_decision(
    session_id: UUID,
    action: Action,
    confidence: float,
    rationale: str,
    vetoed: bool,
    veto_reason: Optional[str],
    db: AsyncSession,
) -> FinalDecision:
    """Save the final trading decision for a session. Deprecated: Use AnalysisService directly."""
    service = AnalysisService(AnalysisDAO(db))
    return await service.save_final_decision(
        session_id, action, confidence, rationale, vetoed, veto_reason, db
    )


async def get_user_analysis_history(
    user_id: UUID, limit: int, db: AsyncSession
) -> List[AnalysisSession]:
    """Get analysis history for a user. Deprecated: Use AnalysisService directly."""
    service = AnalysisService(AnalysisDAO(db))
    return await service.get_user_analysis_history(user_id, limit)
