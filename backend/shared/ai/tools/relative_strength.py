"""Tools for calculating relative strength metrics between stocks."""

from typing import Optional

import numpy as np

from backend.shared.ai.state.agent_state import FundamentalReport
from backend.shared.ai.state.result_state import RelativeStrength


def calculate_correlation_matrix(
    price_histories: dict[str, list[dict]],
) -> dict[str, dict[str, float]]:
    """Calculate correlation matrix between stock price movements."""
    if len(price_histories) < 2:
        return {}

    # Extract close prices for each ticker
    price_arrays = {}
    min_length = float("inf")

    for ticker, history in price_histories.items():
        prices = [p["close"] for p in history]
        price_arrays[ticker] = np.array(prices)
        min_length = min(min_length, len(prices))

    # Trim all arrays to same length
    for ticker in price_arrays:
        price_arrays[ticker] = price_arrays[ticker][-int(min_length) :]

    # Calculate returns
    returns = {}
    for ticker, prices in price_arrays.items():
        returns[ticker] = np.diff(prices) / prices[:-1]

    # Calculate correlation matrix
    correlation_matrix = {}
    tickers = list(returns.keys())

    for ticker1 in tickers:
        correlation_matrix[ticker1] = {}
        for ticker2 in tickers:
            if ticker1 == ticker2:
                correlation_matrix[ticker1][ticker2] = 1.0
            else:
                corr = float(np.corrcoef(returns[ticker1], returns[ticker2])[0, 1])
                correlation_matrix[ticker1][ticker2] = (
                    corr if not np.isnan(corr) else 0.0
                )

    return correlation_matrix


def calculate_relative_performance(
    price_histories: dict[str, list[dict]],
) -> dict[str, float]:
    """Calculate relative performance (% return) for each stock over the period."""
    performance = {}

    for ticker, history in price_histories.items():
        if len(history) < 2:
            performance[ticker] = 0.0
            continue

        first_price = history[0]["close"]
        last_price = history[-1]["close"]

        if first_price > 0:
            ret = ((last_price - first_price) / first_price) * 100
            performance[ticker] = round(ret, 2)
        else:
            performance[ticker] = 0.0

    return performance


def calculate_valuation_comparison(
    fundamentals: dict[str, Optional[FundamentalReport]],
) -> dict[str, dict[str, float]]:
    """Compare valuation metrics across stocks."""
    comparison = {}

    for ticker, report in fundamentals.items():
        if report:
            comparison[ticker] = {
                "pe_ratio": report["pe_ratio"],
                "revenue_growth": report["revenue_growth"]
                * 100,  # Convert to percentage
                "debt_to_equity": report["debt_to_equity"],
                "market_cap": report["market_cap"],
            }
        else:
            comparison[ticker] = {
                "pe_ratio": 0.0,
                "revenue_growth": 0.0,
                "debt_to_equity": 0.0,
                "market_cap": 0.0,
            }

    return comparison


def calculate_relative_strength(
    price_histories: dict[str, list[dict]],
    fundamentals: dict[str, Optional[FundamentalReport]],
) -> RelativeStrength:
    """Calculate comprehensive relative strength metrics."""
    return RelativeStrength(
        correlation_matrix=calculate_correlation_matrix(price_histories),
        relative_performance=calculate_relative_performance(price_histories),
        valuation_comparison=calculate_valuation_comparison(fundamentals),
    )
