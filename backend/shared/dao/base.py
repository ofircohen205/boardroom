# backend/dao/base.py
"""Base DAO with common CRUD operations."""

from functools import lru_cache
from typing import ClassVar, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.db.models import Base

T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    """
    Base Data Access Object with common CRUD operations.

    Generic type T must be a SQLAlchemy model (subclass of Base).
    """

    _instances: ClassVar[dict] = {}

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls, session: AsyncSession, model: Type[T]):
        """
        Get a singleton instance of the DAO.
        Uses LRU cache for optimization.
        """
        if cls not in cls._instances:
            cls._instances[cls] = cls(session, model)
        return cls._instances[cls]

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get a single record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all records with pagination."""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, **kwargs) -> T:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: T) -> T:
        """Update an existing record."""
        self.session.add(instance)
        await self.session.commit()
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> bool:
        """Delete a record by ID. Returns True if deleted, False if not found."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def count(self) -> int:
        """Count total records."""
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0
