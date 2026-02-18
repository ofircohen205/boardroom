# backend/dao/user.py
"""User data access objects."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.shared.db.models import User

from .base import BaseDAO


class UserDAO(BaseDAO[User]):
    """Data access object for User operations."""

    def __init__(self, session: AsyncSession):
        """Initialize UserDAO with a database session."""
        super().__init__(session, User)

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def create_user(
        self, email: str, password_hash: str, first_name: str, last_name: str
    ) -> User:
        """Create a new user with email, password, and name."""
        return await self.create(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )

    async def get_with_relations(self, user_id: UUID) -> Optional[User]:
        """
        Get user with all relationships loaded (watchlists, portfolios, api_keys).
        Useful for dashboard queries.
        """
        result = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.watchlists),
                selectinload(User.portfolios),
            )
        )
        return result.scalars().first()
