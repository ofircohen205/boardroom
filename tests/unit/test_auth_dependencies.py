"""Unit tests for auth dependencies."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.auth.dependencies import get_current_user, get_current_user_optional
from backend.shared.core.security import create_access_token


@pytest.fixture
def mock_db():
    """Mock async database session."""
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """A mock User object that does not require a real database."""
    user = MagicMock()
    user.id = uuid4()
    user.email = "auth-test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def valid_token(mock_user):
    """Create a valid JWT token for the mock user."""
    return create_access_token({"sub": mock_user.email})


async def test_get_current_user_valid_token(mock_user, mock_db, valid_token):
    """get_current_user returns user when given a valid token."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    user = await get_current_user(valid_token, mock_db)

    assert user == mock_user


async def test_get_current_user_invalid_token(mock_db):
    """get_current_user raises 401 for a malformed JWT token."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("invalid.token.here", mock_db)
    assert exc_info.value.status_code == 401


async def test_get_current_user_user_not_found(mock_db, valid_token):
    """get_current_user raises 401 when user is not in the database."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(valid_token, mock_db)
    assert exc_info.value.status_code == 401


async def test_get_current_user_token_missing_sub(mock_db):
    """get_current_user raises 401 when token payload has no sub field.

    The code converts None → 'None' (str), so it still queries the DB;
    the 401 is raised because no user has the email 'None'.
    """
    token_no_sub = create_access_token({"user": "orphan"})
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token_no_sub, mock_db)
    assert exc_info.value.status_code == 401


async def test_get_current_user_sets_www_authenticate_header(mock_db):
    """get_current_user 401 response includes WWW-Authenticate: Bearer header."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user("bad.token", mock_db)
    assert "Bearer" in exc_info.value.headers.get("WWW-Authenticate", "")


async def test_get_current_user_optional_valid_token(mock_user, mock_db, valid_token):
    """get_current_user_optional returns user when given a valid token."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    user = await get_current_user_optional(valid_token, mock_db)

    assert user == mock_user


async def test_get_current_user_optional_no_token(mock_db):
    """get_current_user_optional returns None when no token is provided."""
    user = await get_current_user_optional(None, mock_db)
    assert user is None


async def test_get_current_user_optional_invalid_token(mock_db):
    """get_current_user_optional returns None for invalid token (does not raise)."""
    user = await get_current_user_optional("bad.token.here", mock_db)
    assert user is None


async def test_get_current_user_optional_user_not_found(mock_db, valid_token):
    """get_current_user_optional returns None when user is not in database (does not raise)."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result

    user = await get_current_user_optional(valid_token, mock_db)
    assert user is None
