"""
Background job scheduler for periodic tasks.

Runs outcome tracker job every hour to update recommendation outcomes
and agent accuracy metrics.
"""

import asyncio
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.settings import settings
from backend.jobs.outcome_tracker import run_outcome_tracker_job
from backend.core.logging import get_logger

logger = get_logger(__name__)


class JobScheduler:
    """Manages periodic background jobs."""

    def __init__(self):
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.async_session_maker = sessionmaker(
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
        """Main scheduler loop - runs outcome tracker every hour."""
        # Run immediately on startup
        await self._run_outcome_tracker()

        # Then run every hour
        while self.running:
            try:
                await asyncio.sleep(3600)  # 1 hour
                if self.running:
                    await self._run_outcome_tracker()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                # Continue running even if one iteration fails
                await asyncio.sleep(60)  # Wait 1 minute before retry

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
