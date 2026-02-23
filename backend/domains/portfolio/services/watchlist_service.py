# backend/services/portfolio/watchlist_service.py
"""Watchlist service - manages user watchlists and items."""

from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.ai.state.enums import Market
from backend.shared.dao.portfolio import WatchlistDAO
from backend.shared.db.models import Watchlist, WatchlistItem
from backend.shared.services.base import BaseService

from .watchlist_exceptions import WatchlistError, WatchlistNotFoundError


class WatchlistService(BaseService):
    """Service for watchlist operations."""

    def __init__(self, watchlist_dao: WatchlistDAO):
        """
        Initialize WatchlistService.

        Args:
            watchlist_dao: DAO for watchlist operations
        """
        self.watchlist_dao = watchlist_dao

    async def get_user_watchlists(self, user_id: UUID) -> List[Watchlist]:
        """
        Get all watchlists for a user.

        Args:
            user_id: User ID

        Returns:
            List of Watchlist objects with items loaded

        Raises:
            WatchlistError: If database operation fails
        """
        try:
            return await self.watchlist_dao.get_user_watchlists(user_id)
        except Exception as e:
            raise WatchlistError(
                f"Failed to fetch watchlists for user {user_id}: {e!s}"
            )

    async def create_watchlist(
        self, user_id: UUID, name: str, db: AsyncSession
    ) -> Watchlist:
        """
        Create a new watchlist for a user.

        Args:
            user_id: User ID
            name: Watchlist name
            db: Database session

        Returns:
            Created Watchlist object

        Raises:
            WatchlistError: If creation fails
        """
        try:
            watchlist = await self.watchlist_dao.create(user_id=user_id, name=name)
            await db.commit()
            await db.refresh(watchlist)
            return watchlist
        except Exception as e:
            await db.rollback()
            raise WatchlistError(f"Failed to create watchlist '{name}': {e!s}")

    async def add_to_watchlist(
        self, watchlist_id: UUID, ticker: str, market: Market, db: AsyncSession
    ) -> WatchlistItem:
        """
        Add a stock to a watchlist.

        Args:
            watchlist_id: Watchlist ID
            ticker: Stock ticker symbol
            market: Market enum (US or TASE)
            db: Database session

        Returns:
            Created or existing WatchlistItem

        Raises:
            WatchlistNotFoundError: If watchlist doesn't exist
            WatchlistError: If operation fails
        """
        try:
            # Verify watchlist exists
            watchlist = await self.watchlist_dao.get_by_id(watchlist_id)
            if not watchlist:
                raise WatchlistNotFoundError(f"Watchlist {watchlist_id} not found")

            # Add item to watchlist
            item = await self.watchlist_dao.add_item(watchlist_id, ticker, market)
            await db.commit()
            await db.refresh(item)
            return item
        except WatchlistNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            raise WatchlistError(
                f"Failed to add {ticker} to watchlist {watchlist_id}: {e!s}"
            )

    async def remove_from_watchlist(
        self, watchlist_id: UUID, ticker: str, db: AsyncSession
    ) -> bool:
        """
        Remove a stock from a watchlist.

        Args:
            watchlist_id: Watchlist ID
            ticker: Stock ticker symbol
            db: Database session

        Returns:
            True if item was removed, False if not found

        Raises:
            WatchlistNotFoundError: If watchlist doesn't exist
            WatchlistError: If operation fails
        """
        try:
            # Verify watchlist exists
            watchlist = await self.watchlist_dao.get_by_id(watchlist_id)
            if not watchlist:
                raise WatchlistNotFoundError(f"Watchlist {watchlist_id} not found")

            # Delete the item
            removed = await self.watchlist_dao.remove_item(watchlist_id, ticker)
            await db.commit()
            return removed
        except WatchlistNotFoundError:
            raise
        except Exception as e:
            await db.rollback()
            raise WatchlistError(
                f"Failed to remove {ticker} from watchlist {watchlist_id}: {e!s}"
            )

    async def get_default_watchlist(self, user_id: UUID) -> Watchlist:
        """
        Get or create the default watchlist for a user.

        Args:
            user_id: User ID

        Returns:
            Default Watchlist object

        Raises:
            WatchlistError: If operation fails
        """
        try:
            return await self.watchlist_dao.get_default_watchlist(user_id)
        except Exception as e:
            raise WatchlistError(
                f"Failed to get or create default watchlist for user {user_id}: {e!s}"
            )
