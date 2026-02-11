# backend/dao/__init__.py
"""
Data Access Objects for database operations.

DAOs provide a clean abstraction layer over database models, encapsulating
all SQL queries and database operations. This makes it easier to:
- Test business logic without a database
- Maintain consistent query patterns
- Refactor database schema without touching business logic
"""
from .alerts import NotificationDAO, PriceAlertDAO, ScheduledAnalysisDAO
from .analysis import AnalysisDAO
from .backtesting import (
    BacktestResultDAO,
    HistoricalFundamentalsDAO,
    HistoricalPriceDAO,
    PaperAccountDAO,
    PaperPositionDAO,
    PaperTradeDAO,
    StrategyDAO,
)
from .base import BaseDAO
from .performance import PerformanceDAO
from .portfolio import PortfolioDAO, WatchlistDAO
from .user import UserDAO

__all__ = [
    "AnalysisDAO",
    "BacktestResultDAO",
    "BaseDAO",
    "HistoricalFundamentalsDAO",
    "HistoricalPriceDAO",
    "NotificationDAO",
    "PaperAccountDAO",
    "PaperPositionDAO",
    "PaperTradeDAO",
    "PerformanceDAO",
    "PortfolioDAO",
    "PriceAlertDAO",
    "ScheduledAnalysisDAO",
    "StrategyDAO",
    "UserDAO",
    "WatchlistDAO",
]
