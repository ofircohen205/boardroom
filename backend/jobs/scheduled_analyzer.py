# backend/jobs/scheduled_analyzer.py
"""Background job to run scheduled analyses."""
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from backend.ai.workflow import BoardroomGraph
from backend.core.logging import get_logger
from backend.dao.alerts import ScheduledAnalysisDAO
from backend.db.models import AlertFrequency
from backend.services.alerts import create_analysis_notification

logger = get_logger(__name__)


def calculate_next_run(
    frequency: AlertFrequency, last_run: datetime | None = None
) -> datetime:
    """
    Calculate the next scheduled run time based on frequency.

    Args:
        frequency: Schedule frequency (DAILY, WEEKLY, ON_CHANGE)
        last_run: Last run timestamp (optional)

    Returns:
        Next scheduled run datetime
    """
    et_tz = ZoneInfo("America/New_York")
    now = datetime.now(et_tz)

    if frequency == AlertFrequency.DAILY:
        # Daily at 8 AM ET before market opens
        next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)

        # If already past 8 AM today, schedule for tomorrow
        if now.time() >= next_run.time():
            next_run += timedelta(days=1)

        # Skip weekends (Saturday=5, Sunday=6)
        while next_run.weekday() >= 5:
            next_run += timedelta(days=1)

        return next_run

    elif frequency == AlertFrequency.WEEKLY:
        # Weekly on Monday at 8 AM ET
        next_run = now.replace(hour=8, minute=0, second=0, microsecond=0)

        # Calculate days until next Monday
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0 and now.time() >= next_run.time():
            days_until_monday = 7

        next_run += timedelta(days=days_until_monday)
        return next_run

    elif frequency == AlertFrequency.ON_CHANGE:
        # Every hour during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)
        # For simplicity, run every hour from 10 AM to 4 PM

        # Start with next hour
        next_run = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        # Find next valid run time during market hours
        while True:
            # Skip weekends
            if next_run.weekday() >= 5:
                # Move to Monday 10 AM
                days_to_monday = 7 - next_run.weekday()
                next_run = (next_run + timedelta(days=days_to_monday)).replace(
                    hour=10, minute=0
                )
                continue

            # Check if within market hours (10 AM - 4 PM)
            if 10 <= next_run.hour < 16:
                break

            # If before 10 AM, move to 10 AM today
            if next_run.hour < 10:
                next_run = next_run.replace(hour=10, minute=0)
            # If after 4 PM, move to 10 AM next day
            else:
                next_run = (next_run + timedelta(days=1)).replace(hour=10, minute=0)

        return next_run

    # Default: tomorrow at 8 AM
    return (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)


async def run_scheduled_analyses(db: AsyncSession) -> dict:
    """
    Run all scheduled analyses that are due.

    This function:
    1. Gets all schedules where next_run <= now and active=True
    2. For each schedule: runs BoardroomGraph analysis
    3. Creates a notification with the result
    4. Updates last_run and calculates next_run

    Args:
        db: Database session

    Returns:
        dict with stats: schedules_run, duration_seconds
    """
    start_time = datetime.now()

    logger.info("Starting scheduled analyzer job")
    schedule_dao = ScheduledAnalysisDAO(db)

    try:
        # Get all due schedules
        schedules = await schedule_dao.get_due_schedules()

        if not schedules:
            logger.debug("No scheduled analyses due")
            return {
                "success": True,
                "schedules_run": 0,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
            }

        logger.info(f"Found {len(schedules)} scheduled analyses to run")

        schedules_run = 0

        for schedule in schedules:
            try:
                logger.info(
                    f"Running scheduled analysis {schedule.id} for {schedule.ticker} ({schedule.market.value})"
                )

                # Run the analysis
                graph = BoardroomGraph()
                result = await graph.run_sync(
                    ticker=schedule.ticker,
                    market=schedule.market,
                    portfolio_sector_weight=0.0,  # Scheduled analyses don't have portfolio context
                )

                # Extract final decision
                final_decision = result.get("final_decision")
                if final_decision:
                    action = final_decision.get("action", "HOLD")
                    confidence = final_decision.get("confidence", 0.0)
                    vetoed = False
                    veto_reason = None

                    # Check if vetoed
                    risk_assessment = result.get("risk_assessment")
                    if risk_assessment and risk_assessment.get("veto", False):
                        vetoed = True
                        veto_reason = risk_assessment.get(
                            "reason", "Risk assessment veto"
                        )

                    # Create notification
                    await create_analysis_notification(
                        db=db,
                        user_id=schedule.user_id,
                        ticker=schedule.ticker,
                        action=action,
                        confidence=confidence,
                        vetoed=vetoed,
                        veto_reason=veto_reason,
                    )

                # Update schedule times
                now = datetime.now()
                next_run = calculate_next_run(schedule.frequency, now)

                await schedule_dao.update_run_times(
                    schedule_id=schedule.id, last_run=now, next_run=next_run
                )

                schedules_run += 1
                logger.info(
                    f"Completed scheduled analysis {schedule.id}. Next run: {next_run}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to run scheduled analysis {schedule.id}: {e}",
                    exc_info=True,
                )
                # Continue with other schedules

        # Commit all changes
        await db.commit()

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Scheduled analyzer completed: {schedules_run} analyses run in {duration:.2f}s"
        )

        return {
            "success": True,
            "schedules_run": schedules_run,
            "duration_seconds": duration,
        }

    except Exception as e:
        logger.error(f"Scheduled analyzer job failed: {e}", exc_info=True)
        await db.rollback()
        return {
            "success": False,
            "error": str(e),
            "schedules_run": 0,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
        }
