"""
Technical analysis scorer for backtesting.

Calculates a technical score (0-100) based on:
- Moving averages (trend direction)
- RSI (momentum/overbought/oversold)
- Price action relative to historical levels
"""

import logging
from decimal import Decimal

from backend.shared.ai.tools.technical_indicators import (
    calculate_ma,
    calculate_rsi,
)

logger = logging.getLogger(__name__)


def calculate_technical_score(
    prices: list[Decimal], volumes: list[int] | None = None
) -> float:
    """Calculate technical score from price history.

    This is a rules-based approximation of what the Technical Agent would analyze.
    Uses MA crossovers and RSI to determine trend strength and momentum.

    Scoring Logic:
    - MA50 > MA20: Bullish trend (+20 points)
    - Current price > MA50: Above trend (+20 points)
    - RSI analysis:
      - RSI < 30: Oversold, potential buy (+30 points)
      - RSI 30-45: Slightly oversold (+20 points)
      - RSI 45-55: Neutral (+10 points)
      - RSI 55-70: Slightly overbought (-10 points)
      - RSI > 70: Overbought, potential sell (-20 points)
    - Recent momentum: +/- 10 points based on 5-day return

    Args:
        prices: List of closing prices (most recent last)
        volumes: Optional list of volumes (not currently used)

    Returns:
        Score from 0-100, where:
        - 80-100: Strong buy signal
        - 60-79: Moderate buy
        - 40-59: Neutral/hold
        - 20-39: Moderate sell
        - 0-19: Strong sell signal
    """
    if len(prices) < 50:
        logger.warning(
            f"Not enough price history ({len(prices)} points, need 50+). Returning neutral score."
        )
        return 50.0  # Neutral if insufficient data

    # Convert Decimal to float for calculations
    price_floats = [float(p) for p in prices]
    current_price = price_floats[-1]

    # Calculate moving averages
    # calculate_ma returns a single float, not a list
    ma_20_val = calculate_ma(price_floats, period=20)
    ma_50_val = calculate_ma(price_floats, period=50)

    if ma_20_val == 0.0 or ma_50_val == 0.0:
        # 0.0 is returned if not enough data or other error in calculate_ma
        logger.warning("Failed to calculate moving averages. Returning neutral score.")
        return 50.0

    # Calculate RSI
    rsi = calculate_rsi(price_floats, period=14)
    if rsi is None:
        logger.warning("Failed to calculate RSI. Returning neutral score.")
        return 50.0

    # Start with base score
    score = 50.0

    # 1. Trend analysis (MA crossover and position)
    # 1. Trend analysis (MA crossover and position)
    # 1. Trend analysis (MA crossover and position)
    if ma_20_val > ma_50_val:
        # Bullish: short-term MA above long-term
        score += 20
    elif ma_20_val < ma_50_val:
        # Bearish: short-term MA below long-term
        score -= 20

    # 2. Price position relative to MA50
    # 2. Price position relative to MA50
    if current_price > ma_50_val:
        # Above long-term trend
        score += 20
    else:
        # Below long-term trend
        score -= 20

    # 3. RSI momentum analysis
    if rsi < 30:
        # Oversold - strong buy signal
        score += 30
    elif rsi < 45:
        # Slightly oversold - moderate buy
        score += 20
    elif rsi < 55:
        # Neutral zone
        score += 10
    elif rsi < 70:
        # Slightly overbought - caution
        score -= 10
    else:
        # Overbought - sell signal
        score -= 20

    # 4. Recent momentum (5-day price change)
    if len(price_floats) >= 6:
        five_day_return = (price_floats[-1] - price_floats[-6]) / price_floats[-6]
        if five_day_return > 0.03:  # > 3% gain
            score += 10
        elif five_day_return < -0.03:  # > 3% loss
            score -= 10

    # Clamp to 0-100 range
    score = max(0.0, min(100.0, score))

    logger.debug(
        f"Technical score: {score:.1f} (MA20={ma_20_val:.2f}, MA50={ma_50_val:.2f}, "
        f"RSI={rsi:.1f}, price={current_price:.2f})"
    )

    return score
