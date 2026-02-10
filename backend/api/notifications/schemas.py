# backend/api/notifications/schemas.py
"""Pydantic schemas for notifications API."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class NotificationSchema(BaseModel):
    """Schema for notification response."""
    id: UUID
    type: str
    title: str
    body: str
    data: dict
    read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountSchema(BaseModel):
    """Schema for unread notification count."""
    unread_count: int
