# backend/services/dependencies.py
"""FastAPI dependency injection factories for services.

These functions are used with FastAPI's Depends() to inject properly
configured service instances into endpoints.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao import (
    AnalysisDAO,
    NotificationDAO,
    PerformanceDAO,
    PortfolioDAO,
    PriceAlertDAO,
    ScheduledAnalysisDAO,
    UserDAO,
    WatchlistDAO,
)
from backend.services.alerts.service import AlertService
from backend.services.analysis.service import AnalysisService
from backend.services.auth.service import AuthService
from backend.services.email import EmailService
from backend.services.performance_tracking.service import PerformanceService
from backend.services.portfolio_management.service import PortfolioService
from backend.services.schedules.service import ScheduleService
from backend.services.settings.service import SettingsService
from backend.services.watchlist.service import WatchlistService


async def get_auth_service(db: AsyncSession) -> AuthService:
    """Factory function to create AuthService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        AuthService instance with DAOs injected
    """
    return AuthService(UserDAO(db), WatchlistDAO(db), PortfolioDAO(db))


async def get_watchlist_service(db: AsyncSession) -> WatchlistService:
    """Factory function to create WatchlistService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        WatchlistService instance with DAO injected
    """
    return WatchlistService(WatchlistDAO(db))


async def get_portfolio_service(db: AsyncSession) -> PortfolioService:
    """Factory function to create PortfolioService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        PortfolioService instance with DAO injected
    """
    return PortfolioService(PortfolioDAO(db))


async def get_schedule_service(db: AsyncSession) -> ScheduleService:
    """Factory function to create ScheduleService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ScheduleService instance with DAO injected
    """
    return ScheduleService(ScheduledAnalysisDAO(db))


async def get_analysis_service(db: AsyncSession) -> AnalysisService:
    """Factory function to create AnalysisService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        AnalysisService instance with DAO injected
    """
    return AnalysisService(AnalysisDAO(db))


async def get_alert_service(db: AsyncSession) -> AlertService:
    """Factory function to create AlertService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        AlertService instance with DAOs injected
    """
    return AlertService(PriceAlertDAO(db), NotificationDAO(db))


async def get_performance_service(db: AsyncSession) -> PerformanceService:
    """Factory function to create PerformanceService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        PerformanceService instance with DAO injected
    """
    return PerformanceService(PerformanceDAO(db))


async def get_settings_service(db: AsyncSession) -> SettingsService:
    """Factory function to create SettingsService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        SettingsService instance with DAO injected
    """
    return SettingsService(UserDAO(db))


async def get_email_service() -> EmailService:
    """Factory function to create EmailService with dependency injection.

    Returns:
        EmailService instance
    """
    return EmailService()
