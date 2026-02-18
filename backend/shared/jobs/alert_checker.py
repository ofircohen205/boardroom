# backend/jobs/alert_checker.py
"""Background job to check price alerts and trigger notifications."""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.notifications.services import AlertService
from backend.shared.ai.tools.market_data import get_market_data_client
from backend.shared.core.logging import get_logger
from backend.shared.dao.alerts import NotificationDAO, PriceAlertDAO
from backend.shared.db.models import AlertCondition

logger = get_logger(__name__)

# US market hours: 9:30 AM - 4:00 PM ET, Monday-Friday
US_MARKET_OPEN_HOUR = 9
US_MARKET_OPEN_MINUTE = 30
US_MARKET_CLOSE_HOUR = 16
US_MARKET_CLOSE_MINUTE = 0

# TASE (Tel Aviv Stock Exchange) market hours: 10:00 AM - 4:45 PM IST, Sunday-Thursday
TASE_MARKET_OPEN_HOUR = 10
TASE_MARKET_OPEN_MINUTE = 0
TASE_MARKET_CLOSE_HOUR = 16
TASE_MARKET_CLOSE_MINUTE = 45


def is_market_hours(market: str = "US") -> bool:
    """
    Check if specified market is currently open.

    Args:
        market: Market code ("US" or "TASE")

    Returns:
        True if within market hours, False otherwise
    """
    if market == "TASE":
        return is_tase_market_hours()
    else:  # Default to US market
        return is_us_market_hours()


def is_us_market_hours() -> bool:
    """
    Check if US market is currently open.

    Returns:
        True if within market hours (9:30 AM - 4:00 PM ET, Mon-Fri), False otherwise
    """
    # Get current time in US/Eastern timezone
    et_tz = ZoneInfo("America/New_York")
    now = datetime.now(et_tz)

    # Check if weekday (0=Monday, 4=Friday)
    if now.weekday() > 4:
        return False

    # Check if within market hours
    current_time = now.time()
    market_open = now.replace(
        hour=US_MARKET_OPEN_HOUR, minute=US_MARKET_OPEN_MINUTE
    ).time()
    market_close = now.replace(
        hour=US_MARKET_CLOSE_HOUR, minute=US_MARKET_CLOSE_MINUTE
    ).time()

    return market_open <= current_time < market_close


def is_tase_market_hours() -> bool:
    """
    Check if TASE (Tel Aviv Stock Exchange) market is currently open.

    Returns:
        True if within market hours (10:00 AM - 4:45 PM IST, Sun-Thu), False otherwise
    """
    # Get current time in Israel/Tel Aviv timezone
    ist_tz = ZoneInfo("Asia/Jerusalem")
    now = datetime.now(ist_tz)

    # Check if weekday (6=Sunday, 3=Thursday in Israeli week)
    # weekday() returns 0=Monday, 6=Sunday
    # TASE is open Sunday-Thursday (6, 0, 1, 2, 3)
    if now.weekday() > 3 and now.weekday() < 6:
        return False  # Friday (4) or Saturday (5)

    # Check if within market hours
    current_time = now.time()
    market_open = now.replace(
        hour=TASE_MARKET_OPEN_HOUR, minute=TASE_MARKET_OPEN_MINUTE
    ).time()
    market_close = now.replace(
        hour=TASE_MARKET_CLOSE_HOUR, minute=TASE_MARKET_CLOSE_MINUTE
    ).time()

    return market_open <= current_time < market_close


def check_alert_condition(alert, current_price: float) -> bool:
    """
    Check if an alert condition is met.

    Args:
        alert: PriceAlert object with condition, target_value, and baseline_price
        current_price: Current stock price

    Returns:
        True if alert should be triggered, False otherwise
    """
    if alert.condition == AlertCondition.ABOVE:
        return current_price > alert.target_value

    elif alert.condition == AlertCondition.BELOW:
        return current_price < alert.target_value

    elif alert.condition == AlertCondition.CHANGE_PCT:
        # Use stored baseline price from alert creation
        baseline_price = alert.baseline_price
        if baseline_price is None or baseline_price == 0:
            logger.warning(
                f"Alert {alert.id}: No baseline price for change_pct alert on {alert.ticker}, skipping"
            )
            return False

        pct_change = abs((current_price - baseline_price) / baseline_price * 100)
        logger.debug(
            f"Alert {alert.id}: {alert.ticker} change: {pct_change:.2f}% (current: ${current_price}, baseline: ${baseline_price}, threshold: {alert.target_value}%)"
        )
        return pct_change >= alert.target_value

    return False


