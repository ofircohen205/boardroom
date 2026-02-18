"""
Fundamental analysis scorer for backtesting.

Calculates a fundamental score (0-100) based on:
- Valuation metrics (P/E, P/B, P/S)
- Growth metrics (revenue, earnings growth)
- Financial health (debt/equity ratio)
"""

import logging

from backend.shared.db.models.backtesting import HistoricalFundamentals

logger = logging.getLogger(__name__)


def calculate_fundamental_score(fundamentals: HistoricalFundamentals | None) -> float:
    """Calculate fundamental score from quarterly data.

    This is a rules-based approximation of what the Fundamental Agent would analyze.
    Uses valuation multiples, growth rates, and financial health metrics.

    Scoring Logic:
    - P/E ratio:
      - < 15: Undervalued (+20 points)
      - 15-25: Fair value (+10 points)
      - > 25: Overvalued (-10 points)
    - Growth (revenue/earnings YoY):
      - > 15%: High growth (+20 points)
      - 5-15%: Moderate growth (+10 points)
      - < 5%: Low/no growth (0 points)
      - Negative: Declining (-20 points)
    - Debt/Equity:
      - < 0.5: Low debt (+15 points)
      - 0.5-1.5: Moderate debt (+5 points)
      - > 1.5: High debt (-15 points)
    - Profitability:
      - Positive earnings (+15 points)
      - Negative earnings (-25 points)

    Args:
        fundamentals: Historical fundamentals snapshot (or None if missing)

    Returns:
        Score from 0-100, where:
        - 80-100: Strong fundamentals, buy
        - 60-79: Decent fundamentals, moderate buy
        - 40-59: Mixed fundamentals, neutral
        - 20-39: Weak fundamentals, moderate sell
        - 0-19: Poor fundamentals, strong sell

    Note:
        If fundamentals data is missing, returns neutral score (50).
        Uses forward-fill logic: most recent available data as of backtest date.
    """
    if not fundamentals:
        logger.warning("No fundamental data available. Returning neutral score.")
        return 50.0

    score = 50.0  # Start neutral

    # 1. Valuation - P/E ratio
    if fundamentals.pe_ratio is not None and fundamentals.pe_ratio > 0:
        pe = float(fundamentals.pe_ratio)
        if pe < 15:
            score += 20  # Undervalued
        elif pe < 25:
            score += 10  # Fair value
        else:
            score -= 10  # Overvalued

    # 2. Growth - Revenue growth (prioritize revenue over earnings for consistency)
    growth_score = 0
    if fundamentals.revenue_growth is not None:
        revenue_growth = float(fundamentals.revenue_growth)
        if revenue_growth > 0.15:  # > 15% YoY
            growth_score = 20
        elif revenue_growth > 0.05:  # 5-15% YoY
            growth_score = 10
        elif revenue_growth < 0:  # Declining
            growth_score = -20
    elif fundamentals.earnings_growth is not None:
        # Fallback to earnings growth if revenue growth missing
        earnings_growth = float(fundamentals.earnings_growth)
        if earnings_growth > 0.15:
            growth_score = 20
        elif earnings_growth > 0.05:
            growth_score = 10
        elif earnings_growth < 0:
            growth_score = -20

    score += growth_score

    # 3. Financial Health - Debt/Equity ratio
    if fundamentals.debt_to_equity is not None:
        de_ratio = float(fundamentals.debt_to_equity)
        if de_ratio < 0.5:
            score += 15  # Low debt, healthy
        elif de_ratio < 1.5:
            score += 5  # Moderate debt, acceptable
        else:
            score -= 15  # High debt, risky

    # 4. Profitability - Earnings
    if fundamentals.net_income is not None:
        net_income = float(fundamentals.net_income)
        if net_income > 0:
            score += 15  # Profitable
        else:
            score -= 25  # Unprofitable

    # Clamp to 0-100 range
    score = max(0.0, min(100.0, score))

    logger.debug(
        f"Fundamental score: {score:.1f} (P/E={fundamentals.pe_ratio}, "
        f"Revenue growth={fundamentals.revenue_growth}, D/E={fundamentals.debt_to_equity})"
    )

    return score
