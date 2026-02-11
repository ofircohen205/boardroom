# backend/services/schedules/exceptions.py
"""Schedule service exceptions."""
from backend.services.exceptions import ServiceError


class ScheduleError(ServiceError):
    """Base exception for schedule service errors."""

    pass


class ScheduleNotFoundError(ScheduleError):
    """Raised when a schedule is not found."""

    pass


class ScheduleRateLimitError(ScheduleError):
    """Raised when user has too many schedules."""

    pass
