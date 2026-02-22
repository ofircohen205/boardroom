# backend/api/routes.py
"""Utility endpoints (markets, cache, stock search)."""

from fastapi import APIRouter

from backend.shared.ai.state.enums import Market
from backend.shared.ai.tools.stock_search import search_stocks
from backend.shared.core.cache import get_cache

router = APIRouter()


@router.get("/markets")
async def get_markets():
    """Get available markets."""
    return {m.value: m.name for m in Market}


@router.get("/stocks/search")
async def search_stocks_endpoint(q: str = "", market: Market = Market.US) -> list[dict]:
    """Search for stock symbols matching the query."""
    results = await search_stocks(q, market)
    return [
        {
            "symbol": r.symbol,
            "name": r.name,
            "exchange": r.exchange,
        }
        for r in results
    ]


@router.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return await get_cache().stats()


@router.post("/cache/clear")
async def cache_clear():
    """Clear the cache."""
    await get_cache().clear()
    return {"status": "cleared"}
