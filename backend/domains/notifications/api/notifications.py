# backend/domains/notifications/api/notifications.py
"""API endpoints for user notifications."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

# Use dependency injection getter (we'll implement this next)
from backend.dependencies import get_notification_service
from backend.domains.notifications.services.notification_service import (
    NotificationService,
)
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.models import User

from .schemas import NotificationSchema

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationSchema])
async def get_notifications(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get recent notifications for the current user."""
    notifications = await service.get_user_notifications(current_user.id, limit)
    return notifications


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Get the number of unread notifications for the current user."""
    count = await service.get_unread_count(current_user.id)
    return {"unread_count": count}


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark a specific notification as read."""
    notification = await service.mark_as_read(
        notification_id, current_user.id, service.notification_dao.session
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return {"success": True}


@router.post("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read for the current user."""
    count = await service.mark_all_as_read(
        current_user.id, service.notification_dao.session
    )
    return {"success": True, "updated_count": count}
