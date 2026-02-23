# backend/api/performance/endpoints.py
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

from backend.dependencies import get_performance_service
from backend.domains.performance.services.service import PerformanceService
from backend.shared.ai.state.enums import AgentType
from backend.shared.jobs.scheduler import get_scheduler

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/summary")
async def get_summary(
    service: PerformanceService = Depends(get_performance_service),
):
    """
    Get overall performance summary.

    Returns:
        - Total recommendations made
        - Overall accuracy
        - Breakdown by action type (BUY/SELL/HOLD)
    """
    try:
        summary = await service.get_performance_summary(service.performance_dao.session)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent(
    limit: int = 20,
    ticker: Optional[str] = None,
    service: PerformanceService = Depends(get_performance_service),
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
        outcomes = await service.get_recent_outcomes(
            service.performance_dao.session, limit=limit, ticker=ticker
        )
        return {"outcomes": outcomes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeline")
async def get_timeline(
    days: int = 30,
    service: PerformanceService = Depends(get_performance_service),
):
    """
    Get performance timeline data.

    Args:
        days: Number of days to include (default 30)

    Returns:
        List of daily accuracy metrics
    """
    try:
        timeline = await service.get_performance_timeline(
            service.performance_dao.session, days=days
        )
        return timeline
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def get_agent_accuracy(
    service: PerformanceService = Depends(get_performance_service),
):
    """
    Get accuracy metrics for all agents across different time periods.

    Returns:
        Nested structure: agent_type -> period -> metrics
    """
    try:
        agent_metrics = await service.get_all_agent_accuracy()
        return {"agents": agent_metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/{agent_type}")
async def get_agent_details(
    agent_type: str,
    service: PerformanceService = Depends(get_performance_service),
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
            raise HTTPException(
                status_code=400, detail=f"Invalid agent type: {agent_type}"
            )

        records = await service.get_agent_detailed_accuracy(agent_enum)

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
    service: PerformanceService = Depends(get_performance_service),
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
        outcomes = await service.get_ticker_history(ticker)

        if not outcomes:
            return {
                "ticker": ticker,
                "total_recommendations": 0,
                "history": [],
            }

        # Calculate statistics
        completed_outcomes = [o for o in outcomes if o.outcome_correct is not None]
        accuracy = (
            sum(1 for o in completed_outcomes if o.outcome_correct)
            / len(completed_outcomes)
            if completed_outcomes
            else 0.0
        )

        # Format history
        history = []
        for outcome in outcomes:
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

            history.append(
                {
                    "action": outcome.action_recommended.value,
                    "price_at_recommendation": outcome.price_at_recommendation,
                    "outcome_correct": outcome.outcome_correct,
                    "returns": returns,
                    "created_at": outcome.created_at.isoformat(),
                }
            )

        return {
            "ticker": ticker,
            "total_recommendations": len(outcomes),
            "completed_evaluations": len(completed_outcomes),
            "accuracy": accuracy,
            "history": history,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
