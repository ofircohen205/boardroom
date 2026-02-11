# backend/api/watchlists/endpoints.py
"""Watchlist endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.state.enums import Market
from backend.auth.dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models import User
from backend.services.dependencies import get_watchlist_service
from backend.services.watchlist.service import WatchlistService

from .schemas import WatchlistItemSchema, WatchlistSchema

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


@router.get("")
async def list_watchlists(
    current_user: Annotated[User, Depends(get_current_user)],
    service: WatchlistService = Depends(get_watchlist_service),
) -> list[WatchlistSchema]:
    """Get all watchlists for current user."""
    watchlists = await service.get_user_watchlists(current_user.id)
    return [
        WatchlistSchema(
            id=str(w.id),
            name=w.name,
            items=[
                WatchlistItemSchema(
                    id=str(i.id), ticker=i.ticker, market=i.market.value
                )
                for i in w.items
            ],
        )
        for w in watchlists
    ]


@router.post("")
async def create_new_watchlist(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: WatchlistService = Depends(get_watchlist_service),
    db: AsyncSession = Depends(get_db),
) -> WatchlistSchema:
    """Create a new watchlist."""
    watchlist = await service.create_watchlist(current_user.id, name, db)
    return WatchlistSchema(id=str(watchlist.id), name=watchlist.name, items=[])


@router.post("/{watchlist_id}/items")
async def add_item(
    watchlist_id: UUID,
    ticker: str,
    market: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: WatchlistService = Depends(get_watchlist_service),
    db: AsyncSession = Depends(get_db),
) -> WatchlistItemSchema:
    """Add a stock to a watchlist."""
    market_enum = Market.TASE if market == "TASE" else Market.US
    item = await service.add_to_watchlist(watchlist_id, ticker, market_enum, db)
    return WatchlistItemSchema(
        id=str(item.id), ticker=item.ticker, market=item.market.value
    )


@router.delete("/{watchlist_id}/items/{ticker}")
async def remove_item(
    watchlist_id: UUID,
    ticker: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: WatchlistService = Depends(get_watchlist_service),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Remove a stock from a watchlist."""
    removed = await service.remove_from_watchlist(watchlist_id, ticker, db)
    if not removed:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted"}
