# backend/api/routes.py
"""Utility endpoints (markets, cache, stock search)."""
from fastapi import APIRouter

from backend.cache import get_cache
from backend.ai.state.enums import Market
from backend.ai.tools.stock_search import search_stocks

router = APIRouter()


@router.get("/markets")
async def get_markets():
    """Get available markets."""
    return {m.value: m.name for m in Market}


@router.get("/stocks/search")
async def search_stocks_endpoint(q: str = "", market: str = "US") -> list[dict]:
    """Search for stock symbols matching the query."""
    market_enum = Market.TASE if market == "TASE" else Market.US
    results = await search_stocks(q, market_enum)
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
