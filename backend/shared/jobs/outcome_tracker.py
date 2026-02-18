"""
Background job to track analysis outcomes and update agent accuracy metrics.

Runs periodically to:
1. Fetch follow-up prices for past recommendations (1d, 7d, 30d, 90d)
2. Determine if recommendations were correct
3. Update agent accuracy statistics
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.ai.state.enums import Action, AgentType
from backend.shared.ai.tools.market_data import get_market_data_client
from backend.shared.core.logging import get_logger
from backend.shared.db.models import (
    AgentAccuracy,
    AgentReport,
    AnalysisOutcome,
    AnalysisSession,
    FinalDecision,
)

logger = get_logger(__name__)


async def update_outcome_prices(db: AsyncSession) -> int:
    """
    Update follow-up prices for analysis outcomes that need updates.

    Returns:
        Number of outcomes updated
    """
    now = datetime.now()
    updated_count = 0

    # Find outcomes that need price updates
    query = select(AnalysisOutcome).where(
        (
            AnalysisOutcome.price_after_90d.is_(None)  # Not fully tracked yet
        )
    )

    result = await db.execute(query)
    outcomes = result.scalars().all()

    if not outcomes:
        logger.info("No outcomes to track yet")
        return 0

    for outcome in outcomes:
        session_query = select(AnalysisSession).where(
            AnalysisSession.id == outcome.session_id
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()

        if not session:
            continue

        recommendation_time = session.created_at
        time_since = now - recommendation_time

        try:
            # Get current price
            market_data_client = get_market_data_client()
            quote = await market_data_client.get_stock_data(
                outcome.ticker, session.market
            )
            current_price = quote["current_price"]

            # Update prices based on time elapsed
            if time_since >= timedelta(days=1) and outcome.price_after_1d is None:
                outcome.price_after_1d = current_price
                updated_count += 1
                logger.info(f"Updated 1d price for {outcome.ticker}: ${current_price}")

            if time_since >= timedelta(days=7) and outcome.price_after_7d is None:
                outcome.price_after_7d = current_price
                updated_count += 1
                logger.info(f"Updated 7d price for {outcome.ticker}: ${current_price}")

            if time_since >= timedelta(days=30) and outcome.price_after_30d is None:
                outcome.price_after_30d = current_price
                updated_count += 1
                logger.info(f"Updated 30d price for {outcome.ticker}: ${current_price}")

            if time_since >= timedelta(days=90) and outcome.price_after_90d is None:
                outcome.price_after_90d = current_price
                updated_count += 1
                logger.info(f"Updated 90d price for {outcome.ticker}: ${current_price}")

            # Determine if recommendation was correct (using 30d timeframe as primary)
            if outcome.price_after_30d is not None and outcome.outcome_correct is None:
                outcome.outcome_correct = _was_recommendation_correct(
                    outcome.action_recommended,
                    outcome.price_at_recommendation,
                    outcome.price_after_30d,
                )
                logger.info(
                    f"Marked {outcome.ticker} recommendation as "
                    f"{'correct' if outcome.outcome_correct else 'incorrect'}"
                )

            outcome.last_updated = now
            await db.commit()

        except OSError as e:
            # Network/DNS errors - log as warning and continue
            if e.errno == -2 or "Name or service not known" in str(e):
                logger.warning(
                    f"Network error updating {outcome.ticker} (DNS resolution failed). "
                    "Check internet connection or try again later."
                )
            else:
                logger.warning(f"Network error updating {outcome.ticker}: {e}")
            await db.rollback()
            continue
        except Exception as e:
            logger.error(f"Failed to update outcome for {outcome.ticker}: {e}")
            await db.rollback()
            continue

    return updated_count


def _was_recommendation_correct(
    action: Action,
    price_at_rec: float,
    price_after: float,
    threshold: float = 0.02,  # 2% threshold
) -> bool:
    """
    Determine if a recommendation was correct based on price movement.

    Args:
        action: The recommended action (BUY/SELL/HOLD)
        price_at_rec: Price at time of recommendation
        price_after: Price after evaluation period
        threshold: Percentage change threshold for HOLD

    Returns:
        True if recommendation was correct
    """
    price_change_pct = (price_after - price_at_rec) / price_at_rec

    if action == Action.BUY:
        # BUY is correct if price went up
        return price_change_pct > 0
    elif action == Action.SELL:
        # SELL is correct if price went down
        return price_change_pct < 0
    else:  # HOLD
        # HOLD is correct if price stayed relatively stable
        return abs(price_change_pct) < threshold


async def update_agent_accuracy(db: AsyncSession) -> None:
    """
    Recalculate agent accuracy metrics based on completed outcomes.

    Updates accuracy for each agent type across different time periods.
    """
    periods = ["7d", "30d", "90d"]

    # Only calculate accuracy for analyst agents (not RISK or CHAIRPERSON)
    analyst_agents = [AgentType.FUNDAMENTAL, AgentType.SENTIMENT, AgentType.TECHNICAL]

    for agent_type in analyst_agents:
        for period in periods:
            try:
                await _calculate_agent_accuracy(db, agent_type, period)
            except Exception as e:
                logger.error(
                    f"Failed to calculate accuracy for {agent_type.value} ({period}): {e}"
                )


async def _calculate_agent_accuracy(
    db: AsyncSession, agent_type: AgentType, period: str
) -> None:
    """
    Calculate accuracy for a specific agent type and time period.

    Attribution logic:
    - If agent's signal matched final decision and outcome was correct -> correct signal
    - If agent's signal opposed final decision and outcome was incorrect -> correct signal
    - Otherwise -> incorrect signal
    """
    # Determine which price field to use
    price_field_map = {
        "7d": AnalysisOutcome.price_after_7d,
        "30d": AnalysisOutcome.price_after_30d,
        "90d": AnalysisOutcome.price_after_90d,
    }
    price_field = price_field_map[period]

    # Get all outcomes with complete data for this period
    query = (
        select(AnalysisOutcome, FinalDecision, AgentReport)
        .join(
            FinalDecision,
            AnalysisOutcome.session_id == FinalDecision.session_id,
        )
        .join(
            AgentReport,
            (AgentReport.session_id == AnalysisOutcome.session_id)
            & (AgentReport.agent_type == agent_type),
        )
        .where(
            price_field.is_not(None),
            AnalysisOutcome.outcome_correct.is_not(None),
        )
    )

    result = await db.execute(query)
    rows = result.all()

    total_signals = 0
    correct_signals = 0

    for outcome, decision, agent_report in rows:
        # Extract agent's recommendation from report_data
        agent_action = _extract_agent_action(agent_report.report_data, agent_type)

        if agent_action is None:
            continue

        total_signals += 1

        # Attribution logic: did this agent's signal contribute to a correct outcome?
        if agent_action == decision.action:
            # Agent agreed with final decision
            if outcome.outcome_correct:
                correct_signals += 1
        else:
            # Agent disagreed with final decision
            if not outcome.outcome_correct:
                correct_signals += 1

    # Update or create accuracy record
    accuracy_value = (correct_signals / total_signals) if total_signals > 0 else 0.0

    accuracy_query = select(AgentAccuracy).where(
        AgentAccuracy.agent_type == agent_type,
        AgentAccuracy.period == period,
    )
    result = await db.execute(accuracy_query)
    accuracy_record = result.scalar_one_or_none()

    if accuracy_record:
        accuracy_record.total_signals = total_signals
        accuracy_record.correct_signals = correct_signals
        accuracy_record.accuracy = accuracy_value
        accuracy_record.last_calculated = datetime.now()
    else:
        accuracy_record = AgentAccuracy(
            agent_type=agent_type,
            period=period,
            total_signals=total_signals,
            correct_signals=correct_signals,
            accuracy=accuracy_value,
            last_calculated=datetime.now(),
        )
        db.add(accuracy_record)

    await db.commit()
    logger.info(
        f"Updated accuracy for {agent_type.value} ({period}): "
        f"{accuracy_value:.1%} ({correct_signals}/{total_signals})"
    )


def _extract_agent_action(report_data: dict, agent_type: AgentType) -> Optional[Action]:
    """
    Extract the action recommendation from an agent's report data.

    Different agents structure their reports differently, so we need
    type-specific extraction logic.
    """
    if agent_type == AgentType.FUNDAMENTAL:
        signal = report_data.get("signal")
        if signal == "bullish":
            return Action.BUY
        elif signal == "bearish":
            return Action.SELL
        else:
            return Action.HOLD

    elif agent_type == AgentType.SENTIMENT:
        sentiment_score = report_data.get("sentiment_score", 0)
        if sentiment_score > 60:
            return Action.BUY
        elif sentiment_score < 40:
            return Action.SELL
        else:
            return Action.HOLD

    elif agent_type == AgentType.TECHNICAL:
        signal = report_data.get("signal")
        if signal == "buy":
            return Action.BUY
        elif signal == "sell":
            return Action.SELL
        else:
            return Action.HOLD

    elif agent_type == AgentType.RISK:
        # Risk manager doesn't make buy/sell decisions
        # Only vetos, which are handled separately
        return None

    return None


async def run_outcome_tracker_job(db: AsyncSession) -> dict:
    """
    Main entry point for the outcome tracker job.

    Returns:
        Dictionary with job execution statistics
    """
    logger.info("Starting outcome tracker job")
    start_time = datetime.now()

    try:
        # Update outcome prices
        updated_count = await update_outcome_prices(db)

        # Recalculate agent accuracy
        await update_agent_accuracy(db)

        duration = (datetime.now() - start_time).total_seconds()

        logger.info(
            f"Outcome tracker job completed in {duration:.2f}s. "
            f"Updated {updated_count} outcomes."
        )

        return {
            "success": True,
            "duration_seconds": duration,
            "outcomes_updated": updated_count,
        }

    except Exception as e:
        logger.error(f"Outcome tracker job failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }
