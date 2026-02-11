# backend/services/schedules/service.py
"""Schedule service - manages scheduled analysis execution."""

from datetime import datetime
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Market
from backend.dao.alerts import ScheduledAnalysisDAO
from backend.db.models import ScheduledAnalysis
from backend.services.base import BaseService

from .exceptions import (
    ScheduleError,
    ScheduleNotFoundError,
    ScheduleRateLimitError,
)


class ScheduleService(BaseService):
    """Service for scheduled analysis operations."""

    MAX_SCHEDULES_PER_USER = 50

    def __init__(self, schedule_dao: ScheduledAnalysisDAO):
        """
        Initialize ScheduleService.

        Args:
            schedule_dao: DAO for scheduled analysis operations
        """
        self.schedule_dao = schedule_dao

    async def create_scheduled_analysis(
        self,
        user_id: UUID,
        ticker: str,
        market: Market,
        frequency: str,
        db: AsyncSession,
    ) -> ScheduledAnalysis:
        """
        Create a new scheduled analysis.

        Args:
            user_id: User ID
            ticker: Stock ticker symbol
            market: Market enum (US or TASE)
            frequency: Frequency enum string (DAILY, WEEKLY, ON_CHANGE)
            db: Database session

        Returns:
            Created ScheduledAnalysis object

        Raises:
            ScheduleRateLimitError: If user has reached max schedules
            ScheduleError: If creation fails
        """
        try:
            # Check rate limit
            count = await self.schedule_dao.count_user_schedules(user_id)
            if count >= self.MAX_SCHEDULES_PER_USER:
                raise ScheduleRateLimitError(
                    f"User has reached maximum of {self.MAX_SCHEDULES_PER_USER} schedules"
                )

            # Create schedule
            schedule = await self.schedule_dao.create(
                user_id=user_id,
                ticker=ticker,
                market=market,
                frequency=frequency,
                active=True,
                next_run=datetime.now(),  # Will be calculated by job
            )
            await db.commit()
            await db.refresh(schedule)
            return schedule
        except ScheduleRateLimitError:
            raise
        except Exception as e:
            await db.rollback()
            raise ScheduleError(f"Failed to create schedule for {ticker}: {e!s}")

    async def get_user_schedules(self, user_id: UUID) -> List[ScheduledAnalysis]:
        """
        Get all schedules for a user.

        Args:
            user_id: User ID

        Returns:
            List of ScheduledAnalysis objects

        Raises:
            ScheduleError: If operation fails
        """
        try:
            return await self.schedule_dao.get_user_schedules(user_id)
        except Exception as e:
            raise ScheduleError(f"Failed to fetch schedules for user {user_id}: {e!s}")

    async def get_due_schedules(self) -> List[ScheduledAnalysis]:
        """
        Get all schedules that are due to run.

        Returns:
            List of ScheduledAnalysis objects ready to run

        Raises:
            ScheduleError: If operation fails
        """
        try:
            return await self.schedule_dao.get_due_schedules()
        except Exception as e:
            raise ScheduleError(f"Failed to fetch due schedules: {e!s}")

    async def update_run_times(
        self,
        schedule_id: UUID,
        last_run: datetime,
        next_run: datetime,
        db: AsyncSession,
    ) -> ScheduledAnalysis:
        """
        Update the last_run and next_run times for a schedule.

        Args:
            schedule_id: Schedule ID
            last_run: Timestamp of last run
            next_run: Timestamp of next scheduled run
            db: Database session

        Returns:
            Updated ScheduledAnalysis

        Raises:
            ScheduleNotFoundError: If schedule doesn't exist
            ScheduleError: If operation fails
        """
        try:
            schedule = await self.schedule_dao.update_run_times(
                schedule_id, last_run, next_run
            )
            if not schedule:
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")

            await db.commit()
            return schedule
        except ScheduleNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            raise ScheduleError(f"Failed to update schedule {schedule_id}: {e!s}")

    async def toggle_schedule(
        self, schedule_id: UUID, active: bool, db: AsyncSession
    ) -> ScheduledAnalysis:
        """
        Pause or resume a schedule.

        Args:
            schedule_id: Schedule ID
            active: True to activate, False to pause
            db: Database session

        Returns:
            Updated ScheduledAnalysis

        Raises:
            ScheduleNotFoundError: If schedule doesn't exist
            ScheduleError: If operation fails
        """
        try:
            schedule = await self.schedule_dao.get_by_id(schedule_id)
            if not schedule:
                raise ScheduleNotFoundError(f"Schedule {schedule_id} not found")

            schedule.active = active
            updated = await self.schedule_dao.update(schedule)
            await db.commit()
            return updated
        except ScheduleNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            raise ScheduleError(f"Failed to toggle schedule {schedule_id}: {e!s}")

    async def delete_schedule(self, schedule_id: UUID, db: AsyncSession) -> bool:
        """
        Delete a schedule.

        Args:
            schedule_id: Schedule ID
            db: Database session

        Returns:
            True if deleted, False if not found

        Raises:
            ScheduleError: If operation fails
        """
        try:
            deleted = await self.schedule_dao.delete(schedule_id)
            await db.commit()
            return deleted
        except Exception as e:
            await db.rollback()
            raise ScheduleError(f"Failed to delete schedule {schedule_id}: {e!s}")
