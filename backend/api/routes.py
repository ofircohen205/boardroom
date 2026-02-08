from fastapi import APIRouter

from backend.state.enums import Market
from backend.tools.stock_search import StockSuggestion, search_stocks

router = APIRouter(prefix="/api")


@router.get("/markets")
async def get_markets():
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

