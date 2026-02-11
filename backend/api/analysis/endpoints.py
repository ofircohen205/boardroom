# backend/api/analysis/endpoints.py
"""Analysis history endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.auth.dependencies import get_current_user
from backend.db.models import User
from backend.services.analysis.service import AnalysisService
from backend.services.dependencies import get_analysis_service

from .schemas import AnalysisHistoryItemSchema, DecisionSchema

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("")
async def get_analysis_history(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 50,
    service: AnalysisService = Depends(get_analysis_service),
) -> list[AnalysisHistoryItemSchema]:
    """Get analysis history for current user."""
    sessions = await service.get_user_analysis_history(current_user.id, limit)
    return [
        AnalysisHistoryItemSchema(
            id=s.id,
            ticker=s.ticker,
            market=s.market.value,
            created_at=s.created_at,
            decision=DecisionSchema(
                action=s.final_decision.action.value,
                confidence=s.final_decision.confidence,
                rationale=s.final_decision.rationale,
            )
            if s.final_decision
            else None,
        )
        for s in sessions
    ]
