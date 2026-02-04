from abc import ABC, abstractmethod
from typing import Optional, TypedDict

import yfinance as yf

from backend.config import MarketDataProvider, settings
from backend.state.enums import Market


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
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_stock_data(self, ticker: str, market: Market) -> StockData:
        raise NotImplementedError("Alpha Vantage client not yet implemented")

    async def get_price_history(
        self, ticker: str, market: Market, days: int = 90
    ) -> list[dict]:
        raise NotImplementedError("Alpha Vantage client not yet implemented")


def get_market_data_client(
    provider: MarketDataProvider | None = None,
) -> BaseMarketDataClient:
    provider = provider or settings.market_data_provider
    match provider:
        case MarketDataProvider.YAHOO:
            return YahooFinanceClient()
        case MarketDataProvider.ALPHA_VANTAGE:
            return AlphaVantageClient(settings.alpha_vantage_api_key)
