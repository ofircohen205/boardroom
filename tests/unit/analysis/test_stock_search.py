"""Unit tests for backend.shared.ai.tools.stock_search."""

from unittest.mock import MagicMock, patch

import pytest

from backend.shared.ai.state.enums import Market
from backend.shared.ai.tools.stock_search import (
    _POPULAR_STOCKS,
    POPULAR_TASE_STOCKS,
    StockSuggestion,
    search_stocks,
)

# ===========================================================================
# StockSuggestion dataclass
# ===========================================================================


class TestStockSuggestion:
    def test_has_required_fields(self):
        suggestion = StockSuggestion(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            market=Market.US,
        )
        assert suggestion.symbol == "AAPL"
        assert suggestion.name == "Apple Inc."
        assert suggestion.exchange == "NASDAQ"
        assert suggestion.market == Market.US

    def test_tase_market_field(self):
        suggestion = StockSuggestion(
            symbol="TEVA",
            name="Teva Pharmaceutical Industries",
            exchange="TASE",
            market=Market.TASE,
        )
        assert suggestion.market == Market.TASE


# ===========================================================================
# search_stocks — empty / short queries
# ===========================================================================


class TestSearchStocksEmptyQuery:
    async def test_empty_string_returns_empty_list(self):
        result = await search_stocks("", Market.US)
        assert result == []

    async def test_none_like_empty_string_returns_empty_list(self):
        # The function guards `if not query or len(query) < 1`
        result = await search_stocks("", Market.US)
        assert result == []


# ===========================================================================
# search_stocks — popular US stocks cache
# ===========================================================================


class TestSearchStocksPopularUS:
    async def test_exact_us_ticker_found(self):
        result = await search_stocks("AAPL", Market.US)

        symbols = [r.symbol for r in result]
        assert "AAPL" in symbols

    async def test_exact_us_ticker_result_has_correct_fields(self):
        result = await search_stocks("AAPL", Market.US)

        aapl = next(r for r in result if r.symbol == "AAPL")
        assert aapl.name == "Apple Inc."
        assert aapl.exchange == "NASDAQ"
        assert aapl.market == Market.US

    async def test_name_search_case_insensitive_apple(self):
        # "apple" (lowercase) should match AAPL whose name contains "Apple"
        result = await search_stocks("apple", Market.US)

        symbols = [r.symbol for r in result]
        assert "AAPL" in symbols

    async def test_partial_ticker_prefix_matches(self):
        # "AMAZ" is a prefix of nothing directly, but "AMZN" contains "AMZ"
        result = await search_stocks("AMZ", Market.US)

        symbols = [r.symbol for r in result]
        assert "AMZN" in symbols

    async def test_result_type_is_stock_suggestion(self):
        result = await search_stocks("MSFT", Market.US)

        for item in result:
            assert isinstance(item, StockSuggestion)

    async def test_market_field_set_to_us(self):
        result = await search_stocks("TSLA", Market.US)

        for item in result:
            assert item.market == Market.US


# ===========================================================================
# search_stocks — limit parameter
# ===========================================================================


class TestSearchStocksLimit:
    async def test_limit_respected(self):
        # "A" matches many US tickers (AAPL, AMZN, ADBE, AMD, ABNB …)
        result = await search_stocks("A", Market.US, limit=2)

        assert len(result) <= 2

    async def test_default_limit_is_8(self):
        # Broad query that would match more than 8 if uncapped
        result = await search_stocks("A", Market.US)

        assert len(result) <= 8

    async def test_limit_zero_means_fallback_to_yfinance_only(self):
        # limit=0 — popular cache returns immediately when >= limit.
        # With limit=0 the cache loop exits immediately (0 >= 0) but then
        # yfinance branch also runs (len(results) < 0 is False for empty list).
        # Functionally results[:0] == []. Just verify no crash.
        result = await search_stocks("AAPL", Market.US, limit=0)
        assert isinstance(result, list)


# ===========================================================================
# search_stocks — TASE market
# ===========================================================================


class TestSearchStocksTASE:
    async def test_teva_found_in_tase(self):
        result = await search_stocks("TEVA", Market.TASE)

        symbols = [r.symbol for r in result]
        assert "TEVA" in symbols

    async def test_tase_result_has_correct_market(self):
        result = await search_stocks("TEVA", Market.TASE)

        teva = next(r for r in result if r.symbol == "TEVA")
        assert teva.market == Market.TASE
        assert teva.exchange == "TASE"

    async def test_us_ticker_not_found_in_tase_cache(self):
        # AAPL is only in POPULAR_US_STOCKS, not POPULAR_TASE_STOCKS
        result = await search_stocks("AAPL", Market.TASE)

        # Should not come from the cache; result may come from yfinance or be empty
        symbols_from_cache = [
            r.symbol for r in result if r.symbol in POPULAR_TASE_STOCKS
        ]
        assert "AAPL" not in symbols_from_cache


# ===========================================================================
# search_stocks — yfinance fallback (mocked)
# ===========================================================================


