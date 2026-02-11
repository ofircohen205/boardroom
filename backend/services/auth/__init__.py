# backend/services/auth/__init__.py
"""Authentication service."""
from .exceptions import InvalidCredentialsError, UserAlreadyExistsError
from .service import AuthService

__all__ = [
    "AuthService",
    "UserAlreadyExistsError",
    "InvalidCredentialsError",
]
