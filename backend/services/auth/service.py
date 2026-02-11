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

from .exceptions import InvalidCredentialsError, UserAlreadyExistsError


async def register_user(
    email: str, password: str, first_name: str, last_name: str, db: AsyncSession
) -> tuple[User, str]:
    """
    Register a new user with email, password, and name.

    Creates default watchlist and portfolio for the user.
    Returns (user, access_token).

    Raises:
        UserAlreadyExistsError: If email is already registered
    """
    user_dao = UserDAO(db)

    # Check if user exists
    existing = await user_dao.find_by_email(email)
    if existing:
        raise UserAlreadyExistsError(f"Email {email} already registered")

    # Create user
    hashed_password = get_password_hash(password)
    user = await user_dao.create_user(
        email=email,
        password_hash=hashed_password,
        first_name=first_name,
        last_name=last_name,
    )

    # Create default watchlist and portfolio
    watchlist_dao = WatchlistDAO(db)
    portfolio_dao = PortfolioDAO(db)

    await watchlist_dao.create(user_id=user.id, name="My Watchlist")
    await portfolio_dao.create(user_id=user.id, name="My Portfolio")

    await db.commit()
    await db.refresh(user)

    # Generate access token
    access_token = _create_user_token(user.email)

    return user, access_token


async def login_user(email: str, password: str, db: AsyncSession) -> tuple[User, str]:
    """
    Authenticate user and return access token.

    Returns (user, access_token).

    Raises:
        InvalidCredentialsError: If email or password is incorrect
    """
    user_dao = UserDAO(db)

    user = await user_dao.find_by_email(email)
    if not user or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Incorrect email or password")

    access_token = _create_user_token(user.email)

    return user, access_token


async def authenticate_user(email: str, db: AsyncSession) -> Optional[User]:
    """
    Get user by email (for JWT token validation).

    Returns None if user not found.
    """
    user_dao = UserDAO(db)
    return await user_dao.find_by_email(email)


def _create_user_token(email: str) -> str:
    """Create JWT access token for a user."""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    return create_access_token(data={"sub": email}, expires_delta=access_token_expires)
