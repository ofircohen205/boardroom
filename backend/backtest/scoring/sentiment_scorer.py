"""
Sentiment analysis scorer for backtesting.

Since we cannot replay historical news/social sentiment, we use price
momentum as a proxy for market sentiment.
"""

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


def calculate_sentiment_score(prices: list[Decimal]) -> float:
    """Calculate sentiment score from price momentum.

    This is a proxy for sentiment since we cannot replay historical news.
    Uses multi-timeframe momentum to estimate market sentiment:
    - 5-day momentum: Short-term sentiment
    - 20-day momentum: Medium-term sentiment
    - Volume-weighted momentum (if available): Conviction strength

    Scoring Logic:
    - 5-day return:
      - > +5%: Strong positive (+30 points)
      - +2% to +5%: Moderate positive (+15 points)
      - -2% to +2%: Neutral (0 points)
      - -5% to -2%: Moderate negative (-15 points)
      - < -5%: Strong negative (-30 points)
    - 20-day return:
      - > +10%: Bullish trend (+20 points)
      - +5% to +10%: Moderate trend (+10 points)
      - -5% to +5%: Neutral (0 points)
      - -10% to -5%: Bearish trend (-10 points)
      - < -10%: Strong bearish (-20 points)

    Args:
        prices: List of closing prices (most recent last)

    Returns:
        Score from 0-100, where:
        - 80-100: Very positive sentiment, buy
        - 60-79: Positive sentiment, moderate buy
        - 40-59: Neutral sentiment, hold
        - 20-39: Negative sentiment, moderate sell
        - 0-19: Very negative sentiment, sell

    Note:
        This is a simplified proxy. Real sentiment would use news,
        social media, analyst ratings, etc.
    """
    if len(prices) < 20:
        logger.warning(
            f"Not enough price history ({len(prices)} points, need 20+). Returning neutral score."
        )
        return 50.0  # Neutral if insufficient data

    # Convert Decimal to float for calculations
    price_floats = [float(p) for p in prices]

    score = 50.0  # Start neutral

    # 1. Short-term momentum (5-day return)
    if len(price_floats) >= 6:
        five_day_return = (price_floats[-1] - price_floats[-6]) / price_floats[-6]

        if five_day_return > 0.05:  # > 5% gain
            score += 30
        elif five_day_return > 0.02:  # 2-5% gain
            score += 15
        elif five_day_return < -0.05:  # > 5% loss
            score -= 30
        elif five_day_return < -0.02:  # 2-5% loss
            score -= 15
        # Else: -2% to +2% is neutral, no change

    # 2. Medium-term momentum (20-day return)
    if len(price_floats) >= 21:
        twenty_day_return = (price_floats[-1] - price_floats[-21]) / price_floats[-21]

        if twenty_day_return > 0.10:  # > 10% gain
            score += 20
        elif twenty_day_return > 0.05:  # 5-10% gain
            score += 10
        elif twenty_day_return < -0.10:  # > 10% loss
            score -= 20
        elif twenty_day_return < -0.05:  # 5-10% loss
            score -= 10
        # Else: -5% to +5% is neutral, no change

    # Clamp to 0-100 range
    score = max(0.0, min(100.0, score))

    logger.debug(
        f"Sentiment score: {score:.1f} (5d return={(price_floats[-1] - price_floats[-6]) / price_floats[-6]:.2%}, "
        f"20d return={(price_floats[-1] - price_floats[-21]) / price_floats[-21]:.2%})"
    )

    return score
