# backend/api/watchlists/endpoints.py
"""Watchlist endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_watchlist_service
from backend.domains.portfolio.services import WatchlistService
from backend.shared.ai.state.enums import Market
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.models import User

from .watchlists_schemas import WatchlistItemSchema, WatchlistSchema

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
) -> WatchlistSchema:
    """Create a new watchlist."""
    watchlist = await service.create_watchlist(
        current_user.id, name, service.watchlist_dao.session
    )
    return WatchlistSchema(id=str(watchlist.id), name=watchlist.name, items=[])


@router.post("/{watchlist_id}/items")
async def add_item(
    watchlist_id: UUID,
    ticker: str,
    market: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistItemSchema:
    """Add a stock to a watchlist."""
    try:
        market_enum = Market(market)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid market: {market}")
    item = await service.add_to_watchlist(
        watchlist_id, ticker, market_enum, service.watchlist_dao.session
    )
    return WatchlistItemSchema(
        id=str(item.id), ticker=item.ticker, market=item.market.value
    )


@router.delete("/{watchlist_id}/items/{ticker}")
async def remove_item(
    watchlist_id: UUID,
    ticker: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: WatchlistService = Depends(get_watchlist_service),
) -> dict[str, str]:
    """Remove a stock from a watchlist."""
    removed = await service.remove_from_watchlist(
        watchlist_id, ticker, service.watchlist_dao.session
    )
    if not removed:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted"}
