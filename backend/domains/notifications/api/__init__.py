"""Notifications API endpoints."""

from .alerts import router as alerts_router
from .endpoints import router as notifications_router
from .schedules import router as schedules_router

__all__ = ["alerts_router", "notifications_router", "schedules_router"]
