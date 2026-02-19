"""Unit tests for backend.shared.ai.tools.market_data."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.shared.ai.state.enums import Market
from backend.shared.ai.tools.market_data import (
    AlphaVantageClient,
    FallbackMarketDataClient,
    YahooFinanceClient,
    get_market_data_client,
)
from backend.shared.core.enums import MarketDataProvider

# ---------------------------------------------------------------------------
# YahooFinanceClient
# ---------------------------------------------------------------------------


class TestYahooFinanceClientFormatTicker:
    def test_us_market_unchanged(self):
        client = YahooFinanceClient()
        assert client._format_ticker("AAPL", Market.US) == "AAPL"

    def test_tase_market_appends_ta(self):
        client = YahooFinanceClient()
        assert client._format_ticker("TEVA", Market.TASE) == "TEVA.TA"


class TestYahooFinanceClientGetStockData:
    @pytest.mark.asyncio
    async def test_get_stock_data_builds_stock_data(self):
        client = YahooFinanceClient()

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "Open": 150.0,
            "High": 155.0,
            "Low": 148.0,
            "Close": 152.0,
            "Volume": 1000000,
        }[key]

        mock_hist = MagicMock()
        mock_hist.iterrows.return_value = [
            (MagicMock(isoformat=lambda: "2024-01-01"), mock_row)
        ]

        mock_stock = MagicMock()
        mock_stock.info = {
            "currentPrice": 152.0,
            "open": 150.0,
            "dayHigh": 155.0,
            "dayLow": 148.0,
            "volume": 1000000,
            "marketCap": 2_500_000_000_000,
            "trailingPE": 28.5,
            "revenueGrowth": 0.08,
            "debtToEquity": 1.5,
            "sector": "Technology",
        }
        mock_stock.history.return_value = mock_hist

        with patch(
            "backend.shared.ai.tools.market_data.yf.Ticker", return_value=mock_stock
        ):
            result = await client.get_stock_data("AAPL", Market.US)

        assert result["ticker"] == "AAPL"
        assert result["market"] == Market.US
        assert result["current_price"] == 152.0
        assert result["sector"] == "Technology"
        assert result["pe_ratio"] == 28.5

    @pytest.mark.asyncio
    async def test_get_price_history_uses_days_period(self):
        client = YahooFinanceClient()

        mock_row = MagicMock()
        mock_row.__getitem__ = lambda self, key: {
            "Open": 100.0,
            "High": 110.0,
            "Low": 95.0,
            "Close": 105.0,
            "Volume": 500000,
        }[key]

        mock_hist = MagicMock()
        mock_hist.iterrows.return_value = [
            (MagicMock(isoformat=lambda: "2024-01-10"), mock_row)
        ]

        mock_stock = MagicMock()
        mock_stock.history.return_value = mock_hist

        with patch(
            "backend.shared.ai.tools.market_data.yf.Ticker", return_value=mock_stock
        ):
            result = await client.get_price_history("AAPL", Market.US, days=30)

        mock_stock.history.assert_called_once_with(period="30d")
        assert len(result) == 1
        assert result[0]["close"] == 105.0


# ---------------------------------------------------------------------------
# AlphaVantageClient
# ---------------------------------------------------------------------------


class TestAlphaVantageClient:
    @pytest.mark.asyncio
    async def test_get_stock_data_maps_fields(self):
        client = AlphaVantageClient(api_key="test-key")

        overview = {
            "MarketCapitalization": "1000000000",
            "TrailingPE": "25.0",
            "QuarterlyRevenueGrowthYOY": "0.1",
            "Sector": "Technology",
        }
        quote = {
            "Global Quote": {
                "05. price": "150.0",
                "02. open": "148.0",
                "03. high": "152.0",
                "04. low": "147.0",
                "06. volume": "2000000",
            }
        }
        history_data = {"Time Series (Daily)": {}}

        with patch.object(client, "_fetch", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [overview, quote, history_data]
            result = await client.get_stock_data("AAPL", Market.US)

        assert result["ticker"] == "AAPL"
        assert result["current_price"] == 150.0
        assert result["open"] == 148.0
        assert result["sector"] == "Technology"

    @pytest.mark.asyncio
    async def test_get_price_history_slices_to_days(self):
        client = AlphaVantageClient(api_key="test-key")

        ts = {
            f"2024-01-{i:02d}": {
                "1. open": "100",
                "2. high": "110",
                "3. low": "95",
                "4. close": "105",
                "5. volume": "1000",
            }
            for i in range(1, 11)
        }
        data = {"Time Series (Daily)": ts}

        with patch.object(client, "_fetch", new_callable=AsyncMock, return_value=data):
            result = await client.get_price_history("AAPL", Market.US, days=5)

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_fetch_raises_on_http_error(self):
        import httpx

        client = AlphaVantageClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )

        with patch.object(
            client._client, "get", new_callable=AsyncMock, return_value=mock_response
        ):
            with pytest.raises(httpx.HTTPStatusError):
                await client._fetch("OVERVIEW", "AAPL")


# ---------------------------------------------------------------------------
# FallbackMarketDataClient
# ---------------------------------------------------------------------------


class TestFallbackMarketDataClient:
    @pytest.mark.asyncio
    async def test_get_stock_data_uses_primary_on_success(self):
        primary = MagicMock()
        primary.get_stock_data = AsyncMock(return_value={"ticker": "AAPL"})
        fallback = MagicMock()
        fallback.get_stock_data = AsyncMock(return_value={"ticker": "FALLBACK"})

        client = FallbackMarketDataClient(primary, fallback)
        result = await client.get_stock_data("AAPL", Market.US)

        assert result["ticker"] == "AAPL"
        fallback.get_stock_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_stock_data_falls_back_on_primary_failure(self):
        primary = MagicMock()
        primary.get_stock_data = AsyncMock(side_effect=Exception("primary failed"))
        fallback = MagicMock()
        fallback.get_stock_data = AsyncMock(return_value={"ticker": "AAPL_FALLBACK"})

        client = FallbackMarketDataClient(primary, fallback)
        result = await client.get_stock_data("AAPL", Market.US)

        assert result["ticker"] == "AAPL_FALLBACK"

    @pytest.mark.asyncio
    async def test_get_price_history_uses_primary(self):
        primary = MagicMock()
        primary.get_price_history = AsyncMock(return_value=[{"date": "2024-01-01"}])
        fallback = MagicMock()
        fallback.get_price_history = AsyncMock(return_value=[])

        client = FallbackMarketDataClient(primary, fallback)
        result = await client.get_price_history("AAPL", Market.US, days=30)

        assert len(result) == 1
        fallback.get_price_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_price_history_falls_back_on_failure(self):
        primary = MagicMock()
        primary.get_price_history = AsyncMock(side_effect=Exception("fail"))
        fallback = MagicMock()
        fallback.get_price_history = AsyncMock(return_value=[{"date": "2024-01-01"}])

        client = FallbackMarketDataClient(primary, fallback)
        result = await client.get_price_history("AAPL", Market.US, days=30)

        assert len(result) == 1


# ---------------------------------------------------------------------------
# get_market_data_client factory
# ---------------------------------------------------------------------------


class TestGetMarketDataClient:
    def test_returns_yahoo_client_when_no_alpha_key(self):
        with patch("backend.shared.ai.tools.market_data.settings") as mock_settings:
            mock_settings.market_data_provider = MarketDataProvider.YAHOO
            mock_settings.alpha_vantage_api_key.get_secret_value.return_value = ""

            client = get_market_data_client()

        assert isinstance(client, YahooFinanceClient)

    def test_returns_fallback_client_when_alpha_key_present(self):
        with patch("backend.shared.ai.tools.market_data.settings") as mock_settings:
            mock_settings.market_data_provider = MarketDataProvider.YAHOO
            mock_settings.alpha_vantage_api_key.get_secret_value.return_value = (
                "av-key-123"
            )

            client = get_market_data_client(MarketDataProvider.YAHOO)

        assert isinstance(client, FallbackMarketDataClient)

    def test_returns_alpha_vantage_client_directly(self):
        with patch("backend.shared.ai.tools.market_data.settings") as mock_settings:
            mock_settings.alpha_vantage_api_key.get_secret_value.return_value = (
                "av-key-123"
            )

            client = get_market_data_client(MarketDataProvider.ALPHA_VANTAGE)

        assert isinstance(client, AlphaVantageClient)

    def test_uses_settings_provider_when_none_given(self):
        with patch("backend.shared.ai.tools.market_data.settings") as mock_settings:
            mock_settings.market_data_provider = MarketDataProvider.YAHOO
            mock_settings.alpha_vantage_api_key.get_secret_value.return_value = ""

            client = get_market_data_client(None)

        assert isinstance(client, YahooFinanceClient)
