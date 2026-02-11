# backend/services/performance_tracking/service.py
"""
Service for creating and managing analysis outcomes.

When a stock analysis completes with a recommendation, we create an
AnalysisOutcome record to track what actually happens to the price.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Action
from backend.ai.tools.market_data import get_market_data_client
from backend.core.logging import get_logger
from backend.dao.performance import PerformanceDAO
from backend.db.models import AnalysisOutcome, AnalysisSession, FinalDecision
from backend.services.base import BaseService

logger = get_logger(__name__)


class PerformanceService(BaseService):
    """Service for performance tracking operations."""

    def __init__(self, performance_dao: PerformanceDAO):
        """
        Initialize PerformanceService.

        Args:
            performance_dao: DAO for performance tracking operations
        """
        self.performance_dao = performance_dao

    async def create_analysis_outcome(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> Optional[AnalysisOutcome]:
        """
        Create an AnalysisOutcome record for a completed analysis session.

        Args:
            db: Database session
            session_id: ID of the completed analysis session

        Returns:
            Created AnalysisOutcome or None if creation failed
        """
        try:
            # Get the analysis session
            session_query = select(AnalysisSession).where(
                AnalysisSession.id == session_id
            )
            session_result = await db.execute(session_query)
            session = session_result.scalar_one_or_none()

            if not session:
                logger.error(f"Session {session_id} not found")
                return None

            # Get the final decision
            decision_query = select(FinalDecision).where(
                FinalDecision.session_id == session_id
            )
            decision_result = await db.execute(decision_query)
            decision = decision_result.scalar_one_or_none()

            if not decision:
                logger.error(f"No decision found for session {session_id}")
                return None

            # Check if outcome already exists
            existing_query = select(AnalysisOutcome).where(
                AnalysisOutcome.session_id == session_id
            )
            existing_result = await db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                logger.info(f"Outcome already exists for session {session_id}")
                return None

            # Get current price
            try:
                market_data_client = get_market_data_client()
                quote = await market_data_client.get_stock_data(
                    session.ticker, session.market
                )
                current_price = quote["current_price"]
            except Exception as e:
                logger.error(f"Failed to get price for {session.ticker}: {e}")
                return None

            # Create outcome record
            outcome = await self.performance_dao.create(
                session_id=session_id,
                ticker=session.ticker,
                action_recommended=decision.action,
                price_at_recommendation=current_price,
                created_at=datetime.now(),
                last_updated=datetime.now(),
            )

            await db.commit()
            await db.refresh(outcome)

            logger.info(
                f"Created outcome for {session.ticker}: {decision.action.value} @ ${current_price:.2f}"
            )

            return outcome

        except Exception as e:
            logger.error(f"Failed to create analysis outcome: {e}", exc_info=True)
            await db.rollback()
            return None

    async def get_performance_summary(self, db: AsyncSession) -> dict:
        """
        Get overall performance summary across all tracked outcomes.

        Returns:
            Dictionary with performance metrics
        """
        outcomes = await self.performance_dao.get_all()

        if not outcomes:
            return {
                "total_recommendations": 0,
                "correct_count": 0,
                "accuracy": 0.0,
                "by_action": {},
            }

        total = len(outcomes)
        correct = sum(1 for o in outcomes if o.outcome_correct)
        accuracy = correct / total if total > 0 else 0.0

        # Break down by action type
        by_action = {}
        for action in Action:
            action_outcomes = [o for o in outcomes if o.action_recommended == action]
            if action_outcomes:
                action_correct = sum(1 for o in action_outcomes if o.outcome_correct)
                by_action[action.value] = {
                    "total": len(action_outcomes),
                    "correct": action_correct,
                    "accuracy": action_correct / len(action_outcomes),
                }

        return {
            "total_recommendations": total,
            "correct_count": correct,
            "accuracy": accuracy,
            "by_action": by_action,
        }

    async def get_recent_outcomes(
        self,
        db: AsyncSession,
        limit: int = 20,
        ticker: Optional[str] = None,
    ) -> list[dict]:
        """
        Get recent analysis outcomes with details.

        Args:
            db: Database session
            limit: Maximum number of outcomes to return
            ticker: Optional ticker to filter by

        Returns:
            List of outcome dictionaries
        """
        rows = await self.performance_dao.get_recent_outcomes(
            limit=limit, ticker=ticker
        )

        outcomes = []
        for outcome, decision, session in rows:
            # Calculate return if we have follow-up price
            returns = {}
            if outcome.price_after_1d:
                returns["1d"] = (
                    outcome.price_after_1d - outcome.price_at_recommendation
                ) / outcome.price_at_recommendation
            if outcome.price_after_7d:
                returns["7d"] = (
                    outcome.price_after_7d - outcome.price_at_recommendation
                ) / outcome.price_at_recommendation
            if outcome.price_after_30d:
                returns["30d"] = (
                    outcome.price_after_30d - outcome.price_at_recommendation
                ) / outcome.price_at_recommendation
            if outcome.price_after_90d:
                returns["90d"] = (
                    outcome.price_after_90d - outcome.price_at_recommendation
                ) / outcome.price_at_recommendation

            outcomes.append(
                {
                    "ticker": outcome.ticker,
                    "action": outcome.action_recommended.value,
                    "price_at_recommendation": outcome.price_at_recommendation,
                    "confidence": decision.confidence,
                    "outcome_correct": outcome.outcome_correct,
                    "returns": returns,
                    "created_at": outcome.created_at.isoformat(),
                }
            )

        return outcomes
