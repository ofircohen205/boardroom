# backend/services/__init__.py
"""Business logic services organized by domain."""
from .alerts.service import AlertService
from .analysis.service import AnalysisService
from .auth.service import AuthService
from .base import BaseService
from .email.service import EmailService
from .exceptions import ServiceError
from .performance_tracking.service import PerformanceService
from .portfolio_management.service import PortfolioService
from .schedules.service import ScheduleService
from .settings.service import SettingsService
from .watchlist.service import WatchlistService

__all__ = [
    # Base classes
    "BaseService",
    "ServiceError",
    # Service classes
    "AlertService",
    "AnalysisService",
    "AuthService",
    "EmailService",
    "PerformanceService",
    "PortfolioService",
    "ScheduleService",
    "SettingsService",
    "WatchlistService",
]
