# backend/services/portfolio_management/__init__.py
"""Portfolio and watchlist management."""
from .service import (
    add_position,
    add_to_watchlist,
    create_portfolio,
    create_watchlist,
    get_user_portfolios,
    get_user_watchlists,
    remove_from_watchlist,
)

__all__ = [
    "get_user_watchlists",
    "create_watchlist",
    "add_to_watchlist",
    "remove_from_watchlist",
    "get_user_portfolios",
    "create_portfolio",
    "add_position",
]
