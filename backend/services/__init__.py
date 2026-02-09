# backend/services/__init__.py
"""Business logic services organized by domain."""
from .auth.service import register_user, login_user, authenticate_user
from .portfolio_management.service import (
    create_watchlist,
    add_to_watchlist,
    remove_from_watchlist,
    get_user_watchlists,
    create_portfolio,
    add_position,
    get_user_portfolios,
)
from .analysis_history.service import (
    create_analysis_session,
    save_agent_report,
    save_final_decision,
    get_user_analysis_history,
)

__all__ = [
    "register_user",
    "login_user",
    "authenticate_user",
    "create_watchlist",
    "add_to_watchlist",
    "remove_from_watchlist",
    "get_user_watchlists",
    "create_portfolio",
    "add_position",
    "get_user_portfolios",
    "create_analysis_session",
    "save_agent_report",
    "save_final_decision",
    "get_user_analysis_history",
]
