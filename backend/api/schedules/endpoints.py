# backend/api/schedules/endpoints.py
"""API endpoints for scheduled analyses."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Market
from backend.auth.dependencies import get_current_user
from backend.core.logging import get_logger
from backend.db.database import get_db
from backend.db.models import User
from backend.services.dependencies import get_schedule_service
from backend.services.schedules.exceptions import (
    ScheduleError,
    ScheduleNotFoundError,
    ScheduleRateLimitError,
)
from backend.services.schedules.service import ScheduleService

from .schemas import (
    ScheduledAnalysisCreate,
    ScheduledAnalysisSchema,
    ScheduledAnalysisToggle,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post(
    "", response_model=ScheduledAnalysisSchema, status_code=status.HTTP_201_CREATED
)
async def create_schedule(
    schedule_data: ScheduledAnalysisCreate,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new scheduled analysis.

    The next_run time is automatically calculated based on the frequency:
    - daily: 8 AM ET before market open (Mon-Fri)
    - weekly: Monday 8 AM ET
    - on_change: Every hour during market hours (10 AM - 4 PM ET)
    """
    try:
        # Create schedule using service (includes rate limiting)
        schedule = await service.create_scheduled_analysis(
            user_id=current_user.id,
            ticker=schedule_data.ticker.upper(),
            market=Market(schedule_data.market),
            frequency=schedule_data.frequency,
            db=db,
        )

        logger.info(
            f"User {current_user.id} created schedule {schedule.id} for {schedule.ticker} "
            f"({schedule.market.value}) {schedule.frequency} - next run: {schedule.next_run}"
        )
        return schedule

    except ScheduleRateLimitError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ScheduleError as e:
        logger.error(f"Failed to create schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule",
        )


@router.get("", response_model=list[ScheduledAnalysisSchema])
async def list_schedules(
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
):
    """
    List all scheduled analyses for the current user.
    """
    schedules = await service.get_user_schedules(current_user.id)
    return schedules


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a scheduled analysis.

    Only the owner can delete their schedule.
    """
    try:
        await service.delete_schedule(schedule_id, db)
        logger.info(f"User {current_user.id} deleted schedule {schedule_id}")
    except ScheduleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    except ScheduleError as e:
        logger.error(f"Failed to delete schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule",
        )


@router.patch("/{schedule_id}/toggle", response_model=ScheduledAnalysisSchema)
async def toggle_schedule(
    schedule_id: UUID,
    toggle_data: ScheduledAnalysisToggle,
    current_user: User = Depends(get_current_user),
    service: ScheduleService = Depends(get_schedule_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle schedule active status (pause/resume).

    When reactivating a paused schedule, the next_run time is recalculated
    to avoid running stale schedules immediately.
    """
    try:
        updated_schedule = await service.toggle_schedule(
            schedule_id, toggle_data.active, db
        )
        logger.info(
            f"User {current_user.id} toggled schedule {schedule_id} to active={toggle_data.active}"
        )
        return updated_schedule
    except ScheduleNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )
    except ScheduleError as e:
        logger.error(f"Failed to toggle schedule: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle schedule",
        )
