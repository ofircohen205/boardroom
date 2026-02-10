from abc import ABC, abstractmethod
from typing import Optional, TypedDict

import httpx
import yfinance as yf

from backend.ai.state.enums import Market
from backend.core.cache import cached
from backend.core.enums import MarketDataProvider
from backend.core.logging import get_logger
from backend.core.settings import settings

logger = get_logger(__name__)


class StockData(TypedDict):
    ticker: str
    market: Market
    current_price: float
    open: float
    high: float
    low: float
    volume: int
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    revenue_growth: Optional[float]
    debt_to_equity: Optional[float]
    sector: Optional[str]
    price_history: list[dict]


class BaseMarketDataClient(ABC):
    @abstractmethod
    async def get_stock_data(self, ticker: str, market: Market) -> StockData:
        pass

    @abstractmethod
    async def get_price_history(
        self, ticker: str, market: Market, days: int = 90
    ) -> list[dict]:
        pass


class YahooFinanceClient(BaseMarketDataClient):
    def _format_ticker(self, ticker: str, market: Market) -> str:
        if market == Market.TASE:
            return f"{ticker}.TA"
        return ticker

    @cached(ttl=300, skip_self=True)
    async def get_stock_data(self, ticker: str, market: Market) -> StockData:
        symbol = self._format_ticker(ticker, market)
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="3mo")

        price_history = [
            {
                "date": idx.isoformat(),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": int(row["Volume"]),
            }
            for idx, row in hist.iterrows()
        ]

        return StockData(
            ticker=ticker,
            market=market,
            current_price=info.get("currentPrice", info.get("regularMarketPrice", 0)),
            open=info.get("open", info.get("regularMarketOpen", 0)),
            high=info.get("dayHigh", info.get("regularMarketDayHigh", 0)),
            low=info.get("dayLow", info.get("regularMarketDayLow", 0)),
            volume=info.get("volume", info.get("regularMarketVolume", 0)),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            revenue_growth=info.get("revenueGrowth"),
            debt_to_equity=info.get("debtToEquity"),
            sector=info.get("sector"),
            price_history=price_history,
        )

    @cached(ttl=300, skip_self=True)
    async def get_price_history(
        self, ticker: str, market: Market, days: int = 90
    ) -> list[dict]:
        symbol = self._format_ticker(ticker, market)
        stock = yf.Ticker(symbol)
        hist = stock.history(period=f"{days}d")

        return [
            {
                "date": idx.isoformat(),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": int(row["Volume"]),
            }
            for idx, row in hist.iterrows()
        ]


class AlphaVantageClient(BaseMarketDataClient):
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=30)

    async def get_stock_data(self, ticker: str, market: Market) -> StockData:
        overview = await self._fetch("OVERVIEW", ticker)
        quote = await self._fetch("GLOBAL_QUOTE", ticker)
        history = await self.get_price_history(ticker, market)

        gq = quote.get("Global Quote", {})
        price = float(gq.get("05. price", 0))

        return StockData(
            ticker=ticker,
            market=market,
            current_price=price,
            open=float(gq.get("02. open", 0)),
            high=float(gq.get("03. high", 0)),
            low=float(gq.get("04. low", 0)),
            volume=int(gq.get("06. volume", 0)),
            market_cap=float(overview.get("MarketCapitalization", 0)) or None,
            pe_ratio=float(overview.get("TrailingPE", 0)) or None,
            revenue_growth=float(overview.get("QuarterlyRevenueGrowthYOY", 0)) or None,
            debt_to_equity=None,
            sector=overview.get("Sector"),
            price_history=history,
        )

    async def get_price_history(
        self, ticker: str, market: Market, days: int = 90
    ) -> list[dict]:
        data = await self._fetch("TIME_SERIES_DAILY", ticker)
        ts = data.get("Time Series (Daily)", {})
        entries = sorted(ts.items(), key=lambda x: x[0])[-days:]
        return [
            {
                "date": date,
                "open": float(vals["1. open"]),
                "high": float(vals["2. high"]),
                "low": float(vals["3. low"]),
                "close": float(vals["4. close"]),
                "volume": int(vals["5. volume"]),
            }
            for date, vals in entries
        ]

    async def _fetch(self, function: str, symbol: str) -> dict:
        resp = await self._client.get(
            self.BASE_URL,
            params={"function": function, "symbol": symbol, "apikey": self.api_key},
        )
        resp.raise_for_status()
        return resp.json()


class FallbackMarketDataClient(BaseMarketDataClient):
    """Wraps a primary client with a fallback."""

    def __init__(self, primary: BaseMarketDataClient, fallback: BaseMarketDataClient):
        self.primary = primary
        self.fallback = fallback

    async def get_stock_data(self, ticker: str, market: Market) -> StockData:
        try:
            return await self.primary.get_stock_data(ticker, market)
        except Exception:
            logger.warning("Primary market data failed for %s, using fallback", ticker)
            return await self.fallback.get_stock_data(ticker, market)

    async def get_price_history(
        self, ticker: str, market: Market, days: int = 90
    ) -> list[dict]:
        try:
            return await self.primary.get_price_history(ticker, market, days)
        except Exception:
            logger.warning(
                "Primary price history failed for %s, using fallback", ticker
            )
            return await self.fallback.get_price_history(ticker, market, days)


def get_market_data_client(
    provider: MarketDataProvider | None = None,
) -> BaseMarketDataClient:
    provider = provider or settings.market_data_provider
    match provider:
        case MarketDataProvider.YAHOO:
            yahoo = YahooFinanceClient()
            if settings.alpha_vantage_api_key:
                return FallbackMarketDataClient(
                    yahoo, AlphaVantageClient(settings.alpha_vantage_api_key)
                )
            return yahoo
        case MarketDataProvider.ALPHA_VANTAGE:
            return AlphaVantageClient(settings.alpha_vantage_api_key)
