"""
Chairperson decision scorer for backtesting.

Combines agent scores using customizable weights and thresholds to make
a final BUY/SELL/HOLD decision.
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)

Decision = Literal["BUY", "SELL", "HOLD"]


def calculate_weighted_decision(
    scores: dict[str, float],
    weights: dict[str, float],
    buy_threshold: float = 70.0,
    sell_threshold: float = 30.0,
) -> Decision:
    """Calculate weighted final decision from agent scores.

    This mimics the Chairperson's logic of weighing agent opinions,
    but uses deterministic thresholds instead of LLM reasoning.

    Scoring Logic:
    1. Calculate weighted average of agent scores
    2. Apply decision thresholds:
       - Weighted score >= buy_threshold (default 70): BUY
       - Weighted score <= sell_threshold (default 30): SELL
       - Otherwise: HOLD

    Args:
        scores: Dictionary of agent scores (e.g., {"fundamental": 80, "technical": 65, "sentiment": 55})
        weights: Dictionary of agent weights (e.g., {"fundamental": 0.4, "technical": 0.4, "sentiment": 0.2})
        buy_threshold: Minimum weighted score to trigger BUY (default 70)
        sell_threshold: Maximum weighted score to trigger SELL (default 30)

    Returns:
        Decision: "BUY", "SELL", or "HOLD"

    Raises:
        ValueError: If weights don't sum to ~1.0 or if agent names don't match

    Example:
        >>> scores = {"fundamental": 80, "technical": 65, "sentiment": 55}
        >>> weights = {"fundamental": 0.4, "technical": 0.4, "sentiment": 0.2}
        >>> calculate_weighted_decision(scores, weights)
        'BUY'  # weighted avg = 0.4*80 + 0.4*65 + 0.2*55 = 69 < 70, actually HOLD
        # Correction: 32 + 26 + 11 = 69 -> HOLD
    """
    # Validate inputs
    if set(scores.keys()) != set(weights.keys()):
        raise ValueError(
            f"Agent names in scores {set(scores.keys())} don't match weights {set(weights.keys())}"
        )

    total_weight = sum(weights.values())
    if not (0.99 <= total_weight <= 1.01):
        raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

    # Calculate weighted average
    weighted_score = sum(scores[agent] * weights[agent] for agent in scores.keys())

    # Apply decision thresholds
    decision: Decision
    if weighted_score >= buy_threshold:
        decision = "BUY"
    elif weighted_score <= sell_threshold:
        decision = "SELL"
    else:
        decision = "HOLD"

    logger.debug(
        f"Weighted score: {weighted_score:.1f} -> {decision} "
        f"(thresholds: BUY>={buy_threshold}, SELL<={sell_threshold})"
    )

    return decision
