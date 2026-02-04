import pytest
from backend.tools.market_data import (
    YahooFinanceClient,
    get_market_data_client,
)
from backend.state.enums import Market
from backend.config import MarketDataProvider


def test_get_market_data_client_yahoo():
    client = get_market_data_client(MarketDataProvider.YAHOO)
    assert isinstance(client, YahooFinanceClient)


def test_yahoo_ticker_formatting():
    client = YahooFinanceClient()
    assert client._format_ticker("AAPL", Market.US) == "AAPL"
    assert client._format_ticker("TEVA", Market.TASE) == "TEVA.TA"


@pytest.mark.asyncio
async def test_yahoo_get_stock_data():
    client = YahooFinanceClient()
    data = await client.get_stock_data("AAPL", Market.US)
    assert data["ticker"] == "AAPL"
    assert data["current_price"] > 0
    assert "pe_ratio" in data
