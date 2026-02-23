# backend/services/performance/service.py
"""
Service for creating and managing analysis outcomes.

When a stock analysis completes with a recommendation, we create an
AnalysisOutcome record to track what actually happens to the price.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.ai.state.enums import Action, AgentType
from backend.shared.ai.tools.market_data import get_market_data_client
from backend.shared.core.logging import get_logger
from backend.shared.dao.performance import PerformanceDAO
from backend.shared.db.models import AgentAccuracy, AnalysisOutcome
from backend.shared.services.base import BaseService

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
            db: Database session (deprecated, use self.performance_dao.session)
            session_id: ID of the completed analysis session

        Returns:
            Created AnalysisOutcome or None if creation failed
        """
        try:
            # Get the analysis session
            session = await self.performance_dao.get_analysis_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return None

            # Get the final decision
            decision = await self.performance_dao.get_final_decision(session_id)
            if not decision:
                logger.error(f"No decision found for session {session_id}")
                return None

            # Check if outcome already exists
            existing_outcome = await self.performance_dao.get_by_session_id(session_id)
            if existing_outcome:
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
            outcome = await self.performance_dao.create_outcome(
                session_id=session_id,
                ticker=session.ticker,
                action_recommended=decision.action,
                price_at_recommendation=current_price,
            )

            # Note: create() handles commit and refresh inside BaseDAO
            logger.info(
                f"Created outcome for {session.ticker}: {decision.action.value} @ ${current_price:.2f}"
            )

            return outcome

        except Exception as e:
            logger.error(f"Failed to create analysis outcome: {e}", exc_info=True)
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

    async def get_performance_timeline(
        self, db: AsyncSession, days: int = 30
    ) -> list[dict]:
        """
        Get accuracy timeline over the last N days.

        Args:
            db: Database session
            days: Number of days to look back

        Returns:
            List of dictionaries with date, accuracy, and total_decisions
        """
        outcomes = await self.performance_dao.get_timeline_outcomes(days)

        # Group by date (YYYY-MM-DD)
        daily_stats = {}
        for o in outcomes:
            date_str = o.created_at.strftime("%Y-%m-%d")
            if date_str not in daily_stats:
                daily_stats[date_str] = {"total": 0, "correct": 0}

            daily_stats[date_str]["total"] += 1
            if o.outcome_correct:
                daily_stats[date_str]["correct"] += 1

        # Format the result
        timeline = []
        # Create a zeroed entry for missing days up to today to ensure a continuous line chart could be rendered if needed (optional, just building the existing points is safer for now based on the previous implementation)
        for date_str, stats in daily_stats.items():
            total = stats["total"]
            correct = stats["correct"]
            accuracy = correct / total if total > 0 else 0.0

            timeline.append(
                {
                    "date": date_str,
                    "accuracy": accuracy,
                    "total_decisions": total,
                }
            )

        return timeline

    async def get_all_agent_accuracy(self) -> dict[str, dict]:
        """Get accuracy metrics for all agents across periods."""
        records = await self.performance_dao.get_all_agent_accuracy()

        agent_metrics: dict[str, dict] = {}
        for record in records:
            agent_name = record.agent_type.value
            if agent_name not in agent_metrics:
                agent_metrics[agent_name] = {}

            agent_metrics[agent_name][record.period] = {
                "total_signals": record.total_signals,
                "correct_signals": record.correct_signals,
                "accuracy": record.accuracy,
                "last_calculated": record.last_calculated.isoformat()
                if record.last_calculated
                else None,
            }

        return agent_metrics

    async def get_agent_detailed_accuracy(
        self, agent_enum: AgentType
    ) -> list[AgentAccuracy]:
        """Get detailed accuracy metrics for a specific agent."""
        return await self.performance_dao.get_agent_detailed_accuracy(agent_enum)

    async def get_ticker_history(self, ticker: str) -> list[AnalysisOutcome]:
        """Get performance history for a specific ticker."""
        return await self.performance_dao.get_ticker_history(ticker)
