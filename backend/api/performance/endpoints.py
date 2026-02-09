"""
API endpoints for performance tracking and analytics.

Provides insights into:
- Overall recommendation accuracy
- Agent-specific accuracy metrics
- Recent outcomes and returns
- Historical performance trends
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.models import AgentAccuracy, AnalysisOutcome
from backend.jobs.scheduler import get_scheduler
from backend.services.performance_tracking.service import (
    get_performance_summary,
    get_recent_outcomes,
)
from backend.ai.state.enums import AgentType

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    """
    Get overall performance summary.

    Returns:
        - Total recommendations made
        - Overall accuracy
        - Breakdown by action type (BUY/SELL/HOLD)
    """
    try:
        summary = await get_performance_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent(
    limit: int = 20,
    ticker: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent analysis outcomes with returns.

    Args:
        limit: Maximum number of outcomes to return (default 20)
        ticker: Optional ticker to filter by

    Returns:
        List of recent outcomes with price returns
    """
    try:
        outcomes = await get_recent_outcomes(db, limit=limit, ticker=ticker)
        return {"outcomes": outcomes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agent_accuracy(db: AsyncSession = Depends(get_db)):
    """
    Get accuracy metrics for all agents across different time periods.

    Returns:
        Nested structure: agent_type -> period -> metrics
    """
    try:
        query = select(AgentAccuracy)
        result = await db.execute(query)
        records = result.scalars().all()

        # Organize by agent type and period
        agent_metrics = {}
        for record in records:
            agent_name = record.agent_type.value
            if agent_name not in agent_metrics:
                agent_metrics[agent_name] = {}

            agent_metrics[agent_name][record.period] = {
                "total_signals": record.total_signals,
                "correct_signals": record.correct_signals,
                "accuracy": record.accuracy,
                "last_calculated": record.last_calculated.isoformat(),
            }

        return {"agents": agent_metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_type}")
async def get_agent_details(
    agent_type: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed accuracy metrics for a specific agent.

    Args:
        agent_type: The agent type (fundamental, sentiment, technical)

    Returns:
        Accuracy metrics across all tracked periods
    """
    try:
        # Validate agent type
        try:
            agent_enum = AgentType(agent_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")

        query = select(AgentAccuracy).where(AgentAccuracy.agent_type == agent_enum)
        result = await db.execute(query)
        records = result.scalars().all()

        if not records:
            return {
                "agent_type": agent_type,
                "metrics": {},
                "message": "No performance data available yet",
            }

        metrics = {}
        for record in records:
            metrics[record.period] = {
                "total_signals": record.total_signals,
                "correct_signals": record.correct_signals,
                "accuracy": record.accuracy,
                "last_calculated": record.last_calculated.isoformat(),
            }

        return {
            "agent_type": agent_type,
            "metrics": metrics,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-update")
async def trigger_update():
    """
    Manually trigger the outcome tracker job.

    Useful for testing or forcing an immediate update.

    Returns:
        Job execution result
    """
    try:
        scheduler = get_scheduler()
        result = await scheduler.run_now()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ticker/{ticker}")
async def get_ticker_performance(
    ticker: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get performance history for a specific ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        All recommendations and outcomes for this ticker
    """
    try:
        ticker = ticker.upper()
        query = select(AnalysisOutcome).where(
            AnalysisOutcome.ticker == ticker
        ).order_by(AnalysisOutcome.created_at.desc())

        result = await db.execute(query)
        outcomes = result.scalars().all()

        if not outcomes:
            return {
                "ticker": ticker,
                "total_recommendations": 0,
                "history": [],
            }

        # Calculate statistics
        completed_outcomes = [o for o in outcomes if o.outcome_correct is not None]
        accuracy = (
            sum(1 for o in completed_outcomes if o.outcome_correct) / len(completed_outcomes)
            if completed_outcomes else 0.0
        )

        # Format history
        history = []
        for outcome in outcomes:
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

            history.append({
                "action": outcome.action_recommended.value,
                "price_at_recommendation": outcome.price_at_recommendation,
                "outcome_correct": outcome.outcome_correct,
                "returns": returns,
                "created_at": outcome.created_at.isoformat(),
            })

        return {
            "ticker": ticker,
            "total_recommendations": len(outcomes),
            "completed_evaluations": len(completed_outcomes),
            "accuracy": accuracy,
            "history": history,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
