# backend/services/auth/service.py
"""Authentication service - handles user registration and login."""

from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from backend.core.settings import settings
from backend.dao.portfolio import PortfolioDAO, WatchlistDAO
from backend.dao.user import UserDAO
from backend.db.models import User
from backend.services.base import BaseService

from .exceptions import InvalidCredentialsError, UserAlreadyExistsError


class AuthService(BaseService):
    """Service for authentication operations."""

    def __init__(
        self,
        user_dao: UserDAO,
        watchlist_dao: WatchlistDAO,
        portfolio_dao: PortfolioDAO,
    ):
        """
        Initialize AuthService.

        Args:
            user_dao: DAO for user operations
            watchlist_dao: DAO for watchlist operations
            portfolio_dao: DAO for portfolio operations
        """
        self.user_dao = user_dao
        self.watchlist_dao = watchlist_dao
        self.portfolio_dao = portfolio_dao

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        db: AsyncSession,
    ) -> tuple[User, str]:
        """
        Register a new user with email, password, and name.

        Creates default watchlist and portfolio for the user.
        Returns (user, access_token).

        Args:
            email: User email address
            password: User password (will be hashed)
            first_name: User first name
            last_name: User last name
            db: Database session

        Returns:
            Tuple of (created User object, access token)

        Raises:
            UserAlreadyExistsError: If email is already registered
        """
        # Check if user exists
        existing = await self.user_dao.find_by_email(email)
        if existing:
            raise UserAlreadyExistsError(f"Email {email} already registered")

        # Create user
        hashed_password = get_password_hash(password)
        user = await self.user_dao.create_user(
            email=email,
            password_hash=hashed_password,
            first_name=first_name,
            last_name=last_name,
        )

        # Create default watchlist and portfolio
        await self.watchlist_dao.create(user_id=user.id, name="My Watchlist")
        await self.portfolio_dao.create(user_id=user.id, name="My Portfolio")

        await db.commit()
        await db.refresh(user)

        # Generate access token
        access_token = self._create_user_token(user.email)

        return user, access_token

    async def login_user(
        self, email: str, password: str, db: AsyncSession
    ) -> tuple[User, str]:
        """
        Authenticate user and return access token.

        Args:
            email: User email address
            password: User password (will be verified against hash)
            db: Database session

        Returns:
            Tuple of (authenticated User object, access token)

        Raises:
            InvalidCredentialsError: If email or password is incorrect
        """
        user = await self.user_dao.find_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Incorrect email or password")

        access_token = self._create_user_token(user.email)

        return user, access_token

    async def authenticate_user(self, email: str) -> Optional[User]:
        """
        Get user by email (for JWT token validation).

        Args:
            email: User email address

        Returns:
            User object or None if user not found
        """
        return await self.user_dao.find_by_email(email)

    def _create_user_token(self, email: str) -> str:
        """
        Create JWT access token for a user.

        Args:
            email: User email address

        Returns:
            Encoded JWT token string
        """
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        return create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
