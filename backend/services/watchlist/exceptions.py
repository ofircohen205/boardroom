# backend/services/watchlist/exceptions.py
"""Watchlist service exceptions."""
from backend.services.exceptions import ServiceError


class WatchlistError(ServiceError):
    """Base exception for watchlist service errors."""

    pass


class WatchlistNotFoundError(WatchlistError):
    """Raised when a watchlist is not found."""

    pass
