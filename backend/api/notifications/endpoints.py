# backend/api/notifications/endpoints.py
"""API endpoints for notifications."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.db.models import User
from backend.db.database import get_db
from backend.dao.alerts import NotificationDAO
from backend.core.logging import get_logger
from .schemas import NotificationSchema, UnreadCountSchema

logger = get_logger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationSchema])
async def list_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List notifications for the current user.

    Query params:
    - unread_only: If true, only return unread notifications (default: false)
    - limit: Maximum number of notifications (default: 50, max: 100)
    """
    notification_dao = NotificationDAO(db)
    notifications = await notification_dao.get_user_notifications(
        current_user.id,
        unread_only=unread_only,
        limit=limit
    )
    return notifications


@router.get("/unread-count", response_model=UnreadCountSchema)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get count of unread notifications for the current user.

    Used to display badge count in notification bell.
    """
    notification_dao = NotificationDAO(db)
    unread_count = await notification_dao.get_unread_count(current_user.id)
    return {"unread_count": unread_count}


@router.patch("/{notification_id}/read", response_model=NotificationSchema)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read.

    Only the owner can mark their notification as read.
    """
    notification_dao = NotificationDAO(db)
    notification = await notification_dao.get_by_id(notification_id)

    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    if notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this notification")

    updated_notification = await notification_dao.mark_as_read(notification_id)
    await db.commit()

    logger.debug(f"User {current_user.id} marked notification {notification_id} as read")
    return updated_notification


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all notifications as read for the current user.
    """
    notification_dao = NotificationDAO(db)
    marked_count = await notification_dao.mark_all_read(current_user.id)
    await db.commit()

    logger.info(f"User {current_user.id} marked {marked_count} notifications as read")
    return {"marked_count": marked_count}
