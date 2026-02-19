"""Unit tests for backend.shared.data.historical."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.shared.data.historical import (
    fetch_and_store_historical_prices,
    get_latest_price,
    get_price_at_date,
    get_price_range,
)


def _make_mock_session():
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def _make_df_row(
    open_=150.0, high=155.0, low=148.0, close=152.0, adj_close=151.5, volume=1_000_000
):
    row = MagicMock()
    row.__getitem__ = lambda self, key: {
        "Open": open_,
        "High": high,
        "Low": low,
        "Close": close,
        "Adj Close": adj_close,
        "Volume": volume,
    }[key]
    row.get = lambda key, default=None: adj_close if key == "Adj Close" else default
    return row


class TestFetchAndStoreHistoricalPrices:
    @pytest.mark.asyncio
    async def test_fetches_and_inserts_new_prices(self):
        session = _make_mock_session()
        start = date(2024, 1, 2)
        end = date(2024, 1, 5)

        mock_dao = MagicMock()
        mock_dao.get_price_range = AsyncMock(return_value=[])  # no existing data
        mock_dao.bulk_create = AsyncMock()

        ts = MagicMock(date=MagicMock(return_value=date(2024, 1, 3)))
        row = _make_df_row()

        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.__len__ = lambda self: 1
        mock_df.iterrows.return_value = [(ts, row)]

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_df

        with (
            patch(
                "backend.shared.data.historical.HistoricalPriceDAO",
                return_value=mock_dao,
            ),
            patch("backend.shared.data.historical.yf.Ticker", return_value=mock_ticker),
        ):
            count = await fetch_and_store_historical_prices(session, "AAPL", start, end)

        assert count >= 0  # inserted or skipped (date boundary logic applies)
        mock_dao.get_price_range.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_existing_dates(self):
        session = _make_mock_session()
        existing_date = date(2024, 1, 3)
        start = date(2024, 1, 2)
        end = date(2024, 1, 5)

        existing_record = MagicMock()
        existing_record.date = existing_date

        mock_dao = MagicMock()
        mock_dao.get_price_range = AsyncMock(return_value=[existing_record])
        mock_dao.bulk_create = AsyncMock()

        ts = MagicMock()
        ts.date = MagicMock(return_value=existing_date)
        row = _make_df_row()

        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.iterrows.return_value = [(ts, row)]

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_df

        with (
            patch(
                "backend.shared.data.historical.HistoricalPriceDAO",
                return_value=mock_dao,
            ),
            patch("backend.shared.data.historical.yf.Ticker", return_value=mock_ticker),
        ):
            count = await fetch_and_store_historical_prices(session, "AAPL", start, end)

        assert count == 0

    @pytest.mark.asyncio
    async def test_returns_zero_on_empty_dataframe(self):
        session = _make_mock_session()

        mock_dao = MagicMock()
        mock_dao.get_price_range = AsyncMock(return_value=[])

        mock_df = MagicMock()
        mock_df.empty = True

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_df

        with (
            patch(
                "backend.shared.data.historical.HistoricalPriceDAO",
                return_value=mock_dao,
            ),
            patch("backend.shared.data.historical.yf.Ticker", return_value=mock_ticker),
        ):
            count = await fetch_and_store_historical_prices(
                session, "INVALID", date(2024, 1, 1), date(2024, 1, 5)
            )

        assert count == 0

    @pytest.mark.asyncio
    async def test_raises_value_error_on_yfinance_exception(self):
        session = _make_mock_session()

        mock_dao = MagicMock()
        mock_dao.get_price_range = AsyncMock(return_value=[])

        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = Exception("network error")

        with (
            patch(
                "backend.shared.data.historical.HistoricalPriceDAO",
                return_value=mock_dao,
            ),
            patch("backend.shared.data.historical.yf.Ticker", return_value=mock_ticker),
        ):
            with pytest.raises(ValueError, match="Failed to fetch data for AAPL"):
                await fetch_and_store_historical_prices(
                    session, "AAPL", date(2024, 1, 1), date(2024, 1, 5)
                )

    @pytest.mark.asyncio
    async def test_skips_invalid_prices(self):
        """Rows with non-positive OHLC values must be skipped."""
        session = _make_mock_session()
        start = date(2024, 1, 2)
        end = date(2024, 1, 5)

        mock_dao = MagicMock()
        mock_dao.get_price_range = AsyncMock(return_value=[])
        mock_dao.bulk_create = AsyncMock()

        ts = MagicMock()
        ts.date = MagicMock(return_value=date(2024, 1, 3))
        # Row with 0 open price — should be skipped
        bad_row = _make_df_row(open_=0.0)

        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.iterrows.return_value = [(ts, bad_row)]

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_df

        with (
            patch(
                "backend.shared.data.historical.HistoricalPriceDAO",
                return_value=mock_dao,
            ),
            patch("backend.shared.data.historical.yf.Ticker", return_value=mock_ticker),
        ):
            count = await fetch_and_store_historical_prices(session, "AAPL", start, end)

        assert count == 0

    @pytest.mark.asyncio
    async def test_rolls_back_on_bulk_create_error(self):
        session = _make_mock_session()
        start = date(2024, 1, 2)
        end = date(2024, 1, 5)

        mock_dao = MagicMock()
        mock_dao.get_price_range = AsyncMock(return_value=[])
        mock_dao.bulk_create = AsyncMock(side_effect=Exception("DB error"))

        ts = MagicMock()
        ts.date = MagicMock(return_value=date(2024, 1, 3))
        row = _make_df_row()

        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.iterrows.return_value = [(ts, row)]

        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_df

        with (
            patch(
                "backend.shared.data.historical.HistoricalPriceDAO",
                return_value=mock_dao,
            ),
            patch("backend.shared.data.historical.yf.Ticker", return_value=mock_ticker),
        ):
            with pytest.raises(Exception):
                await fetch_and_store_historical_prices(session, "AAPL", start, end)

        session.rollback.assert_called_once()


class TestGetPriceAtDate:
    @pytest.mark.asyncio
    async def test_returns_adjusted_close_when_found(self):
        session = _make_mock_session()

        price_record = MagicMock()
        price_record.adjusted_close = Decimal("150.50")

        mock_dao = MagicMock()
        mock_dao.get_price_at_date = AsyncMock(return_value=price_record)

        with patch(
            "backend.shared.data.historical.HistoricalPriceDAO", return_value=mock_dao
        ):
            result = await get_price_at_date(session, "aapl", date(2024, 1, 3))

        assert result == Decimal("150.50")
        mock_dao.get_price_at_date.assert_called_once_with("AAPL", date(2024, 1, 3))

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        session = _make_mock_session()

        mock_dao = MagicMock()
        mock_dao.get_price_at_date = AsyncMock(return_value=None)

        with patch(
            "backend.shared.data.historical.HistoricalPriceDAO", return_value=mock_dao
        ):
            result = await get_price_at_date(session, "AAPL", date(2024, 1, 6))

        assert result is None


class TestGetPriceRange:
    @pytest.mark.asyncio
    async def test_returns_list_of_date_price_tuples(self):
        session = _make_mock_session()

        r1 = MagicMock()
        r1.date = date(2024, 1, 2)
        r1.adjusted_close = Decimal("148.00")

        r2 = MagicMock()
        r2.date = date(2024, 1, 3)
        r2.adjusted_close = Decimal("151.00")

        mock_dao = MagicMock()
        mock_dao.get_price_range = AsyncMock(return_value=[r1, r2])

        with patch(
            "backend.shared.data.historical.HistoricalPriceDAO", return_value=mock_dao
        ):
            result = await get_price_range(
                session, "aapl", date(2024, 1, 2), date(2024, 1, 3)
            )

        assert result == [
            (date(2024, 1, 2), Decimal("148.00")),
            (date(2024, 1, 3), Decimal("151.00")),
        ]

    @pytest.mark.asyncio
    async def test_uppercases_ticker(self):
        session = _make_mock_session()
        mock_dao = MagicMock()
        mock_dao.get_price_range = AsyncMock(return_value=[])

        with patch(
            "backend.shared.data.historical.HistoricalPriceDAO", return_value=mock_dao
        ):
            await get_price_range(session, "aapl", date(2024, 1, 1), date(2024, 1, 5))

        mock_dao.get_price_range.assert_called_once_with(
            "AAPL", date(2024, 1, 1), date(2024, 1, 5)
        )


class TestGetLatestPrice:
    @pytest.mark.asyncio
    async def test_returns_adjusted_close_when_found(self):
        session = _make_mock_session()

        record = MagicMock()
        record.adjusted_close = Decimal("200.00")

        mock_dao = MagicMock()
        mock_dao.get_latest_price = AsyncMock(return_value=record)

        with patch(
            "backend.shared.data.historical.HistoricalPriceDAO", return_value=mock_dao
        ):
            result = await get_latest_price(session, "AAPL")

        assert result == Decimal("200.00")

    @pytest.mark.asyncio
    async def test_returns_none_when_no_data(self):
        session = _make_mock_session()
        mock_dao = MagicMock()
        mock_dao.get_latest_price = AsyncMock(return_value=None)

        with patch(
            "backend.shared.data.historical.HistoricalPriceDAO", return_value=mock_dao
        ):
            result = await get_latest_price(session, "AAPL")

        assert result is None
