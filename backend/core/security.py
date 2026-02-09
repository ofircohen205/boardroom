# backend/core/security.py
"""Security utilities: JWT tokens, password hashing."""
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
import bcrypt
# Monkeypatch bcrypt for passlib compatibility
bcrypt.__about__ = type("about", (object,), {"__version__": bcrypt.__version__})
from passlib.context import CryptContext

from .settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.

    Handles unicode correctly by encoding to UTF-8 and truncating to 72 bytes
    (bcrypt's maximum input length).
    """
    # Encode to bytes first, then truncate to 72 bytes (bcrypt limit)
    # This handles unicode characters correctly
    password_bytes = password.encode('utf-8')
    truncated = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload to encode in the token
        expires_delta: Optional expiration time delta. Defaults to 15 minutes.

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.algorithm)
    return encoded_jwt
