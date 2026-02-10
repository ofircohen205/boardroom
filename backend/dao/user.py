# backend/dao/user.py
"""User data access objects."""
from functools import lru_cache
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.enums import LLMProvider
from backend.db.models import User, UserAPIKey

from .base import BaseDAO


class UserDAO(BaseDAO[User]):
    """Data access object for User operations."""

    @classmethod
    @lru_cache(maxsize=None)
    def get_instance(cls, session: AsyncSession):
        """Get a singleton instance of the UserDAO."""
        return super().get_instance(session, User)

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
                selectinload(User.api_keys),
            )
        )
        return result.scalars().first()

    async def get_api_keys(self, user_id: UUID) -> List[UserAPIKey]:
        """Get all API keys for a user."""
        result = await self.session.execute(
            select(UserAPIKey).where(UserAPIKey.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_api_key_by_provider(
        self, user_id: UUID, provider: LLMProvider
    ) -> Optional[UserAPIKey]:
        """Get a specific API key for a user by provider."""
        result = await self.session.execute(
            select(UserAPIKey)
            .where(UserAPIKey.user_id == user_id)
            .where(UserAPIKey.provider == provider)
        )
        return result.scalars().first()

    async def create_api_key(
        self, user_id: UUID, provider: LLMProvider, encrypted_key: bytes
    ) -> UserAPIKey:
        """Create or update an API key for a user."""
        # Check if key already exists
        existing = await self.get_api_key_by_provider(user_id, provider)
        if existing:
            # Update existing key
            existing.encrypted_key = encrypted_key
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        else:
            # Create new key
            api_key = UserAPIKey(
                user_id=user_id,
                provider=provider,
                encrypted_key=encrypted_key,
            )
            self.session.add(api_key)
            await self.session.flush()
            await self.session.refresh(api_key)
            return api_key

    async def delete_api_key(self, user_id: UUID, provider: LLMProvider) -> bool:
        """Delete an API key for a user. Returns True if deleted."""
        from sqlalchemy import delete

        result = await self.session.execute(
            delete(UserAPIKey)
            .where(UserAPIKey.user_id == user_id)
            .where(UserAPIKey.provider == provider)
        )
        await self.session.flush()
        return result.rowcount > 0
