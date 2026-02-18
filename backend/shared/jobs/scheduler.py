"""
Background job scheduler for periodic tasks.

Runs outcome tracker job every hour to update recommendation outcomes
and agent accuracy metrics.
"""

import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.shared.core.logging import get_logger
from backend.shared.core.settings import settings
from backend.shared.jobs.alert_checker import check_price_alerts
from backend.shared.jobs.outcome_tracker import run_outcome_tracker_job
from backend.shared.jobs.scheduled_analyzer import run_scheduled_analyses

logger = get_logger(__name__)


class JobScheduler:
    """Manages periodic background jobs."""

    def __init__(self):
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the job scheduler."""
        if self.running:
            logger.warning("Job scheduler is already running")
            return

        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Job scheduler started")

    async def stop(self):
        """Stop the job scheduler."""
        if not self.running:
            return

        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await self.engine.dispose()
        logger.info("Job scheduler stopped")

    async def _run_loop(self):
        """
        Main scheduler loop.
        - Alert checker: every 5 minutes
        - Scheduled analyzer: every 15 minutes
        - Outcome tracker: every hour
        """
        # Run all jobs immediately on startup
        await self._run_alert_checker()
        await self._run_scheduled_analyzer()
        await self._run_outcome_tracker()

        # Then run on schedule
        minute_counter = 0
        while self.running:
            try:
                await asyncio.sleep(60)  # 1 minute
                if not self.running:
                    break

                minute_counter += 1

                # Alert checker: every 5 minutes
                if minute_counter % 5 == 0:
                    await self._run_alert_checker()

                # Scheduled analyzer: every 15 minutes
                if minute_counter % 15 == 0:
                    await self._run_scheduled_analyzer()

                # Outcome tracker: every hour
                if minute_counter % 60 == 0:
                    await self._run_outcome_tracker()
                    minute_counter = 0  # Reset counter

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                # Continue running even if one iteration fails
                await asyncio.sleep(60)  # Wait 1 minute before retry

    async def _run_alert_checker(self):
        """Run the alert checker job."""
        async with self.async_session_maker() as session:
            try:
                result = await check_price_alerts(session)
                if result["success"]:
                    if result.get("skipped") == "market_closed":
                        logger.debug("Alert checker skipped: market closed")
                    else:
                        logger.info(
                            f"Alert checker completed: {result['alerts_checked']} checked, "
                            f"{result['alerts_triggered']} triggered"
                        )
                else:
                    logger.error(f"Alert checker failed: {result.get('error')}")
            except Exception as e:
                logger.error(f"Failed to run alert checker: {e}", exc_info=True)

    async def _run_scheduled_analyzer(self):
        """Run the scheduled analyzer job."""
        async with self.async_session_maker() as session:
            try:
                result = await run_scheduled_analyses(session)
                if result["success"]:
                    if result["schedules_run"] > 0:
                        logger.info(
                            f"Scheduled analyzer completed: {result['schedules_run']} analyses run"
                        )
                else:
                    logger.error(f"Scheduled analyzer failed: {result.get('error')}")
            except Exception as e:
                logger.error(f"Failed to run scheduled analyzer: {e}", exc_info=True)

    async def _run_outcome_tracker(self):
        """Run the outcome tracker job."""
        async with self.async_session_maker() as session:
            try:
                result = await run_outcome_tracker_job(session)
                if result["success"]:
                    logger.info(
                        f"Outcome tracker completed: {result['outcomes_updated']} updates"
                    )
                else:
                    logger.error(f"Outcome tracker failed: {result.get('error')}")
            except Exception as e:
                logger.error(f"Failed to run outcome tracker: {e}", exc_info=True)

    async def run_now(self) -> dict:
        """
        Run the outcome tracker job immediately (for manual triggering).

        Returns:
            Job execution result
        """
        async with self.async_session_maker() as session:
            return await run_outcome_tracker_job(session)


# Global scheduler instance
_scheduler: Optional[JobScheduler] = None


def get_scheduler() -> JobScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler


async def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    await scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler."""
    if _scheduler is not None:
        await _scheduler.stop()
