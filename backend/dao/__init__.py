# backend/dao/__init__.py
"""
Data Access Objects for database operations.

DAOs provide a clean abstraction layer over database models, encapsulating
all SQL queries and database operations. This makes it easier to:
- Test business logic without a database
- Maintain consistent query patterns
- Refactor database schema without touching business logic
"""
from .base import BaseDAO
from .user import UserDAO
from .portfolio import WatchlistDAO, PortfolioDAO
from .analysis import AnalysisDAO
from .performance import PerformanceDAO

__all__ = [
    "BaseDAO",
    "UserDAO",
    "WatchlistDAO",
    "PortfolioDAO",
    "AnalysisDAO",
    "PerformanceDAO",
]