class TestSearchStocksYFinanceFallback:
    async def test_unknown_ticker_yfinance_returns_valid_name(self):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Fake Corp", "exchange": "NASDAQ"}

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ):
            result = await search_stocks("FAKE", Market.US)

        symbols = [r.symbol for r in result]
        assert "FAKE" in symbols
        fake = next(r for r in result if r.symbol == "FAKE")
        assert fake.name == "Fake Corp"
        assert fake.exchange == "NASDAQ"

    async def test_unknown_ticker_yfinance_longname_fallback(self):
        mock_ticker = MagicMock()
        # shortName missing, longName present
        mock_ticker.info = {
            "shortName": None,
            "longName": "Long Fake Corp",
            "exchange": "NYSE",
        }

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ):
            result = await search_stocks("LNGF", Market.US)

        symbols = [r.symbol for r in result]
        assert "LNGF" in symbols
        item = next(r for r in result if r.symbol == "LNGF")
        assert item.name == "Long Fake Corp"

    async def test_unknown_ticker_yfinance_raises_exception_returns_empty(self):
        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker",
            side_effect=Exception("network error"),
        ):
            result = await search_stocks("BOOM", Market.US)

        # Gracefully returns [] (no popular match, yfinance failed)
        assert result == []

    async def test_tase_market_yfinance_called_with_ta_suffix(self):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Israeli Corp", "exchange": "TASE"}

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ) as mock_yf:
            await search_stocks("UNKN", Market.TASE)

        mock_yf.assert_called_once_with("UNKN.TA")

    async def test_us_market_yfinance_called_without_suffix(self):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "US Corp", "exchange": "NYSE"}

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ) as mock_yf:
            await search_stocks("UNKN", Market.US)

        mock_yf.assert_called_once_with("UNKN")

    async def test_no_duplicate_when_ticker_already_in_popular(self):
        """If AAPL is found in cache, yfinance result must not be appended again."""
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Apple Inc.", "exchange": "NASDAQ"}

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ):
            result = await search_stocks("AAPL", Market.US)

        aapl_count = sum(1 for r in result if r.symbol == "AAPL")
        assert aapl_count == 1

    async def test_yfinance_empty_info_does_not_add_result(self):
        """If yfinance returns info without shortName or longName, skip it."""
        mock_ticker = MagicMock()
        mock_ticker.info = {}

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ):
            result = await search_stocks("NOOP", Market.US)

        symbols = [r.symbol for r in result]
        assert "NOOP" not in symbols


# ===========================================================================
# International markets — _POPULAR_STOCKS coverage
# ===========================================================================


class TestPopularStocksCoversAllMarkets:
    def test_popular_stocks_covers_all_markets(self):
        """Every Market enum value has a popular stocks entry."""
        for market in Market:
            assert market in _POPULAR_STOCKS, f"Missing popular stocks for {market}"


# ===========================================================================
# International markets — LSE
# ===========================================================================


class TestSearchStocksLSE:
    @pytest.mark.asyncio
    async def test_search_lse_popular(self):
        results = await search_stocks("HSBA", Market.LSE)
        assert any(r.symbol == "HSBA" for r in results)
        assert all(r.market == Market.LSE for r in results)

    @pytest.mark.asyncio
    async def test_lse_yfinance_called_with_l_suffix(self):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Some UK Corp", "exchange": "LSE"}

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ) as mock_yf:
            await search_stocks("UNKN", Market.LSE)

        mock_yf.assert_called_once_with("UNKN.L")


# ===========================================================================
# International markets — TSE
# ===========================================================================


class TestSearchStocksTSE:
    @pytest.mark.asyncio
    async def test_search_tse_popular(self):
        results = await search_stocks("7203", Market.TSE)
        assert any(r.symbol == "7203" for r in results)

    @pytest.mark.asyncio
    async def test_tse_yfinance_called_with_t_suffix(self):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Some JP Corp", "exchange": "TSE"}

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ) as mock_yf:
            await search_stocks("9999", Market.TSE)

        mock_yf.assert_called_once_with("9999.T")


# ===========================================================================
# International markets — HKEX
# ===========================================================================


class TestSearchStocksHKEX:
    @pytest.mark.asyncio
    async def test_search_hkex_popular(self):
        results = await search_stocks("0700", Market.HKEX)
        assert any(r.symbol == "0700" for r in results)

    @pytest.mark.asyncio
    async def test_hkex_yfinance_called_with_hk_suffix(self):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Some HK Corp", "exchange": "HKEX"}

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ) as mock_yf:
            await search_stocks("9999", Market.HKEX)

        mock_yf.assert_called_once_with("9999.HK")


# ===========================================================================
# International markets — XETRA
# ===========================================================================


class TestSearchStocksXETRA:
    @pytest.mark.asyncio
    async def test_search_xetra_popular(self):
        results = await search_stocks("SAP", Market.XETRA)
        assert any(r.symbol == "SAP" for r in results)

    @pytest.mark.asyncio
    async def test_xetra_yfinance_called_with_de_suffix(self):
        mock_ticker = MagicMock()
        mock_ticker.info = {"shortName": "Some DE Corp", "exchange": "XETRA"}

        with patch(
            "backend.shared.ai.tools.stock_search.yf.Ticker", return_value=mock_ticker
        ) as mock_yf:
            await search_stocks("UNKN", Market.XETRA)

        mock_yf.assert_called_once_with("UNKN.DE")