async def check_price_alerts(db: AsyncSession) -> dict:
    """
    Check all active price alerts and trigger notifications.

    This function:
    1. Gets all unique tickers with active alerts
    2. Groups by market and checks if each market is open
    3. Batch fetches prices for all tickers
    4. Checks each alert condition
    5. Triggers notifications for alerts that meet conditions

    Args:
        db: Database session

    Returns:
        dict with stats: alerts_checked, alerts_triggered, duration_seconds
    """
    start_time = datetime.now()

    logger.info("Starting alert checker job")
    alert_dao = PriceAlertDAO(db)
    # TODO: Refactor jobs to be class-based and inject services
    alert_service = AlertService(alert_dao, NotificationDAO(db))

    try:
        # Get all unique (ticker, market) pairs with active alerts
        tickers = await alert_dao.get_all_active_tickers()

        if not tickers:
            logger.info("No active alerts to check")
            return {
                "success": True,
                "alerts_checked": 0,
                "alerts_triggered": 0,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
            }

        logger.info(f"Checking alerts for {len(tickers)} unique tickers")

        # Check which markets are open and filter tickers
        open_tickers = []
        us_open = is_us_market_hours()
        tase_open = is_tase_market_hours()

        for ticker, market in tickers:
            market_str = market.value if hasattr(market, "value") else str(market)
            if market_str == "US" and us_open:
                open_tickers.append((ticker, market))
            elif market_str == "TASE" and tase_open:
                open_tickers.append((ticker, market))
            else:
                logger.debug(f"Skipping {ticker} ({market_str}) - market closed")

        if not open_tickers:
            logger.info("No markets are currently open, skipping alert checker")
            return {
                "success": True,
                "alerts_checked": 0,
                "alerts_triggered": 0,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "skipped": "all_markets_closed",
            }

        logger.info(
            f"Markets open - US: {us_open}, TASE: {tase_open}. Checking {len(open_tickers)} tickers"
        )

        # Batch fetch prices for tickers in open markets
        market_data_client = get_market_data_client()
        prices = {}

        for ticker, market in open_tickers:
            try:
                stock_data = await market_data_client.get_stock_data(ticker, market)
                prices[(ticker, market)] = stock_data.get("current_price")
                logger.debug(
                    f"Fetched price for {ticker} ({market.value}): ${prices[(ticker, market)]}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to fetch price for {ticker} ({market.value}): {e}"
                )
                prices[(ticker, market)] = None

        # Check each ticker's alerts (only for open markets)
        alerts_checked = 0
        alerts_triggered = 0

        for ticker, market in open_tickers:
            current_price = prices.get((ticker, market))
            if current_price is None:
                logger.warning(f"Skipping alerts for {ticker} - no price data")
                continue

            # Get all active alerts for this ticker
            alerts = await alert_dao.get_active_alerts_for_ticker(ticker, market)

            for alert in alerts:
                alerts_checked += 1

                # Check alert condition (baseline_price now stored in alert object for change_pct)
                if check_alert_condition(alert, current_price):
                    try:
                        await alert_service.trigger_alert(db, alert, current_price)
                        alerts_triggered += 1
                        logger.info(
                            f"Triggered alert {alert.id} for {ticker} at ${current_price}"
                        )
                    except Exception as e:
                        logger.error(f"Failed to trigger alert {alert.id}: {e}")

        # Commit all changes
        await db.commit()

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"Alert checker completed: {alerts_checked} checked, {alerts_triggered} triggered in {duration:.2f}s"
        )

        return {
            "success": True,
            "alerts_checked": alerts_checked,
            "alerts_triggered": alerts_triggered,
            "duration_seconds": duration,
        }

    except Exception as e:
        logger.error(f"Alert checker job failed: {e}", exc_info=True)
        await db.rollback()
        return {
            "success": False,
            "error": str(e),
            "alerts_checked": 0,
            "alerts_triggered": 0,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
        }
