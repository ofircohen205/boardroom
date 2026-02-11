# backend/services/__init__.py
"""Business logic services organized by domain."""
from .analysis.service import AnalysisService
from .analysis_history.service import (
    create_analysis_session,
    get_user_analysis_history,
    save_agent_report,
    save_final_decision,
)
from .auth.service import AuthService, authenticate_user, login_user, register_user
from .base import BaseService
from .exceptions import ServiceError
from .portfolio_management.service import (
    PortfolioService,
    add_position,
    add_to_watchlist,
    create_portfolio,
    create_watchlist,
    get_user_portfolios,
    get_user_watchlists,
    remove_from_watchlist,
)
from .schedules.service import ScheduleService
from .watchlist.service import WatchlistService

__all__ = [
    # Base classes
    "BaseService",
    "ServiceError",
    # Service classes
    "AuthService",
    "WatchlistService",
    "PortfolioService",
    "ScheduleService",
    "AnalysisService",
    # Auth service functions (deprecated, use AuthService)
    "register_user",
    "login_user",
    "authenticate_user",
    # Portfolio/Watchlist service functions (deprecated, use PortfolioService/WatchlistService)
    "create_watchlist",
    "add_to_watchlist",
    "remove_from_watchlist",
    "get_user_watchlists",
    "create_portfolio",
    "add_position",
    "get_user_portfolios",
    # Analysis service functions (deprecated, use AnalysisService)
    "create_analysis_session",
    "save_agent_report",
    "save_final_decision",
    "get_user_analysis_history",
]
