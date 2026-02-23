# backend/domains/notifications/api/schemas.py
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.shared.db.models.alerts import NotificationType


class NotificationSchema(BaseModel):
    """Schema for a notification."""

    id: UUID
    type: NotificationType
    title: str
    body: str
    data: dict[str, Any]
    read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
