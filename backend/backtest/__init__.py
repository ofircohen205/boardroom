"""
Backtesting engine for strategy validation.

Provides deterministic, rules-based simulation of agent decisions on
historical data without making LLM calls.
"""

from .engine import BacktestConfig, BacktestResult, run_backtest

__all__ = [
    "BacktestConfig",
    "BacktestResult",
    "run_backtest",
]
