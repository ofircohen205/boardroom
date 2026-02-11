# backend/api/alerts/endpoints.py
"""API endpoints for price alerts."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Market
from backend.auth.dependencies import get_current_user
from backend.core.logging import get_logger
from backend.db.database import get_db
from backend.db.models import AlertCondition, User
from backend.services.alerts.service import AlertService, AlertValidationError
from backend.services.dependencies import get_alert_service

from .schemas import PriceAlertCreate, PriceAlertSchema, PriceAlertToggle

logger = get_logger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("", response_model=PriceAlertSchema, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: PriceAlertCreate,
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new price alert.

    Validates:
    - User hasn't exceeded max 50 alerts
    - Target value is positive
    - Change_pct is between 0.1 and 100
    """
    try:
        alert = await service.create_price_alert(
            db=db,
            user_id=current_user.id,
            ticker=alert_data.ticker,
            market=Market(alert_data.market),
            condition=AlertCondition(alert_data.condition),
            target_value=alert_data.target_value,
        )
        await db.commit()

        logger.info(f"User {current_user.id} created alert {alert.id}")
        return alert

    except AlertValidationError as e:
        logger.warning(f"Alert validation failed for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create alert: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert",
        )


@router.get("", response_model=list[PriceAlertSchema])
async def list_alerts(
    active_only: bool = Query(True, description="Only return active alerts"),
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    """
    List all alerts for the current user.

    Query params:
    - active_only: If true (default), only return active alerts
    """
    alerts = await service.price_alert_dao.get_user_alerts(
        current_user.id, active_only=active_only
    )
    return alerts


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    """
    Delete a price alert.

    Only the owner can delete their alert.
    """
    alert = await service.price_alert_dao.get_by_id(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )

    if alert.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this alert",
        )

    await service.price_alert_dao.delete(alert_id)
    await service.price_alert_dao.session.commit()

    logger.info(f"User {current_user.id} deleted alert {alert_id}")


@router.patch("/{alert_id}/reset", response_model=PriceAlertSchema)
async def reset_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    """
    Reset a triggered alert to re-enable it.

    Clears triggered status and cooldown.
    """
    alert = await service.price_alert_dao.get_by_id(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )

    if alert.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this alert",
        )

    updated_alert = await service.price_alert_dao.reset_alert(alert_id)
    await service.price_alert_dao.session.commit()

    logger.info(f"User {current_user.id} reset alert {alert_id}")
    return updated_alert


@router.patch("/{alert_id}/toggle", response_model=PriceAlertSchema)
async def toggle_alert(
    alert_id: UUID,
    toggle_data: PriceAlertToggle,
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
):
    """
    Toggle alert active status (pause/resume).
    """
    alert = await service.price_alert_dao.get_by_id(alert_id)

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
        )

    if alert.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this alert",
        )

    alert.active = toggle_data.active
    updated_alert = await service.price_alert_dao.update(alert)
    await service.price_alert_dao.session.commit()

    logger.info(
        f"User {current_user.id} toggled alert {alert_id} to active={toggle_data.active}"
    )
    return updated_alert
