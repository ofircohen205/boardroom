# tests/unit/shared/test_dao_base.py
"""Unit tests for BaseDAO (backend/shared/dao/base.py).

Tests use a concrete UserDAO subclass and a fully mocked AsyncSession
so no real database connection is required.  asyncio_mode = "auto" in
pyproject.toml means @pytest.mark.asyncio is not needed.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.shared.dao.base import BaseDAO
from backend.shared.db.models import User

# ---------------------------------------------------------------------------
# Concrete subclass used to exercise the generic BaseDAO
# ---------------------------------------------------------------------------


class UserDAO(BaseDAO[User]):
    """Minimal concrete DAO used only for testing BaseDAO behaviour."""

    def __init__(self, session):
        super().__init__(session, User)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_first_result(item):
    """Return a mock execute() result whose scalars().first() yields *item*."""
    result = MagicMock()
    result.scalars.return_value.first.return_value = item
    return result


def make_scalars_all(items):
    """Return a mock execute() result whose scalars().all() yields *items*."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


def make_delete_result(rowcount: int):
    """Return a mock execute() result with the given rowcount (for DELETE)."""
    result = MagicMock()
    result.rowcount = rowcount
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """AsyncSession mock with all required async methods."""
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
# get_by_id
# ---------------------------------------------------------------------------


async def test_get_by_id_returns_record_when_found(dao, mock_session):
    """get_by_id should return the model instance when the query finds a row."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    mock_session.execute.return_value = make_first_result(user)

    result = await dao.get_by_id(user.id)

    assert result is user
    mock_session.execute.assert_awaited_once()


async def test_get_by_id_returns_none_when_not_found(dao, mock_session):
    """get_by_id should return None when no matching row exists."""
    mock_session.execute.return_value = make_first_result(None)

    result = await dao.get_by_id(uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# get_all
# ---------------------------------------------------------------------------


async def test_get_all_returns_list_with_default_pagination(dao, mock_session):
    """get_all with no arguments should return all items as a list."""
    users = [MagicMock(spec=User), MagicMock(spec=User)]
    mock_session.execute.return_value = make_scalars_all(users)

    result = await dao.get_all()

    assert result == users
    assert isinstance(result, list)
    mock_session.execute.assert_awaited_once()


async def test_get_all_accepts_custom_limit_and_offset(dao, mock_session):
    """get_all should forward limit and offset to the underlying query."""
    users = [MagicMock(spec=User)]
    mock_session.execute.return_value = make_scalars_all(users)

    result = await dao.get_all(limit=10, offset=5)

    assert result == users
    mock_session.execute.assert_awaited_once()


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


async def test_create_adds_commits_flushes_and_refreshes(dao, mock_session):
    """create() must add the new instance and persist it via commit/flush/refresh."""
    created_user = MagicMock(spec=User)
    dao.model = MagicMock(return_value=created_user)

    result = await dao.create(
        email="test@example.com",
        hashed_password="hashed",  # pragma: allowlist secret
    )

    mock_session.add.assert_called_once_with(created_user)
    mock_session.commit.assert_awaited_once()
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(created_user)
    assert result is created_user


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


async def test_save_adds_commits_flushes_and_refreshes(dao, mock_session):
    """save() must persist an existing instance and refresh it."""
    user = MagicMock(spec=User)

    result = await dao.save(user)

    mock_session.add.assert_called_once_with(user)
    mock_session.commit.assert_awaited_once()
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(user)
    assert result is user


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


async def test_update_adds_commits_flushes_and_refreshes(dao, mock_session):
    """update() must re-add the instance and persist changes."""
    user = MagicMock(spec=User)

    result = await dao.update(user)

    mock_session.add.assert_called_once_with(user)
    mock_session.commit.assert_awaited_once()
    mock_session.flush.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(user)
    assert result is user


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


async def test_delete_returns_true_when_row_deleted(dao, mock_session):
    """delete() should return True when the DELETE statement affects a row."""
    mock_session.execute.return_value = make_delete_result(rowcount=1)

    result = await dao.delete(uuid4())

    assert result is True
    mock_session.flush.assert_awaited_once()


async def test_delete_returns_false_when_row_not_found(dao, mock_session):
    """delete() should return False when no matching row exists."""
    mock_session.execute.return_value = make_delete_result(rowcount=0)

    result = await dao.delete(uuid4())

    assert result is False
    mock_session.flush.assert_awaited_once()
