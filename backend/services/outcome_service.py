"""
Service for creating and managing analysis outcomes.

When a stock analysis completes with a recommendation, we create an
AnalysisOutcome record to track what actually happens to the price.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import AnalysisOutcome, AnalysisSession, FinalDecision
from backend.state.enums import Action, Market
from backend.tools.market_data import get_market_data_client

logger = logging.getLogger(__name__)


async def create_analysis_outcome(
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
        session_query = select(AnalysisSession).where(AnalysisSession.id == session_id)
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
            quote = await market_data_client.get_stock_data(session.ticker, session.market)
            current_price = quote["current_price"]
        except Exception as e:
            logger.error(f"Failed to get price for {session.ticker}: {e}")
            return None

        # Create outcome record
        outcome = AnalysisOutcome(
            session_id=session_id,
            ticker=session.ticker,
            action_recommended=decision.action,
            price_at_recommendation=current_price,
            created_at=datetime.now(),
            last_updated=datetime.now(),
        )

        db.add(outcome)
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


async def get_performance_summary(db: AsyncSession) -> dict:
    """
    Get overall performance summary across all tracked outcomes.

    Returns:
        Dictionary with performance metrics
    """
    query = select(AnalysisOutcome).where(
        AnalysisOutcome.outcome_correct.is_not(None)
    )
    result = await db.execute(query)
    outcomes = result.scalars().all()

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
    query = select(AnalysisOutcome, FinalDecision, AnalysisSession).join(
        FinalDecision, AnalysisOutcome.session_id == FinalDecision.session_id
    ).join(
        AnalysisSession, AnalysisOutcome.session_id == AnalysisSession.id
    )

    if ticker:
        query = query.where(AnalysisOutcome.ticker == ticker.upper())

    query = query.order_by(AnalysisOutcome.created_at.desc()).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    outcomes = []
    for outcome, decision, session in rows:
        # Calculate return if we have follow-up price
        returns = {}
        if outcome.price_after_1d:
            returns["1d"] = (
                (outcome.price_after_1d - outcome.price_at_recommendation)
                / outcome.price_at_recommendation
            )
        if outcome.price_after_7d:
            returns["7d"] = (
                (outcome.price_after_7d - outcome.price_at_recommendation)
                / outcome.price_at_recommendation
            )
        if outcome.price_after_30d:
            returns["30d"] = (
                (outcome.price_after_30d - outcome.price_at_recommendation)
                / outcome.price_at_recommendation
            )
        if outcome.price_after_90d:
            returns["90d"] = (
                (outcome.price_after_90d - outcome.price_at_recommendation)
                / outcome.price_at_recommendation
            )

        outcomes.append({
            "ticker": outcome.ticker,
            "action": outcome.action_recommended.value,
            "price_at_recommendation": outcome.price_at_recommendation,
            "confidence": decision.confidence,
            "outcome_correct": outcome.outcome_correct,
            "returns": returns,
            "created_at": outcome.created_at.isoformat(),
        })

    return outcomes
