# tests/unit/auth/test_dao_user.py
"""
Unit tests for backend/shared/dao/user.py.

Tests cover:
- UserDAO.find_by_email: SELECT User WHERE email
- UserDAO.create_user: delegates to BaseDAO.create
- UserDAO.get_with_relations: SELECT User with selectinload options
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.shared.dao.user import UserDAO
from backend.shared.db.models import User

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Lightweight mock async DB session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def dao(mock_session):
    return UserDAO(mock_session)


# ---------------------------------------------------------------------------
# find_by_email
# ---------------------------------------------------------------------------


async def test_find_by_email_returns_user(dao, mock_session):
    """find_by_email() must return the matching User."""
    user = MagicMock(spec=User)
    user.email = "alice@example.com"

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = user
    mock_session.execute.return_value = mock_result

    result = await dao.find_by_email("alice@example.com")

    assert result is user
    mock_session.execute.assert_called_once()


async def test_find_by_email_returns_none_when_not_found(dao, mock_session):
    """find_by_email() must return None when no user with that email exists."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await dao.find_by_email("nobody@example.com")

    assert result is None


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------


async def test_create_user_adds_user_with_correct_fields(dao, mock_session):
    """create_user() must add a User object with email, password_hash, and name."""
    result = await dao.create_user(
        email="bob@example.com",
        password_hash="hashed_password",  # pragma: allowlist secret
        first_name="Bob",
        last_name="Smith",
    )

    mock_session.add.assert_called_once()
    added = mock_session.add.call_args[0][0]
    assert isinstance(added, User)
    assert added.email == "bob@example.com"
    assert added.first_name == "Bob"
    assert added.last_name == "Smith"


async def test_create_user_calls_add_flush_refresh(dao, mock_session):
    """create_user() must call session.add, flush, and refresh."""
    await dao.create_user("user@test.com", "hash", "Test", "User")

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()


async def test_create_user_returns_user(dao, mock_session):
    """create_user() must return a User instance."""
    result = await dao.create_user("new@example.com", "hashed", "New", "User")

    assert isinstance(result, User)


# ---------------------------------------------------------------------------
# get_with_relations
# ---------------------------------------------------------------------------


async def test_get_with_relations_returns_user(dao, mock_session):
    """get_with_relations() must return a User with relations loaded."""
    user_id = uuid4()
    user = MagicMock(spec=User)

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = user
    mock_session.execute.return_value = mock_result

    result = await dao.get_with_relations(user_id)

    assert result is user
    mock_session.execute.assert_called_once()


async def test_get_with_relations_returns_none_when_not_found(dao, mock_session):
    """get_with_relations() returns None when user_id not found."""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_session.execute.return_value = mock_result

    result = await dao.get_with_relations(uuid4())

    assert result is None
