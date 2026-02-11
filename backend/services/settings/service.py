# backend/services/settings/service.py
"""User settings service layer."""
import base64
import binascii
from typing import List

from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.enums import LLMProvider
from backend.core.security import get_password_hash, verify_password
from backend.dao.user import UserDAO
from backend.services.base import BaseService

from .exceptions import EmailAlreadyTakenError, InvalidPasswordError, SettingsError


def _get_fernet() -> Fernet:
    """Get Fernet instance for API key encryption."""
    from backend.core.settings import settings

    # The key must be a URL-safe base64-encoded 32-byte key.
    # You can generate one using `cryptography.fernet.Fernet.generate_key()`
    if not settings.api_key_encryption_key:
        # This check is redundant if the setting has no default, but it's good practice.
        raise ValueError("API_KEY_ENCRYPTION_KEY is not set in the environment.")

    try:
        key = settings.api_key_encryption_key.encode()
        # Validate that the key is a valid 32-byte Fernet key
        if len(base64.urlsafe_b64decode(key)) != 32:
            raise ValueError()
    except (ValueError, binascii.Error):
        raise ValueError(
            "API_KEY_ENCRYPTION_KEY must be a valid URL-safe base64-encoded 32-byte key."
        )

    return Fernet(key)


def _mask_key(raw_key: str) -> str:
    """Mask an API key for display, showing first 4 and last 3 chars."""
    if len(raw_key) <= 8:
        return raw_key[:2] + "..." + "***"
    return raw_key[:4] + "..." + raw_key[-3:]


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

    async def get_api_keys_masked(self, user_id, db: AsyncSession) -> List[dict]:
        """Get all API keys for a user with masked values."""
        keys = await self.user_dao.get_api_keys(user_id)
        fernet = _get_fernet()

        result = []
        for key in keys:
            try:
                decrypted = fernet.decrypt(key.encrypted_key).decode()
                masked = _mask_key(decrypted)
            except Exception:
                masked = "***invalid***"

            result.append(
                {
                    "provider": key.provider.value,
                    "masked_key": masked,
                    "created_at": key.created_at,
                }
            )

        return result

    async def upsert_api_key(
        self, user_id, provider: LLMProvider, raw_key: str, db: AsyncSession
    ) -> dict:
        """Create or update an API key for a user."""
        fernet = _get_fernet()
        encrypted = fernet.encrypt(raw_key.encode())

        api_key = await self.user_dao.create_api_key(user_id, provider, encrypted)
        await db.commit()

        return {
            "provider": api_key.provider.value,
            "masked_key": _mask_key(raw_key),
            "created_at": api_key.created_at,
        }

    async def delete_api_key(
        self, user_id, provider: LLMProvider, db: AsyncSession
    ) -> bool:
        """Delete an API key for a user."""
        deleted = await self.user_dao.delete_api_key(user_id, provider)
        await db.commit()
        return deleted
