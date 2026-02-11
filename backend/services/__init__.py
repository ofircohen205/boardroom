# backend/services/__init__.py
"""Business logic services organized by domain."""
from .analysis.service import AnalysisService
from .analysis_history.service import (
    create_analysis_session,
    get_user_analysis_history,
    save_agent_report,
    save_final_decision,
)
from .auth.service import authenticate_user, login_user, register_user
from .base import BaseService
from .exceptions import ServiceError
from .portfolio_management.service import (
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
    "WatchlistService",
    "ScheduleService",
    "AnalysisService",
    # Auth service functions
    "register_user",
    "login_user",
    "authenticate_user",
    # Portfolio/Watchlist service functions
    "create_watchlist",
    "add_to_watchlist",
    "remove_from_watchlist",
    "get_user_watchlists",
    "create_portfolio",
    "add_position",
    "get_user_portfolios",
    # Analysis service functions
    "create_analysis_session",
    "save_agent_report",
    "save_final_decision",
    "get_user_analysis_history",
]
