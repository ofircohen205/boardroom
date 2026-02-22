import pytest

from backend.shared.ai.state.enums import Market
from backend.shared.ai.tools.market_data import (
    YahooFinanceClient,
    get_market_data_client,
)
from backend.shared.core.enums import MarketDataProvider


def test_get_market_data_client_yahoo():
    client = get_market_data_client(MarketDataProvider.YAHOO)
    assert isinstance(client, YahooFinanceClient)


def test_yahoo_ticker_formatting():
    client = YahooFinanceClient()
    assert client._format_ticker("AAPL", Market.US) == "AAPL"
    assert client._format_ticker("TEVA", Market.TASE) == "TEVA.TA"


def test_format_ticker_new_markets():
    client = YahooFinanceClient()
    assert client._format_ticker("HSBA", Market.LSE) == "HSBA.L"
    assert client._format_ticker("7203", Market.TSE) == "7203.T"
    assert client._format_ticker("0700", Market.HKEX) == "0700.HK"
    assert client._format_ticker("SAP", Market.XETRA) == "SAP.DE"
    assert client._format_ticker("AAPL", Market.US) == "AAPL"


@pytest.mark.asyncio
async def test_yahoo_get_stock_data():
    client = YahooFinanceClient()
    data = await client.get_stock_data("AAPL", Market.US)
    assert data["ticker"] == "AAPL"
    assert data["current_price"] > 0
    assert "pe_ratio" in data
