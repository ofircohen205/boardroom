# Boardroom System Design

Multi-agent financial analysis system using LangGraph with React dashboard.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Dashboard                          │
│  Vite + TailwindCSS + shadcn/ui + lightweight-charts            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph Workflow                             │
│                                                                  │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│   │Fundamental │  │ Sentiment  │  │ Technical  │  ← Parallel    │
│   └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                │
│         └───────────────┼───────────────┘                        │
│                         ▼                                        │
│                 ┌──────────────┐                                 │
│                 │ Risk Manager │  ← Can VETO                     │
│                 └───────┬──────┘                                 │
│              ┌──────────┴──────────┐                             │
│         [VETO=true]          [VETO=false]                        │
│              ▼                     ▼                             │
│         End (No Trade)      ┌─────────────┐                      │
│                             │ Chairperson │                      │
│                             └─────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Audit Trail                        │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
boardroom/
├── backend/
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── routes.py
│   │   └── websocket.py
│   │
│   ├── state/
│   │   ├── enums.py
│   │   └── agent_state.py
│   │
│   ├── agents/
│   │   ├── base.py
│   │   ├── fundamental.py
│   │   ├── sentiment.py
│   │   ├── technical.py
│   │   ├── risk_manager.py
│   │   └── chairperson.py
│   │
│   ├── tools/
│   │   ├── market_data.py
│   │   ├── search.py
│   │   └── technical_indicators.py
│   │
│   ├── dao/
│   │   ├── models.py
│   │   └── repository.py
│   │
│   ├── graph/
│   │   └── workflow.py
│   │
│   └── evaluation/
│       └── ragas_eval.py
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard.tsx
    │   │   ├── TickerInput.tsx
    │   │   ├── AgentPanel.tsx
    │   │   ├── StockChart.tsx
    │   │   ├── NewsFeed.tsx
    │   │   └── DecisionCard.tsx
    │   ├── hooks/
    │   │   └── useWebSocket.ts
    │   └── App.tsx
    └── package.json
```

## Enums

```python
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

class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"

class MarketDataProvider(str, Enum):
    YAHOO = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"

class WSMessageType(str, Enum):
    ANALYSIS_STARTED = "analysis_started"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    VETO = "veto"
    DECISION = "decision"
    ERROR = "error"

class AgentType(str, Enum):
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    TECHNICAL = "technical"
    RISK = "risk"
    CHAIRPERSON = "chairperson"
```

## Data Models

```python
class NewsItem(TypedDict):
    source: SentimentSource
    title: str
    url: str
    published_at: datetime
    sentiment: float  # -1.0 to 1.0
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
```

## Database Models (Audit Trail)

```python
class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str]
    market: Mapped[Market]
    created_at: Mapped[datetime]
    completed_at: Mapped[Optional[datetime]]

    agent_reports: Mapped[list["AgentReport"]] = relationship(back_populates="session")
    final_decision: Mapped[Optional["FinalDecision"]] = relationship(back_populates="session")

class AgentReport(Base):
    __tablename__ = "agent_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_sessions.id"))
    agent_type: Mapped[AgentType]
    report_data: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime]

class FinalDecision(Base):
    __tablename__ = "final_decisions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_sessions.id"))
    action: Mapped[Action]
    confidence: Mapped[float]
    rationale: Mapped[str]
    vetoed: Mapped[bool]
    veto_reason: Mapped[Optional[str]]
    created_at: Mapped[datetime]
```

## WebSocket Message Format

```python
class WSMessage(TypedDict):
    type: WSMessageType
    agent: Optional[AgentType]
    data: dict
    timestamp: datetime
```

## LLM Abstraction

Configurable providers: Anthropic (Claude), OpenAI (GPT-4), Google (Gemini)

```python
class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: list[dict], tools: list[dict] = None) -> str:
        pass

    @abstractmethod
    async def complete_with_tools(self, messages: list[dict], tools: list[dict]) -> dict:
        pass
```

## Market Data Abstraction

Configurable providers: Yahoo Finance (recommended for TASE), Alpha Vantage

Israeli stocks use `.TA` suffix (e.g., `TEVA.TA`)

## Dependencies

### Backend
- fastapi, uvicorn, websockets
- langgraph
- anthropic, openai, google-generativeai
- yfinance
- exa-py
- sqlalchemy[asyncio], asyncpg, alembic
- pydantic-settings
- ragas

### Frontend
- react, react-dom
- tailwindcss, @shadcn/ui
- lightweight-charts
- lucide-react

## Key Design Decisions

1. **Parallel analyst agents** - Fundamental, Sentiment, Technical run concurrently for speed
2. **Risk Manager veto power** - Can stop trades before Chairperson sees them
3. **WebSocket streaming** - Real-time updates as each agent completes
4. **Full audit trail** - Every decision logged to PostgreSQL with session tracking
5. **Provider abstraction** - LLM and market data providers are swappable
6. **Israeli market support** - TASE stocks via Yahoo Finance with `.TA` suffix
