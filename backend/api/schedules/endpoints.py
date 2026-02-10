# backend/api/schedules/endpoints.py
"""API endpoints for scheduled analyses."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Market
from backend.auth.dependencies import get_current_user
from backend.core.logging import get_logger
from backend.dao.alerts import ScheduledAnalysisDAO
from backend.db.database import get_db
from backend.db.models import AlertFrequency, User
from backend.jobs.scheduled_analyzer import calculate_next_run

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
        schedule_dao = ScheduledAnalysisDAO(db)

        # Rate limiting: max 50 schedules per user
        schedule_count = await schedule_dao.count_user_schedules(current_user.id)
        if schedule_count >= 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 scheduled analyses per user exceeded",
            )

        # Check for duplicate (same ticker + market + frequency)
        existing = await schedule_dao.get_by_ticker_market_frequency(
            user_id=current_user.id,
            ticker=schedule_data.ticker,
            market=Market(schedule_data.market),
            frequency=AlertFrequency(schedule_data.frequency),
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Schedule already exists for {schedule_data.ticker} ({schedule_data.market}) with frequency {schedule_data.frequency}",
            )

        # Calculate next run time
        frequency = AlertFrequency(schedule_data.frequency)
        next_run = calculate_next_run(frequency)

        # Create schedule
        schedule = await schedule_dao.create(
            user_id=current_user.id,
            ticker=schedule_data.ticker.upper(),
            market=Market(schedule_data.market),
            frequency=frequency,
            next_run=next_run,
            active=True,
        )
        await db.commit()

        logger.info(
            f"User {current_user.id} created schedule {schedule.id} for {schedule.ticker} "
            f"({schedule.market.value}) {schedule.frequency.value} - next run: {next_run}"
        )
        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create schedule",
        )


@router.get("", response_model=list[ScheduledAnalysisSchema])
async def list_schedules(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    List all scheduled analyses for the current user.
    """
    schedule_dao = ScheduledAnalysisDAO(db)
    schedules = await schedule_dao.get_user_schedules(current_user.id)
    return schedules


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a scheduled analysis.

    Only the owner can delete their schedule.
    """
    schedule_dao = ScheduledAnalysisDAO(db)
    schedule = await schedule_dao.get_by_id(schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    if schedule.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this schedule",
        )

    await schedule_dao.delete(schedule_id)
    await db.commit()

    logger.info(f"User {current_user.id} deleted schedule {schedule_id}")


@router.patch("/{schedule_id}/toggle", response_model=ScheduledAnalysisSchema)
async def toggle_schedule(
    schedule_id: UUID,
    toggle_data: ScheduledAnalysisToggle,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle schedule active status (pause/resume).

    When reactivating a paused schedule, the next_run time is recalculated
    to avoid running stale schedules immediately.
    """
    schedule_dao = ScheduledAnalysisDAO(db)
    schedule = await schedule_dao.get_by_id(schedule_id)

    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule not found"
        )

    if schedule.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this schedule",
        )

    schedule.active = toggle_data.active

    # If reactivating, recalculate next_run to avoid immediate execution
    if toggle_data.active:
        schedule.next_run = calculate_next_run(schedule.frequency, schedule.last_run)
        logger.info(
            f"Reactivating schedule {schedule_id}, next run recalculated to {schedule.next_run}"
        )

    updated_schedule = await schedule_dao.update(schedule)
    await db.commit()

    logger.info(
        f"User {current_user.id} toggled schedule {schedule_id} to active={toggle_data.active}"
    )
    return updated_schedule
