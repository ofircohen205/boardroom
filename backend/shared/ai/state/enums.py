from enum import Enum


class Market(str, Enum):
    US = "US"
    TASE = "TASE"


class Trend(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SentimentSource(str, Enum):
    NEWS = "news"
    REDDIT = "reddit"
    TWITTER = "twitter"
    GLOBES = "globes"
    CALCALIST = "calcalist"


class AgentType(str, Enum):
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    TECHNICAL = "technical"
    RISK = "risk"
    CHAIRPERSON = "chairperson"


class AnalysisMode(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class WSMessageType(str, Enum):
    ANALYSIS_STARTED = "analysis_started"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    VETO = "veto"
    DECISION = "decision"
    COMPARISON_RESULT = "comparison_result"
    NOTIFICATION = "notification"
    ERROR = "error"
