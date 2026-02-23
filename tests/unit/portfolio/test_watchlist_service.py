# tests/unit/test_services_watchlist.py
"""Unit tests for WatchlistService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.domains.portfolio.services.watchlist_exceptions import (
    WatchlistError,
    WatchlistNotFoundError,
)
from backend.domains.portfolio.services.watchlist_service import WatchlistService
from backend.shared.ai.state.enums import Market
from backend.shared.db.models.portfolio import Watchlist, WatchlistItem

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_watchlist_dao():
    dao = MagicMock()
    dao.session = MagicMock()
    dao.session.execute = AsyncMock()
    dao.get_user_watchlists = AsyncMock()
    dao.create = AsyncMock()
    dao.get_by_id = AsyncMock()
    dao.add_item = AsyncMock()
    dao.remove_item = AsyncMock()
    dao.delete = AsyncMock()
    dao.get_default_watchlist = AsyncMock()
    return dao


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def watchlist_service(mock_watchlist_dao):
    return WatchlistService(watchlist_dao=mock_watchlist_dao)


@pytest.fixture
def sample_user_id():
    return uuid.uuid4()


@pytest.fixture
def sample_watchlist_id():
    return uuid.uuid4()


@pytest.fixture
def sample_watchlist(sample_user_id, sample_watchlist_id):
    watchlist = MagicMock(spec=Watchlist)
    watchlist.id = sample_watchlist_id
    watchlist.user_id = sample_user_id
    watchlist.name = "My Watchlist"
    return watchlist


@pytest.fixture
def sample_item(sample_watchlist_id):
    item = MagicMock(spec=WatchlistItem)
    item.id = uuid.uuid4()
    item.watchlist_id = sample_watchlist_id
    item.ticker = "AAPL"
    item.market = Market.US
    return item


# ---------------------------------------------------------------------------
# get_user_watchlists
# ---------------------------------------------------------------------------


class TestGetUserWatchlists:
    async def test_success_returns_watchlists(
        self, watchlist_service, mock_watchlist_dao, sample_user_id, sample_watchlist
    ):
        """Returns the list of watchlists from the DAO on success."""
        mock_watchlist_dao.get_user_watchlists.return_value = [sample_watchlist]

        result = await watchlist_service.get_user_watchlists(sample_user_id)

        assert result == [sample_watchlist]
        mock_watchlist_dao.get_user_watchlists.assert_awaited_once_with(sample_user_id)

    async def test_success_empty_list(
        self, watchlist_service, mock_watchlist_dao, sample_user_id
    ):
        """Returns empty list when the user has no watchlists."""
        mock_watchlist_dao.get_user_watchlists.return_value = []

        result = await watchlist_service.get_user_watchlists(sample_user_id)

        assert result == []

    async def test_dao_error_raises_watchlist_error(
        self, watchlist_service, mock_watchlist_dao, sample_user_id
    ):
        """DAO exception is wrapped in WatchlistError."""
        mock_watchlist_dao.get_user_watchlists.side_effect = RuntimeError("db error")

        with pytest.raises(WatchlistError) as exc_info:
            await watchlist_service.get_user_watchlists(sample_user_id)

        assert str(sample_user_id) in str(exc_info.value)


# ---------------------------------------------------------------------------
# create_watchlist
# ---------------------------------------------------------------------------


class TestCreateWatchlist:
    async def test_success_commits_and_refreshes(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_user_id,
        sample_watchlist,
    ):
        """On success, commit and refresh are called, and the watchlist is returned."""
        mock_watchlist_dao.create.return_value = sample_watchlist

        result = await watchlist_service.create_watchlist(
            user_id=sample_user_id, name="Tech Stocks", db=mock_db
        )

        assert result is sample_watchlist
        mock_watchlist_dao.create.assert_awaited_once_with(
            user_id=sample_user_id, name="Tech Stocks"
        )
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(sample_watchlist)
        mock_db.rollback.assert_not_awaited()

    async def test_dao_error_rolls_back_and_raises_watchlist_error(
        self, watchlist_service, mock_watchlist_dao, mock_db, sample_user_id
    ):
        """DAO exception triggers rollback and is wrapped in WatchlistError."""
        mock_watchlist_dao.create.side_effect = RuntimeError("insert failed")

        with pytest.raises(WatchlistError) as exc_info:
            await watchlist_service.create_watchlist(
                user_id=sample_user_id, name="Broken", db=mock_db
            )

        assert "Broken" in str(exc_info.value)
        mock_db.rollback.assert_awaited_once()
        mock_db.commit.assert_not_awaited()

    async def test_commit_error_rolls_back_and_raises_watchlist_error(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_user_id,
        sample_watchlist,
    ):
        """If commit raises, rollback is called and WatchlistError is raised."""
        mock_watchlist_dao.create.return_value = sample_watchlist
        mock_db.commit.side_effect = RuntimeError("commit failed")

        with pytest.raises(WatchlistError):
            await watchlist_service.create_watchlist(
                user_id=sample_user_id, name="Watchlist", db=mock_db
            )

        mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# add_to_watchlist
# ---------------------------------------------------------------------------


class TestAddToWatchlist:
    async def test_success_returns_item(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
        sample_watchlist,
        sample_item,
    ):
        """On success, the new item is returned after commit and refresh."""
        mock_watchlist_dao.get_by_id.return_value = sample_watchlist
        mock_watchlist_dao.add_item.return_value = sample_item

        result = await watchlist_service.add_to_watchlist(
            watchlist_id=sample_watchlist_id,
            ticker="AAPL",
            market=Market.US,
            db=mock_db,
        )

        assert result is sample_item
        mock_watchlist_dao.get_by_id.assert_awaited_once_with(sample_watchlist_id)
        mock_watchlist_dao.add_item.assert_awaited_once_with(
            sample_watchlist_id, "AAPL", Market.US
        )
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(sample_item)
        mock_db.rollback.assert_not_awaited()

    async def test_watchlist_not_found_raises_not_found_error(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
    ):
        """Raises WatchlistNotFoundError when watchlist does not exist."""
        mock_watchlist_dao.get_by_id.return_value = None

        with pytest.raises(WatchlistNotFoundError) as exc_info:
            await watchlist_service.add_to_watchlist(
                watchlist_id=sample_watchlist_id,
                ticker="TSLA",
                market=Market.US,
                db=mock_db,
            )

        assert str(sample_watchlist_id) in str(exc_info.value)
        mock_db.rollback.assert_not_awaited()
        mock_db.commit.assert_not_awaited()

    async def test_dao_add_item_error_rolls_back_and_raises_watchlist_error(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
        sample_watchlist,
    ):
        """DAO error in add_item triggers rollback and raises WatchlistError."""
        mock_watchlist_dao.get_by_id.return_value = sample_watchlist
        mock_watchlist_dao.add_item.side_effect = RuntimeError("add failed")

        with pytest.raises(WatchlistError) as exc_info:
            await watchlist_service.add_to_watchlist(
                watchlist_id=sample_watchlist_id,
                ticker="MSFT",
                market=Market.US,
                db=mock_db,
            )

        assert "MSFT" in str(exc_info.value)
        mock_db.rollback.assert_awaited_once()
        mock_db.commit.assert_not_awaited()

    async def test_watchlist_not_found_error_is_not_swallowed(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
    ):
        """WatchlistNotFoundError propagates unmodified (not wrapped in WatchlistError)."""
        mock_watchlist_dao.get_by_id.return_value = None

        with pytest.raises(WatchlistNotFoundError):
            await watchlist_service.add_to_watchlist(
                watchlist_id=sample_watchlist_id,
                ticker="GOOG",
                market=Market.US,
                db=mock_db,
            )


# ---------------------------------------------------------------------------
# remove_from_watchlist
# ---------------------------------------------------------------------------


class TestRemoveFromWatchlist:
    def _make_execute_result(self, item):
        """Build the layered mock that execute() returns."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = item
        return mock_result

    async def test_success_returns_true(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
        sample_watchlist,
        sample_item,
    ):
        """Returns True after successfully removing an existing item."""
        mock_watchlist_dao.get_by_id.return_value = sample_watchlist
        mock_watchlist_dao.remove_item.return_value = True

        result = await watchlist_service.remove_from_watchlist(
            watchlist_id=sample_watchlist_id, ticker="AAPL", db=mock_db
        )

        assert result is True
        mock_watchlist_dao.remove_item.assert_awaited_once_with(
            sample_watchlist_id, "AAPL"
        )
        mock_db.commit.assert_awaited_once()
        mock_db.rollback.assert_not_awaited()

    async def test_item_not_found_returns_false(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
        sample_watchlist,
    ):
        """Returns False when the ticker is not in the watchlist (no deletion performed)."""
        mock_watchlist_dao.get_by_id.return_value = sample_watchlist
        mock_watchlist_dao.remove_item.return_value = False

        result = await watchlist_service.remove_from_watchlist(
            watchlist_id=sample_watchlist_id, ticker="UNKNOWN", db=mock_db
        )

        assert result is False
        mock_watchlist_dao.remove_item.assert_awaited_once_with(
            sample_watchlist_id, "UNKNOWN"
        )
        mock_db.commit.assert_awaited_once()
        mock_db.rollback.assert_not_awaited()

    async def test_watchlist_not_found_raises_not_found_error(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
    ):
        """Raises WatchlistNotFoundError when the watchlist itself does not exist."""
        mock_watchlist_dao.get_by_id.return_value = None

        with pytest.raises(WatchlistNotFoundError) as exc_info:
            await watchlist_service.remove_from_watchlist(
                watchlist_id=sample_watchlist_id, ticker="AAPL", db=mock_db
            )

        assert str(sample_watchlist_id) in str(exc_info.value)
        mock_db.rollback.assert_not_awaited()
        mock_db.commit.assert_not_awaited()

    async def test_watchlist_not_found_error_propagates_unmodified(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
    ):
        """WatchlistNotFoundError is not wrapped in WatchlistError."""
        mock_watchlist_dao.get_by_id.return_value = None

        with pytest.raises(WatchlistNotFoundError):
            await watchlist_service.remove_from_watchlist(
                watchlist_id=sample_watchlist_id, ticker="AAPL", db=mock_db
            )

    async def test_execute_error_rolls_back_and_raises_watchlist_error(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
        sample_watchlist,
    ):
        """DAO remove_item failure triggers rollback and raises WatchlistError."""
        mock_watchlist_dao.get_by_id.return_value = sample_watchlist
        mock_watchlist_dao.remove_item.side_effect = RuntimeError("query failed")

        with pytest.raises(WatchlistError) as exc_info:
            await watchlist_service.remove_from_watchlist(
                watchlist_id=sample_watchlist_id, ticker="AAPL", db=mock_db
            )

        assert "AAPL" in str(exc_info.value)
        mock_db.rollback.assert_awaited_once()
        mock_db.commit.assert_not_awaited()

    async def test_delete_error_rolls_back_and_raises_watchlist_error(
        self,
        watchlist_service,
        mock_watchlist_dao,
        mock_db,
        sample_watchlist_id,
        sample_watchlist,
        sample_item,
    ):
        """DAO commit failure triggers rollback and raises WatchlistError."""
        mock_watchlist_dao.get_by_id.return_value = sample_watchlist
        mock_watchlist_dao.remove_item.return_value = True
        mock_db.commit.side_effect = RuntimeError("commit failed")

        with pytest.raises(WatchlistError):
            await watchlist_service.remove_from_watchlist(
                watchlist_id=sample_watchlist_id, ticker="AAPL", db=mock_db
            )

        mock_db.rollback.assert_awaited_once()


# ---------------------------------------------------------------------------
# get_default_watchlist
# ---------------------------------------------------------------------------


class TestGetDefaultWatchlist:
    async def test_success_returns_default_watchlist(
        self,
        watchlist_service,
        mock_watchlist_dao,
        sample_user_id,
        sample_watchlist,
    ):
        """Returns the default watchlist from the DAO on success."""
        mock_watchlist_dao.get_default_watchlist.return_value = sample_watchlist

        result = await watchlist_service.get_default_watchlist(sample_user_id)

        assert result is sample_watchlist
        mock_watchlist_dao.get_default_watchlist.assert_awaited_once_with(
            sample_user_id
        )

    async def test_dao_error_raises_watchlist_error(
        self,
        watchlist_service,
        mock_watchlist_dao,
        sample_user_id,
    ):
        """DAO exception is wrapped in WatchlistError."""
        mock_watchlist_dao.get_default_watchlist.side_effect = RuntimeError(
            "db unavailable"
        )

        with pytest.raises(WatchlistError) as exc_info:
            await watchlist_service.get_default_watchlist(sample_user_id)

        assert str(sample_user_id) in str(exc_info.value)
