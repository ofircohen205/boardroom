"""
Scoring modules for rules-based backtesting.

These modules calculate deterministic scores (0-100) for each agent type
based on historical data, without making LLM calls.
"""

from .chairperson_scorer import calculate_weighted_decision
from .fundamental_scorer import calculate_fundamental_score
from .sentiment_scorer import calculate_sentiment_score
from .technical_scorer import calculate_technical_score

__all__ = [
    "calculate_technical_score",
    "calculate_fundamental_score",
    "calculate_sentiment_score",
    "calculate_weighted_decision",
]
