# backend/dependencies.py
"""FastAPI dependency injection factories for services.

These functions are used with FastAPI's Depends() to inject properly
configured service instances into endpoints.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.analysis.services.backtesting_services import (
    BacktestService,
    PaperTradingService,
    StrategyService,
)
from backend.domains.analysis.services.service import AnalysisService
from backend.domains.auth.services.service import AuthService
from backend.domains.notifications.services import (
    AlertService,
    EmailService,
    ScheduleService,
)
from backend.domains.notifications.services.notification_service import (
    NotificationService,
)
from backend.domains.performance.services.service import PerformanceService
from backend.domains.portfolio.services import PortfolioService, WatchlistService
from backend.domains.settings.services.service import SettingsService
from backend.shared.dao import (
    AnalysisDAO,
    NotificationDAO,
    PerformanceDAO,
    PortfolioDAO,
    PriceAlertDAO,
    ScheduledAnalysisDAO,
    UserDAO,
    WatchlistDAO,
)
from backend.shared.db.database import get_db


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Factory function to create AuthService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        AuthService instance with DAOs injected
    """
    return AuthService(UserDAO(db), WatchlistDAO(db), PortfolioDAO(db))


async def get_watchlist_service(db: AsyncSession = Depends(get_db)) -> WatchlistService:
    """Factory function to create WatchlistService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        WatchlistService instance with DAO injected
    """
    return WatchlistService(WatchlistDAO(db))


async def get_portfolio_service(db: AsyncSession = Depends(get_db)) -> PortfolioService:
    """Factory function to create PortfolioService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        PortfolioService instance with DAO injected
    """
    return PortfolioService(PortfolioDAO(db))


async def get_schedule_service(db: AsyncSession = Depends(get_db)) -> ScheduleService:
    """Factory function to create ScheduleService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        ScheduleService instance with DAO injected
    """
    return ScheduleService(ScheduledAnalysisDAO(db))


async def get_analysis_service(db: AsyncSession = Depends(get_db)) -> AnalysisService:
    """Factory function to create AnalysisService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        AnalysisService instance with DAO injected
    """
    return AnalysisService(AnalysisDAO(db))


async def get_alert_service(db: AsyncSession = Depends(get_db)) -> AlertService:
    """Factory function to create AlertService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        AlertService instance with DAOs injected
    """
    return AlertService(PriceAlertDAO(db), NotificationDAO(db))


async def get_performance_service(
    db: AsyncSession = Depends(get_db),
) -> PerformanceService:
    """Factory function to create PerformanceService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        PerformanceService instance with DAO injected
    """
    return PerformanceService(PerformanceDAO(db))


async def get_notification_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationService:
    """Factory function to create NotificationService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        NotificationService instance with DAO injected
    """
    return NotificationService(NotificationDAO(db))


async def get_settings_service(db: AsyncSession = Depends(get_db)) -> SettingsService:
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


async def get_strategy_service(
    db: AsyncSession = Depends(get_db),
) -> StrategyService:
    """Factory function to create StrategyService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        StrategyService instance with DAO injected
    """
    return StrategyService(db)


async def get_backtest_service(
    db: AsyncSession = Depends(get_db),
) -> BacktestService:
    """Factory function to create BacktestService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        BacktestService instance with DAO injected
    """
    return BacktestService(db)


async def get_paper_trading_service(
    db: AsyncSession = Depends(get_db),
) -> PaperTradingService:
    """Factory function to create PaperTradingService with dependency injection.

    Args:
        db: Database session (injected by FastAPI)

    Returns:
        PaperTradingService instance with DAO injected
    """
    return PaperTradingService(db)
