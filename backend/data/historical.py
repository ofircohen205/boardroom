"""
Service for fetching and storing historical market data.

Uses Yahoo Finance (via existing market_data tool) to fetch historical OHLCV data
and stores it in the database for backtesting.
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dao.backtesting import HistoricalPriceDAO
from backend.db.models.backtesting import HistoricalPrice

logger = logging.getLogger(__name__)


async def fetch_and_store_historical_prices(
    session: AsyncSession,
    ticker: str,
    start_date: date,
    end_date: date,
) -> int:
    """Fetch historical prices from Yahoo Finance and store in database.

    This function:
    1. Checks for existing data to avoid redundant fetches
    2. Fetches missing data from Yahoo Finance
    3. Stores new data in the database
    4. Handles duplicates gracefully (skip on conflict)

    Args:
        session: Database session
        ticker: Stock ticker symbol
        start_date: Start date for historical data
        end_date: End date for historical data

    Returns:
        Number of new price records inserted

    Raises:
        ValueError: If ticker is invalid or data fetch fails
    """
    dao = HistoricalPriceDAO(session)
    ticker_upper = ticker.upper()

    logger.info(
        f"Fetching historical prices for {ticker_upper} from {start_date} to {end_date}"
    )

    # Check if we already have some data
    existing_prices = await dao.get_price_range(ticker_upper, start_date, end_date)
    existing_dates = {price.date for price in existing_prices}

    logger.info(
        f"Found {len(existing_dates)} existing price records for {ticker_upper}"
    )

    # Fetch data from Yahoo Finance
    try:
        ticker_obj = yf.Ticker(ticker_upper)
        # Add one day buffer to ensure we get end_date data
        df = ticker_obj.history(
            start=start_date.isoformat(),
            end=(end_date + timedelta(days=1)).isoformat(),
            auto_adjust=False,  # We want raw prices and separately adjusted close
        )

        if df.empty:
            logger.warning(f"No historical data found for {ticker_upper}")
            return 0

        logger.info(
            f"Fetched {len(df)} price records from Yahoo Finance for {ticker_upper}"
        )

    except Exception as e:
        logger.error(f"Failed to fetch historical data for {ticker_upper}: {e}")
        raise ValueError(f"Failed to fetch data for {ticker_upper}") from e

    # Convert DataFrame to HistoricalPrice models
    new_prices = []
    for date_val, row in df.iterrows():
        # Convert pandas Timestamp to date
        price_date = date_val.date()

        # Skip if we already have this date
        if price_date in existing_dates:
            continue

        # Skip if date is outside our range
        if price_date < start_date or price_date > end_date:
            continue

        # Validate data quality
        if row["Open"] <= 0 or row["High"] <= 0 or row["Low"] <= 0 or row["Close"] <= 0:
            logger.warning(
                f"Skipping {ticker_upper} {price_date}: invalid prices (non-positive)"
            )
            continue

        # Use Adj Close if available, otherwise use Close
        adjusted_close = row.get("Adj Close", row["Close"])
        if adjusted_close <= 0:
            adjusted_close = row["Close"]

        price_record = HistoricalPrice(
            ticker=ticker_upper,
            date=price_date,
            open=Decimal(str(row["Open"])),
            high=Decimal(str(row["High"])),
            low=Decimal(str(row["Low"])),
            close=Decimal(str(row["Close"])),
            adjusted_close=Decimal(str(adjusted_close)),
            volume=int(row["Volume"]),
            created_at=datetime.utcnow(),
        )
        new_prices.append(price_record)

    if not new_prices:
        logger.info(f"No new prices to insert for {ticker_upper}")
        return 0

    # Bulk insert
    try:
        await dao.bulk_create(new_prices)
        await session.commit()
        logger.info(f"Inserted {len(new_prices)} new price records for {ticker_upper}")
        return len(new_prices)
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to insert prices for {ticker_upper}: {e}")
        raise


async def get_price_at_date(
    session: AsyncSession, ticker: str, target_date: date
) -> Decimal | None:
    """Get adjusted close price for a ticker at a specific date.

    If the exact date doesn't exist (e.g., weekend/holiday), returns None.
    Caller should handle missing dates appropriately.

    Args:
        session: Database session
        ticker: Stock ticker symbol
        target_date: Date to get price for

    Returns:
        Adjusted close price as Decimal, or None if not found
    """
    dao = HistoricalPriceDAO(session)
    price_record = await dao.get_price_at_date(ticker.upper(), target_date)

    if price_record:
        return price_record.adjusted_close
    return None


async def get_price_range(
    session: AsyncSession, ticker: str, start_date: date, end_date: date
) -> list[tuple[date, Decimal]]:
    """Get adjusted close prices for a ticker within a date range.

    Returns prices ordered by date ascending, using adjusted close for
    accurate backtest calculations (handles splits/dividends).

    Args:
        session: Database session
        ticker: Stock ticker symbol
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        List of (date, price) tuples ordered by date
    """
    dao = HistoricalPriceDAO(session)
    price_records = await dao.get_price_range(ticker.upper(), start_date, end_date)

    return [(record.date, record.adjusted_close) for record in price_records]


async def get_latest_price(session: AsyncSession, ticker: str) -> Decimal | None:
    """Get the most recent price for a ticker from historical data.

    This is useful for paper trading to get current prices.
    For live trading, use the real-time market data API instead.

    Args:
        session: Database session
        ticker: Stock ticker symbol

    Returns:
        Most recent adjusted close price, or None if no data
    """
    dao = HistoricalPriceDAO(session)
    price_record = await dao.get_latest_price(ticker.upper())

    if price_record:
        return price_record.adjusted_close
    return None
