# backend/services/base.py
"""Base service class with common functionality for all services."""
from abc import ABC
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


class BaseService(ABC):
    """
    Abstract base class for all service layer classes.

    Provides common patterns for:
    - Consistent initialization with database session
    - Error handling helpers
    - Logging utilities
    - Type hints for common patterns

    All services should inherit from this class and pass their dependencies (DAOs)
    through __init__.
    """

    def __init__(self, db: Optional[AsyncSession] = None):
        """
        Initialize BaseService.

        Args:
            db: Optional AsyncSession for database operations.
               Some services may not need a session (e.g., pure logic services).
        """
        self.db = db

    def __repr__(self) -> str:
        """Return a string representation of the service."""
        return f"{self.__class__.__name__}()"
