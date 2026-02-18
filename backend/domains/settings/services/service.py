# backend/services/settings/service.py
"""User settings service layer."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.core.security import get_password_hash, verify_password
from backend.shared.dao.user import UserDAO
from backend.shared.services.base import BaseService

from .exceptions import EmailAlreadyTakenError, InvalidPasswordError, SettingsError


class SettingsService(BaseService):
    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao

    async def update_profile(
        self,
        user_id,
        db: AsyncSession,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
    ) -> dict:
        """Update user profile fields. Returns updated user data."""
        user = await self.user_dao.get_by_id(user_id)
        if not user:
            raise SettingsError("User not found")

        if email and email != user.email:
            existing = await self.user_dao.find_by_email(email)
            if existing:
                raise EmailAlreadyTakenError("Email is already in use")
            user.email = email

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

        await db.flush()
        await db.refresh(user)
        await db.commit()

        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "created_at": user.created_at,
        }

    async def change_password(
        self,
        user_id,
        current_password: str,
        new_password: str,
        db: AsyncSession,
    ) -> None:
        """Change user password. Validates current password first."""
        user = await self.user_dao.get_by_id(user_id)
        if not user:
            raise SettingsError("User not found")

        if not verify_password(current_password, user.password_hash):
            raise InvalidPasswordError("Current password is incorrect")

        user.password_hash = get_password_hash(new_password)
        await db.flush()
        await db.commit()
