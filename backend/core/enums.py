# backend/core/enums.py
"""Application-wide enumerations."""
from enum import Enum


class LLMProvider(str, Enum):
    """Large Language Model provider options."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class MarketDataProvider(str, Enum):
    """Market data provider options."""
    YAHOO = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"
