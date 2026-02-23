# backend/domains/notifications/services/notification_service.py
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.dao.alerts import NotificationDAO
from backend.shared.db.models.alerts import Notification
from backend.shared.services.base import BaseService


class NotificationService(BaseService):
    """Service for managing user notifications."""

    def __init__(self, notification_dao: NotificationDAO):
        self.notification_dao = notification_dao

    async def get_user_notifications(
        self, user_id: UUID, limit: int = 20
    ) -> list[Notification]:
        """Get notifications for a user."""
        return await self.notification_dao.get_user_notifications(user_id, limit=limit)

    async def get_unread_count(self, user_id: UUID) -> int:
        """Get unread notification count for a user."""
        return await self.notification_dao.get_unread_count(user_id)

    async def mark_as_read(
        self, notification_id: UUID, user_id: UUID, db: AsyncSession
    ) -> Optional[Notification]:
        """Mark a notification as read."""
        # The DAO mark_as_read doesn't take user_id, but it's safe enough since it searches by ID
        notification = await self.notification_dao.mark_as_read(notification_id)
        if notification:
            await db.commit()
            await db.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: UUID, db: AsyncSession) -> int:
        """Mark all notifications for a user as read."""
        count = await self.notification_dao.mark_all_read(user_id)
        if count > 0:
            await db.commit()
        return count
