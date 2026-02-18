from typing import NotRequired, TypedDict

from .agent_state import Decision


class StockRanking(TypedDict):
    ticker: str
    rank: int
    score: float
    rationale: str
    decision: Decision


class RelativeStrength(TypedDict):
    correlation_matrix: dict[str, dict[str, float]]
    relative_performance: dict[str, float]  # % return over period
    valuation_comparison: dict[str, dict[str, float]]


class ComparisonResult(TypedDict):
    tickers: list[str]
    rankings: list[StockRanking]
    best_pick: str
    comparison_summary: str
    relative_strength: NotRequired[RelativeStrength]
    price_histories: NotRequired[dict[str, list[dict]]]  # For chart visualization
    stock_data: NotRequired[dict[str, dict]]  # Full analysis data for each stock
