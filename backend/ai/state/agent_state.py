from datetime import datetime
from typing import NotRequired, Optional, TypedDict

from .enums import Action, Market, SentimentSource, Trend


class NewsItem(TypedDict):
    source: SentimentSource
    title: str
    url: str
    published_at: datetime
    sentiment: float
    snippet: str


class SocialMention(TypedDict):
    source: SentimentSource
    content: str
    author: str
    url: str
    timestamp: datetime
    engagement: int


class FundamentalReport(TypedDict):
    revenue_growth: float
    pe_ratio: float
    debt_to_equity: float
    market_cap: float
    sector: Optional[str]
    summary: str


class SentimentReport(TypedDict):
    overall_sentiment: float
    news_items: list[NewsItem]
    social_mentions: list[SocialMention]
    summary: str


class TechnicalReport(TypedDict):
    current_price: float
    ma_50: float
    ma_200: float
    rsi: float
    trend: Trend
    price_history: list[dict]
    summary: str


class RiskAssessment(TypedDict):
    sector: str
    portfolio_sector_weight: float
    var_95: float
    veto: bool
    veto_reason: Optional[str]


class Decision(TypedDict):
    action: Action
    confidence: float
    rationale: str


class AgentState(TypedDict):
    ticker: str
    market: Market
    fundamental_report: Optional[FundamentalReport]
    sentiment_report: Optional[SentimentReport]
    technical_report: Optional[TechnicalReport]
    risk_assessment: Optional[RiskAssessment]
    final_decision: Optional[Decision]
    consensus_score: float
    audit_id: str


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
