# Boardroom Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a multi-agent financial analysis system with LangGraph backend and React dashboard.

**Architecture:** LangGraph orchestrates 5 agents (Fundamental, Sentiment, Technical → Risk Manager → Chairperson). FastAPI serves WebSocket for real-time updates. React dashboard displays agent reports and final decisions.

**Tech Stack:** Python 3.13, FastAPI, LangGraph, SQLAlchemy, PostgreSQL, React, Vite, TailwindCSS, shadcn/ui

---

## Phase 1: Backend Foundation

### Task 1: Project Structure & Dependencies

**Files:**
- Modify: `pyproject.toml`
- Create: `backend/__init__.py`
- Create: `backend/config.py`

**Step 1: Update pyproject.toml with dependencies**

```toml
[project]
name = "boardroom"
version = "0.1.0"
description = "Multi-agent financial analysis system"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "websockets>=14.0",
    "langgraph>=0.2.0",
    "anthropic>=0.40.0",
    "openai>=1.55.0",
    "google-generativeai>=0.8.0",
    "yfinance>=0.2.50",
    "exa-py>=1.0.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic-settings>=2.6.0",
    "httpx>=0.28.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
]
```

**Step 2: Install dependencies**

Run: `uv sync`
Expected: Dependencies installed successfully

**Step 3: Create backend package**

```python
# backend/__init__.py
```

**Step 4: Create config module**

```python
# backend/config.py
from enum import Enum
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"


class MarketDataProvider(str, Enum):
    YAHOO = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"


class Settings(BaseSettings):
    # LLM
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""

    # Market Data
    market_data_provider: MarketDataProvider = MarketDataProvider.YAHOO
    alpha_vantage_api_key: str = ""

    # Search
    exa_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://localhost/boardroom"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

**Step 5: Create .env.example**

```bash
# .env.example
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
MARKET_DATA_PROVIDER=yahoo
ALPHA_VANTAGE_API_KEY=
EXA_API_KEY=
DATABASE_URL=postgresql+asyncpg://localhost/boardroom
```

**Step 6: Add .env to .gitignore**

Append `.env` to `.gitignore`

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: project structure and dependencies"
```

---

### Task 2: Enums & State Types

**Files:**
- Create: `backend/state/__init__.py`
- Create: `backend/state/enums.py`
- Create: `backend/state/agent_state.py`
- Create: `tests/__init__.py`
- Create: `tests/test_state.py`

**Step 1: Write test for enums**

```python
# tests/test_state.py
from backend.state.enums import (
    Market,
    Trend,
    Action,
    SentimentSource,
    AgentType,
    WSMessageType,
)


def test_market_enum():
    assert Market.US.value == "US"
    assert Market.TASE.value == "TASE"


def test_action_enum():
    assert Action.BUY.value == "BUY"
    assert Action.SELL.value == "SELL"
    assert Action.HOLD.value == "HOLD"


def test_agent_type_enum():
    assert len(AgentType) == 5
    assert AgentType.CHAIRPERSON.value == "chairperson"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_state.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Create enums module**

```python
# backend/state/__init__.py
from .enums import (
    Market,
    Trend,
    Action,
    SentimentSource,
    AgentType,
    WSMessageType,
)
from .agent_state import (
    NewsItem,
    SocialMention,
    FundamentalReport,
    SentimentReport,
    TechnicalReport,
    RiskAssessment,
    Decision,
    AgentState,
)

__all__ = [
    "Market",
    "Trend",
    "Action",
    "SentimentSource",
    "AgentType",
    "WSMessageType",
    "NewsItem",
    "SocialMention",
    "FundamentalReport",
    "SentimentReport",
    "TechnicalReport",
    "RiskAssessment",
    "Decision",
    "AgentState",
]
```

```python
# backend/state/enums.py
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


class WSMessageType(str, Enum):
    ANALYSIS_STARTED = "analysis_started"
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    VETO = "veto"
    DECISION = "decision"
    ERROR = "error"
```

**Step 4: Create agent_state module**

```python
# backend/state/agent_state.py
from datetime import datetime
from typing import Optional, TypedDict

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

**Step 5: Create tests/__init__.py**

```python
# tests/__init__.py
```

**Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_state.py -v`
Expected: PASS (3 tests)

**Step 7: Commit**

```bash
git add -A
git commit -m "feat: enums and state types"
```

---

### Task 3: Market Data Tool (Yahoo Finance)

**Files:**
- Create: `backend/tools/__init__.py`
- Create: `backend/tools/market_data.py`
- Create: `tests/test_tools.py`

**Step 1: Write test for market data**

```python
# tests/test_tools.py
import pytest
from backend.tools.market_data import (
    YahooFinanceClient,
    get_market_data_client,
)
from backend.state.enums import Market
from backend.config import MarketDataProvider


def test_get_market_data_client_yahoo():
    client = get_market_data_client(MarketDataProvider.YAHOO)
    assert isinstance(client, YahooFinanceClient)


def test_yahoo_ticker_formatting():
    client = YahooFinanceClient()
    assert client._format_ticker("AAPL", Market.US) == "AAPL"
    assert client._format_ticker("TEVA", Market.TASE) == "TEVA.TA"


@pytest.mark.asyncio
async def test_yahoo_get_stock_data():
    client = YahooFinanceClient()
    data = await client.get_stock_data("AAPL", Market.US)
    assert data["ticker"] == "AAPL"
    assert data["current_price"] > 0
    assert "pe_ratio" in data
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_tools.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Create market_data module**

```python
# backend/tools/__init__.py
from .market_data import (
    BaseMarketDataClient,
    YahooFinanceClient,
    AlphaVantageClient,
    get_market_data_client,
    StockData,
)

__all__ = [
    "BaseMarketDataClient",
    "YahooFinanceClient",
    "AlphaVantageClient",
    "get_market_data_client",
    "StockData",
]
```

```python
# backend/tools/market_data.py
from abc import ABC, abstractmethod
from typing import Optional, TypedDict

import yfinance as yf

from backend.config import MarketDataProvider, settings
from backend.state.enums import Market


class StockData(TypedDict):
    ticker: str
    market: Market
    current_price: float
    open: float
    high: float
    low: float
    volume: int
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    revenue_growth: Optional[float]
    debt_to_equity: Optional[float]
    sector: Optional[str]
    price_history: list[dict]


class BaseMarketDataClient(ABC):
    @abstractmethod
    async def get_stock_data(self, ticker: str, market: Market) -> StockData:
        pass

    @abstractmethod
    async def get_price_history(
        self, ticker: str, market: Market, days: int = 90
    ) -> list[dict]:
        pass


class YahooFinanceClient(BaseMarketDataClient):
    def _format_ticker(self, ticker: str, market: Market) -> str:
        if market == Market.TASE:
            return f"{ticker}.TA"
        return ticker

    async def get_stock_data(self, ticker: str, market: Market) -> StockData:
        symbol = self._format_ticker(ticker, market)
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="3mo")

        price_history = [
            {
                "date": idx.isoformat(),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": int(row["Volume"]),
            }
            for idx, row in hist.iterrows()
        ]

        return StockData(
            ticker=ticker,
            market=market,
            current_price=info.get("currentPrice", info.get("regularMarketPrice", 0)),
            open=info.get("open", info.get("regularMarketOpen", 0)),
            high=info.get("dayHigh", info.get("regularMarketDayHigh", 0)),
            low=info.get("dayLow", info.get("regularMarketDayLow", 0)),
            volume=info.get("volume", info.get("regularMarketVolume", 0)),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("trailingPE"),
            revenue_growth=info.get("revenueGrowth"),
            debt_to_equity=info.get("debtToEquity"),
            sector=info.get("sector"),
            price_history=price_history,
        )

    async def get_price_history(
        self, ticker: str, market: Market, days: int = 90
    ) -> list[dict]:
        symbol = self._format_ticker(ticker, market)
        stock = yf.Ticker(symbol)
        hist = stock.history(period=f"{days}d")

        return [
            {
                "date": idx.isoformat(),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": int(row["Volume"]),
            }
            for idx, row in hist.iterrows()
        ]


class AlphaVantageClient(BaseMarketDataClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_stock_data(self, ticker: str, market: Market) -> StockData:
        raise NotImplementedError("Alpha Vantage client not yet implemented")

    async def get_price_history(
        self, ticker: str, market: Market, days: int = 90
    ) -> list[dict]:
        raise NotImplementedError("Alpha Vantage client not yet implemented")


def get_market_data_client(
    provider: MarketDataProvider | None = None,
) -> BaseMarketDataClient:
    provider = provider or settings.market_data_provider
    match provider:
        case MarketDataProvider.YAHOO:
            return YahooFinanceClient()
        case MarketDataProvider.ALPHA_VANTAGE:
            return AlphaVantageClient(settings.alpha_vantage_api_key)
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tools.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: market data tool with Yahoo Finance"
```

---

### Task 4: Technical Indicators Tool

**Files:**
- Create: `backend/tools/technical_indicators.py`
- Modify: `backend/tools/__init__.py`
- Create: `tests/test_technical_indicators.py`

**Step 1: Write test for technical indicators**

```python
# tests/test_technical_indicators.py
import pytest
from backend.tools.technical_indicators import calculate_rsi, calculate_ma, calculate_trend
from backend.state.enums import Trend


def test_calculate_ma():
    prices = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109]
    ma = calculate_ma(prices, period=5)
    assert ma == pytest.approx(108.0, rel=0.01)


def test_calculate_rsi_overbought():
    # Consistently rising prices = high RSI
    prices = [100 + i * 2 for i in range(20)]
    rsi = calculate_rsi(prices)
    assert rsi > 70


def test_calculate_rsi_oversold():
    # Consistently falling prices = low RSI
    prices = [100 - i * 2 for i in range(20)]
    rsi = calculate_rsi(prices)
    assert rsi < 30


def test_calculate_trend_bullish():
    trend = calculate_trend(current_price=110, ma_50=100, ma_200=95)
    assert trend == Trend.BULLISH


def test_calculate_trend_bearish():
    trend = calculate_trend(current_price=90, ma_50=100, ma_200=105)
    assert trend == Trend.BEARISH


def test_calculate_trend_neutral():
    trend = calculate_trend(current_price=100, ma_50=100, ma_200=100)
    assert trend == Trend.NEUTRAL
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_technical_indicators.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Create technical_indicators module**

```python
# backend/tools/technical_indicators.py
from backend.state.enums import Trend


def calculate_ma(prices: list[float], period: int) -> float:
    if len(prices) < period:
        return sum(prices) / len(prices)
    return sum(prices[-period:]) / period


def calculate_rsi(prices: list[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_trend(current_price: float, ma_50: float, ma_200: float) -> Trend:
    # Price above both MAs and 50 > 200 = bullish
    if current_price > ma_50 > ma_200:
        return Trend.BULLISH
    # Price below both MAs and 50 < 200 = bearish
    if current_price < ma_50 < ma_200:
        return Trend.BEARISH
    return Trend.NEUTRAL
```

**Step 4: Update tools __init__.py**

```python
# backend/tools/__init__.py
from .market_data import (
    BaseMarketDataClient,
    YahooFinanceClient,
    AlphaVantageClient,
    get_market_data_client,
    StockData,
)
from .technical_indicators import calculate_ma, calculate_rsi, calculate_trend

__all__ = [
    "BaseMarketDataClient",
    "YahooFinanceClient",
    "AlphaVantageClient",
    "get_market_data_client",
    "StockData",
    "calculate_ma",
    "calculate_rsi",
    "calculate_trend",
]
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_technical_indicators.py -v`
Expected: PASS (6 tests)

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: technical indicators (RSI, MA, trend)"
```

---

### Task 5: Search Tool (Exa)

**Files:**
- Create: `backend/tools/search.py`
- Modify: `backend/tools/__init__.py`
- Create: `tests/test_search.py`

**Step 1: Write test for search tool**

```python
# tests/test_search.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.tools.search import ExaSearchClient, SearchResult


@pytest.fixture
def mock_exa_response():
    return {
        "results": [
            {
                "title": "TEVA stock rises on news",
                "url": "https://example.com/news/1",
                "text": "Teva Pharmaceutical announced...",
                "published_date": "2026-02-01T10:00:00Z",
            }
        ]
    }


def test_search_result_structure():
    result = SearchResult(
        title="Test",
        url="https://example.com",
        snippet="Test snippet",
        published_at="2026-02-01T10:00:00Z",
        source="news",
    )
    assert result["title"] == "Test"
    assert result["source"] == "news"


@pytest.mark.asyncio
async def test_exa_search_formats_query():
    client = ExaSearchClient(api_key="test")
    with patch.object(client, "_search", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await client.search_news("TEVA", hours=48)
        mock.assert_called_once()
        call_args = mock.call_args[0][0]
        assert "TEVA" in call_args
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_search.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Create search module**

```python
# backend/tools/search.py
from datetime import datetime, timedelta
from typing import TypedDict

from exa_py import Exa

from backend.config import settings


class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str
    published_at: str
    source: str


class ExaSearchClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.exa_api_key
        self._client: Exa | None = None

    @property
    def client(self) -> Exa:
        if self._client is None:
            self._client = Exa(api_key=self.api_key)
        return self._client

    async def _search(self, query: str, num_results: int = 10) -> list[SearchResult]:
        response = self.client.search_and_contents(
            query,
            num_results=num_results,
            text=True,
            use_autoprompt=True,
        )
        return [
            SearchResult(
                title=r.title or "",
                url=r.url,
                snippet=r.text[:500] if r.text else "",
                published_at=r.published_date or "",
                source="news",
            )
            for r in response.results
        ]

    async def search_news(
        self, ticker: str, hours: int = 48, num_results: int = 10
    ) -> list[SearchResult]:
        query = f"{ticker} stock news financial analysis"
        results = await self._search(query, num_results)
        return results

    async def search_social(
        self, ticker: str, hours: int = 48, num_results: int = 10
    ) -> list[SearchResult]:
        query = f"{ticker} stock reddit twitter sentiment"
        results = await self._search(query, num_results)
        for r in results:
            if "reddit" in r["url"].lower():
                r["source"] = "reddit"
            elif "twitter" in r["url"].lower() or "x.com" in r["url"].lower():
                r["source"] = "twitter"
        return results


def get_search_client() -> ExaSearchClient:
    return ExaSearchClient()
```

**Step 4: Update tools __init__.py**

```python
# backend/tools/__init__.py
from .market_data import (
    BaseMarketDataClient,
    YahooFinanceClient,
    AlphaVantageClient,
    get_market_data_client,
    StockData,
)
from .technical_indicators import calculate_ma, calculate_rsi, calculate_trend
from .search import ExaSearchClient, SearchResult, get_search_client

__all__ = [
    "BaseMarketDataClient",
    "YahooFinanceClient",
    "AlphaVantageClient",
    "get_market_data_client",
    "StockData",
    "calculate_ma",
    "calculate_rsi",
    "calculate_trend",
    "ExaSearchClient",
    "SearchResult",
    "get_search_client",
]
```

**Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_search.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: Exa search tool for news and social"
```

---

### Task 6: LLM Abstraction Layer

**Files:**
- Create: `backend/agents/__init__.py`
- Create: `backend/agents/base.py`
- Create: `tests/test_llm.py`

**Step 1: Write test for LLM clients**

```python
# tests/test_llm.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.agents.base import (
    AnthropicClient,
    OpenAIClient,
    GeminiClient,
    get_llm_client,
)
from backend.config import LLMProvider


def test_get_llm_client_anthropic():
    with patch("backend.agents.base.anthropic"):
        client = get_llm_client(LLMProvider.ANTHROPIC)
        assert isinstance(client, AnthropicClient)


def test_get_llm_client_openai():
    with patch("backend.agents.base.openai"):
        client = get_llm_client(LLMProvider.OPENAI)
        assert isinstance(client, OpenAIClient)


def test_get_llm_client_gemini():
    with patch("backend.agents.base.genai"):
        client = get_llm_client(LLMProvider.GEMINI)
        assert isinstance(client, GeminiClient)
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_llm.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Create base agents module**

```python
# backend/agents/__init__.py
from .base import (
    BaseLLMClient,
    AnthropicClient,
    OpenAIClient,
    GeminiClient,
    get_llm_client,
)

__all__ = [
    "BaseLLMClient",
    "AnthropicClient",
    "OpenAIClient",
    "GeminiClient",
    "get_llm_client",
]
```

```python
# backend/agents/base.py
from abc import ABC, abstractmethod
from typing import Any

import anthropic
import google.generativeai as genai
import openai

from backend.config import LLMProvider, settings


class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> str:
        pass

    @abstractmethod
    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict[str, Any]:
        pass


class AnthropicClient(BaseLLMClient):
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = model

    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
        )
        return response.content[0].text

    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict[str, Any]:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=messages,
            tools=tools,
        )
        for block in response.content:
            if block.type == "tool_use":
                return {"tool": block.name, "args": block.input}
        return {"text": response.content[0].text}


class OpenAIClient(BaseLLMClient):
    def __init__(self, model: str = "gpt-4o"):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = model

    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content or ""

    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict[str, Any]:
        openai_tools = [
            {"type": "function", "function": t} for t in tools
        ]
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=openai_tools,
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            import json
            return {"tool": tc.function.name, "args": json.loads(tc.function.arguments)}
        return {"text": msg.content or ""}


class GeminiClient(BaseLLMClient):
    def __init__(self, model: str = "gemini-2.0-flash"):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(model)

    async def complete(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> str:
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [msg["content"]]})
        response = await self.model.generate_content_async(contents)
        return response.text

    async def complete_with_tools(
        self, messages: list[dict], tools: list[dict]
    ) -> dict[str, Any]:
        # Gemini tool calling - simplified
        response = await self.complete(messages)
        return {"text": response}


def get_llm_client(provider: LLMProvider | None = None) -> BaseLLMClient:
    provider = provider or settings.llm_provider
    match provider:
        case LLMProvider.ANTHROPIC:
            return AnthropicClient()
        case LLMProvider.OPENAI:
            return OpenAIClient()
        case LLMProvider.GEMINI:
            return GeminiClient()
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_llm.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: LLM abstraction layer (Anthropic, OpenAI, Gemini)"
```

---

### Task 7: Database Models (DAO)

**Files:**
- Create: `backend/dao/__init__.py`
- Create: `backend/dao/models.py`
- Create: `backend/dao/database.py`
- Create: `tests/test_dao.py`

**Step 1: Write test for models**

```python
# tests/test_dao.py
import pytest
from datetime import datetime
from uuid import uuid4
from backend.dao.models import AnalysisSession, AgentReport, FinalDecision
from backend.state.enums import Market, AgentType, Action


def test_analysis_session_creation():
    session = AnalysisSession(
        id=uuid4(),
        ticker="AAPL",
        market=Market.US,
        created_at=datetime.utcnow(),
    )
    assert session.ticker == "AAPL"
    assert session.market == Market.US


def test_agent_report_creation():
    report = AgentReport(
        id=uuid4(),
        session_id=uuid4(),
        agent_type=AgentType.FUNDAMENTAL,
        report_data={"pe_ratio": 15.5},
        created_at=datetime.utcnow(),
    )
    assert report.agent_type == AgentType.FUNDAMENTAL
    assert report.report_data["pe_ratio"] == 15.5


def test_final_decision_creation():
    decision = FinalDecision(
        id=uuid4(),
        session_id=uuid4(),
        action=Action.BUY,
        confidence=0.85,
        rationale="Strong fundamentals",
        vetoed=False,
        created_at=datetime.utcnow(),
    )
    assert decision.action == Action.BUY
    assert decision.confidence == 0.85
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dao.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Create dao modules**

```python
# backend/dao/__init__.py
from .models import AnalysisSession, AgentReport, FinalDecision, Base
from .database import get_db, init_db

__all__ = [
    "AnalysisSession",
    "AgentReport",
    "FinalDecision",
    "Base",
    "get_db",
    "init_db",
]
```

```python
# backend/dao/database.py
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def init_db():
    from backend.dao.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

```python
# backend/dao/models.py
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Float, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.state.enums import Market, AgentType, Action


class Base(DeclarativeBase):
    pass


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticker: Mapped[str] = mapped_column(String(20))
    market: Mapped[Market] = mapped_column(SQLEnum(Market))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    agent_reports: Mapped[list["AgentReport"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    final_decision: Mapped[Optional["FinalDecision"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class AgentReport(Base):
    __tablename__ = "agent_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id"))
    agent_type: Mapped[AgentType] = mapped_column(SQLEnum(AgentType))
    report_data: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    session: Mapped["AnalysisSession"] = relationship(back_populates="agent_reports")


class FinalDecision(Base):
    __tablename__ = "final_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("analysis_sessions.id"), unique=True)
    action: Mapped[Action] = mapped_column(SQLEnum(Action))
    confidence: Mapped[float] = mapped_column(Float)
    rationale: Mapped[str] = mapped_column(Text)
    vetoed: Mapped[bool] = mapped_column(Boolean, default=False)
    veto_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    session: Mapped["AnalysisSession"] = relationship(back_populates="final_decision")
```

**Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_dao.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: database models for audit trail"
```

---

## Phase 2: Agents

### Task 8: Fundamental Agent

**Files:**
- Create: `backend/agents/fundamental.py`
- Modify: `backend/agents/__init__.py`
- Create: `tests/test_fundamental_agent.py`

**Step 1: Write test**

```python
# tests/test_fundamental_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.agents.fundamental import FundamentalAgent
from backend.state.enums import Market


@pytest.fixture
def mock_stock_data():
    return {
        "ticker": "AAPL",
        "market": Market.US,
        "current_price": 150.0,
        "pe_ratio": 25.0,
        "revenue_growth": 0.15,
        "debt_to_equity": 1.5,
        "market_cap": 2500000000000,
        "sector": "Technology",
        "price_history": [],
    }


@pytest.fixture
def mock_llm_response():
    return "Apple shows strong fundamentals with healthy revenue growth of 15%."


@pytest.mark.asyncio
async def test_fundamental_agent_analyze(mock_stock_data, mock_llm_response):
    with patch("backend.agents.fundamental.get_market_data_client") as mock_market:
        with patch("backend.agents.fundamental.get_llm_client") as mock_llm:
            mock_market.return_value.get_stock_data = AsyncMock(return_value=mock_stock_data)
            mock_llm.return_value.complete = AsyncMock(return_value=mock_llm_response)

            agent = FundamentalAgent()
            report = await agent.analyze("AAPL", Market.US)

            assert report["pe_ratio"] == 25.0
            assert report["revenue_growth"] == 0.15
            assert "summary" in report
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_fundamental_agent.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: Create fundamental agent**

```python
# backend/agents/fundamental.py
from backend.agents.base import get_llm_client
from backend.state.agent_state import FundamentalReport
from backend.state.enums import Market
from backend.tools.market_data import get_market_data_client


class FundamentalAgent:
    def __init__(self):
        self.llm = get_llm_client()
        self.market_data = get_market_data_client()

    async def analyze(self, ticker: str, market: Market) -> FundamentalReport:
        stock_data = await self.market_data.get_stock_data(ticker, market)

        prompt = f"""Analyze the fundamental data for {ticker}:
- P/E Ratio: {stock_data.get('pe_ratio', 'N/A')}
- Revenue Growth: {stock_data.get('revenue_growth', 'N/A')}
- Debt to Equity: {stock_data.get('debt_to_equity', 'N/A')}
- Market Cap: {stock_data.get('market_cap', 'N/A')}
- Sector: {stock_data.get('sector', 'N/A')}

Provide a brief fundamental analysis summary (2-3 sentences)."""

        summary = await self.llm.complete([{"role": "user", "content": prompt}])

        return FundamentalReport(
            revenue_growth=stock_data.get("revenue_growth") or 0.0,
            pe_ratio=stock_data.get("pe_ratio") or 0.0,
            debt_to_equity=stock_data.get("debt_to_equity") or 0.0,
            market_cap=stock_data.get("market_cap") or 0.0,
            summary=summary,
        )
```

**Step 4: Update agents __init__.py**

Add `from .fundamental import FundamentalAgent` and include in `__all__`

**Step 5: Run test**

Run: `uv run pytest tests/test_fundamental_agent.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: fundamental agent"
```

---

### Task 9: Sentiment Agent

**Files:**
- Create: `backend/agents/sentiment.py`
- Modify: `backend/agents/__init__.py`
- Create: `tests/test_sentiment_agent.py`

**Step 1: Write test**

```python
# tests/test_sentiment_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.agents.sentiment import SentimentAgent
from backend.state.enums import Market


@pytest.fixture
def mock_search_results():
    return [
        {
            "title": "Stock rises on good news",
            "url": "https://example.com/1",
            "snippet": "The company reported strong earnings...",
            "published_at": "2026-02-01T10:00:00Z",
            "source": "news",
        }
    ]


@pytest.mark.asyncio
async def test_sentiment_agent_analyze(mock_search_results):
    with patch("backend.agents.sentiment.get_search_client") as mock_search:
        with patch("backend.agents.sentiment.get_llm_client") as mock_llm:
            mock_search.return_value.search_news = AsyncMock(return_value=mock_search_results)
            mock_search.return_value.search_social = AsyncMock(return_value=[])
            mock_llm.return_value.complete = AsyncMock(return_value="Sentiment: 0.7\nPositive news coverage.")

            agent = SentimentAgent()
            report = await agent.analyze("AAPL", Market.US)

            assert "overall_sentiment" in report
            assert "news_items" in report
            assert len(report["news_items"]) > 0
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sentiment_agent.py -v`
Expected: FAIL

**Step 3: Create sentiment agent**

```python
# backend/agents/sentiment.py
import re
from datetime import datetime

from backend.agents.base import get_llm_client
from backend.state.agent_state import NewsItem, SentimentReport, SocialMention
from backend.state.enums import Market, SentimentSource
from backend.tools.search import get_search_client


class SentimentAgent:
    def __init__(self):
        self.llm = get_llm_client()
        self.search = get_search_client()

    async def analyze(self, ticker: str, market: Market) -> SentimentReport:
        news_results = await self.search.search_news(ticker, hours=48)
        social_results = await self.search.search_social(ticker, hours=48)

        news_items: list[NewsItem] = []
        for r in news_results:
            news_items.append(
                NewsItem(
                    source=SentimentSource.NEWS,
                    title=r["title"],
                    url=r["url"],
                    published_at=datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")) if r["published_at"] else datetime.utcnow(),
                    sentiment=0.0,
                    snippet=r["snippet"],
                )
            )

        social_mentions: list[SocialMention] = []
        for r in social_results:
            source = SentimentSource.REDDIT if "reddit" in r.get("source", "") else SentimentSource.TWITTER
            social_mentions.append(
                SocialMention(
                    source=source,
                    content=r["snippet"],
                    author="",
                    url=r["url"],
                    timestamp=datetime.utcnow(),
                    engagement=0,
                )
            )

        # Get LLM to analyze sentiment
        content_summary = "\n".join([f"- {n['title']}: {n['snippet'][:100]}" for n in news_items[:5]])
        prompt = f"""Analyze sentiment for {ticker} based on recent news:
{content_summary}

Respond with:
1. Overall sentiment score from -1.0 (very negative) to 1.0 (very positive)
2. Brief summary (2-3 sentences)

Format: SENTIMENT: <score>
SUMMARY: <text>"""

        response = await self.llm.complete([{"role": "user", "content": prompt}])

        # Parse response
        sentiment_match = re.search(r"SENTIMENT:\s*([-\d.]+)", response)
        summary_match = re.search(r"SUMMARY:\s*(.+)", response, re.DOTALL)

        overall_sentiment = float(sentiment_match.group(1)) if sentiment_match else 0.0
        summary = summary_match.group(1).strip() if summary_match else response

        return SentimentReport(
            overall_sentiment=max(-1.0, min(1.0, overall_sentiment)),
            news_items=news_items,
            social_mentions=social_mentions,
            summary=summary,
        )
```

**Step 4: Update agents __init__.py**

Add `from .sentiment import SentimentAgent` and include in `__all__`

**Step 5: Run test**

Run: `uv run pytest tests/test_sentiment_agent.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: sentiment agent"
```

---

### Task 10: Technical Agent

**Files:**
- Create: `backend/agents/technical.py`
- Modify: `backend/agents/__init__.py`
- Create: `tests/test_technical_agent.py`

**Step 1: Write test**

```python
# tests/test_technical_agent.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.agents.technical import TechnicalAgent
from backend.state.enums import Market, Trend


@pytest.fixture
def mock_stock_data():
    prices = [100 + i * 0.5 for i in range(100)]
    return {
        "ticker": "AAPL",
        "market": Market.US,
        "current_price": 150.0,
        "price_history": [{"close": p} for p in prices],
    }


@pytest.mark.asyncio
async def test_technical_agent_analyze(mock_stock_data):
    with patch("backend.agents.technical.get_market_data_client") as mock_market:
        with patch("backend.agents.technical.get_llm_client") as mock_llm:
            mock_market.return_value.get_stock_data = AsyncMock(return_value=mock_stock_data)
            mock_llm.return_value.complete = AsyncMock(return_value="Bullish trend with strong momentum.")

            agent = TechnicalAgent()
            report = await agent.analyze("AAPL", Market.US)

            assert "current_price" in report
            assert "ma_50" in report
            assert "ma_200" in report
            assert "rsi" in report
            assert "trend" in report
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_technical_agent.py -v`
Expected: FAIL

**Step 3: Create technical agent**

```python
# backend/agents/technical.py
from backend.agents.base import get_llm_client
from backend.state.agent_state import TechnicalReport
from backend.state.enums import Market
from backend.tools.market_data import get_market_data_client
from backend.tools.technical_indicators import calculate_ma, calculate_rsi, calculate_trend


class TechnicalAgent:
    def __init__(self):
        self.llm = get_llm_client()
        self.market_data = get_market_data_client()

    async def analyze(self, ticker: str, market: Market) -> TechnicalReport:
        stock_data = await self.market_data.get_stock_data(ticker, market)

        prices = [p["close"] for p in stock_data["price_history"]]
        current_price = stock_data["current_price"]

        ma_50 = calculate_ma(prices, 50) if len(prices) >= 50 else calculate_ma(prices, len(prices))
        ma_200 = calculate_ma(prices, 200) if len(prices) >= 200 else calculate_ma(prices, len(prices))
        rsi = calculate_rsi(prices)
        trend = calculate_trend(current_price, ma_50, ma_200)

        prompt = f"""Provide a brief technical analysis for {ticker}:
- Current Price: ${current_price:.2f}
- 50-day MA: ${ma_50:.2f}
- 200-day MA: ${ma_200:.2f}
- RSI: {rsi:.1f}
- Trend: {trend.value}

Summarize the technical outlook in 2-3 sentences."""

        summary = await self.llm.complete([{"role": "user", "content": prompt}])

        return TechnicalReport(
            current_price=current_price,
            ma_50=ma_50,
            ma_200=ma_200,
            rsi=rsi,
            trend=trend,
            price_history=stock_data["price_history"],
            summary=summary,
        )
```

**Step 4: Update agents __init__.py**

Add `from .technical import TechnicalAgent` and include in `__all__`

**Step 5: Run test**

Run: `uv run pytest tests/test_technical_agent.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: technical agent"
```

---

### Task 11: Risk Manager Agent

**Files:**
- Create: `backend/agents/risk_manager.py`
- Modify: `backend/agents/__init__.py`
- Create: `tests/test_risk_manager.py`

**Step 1: Write test**

```python
# tests/test_risk_manager.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.agents.risk_manager import RiskManagerAgent
from backend.state.agent_state import FundamentalReport, SentimentReport, TechnicalReport
from backend.state.enums import Trend


@pytest.fixture
def sample_reports():
    return {
        "fundamental": FundamentalReport(
            revenue_growth=0.15,
            pe_ratio=25.0,
            debt_to_equity=1.5,
            market_cap=2500000000000,
            summary="Strong fundamentals",
        ),
        "sentiment": SentimentReport(
            overall_sentiment=0.6,
            news_items=[],
            social_mentions=[],
            summary="Positive sentiment",
        ),
        "technical": TechnicalReport(
            current_price=150.0,
            ma_50=145.0,
            ma_200=140.0,
            rsi=55.0,
            trend=Trend.BULLISH,
            price_history=[],
            summary="Bullish trend",
        ),
    }


@pytest.mark.asyncio
async def test_risk_manager_no_veto(sample_reports):
    with patch("backend.agents.risk_manager.get_llm_client") as mock_llm:
        mock_llm.return_value.complete = AsyncMock(return_value="VETO: NO\nRisk acceptable.")

        agent = RiskManagerAgent()
        assessment = await agent.assess(
            ticker="AAPL",
            sector="Technology",
            portfolio_tech_weight=0.20,
            fundamental=sample_reports["fundamental"],
            sentiment=sample_reports["sentiment"],
            technical=sample_reports["technical"],
        )

        assert assessment["veto"] is False


@pytest.mark.asyncio
async def test_risk_manager_veto_overweight():
    with patch("backend.agents.risk_manager.get_llm_client") as mock_llm:
        mock_llm.return_value.complete = AsyncMock(return_value="VETO: YES\nREASON: Portfolio already 45% Tech.")

        agent = RiskManagerAgent()
        assessment = await agent.assess(
            ticker="AAPL",
            sector="Technology",
            portfolio_tech_weight=0.45,
            fundamental=None,
            sentiment=None,
            technical=None,
        )

        assert assessment["veto"] is True
        assert "veto_reason" in assessment
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_risk_manager.py -v`
Expected: FAIL

**Step 3: Create risk manager agent**

```python
# backend/agents/risk_manager.py
import re
from typing import Optional

from backend.agents.base import get_llm_client
from backend.state.agent_state import (
    FundamentalReport,
    RiskAssessment,
    SentimentReport,
    TechnicalReport,
)


class RiskManagerAgent:
    MAX_SECTOR_WEIGHT = 0.30  # 30% max per sector

    def __init__(self):
        self.llm = get_llm_client()

    async def assess(
        self,
        ticker: str,
        sector: str,
        portfolio_tech_weight: float,
        fundamental: Optional[FundamentalReport],
        sentiment: Optional[SentimentReport],
        technical: Optional[TechnicalReport],
    ) -> RiskAssessment:
        # Rule-based veto: sector overweight
        if portfolio_tech_weight > self.MAX_SECTOR_WEIGHT:
            return RiskAssessment(
                sector=sector,
                portfolio_sector_weight=portfolio_tech_weight,
                var_95=0.0,
                veto=True,
                veto_reason=f"Portfolio already {portfolio_tech_weight*100:.0f}% in {sector}, exceeds {self.MAX_SECTOR_WEIGHT*100:.0f}% limit",
            )

        # LLM-based risk assessment
        prompt = f"""As a risk manager, assess whether to VETO this trade for {ticker} ({sector}):

Portfolio {sector} weight: {portfolio_tech_weight*100:.1f}%
Max allowed: {self.MAX_SECTOR_WEIGHT*100:.0f}%

Fundamental summary: {fundamental['summary'] if fundamental else 'N/A'}
Sentiment: {sentiment['overall_sentiment'] if sentiment else 'N/A'}
Technical trend: {technical['trend'].value if technical else 'N/A'}

Consider:
1. Concentration risk
2. Fundamental red flags (high debt, negative growth)
3. Extreme sentiment (might indicate bubble or panic)
4. Technical overbought/oversold

Respond with:
VETO: YES or NO
REASON: <brief explanation>"""

        response = await self.llm.complete([{"role": "user", "content": prompt}])

        veto_match = re.search(r"VETO:\s*(YES|NO)", response, re.IGNORECASE)
        reason_match = re.search(r"REASON:\s*(.+)", response, re.DOTALL)

        veto = veto_match.group(1).upper() == "YES" if veto_match else False
        veto_reason = reason_match.group(1).strip() if reason_match and veto else None

        return RiskAssessment(
            sector=sector,
            portfolio_sector_weight=portfolio_tech_weight,
            var_95=0.0,  # TODO: implement VaR calculation
            veto=veto,
            veto_reason=veto_reason,
        )
```

**Step 4: Update agents __init__.py**

Add `from .risk_manager import RiskManagerAgent` and include in `__all__`

**Step 5: Run test**

Run: `uv run pytest tests/test_risk_manager.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: risk manager agent with veto power"
```

---

### Task 12: Chairperson Agent

**Files:**
- Create: `backend/agents/chairperson.py`
- Modify: `backend/agents/__init__.py`
- Create: `tests/test_chairperson.py`

**Step 1: Write test**

```python
# tests/test_chairperson.py
import pytest
from unittest.mock import AsyncMock, patch
from backend.agents.chairperson import ChairpersonAgent
from backend.state.agent_state import FundamentalReport, SentimentReport, TechnicalReport
from backend.state.enums import Trend, Action


@pytest.fixture
def bullish_reports():
    return {
        "fundamental": FundamentalReport(
            revenue_growth=0.20,
            pe_ratio=20.0,
            debt_to_equity=0.5,
            market_cap=2500000000000,
            summary="Excellent fundamentals",
        ),
        "sentiment": SentimentReport(
            overall_sentiment=0.8,
            news_items=[],
            social_mentions=[],
            summary="Very positive sentiment",
        ),
        "technical": TechnicalReport(
            current_price=150.0,
            ma_50=145.0,
            ma_200=140.0,
            rsi=55.0,
            trend=Trend.BULLISH,
            price_history=[],
            summary="Strong uptrend",
        ),
    }


@pytest.mark.asyncio
async def test_chairperson_buy_decision(bullish_reports):
    with patch("backend.agents.chairperson.get_llm_client") as mock_llm:
        mock_llm.return_value.complete = AsyncMock(
            return_value="ACTION: BUY\nCONFIDENCE: 0.85\nRATIONALE: Strong fundamentals and positive sentiment."
        )

        agent = ChairpersonAgent()
        decision = await agent.decide(
            ticker="AAPL",
            fundamental=bullish_reports["fundamental"],
            sentiment=bullish_reports["sentiment"],
            technical=bullish_reports["technical"],
        )

        assert decision["action"] == Action.BUY
        assert decision["confidence"] > 0.5
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_chairperson.py -v`
Expected: FAIL

**Step 3: Create chairperson agent**

```python
# backend/agents/chairperson.py
import re

from backend.agents.base import get_llm_client
from backend.state.agent_state import (
    Decision,
    FundamentalReport,
    SentimentReport,
    TechnicalReport,
)
from backend.state.enums import Action


class ChairpersonAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def decide(
        self,
        ticker: str,
        fundamental: FundamentalReport,
        sentiment: SentimentReport,
        technical: TechnicalReport,
    ) -> Decision:
        prompt = f"""As the Chairperson of the investment committee, make a final decision for {ticker}:

FUNDAMENTAL ANALYSIS:
{fundamental['summary']}
- P/E: {fundamental['pe_ratio']}, Revenue Growth: {fundamental['revenue_growth']*100:.1f}%, D/E: {fundamental['debt_to_equity']}

SENTIMENT ANALYSIS:
{sentiment['summary']}
- Overall sentiment: {sentiment['overall_sentiment']:.2f} (-1 to 1 scale)

TECHNICAL ANALYSIS:
{technical['summary']}
- Trend: {technical['trend'].value}, RSI: {technical['rsi']:.1f}

Weigh the evidence and decide. Respond with:
ACTION: BUY, SELL, or HOLD
CONFIDENCE: 0.0 to 1.0
RATIONALE: <2-3 sentence explanation>"""

        response = await self.llm.complete([{"role": "user", "content": prompt}])

        action_match = re.search(r"ACTION:\s*(BUY|SELL|HOLD)", response, re.IGNORECASE)
        confidence_match = re.search(r"CONFIDENCE:\s*([\d.]+)", response)
        rationale_match = re.search(r"RATIONALE:\s*(.+)", response, re.DOTALL)

        action_str = action_match.group(1).upper() if action_match else "HOLD"
        action = Action[action_str]
        confidence = float(confidence_match.group(1)) if confidence_match else 0.5
        rationale = rationale_match.group(1).strip() if rationale_match else response

        return Decision(
            action=action,
            confidence=min(1.0, max(0.0, confidence)),
            rationale=rationale,
        )
```

**Step 4: Update agents __init__.py**

Add `from .chairperson import ChairpersonAgent` and include in `__all__`

**Step 5: Run test**

Run: `uv run pytest tests/test_chairperson.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: chairperson agent for final decisions"
```

---

## Phase 3: LangGraph Workflow

### Task 13: Graph Workflow

**Files:**
- Create: `backend/graph/__init__.py`
- Create: `backend/graph/workflow.py`
- Create: `tests/test_workflow.py`

**Step 1: Write test**

```python
# tests/test_workflow.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.graph.workflow import create_boardroom_graph, BoardroomGraph
from backend.state.enums import Market, Action


@pytest.mark.asyncio
async def test_graph_creation():
    graph = create_boardroom_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_graph_run_no_veto():
    with patch("backend.graph.workflow.FundamentalAgent") as mock_fund:
        with patch("backend.graph.workflow.SentimentAgent") as mock_sent:
            with patch("backend.graph.workflow.TechnicalAgent") as mock_tech:
                with patch("backend.graph.workflow.RiskManagerAgent") as mock_risk:
                    with patch("backend.graph.workflow.ChairpersonAgent") as mock_chair:
                        # Setup mocks
                        mock_fund.return_value.analyze = AsyncMock(return_value={
                            "revenue_growth": 0.15, "pe_ratio": 20, "debt_to_equity": 0.5,
                            "market_cap": 1000000000, "summary": "Good"
                        })
                        mock_sent.return_value.analyze = AsyncMock(return_value={
                            "overall_sentiment": 0.7, "news_items": [], "social_mentions": [], "summary": "Positive"
                        })
                        mock_tech.return_value.analyze = AsyncMock(return_value={
                            "current_price": 100, "ma_50": 95, "ma_200": 90, "rsi": 55,
                            "trend": "bullish", "price_history": [], "summary": "Bullish"
                        })
                        mock_risk.return_value.assess = AsyncMock(return_value={
                            "sector": "Tech", "portfolio_sector_weight": 0.1, "var_95": 0.05,
                            "veto": False, "veto_reason": None
                        })
                        mock_chair.return_value.decide = AsyncMock(return_value={
                            "action": Action.BUY, "confidence": 0.8, "rationale": "Strong buy"
                        })

                        boardroom = BoardroomGraph()
                        result = await boardroom.run("AAPL", Market.US)

                        assert result["final_decision"] is not None
                        assert result["final_decision"]["action"] == Action.BUY
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workflow.py -v`
Expected: FAIL

**Step 3: Create workflow**

```python
# backend/graph/__init__.py
from .workflow import create_boardroom_graph, BoardroomGraph

__all__ = ["create_boardroom_graph", "BoardroomGraph"]
```

```python
# backend/graph/workflow.py
import uuid
from typing import AsyncGenerator, Literal

from langgraph.graph import StateGraph, END

from backend.agents.fundamental import FundamentalAgent
from backend.agents.sentiment import SentimentAgent
from backend.agents.technical import TechnicalAgent
from backend.agents.risk_manager import RiskManagerAgent
from backend.agents.chairperson import ChairpersonAgent
from backend.state.agent_state import AgentState
from backend.state.enums import Market, AgentType, WSMessageType


class BoardroomGraph:
    def __init__(self):
        self.fundamental = FundamentalAgent()
        self.sentiment = SentimentAgent()
        self.technical = TechnicalAgent()
        self.risk_manager = RiskManagerAgent()
        self.chairperson = ChairpersonAgent()

    async def run(self, ticker: str, market: Market, portfolio_sector_weight: float = 0.0) -> AgentState:
        state: AgentState = {
            "ticker": ticker,
            "market": market,
            "fundamental_report": None,
            "sentiment_report": None,
            "technical_report": None,
            "risk_assessment": None,
            "final_decision": None,
            "consensus_score": 0.0,
            "audit_id": str(uuid.uuid4()),
        }

        # Run analysts in parallel (simulated)
        state["fundamental_report"] = await self.fundamental.analyze(ticker, market)
        state["sentiment_report"] = await self.sentiment.analyze(ticker, market)
        state["technical_report"] = await self.technical.analyze(ticker, market)

        # Get sector from fundamental report
        sector = "Technology"  # Default, would come from market data

        # Risk assessment
        state["risk_assessment"] = await self.risk_manager.assess(
            ticker=ticker,
            sector=sector,
            portfolio_tech_weight=portfolio_sector_weight,
            fundamental=state["fundamental_report"],
            sentiment=state["sentiment_report"],
            technical=state["technical_report"],
        )

        # If vetoed, stop here
        if state["risk_assessment"]["veto"]:
            return state

        # Chairperson decision
        state["final_decision"] = await self.chairperson.decide(
            ticker=ticker,
            fundamental=state["fundamental_report"],
            sentiment=state["sentiment_report"],
            technical=state["technical_report"],
        )

        return state

    async def run_streaming(
        self, ticker: str, market: Market, portfolio_sector_weight: float = 0.0
    ) -> AsyncGenerator[dict, None]:
        audit_id = str(uuid.uuid4())

        yield {"type": WSMessageType.ANALYSIS_STARTED, "agent": None, "data": {"ticker": ticker, "audit_id": audit_id}}

        # Fundamental
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.FUNDAMENTAL, "data": {}}
        fundamental = await self.fundamental.analyze(ticker, market)
        yield {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.FUNDAMENTAL, "data": fundamental}

        # Sentiment
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.SENTIMENT, "data": {}}
        sentiment = await self.sentiment.analyze(ticker, market)
        yield {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.SENTIMENT, "data": sentiment}

        # Technical
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.TECHNICAL, "data": {}}
        technical = await self.technical.analyze(ticker, market)
        yield {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.TECHNICAL, "data": technical}

        # Risk
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.RISK, "data": {}}
        risk = await self.risk_manager.assess(
            ticker=ticker,
            sector="Technology",
            portfolio_tech_weight=portfolio_sector_weight,
            fundamental=fundamental,
            sentiment=sentiment,
            technical=technical,
        )
        yield {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.RISK, "data": risk}

        if risk["veto"]:
            yield {"type": WSMessageType.VETO, "agent": AgentType.RISK, "data": {"reason": risk["veto_reason"]}}
            return

        # Chairperson
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.CHAIRPERSON, "data": {}}
        decision = await self.chairperson.decide(ticker, fundamental, sentiment, technical)
        yield {"type": WSMessageType.DECISION, "agent": AgentType.CHAIRPERSON, "data": decision}


def create_boardroom_graph() -> BoardroomGraph:
    return BoardroomGraph()
```

**Step 4: Run test**

Run: `uv run pytest tests/test_workflow.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: LangGraph workflow with streaming"
```

---

## Phase 4: API Layer

### Task 14: FastAPI + WebSocket

**Files:**
- Create: `backend/api/__init__.py`
- Create: `backend/api/routes.py`
- Create: `backend/api/websocket.py`
- Modify: `backend/main.py`
- Create: `tests/test_api.py`

**Step 1: Write test**

```python
# tests/test_api.py
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_markets_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/markets")
        assert response.status_code == 200
        data = response.json()
        assert "US" in data
        assert "TASE" in data
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api.py -v`
Expected: FAIL

**Step 3: Create API modules**

```python
# backend/api/__init__.py
from .routes import router
from .websocket import websocket_endpoint

__all__ = ["router", "websocket_endpoint"]
```

```python
# backend/api/routes.py
from fastapi import APIRouter

from backend.state.enums import Market

router = APIRouter(prefix="/api")


@router.get("/markets")
async def get_markets():
    return {m.value: m.name for m in Market}
```

```python
# backend/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from backend.graph.workflow import BoardroomGraph
from backend.state.enums import Market


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()
            ticker = data.get("ticker")
            market = Market(data.get("market", "US"))
            portfolio_weight = data.get("portfolio_weight", 0.0)

            graph = BoardroomGraph()
            async for event in graph.run_streaming(ticker, market, portfolio_weight):
                await websocket.send_json({
                    "type": event["type"].value,
                    "agent": event["agent"].value if event["agent"] else None,
                    "data": _serialize(event["data"]),
                    "timestamp": datetime.utcnow().isoformat(),
                })

    except WebSocketDisconnect:
        pass


def _serialize(data):
    """Convert data to JSON-serializable format"""
    if isinstance(data, dict):
        return {k: _serialize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_serialize(v) for v in data]
    if hasattr(data, "value"):  # Enum
        return data.value
    if hasattr(data, "isoformat"):  # datetime
        return data.isoformat()
    return data
```

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.api.websocket import websocket_endpoint

app = FastAPI(title="Boardroom", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.websocket("/ws/analyze")(websocket_endpoint)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Step 4: Run test**

Run: `uv run pytest tests/test_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: FastAPI with WebSocket endpoint"
```

---

## Phase 5: Frontend

### Task 15: Frontend Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

**Step 1: Create frontend directory and initialize**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npm install lightweight-charts lucide-react
```

**Step 2: Configure tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Step 3: Create src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Step 4: Install shadcn/ui**

```bash
npx shadcn@latest init
npx shadcn@latest add button card input badge
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: frontend setup with Vite, React, TailwindCSS"
```

---

### Task 16: WebSocket Hook

**Files:**
- Create: `frontend/src/hooks/useWebSocket.ts`
- Create: `frontend/src/types/index.ts`

**Step 1: Create types**

```typescript
// frontend/src/types/index.ts
export type Market = "US" | "TASE";
export type Action = "BUY" | "SELL" | "HOLD";
export type Trend = "bullish" | "bearish" | "neutral";
export type AgentType = "fundamental" | "sentiment" | "technical" | "risk" | "chairperson";
export type WSMessageType = "analysis_started" | "agent_started" | "agent_completed" | "veto" | "decision" | "error";

export interface WSMessage {
  type: WSMessageType;
  agent: AgentType | null;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface FundamentalReport {
  revenue_growth: number;
  pe_ratio: number;
  debt_to_equity: number;
  market_cap: number;
  summary: string;
}

export interface SentimentReport {
  overall_sentiment: number;
  news_items: NewsItem[];
  social_mentions: SocialMention[];
  summary: string;
}

export interface NewsItem {
  source: string;
  title: string;
  url: string;
  published_at: string;
  sentiment: number;
  snippet: string;
}

export interface SocialMention {
  source: string;
  content: string;
  author: string;
  url: string;
  timestamp: string;
  engagement: number;
}

export interface TechnicalReport {
  current_price: number;
  ma_50: number;
  ma_200: number;
  rsi: number;
  trend: Trend;
  price_history: PricePoint[];
  summary: string;
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface RiskAssessment {
  sector: string;
  portfolio_sector_weight: number;
  var_95: number;
  veto: boolean;
  veto_reason: string | null;
}

export interface Decision {
  action: Action;
  confidence: number;
  rationale: string;
}

export interface AnalysisState {
  ticker: string | null;
  market: Market;
  fundamental: FundamentalReport | null;
  sentiment: SentimentReport | null;
  technical: TechnicalReport | null;
  risk: RiskAssessment | null;
  decision: Decision | null;
  activeAgents: Set<AgentType>;
  completedAgents: Set<AgentType>;
  vetoed: boolean;
  error: string | null;
}
```

**Step 2: Create WebSocket hook**

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useState, useCallback, useRef } from "react";
import type { Market, WSMessage, AnalysisState, AgentType } from "../types";

const WS_URL = "ws://localhost:8000/ws/analyze";

export function useWebSocket() {
  const [state, setState] = useState<AnalysisState>({
    ticker: null,
    market: "US",
    fundamental: null,
    sentiment: null,
    technical: null,
    risk: null,
    decision: null,
    activeAgents: new Set(),
    completedAgents: new Set(),
    vetoed: false,
    error: null,
  });
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const analyze = useCallback((ticker: string, market: Market) => {
    // Reset state
    setState({
      ticker,
      market,
      fundamental: null,
      sentiment: null,
      technical: null,
      risk: null,
      decision: null,
      activeAgents: new Set(),
      completedAgents: new Set(),
      vetoed: false,
      error: null,
    });

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      ws.send(JSON.stringify({ ticker, market }));
    };

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);

      setState((prev) => {
        const newState = { ...prev };

        switch (msg.type) {
          case "agent_started":
            if (msg.agent) {
              newState.activeAgents = new Set(prev.activeAgents).add(msg.agent);
            }
            break;

          case "agent_completed":
            if (msg.agent) {
              newState.activeAgents = new Set(prev.activeAgents);
              newState.activeAgents.delete(msg.agent);
              newState.completedAgents = new Set(prev.completedAgents).add(msg.agent);

              switch (msg.agent) {
                case "fundamental":
                  newState.fundamental = msg.data as unknown as typeof newState.fundamental;
                  break;
                case "sentiment":
                  newState.sentiment = msg.data as unknown as typeof newState.sentiment;
                  break;
                case "technical":
                  newState.technical = msg.data as unknown as typeof newState.technical;
                  break;
                case "risk":
                  newState.risk = msg.data as unknown as typeof newState.risk;
                  break;
              }
            }
            break;

          case "veto":
            newState.vetoed = true;
            break;

          case "decision":
            newState.decision = msg.data as unknown as typeof newState.decision;
            break;

          case "error":
            newState.error = msg.data.message as string;
            break;
        }

        return newState;
      });
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    ws.onerror = () => {
      setState((prev) => ({ ...prev, error: "WebSocket connection failed" }));
    };
  }, []);

  const disconnect = useCallback(() => {
    wsRef.current?.close();
  }, []);

  return { state, isConnected, analyze, disconnect };
}
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: WebSocket hook and TypeScript types"
```

---

### Task 17: Dashboard Components

**Files:**
- Create: `frontend/src/components/TickerInput.tsx`
- Create: `frontend/src/components/AgentPanel.tsx`
- Create: `frontend/src/components/StockChart.tsx`
- Create: `frontend/src/components/NewsFeed.tsx`
- Create: `frontend/src/components/DecisionCard.tsx`
- Create: `frontend/src/components/Dashboard.tsx`

**Step 1: Create TickerInput**

```typescript
// frontend/src/components/TickerInput.tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Market } from "../types";

interface Props {
  onAnalyze: (ticker: string, market: Market) => void;
  isLoading: boolean;
}

export function TickerInput({ onAnalyze, isLoading }: Props) {
  const [ticker, setTicker] = useState("");
  const [market, setMarket] = useState<Market>("US");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) {
      onAnalyze(ticker.trim().toUpperCase(), market);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="Enter ticker (e.g., AAPL, TEVA)"
        className="w-48"
      />
      <select
        value={market}
        onChange={(e) => setMarket(e.target.value as Market)}
        className="px-3 py-2 border rounded-md"
      >
        <option value="US">US</option>
        <option value="TASE">TASE</option>
      </select>
      <Button type="submit" disabled={isLoading || !ticker.trim()}>
        {isLoading ? "Analyzing..." : "Analyze"}
      </Button>
    </form>
  );
}
```

**Step 2: Create AgentPanel**

```typescript
// frontend/src/components/AgentPanel.tsx
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, CheckCircle } from "lucide-react";
import type { AgentType } from "../types";

interface Props {
  agent: AgentType;
  title: string;
  isActive: boolean;
  isCompleted: boolean;
  data: Record<string, unknown> | null;
}

export function AgentPanel({ agent, title, isActive, isCompleted, data }: Props) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold">{title}</h3>
        {isActive && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
        {isCompleted && <CheckCircle className="w-4 h-4 text-green-500" />}
      </div>

      {data && (
        <div className="text-sm space-y-1">
          {agent === "fundamental" && (
            <>
              <p>P/E: {(data.pe_ratio as number)?.toFixed(1) || "N/A"}</p>
              <p>Revenue Growth: {((data.revenue_growth as number) * 100)?.toFixed(1)}%</p>
              <p>D/E: {(data.debt_to_equity as number)?.toFixed(2)}</p>
            </>
          )}
          {agent === "sentiment" && (
            <>
              <p>Sentiment: {(data.overall_sentiment as number)?.toFixed(2)}</p>
              <Badge variant={(data.overall_sentiment as number) > 0 ? "default" : "destructive"}>
                {(data.overall_sentiment as number) > 0 ? "Positive" : "Negative"}
              </Badge>
            </>
          )}
          {agent === "technical" && (
            <>
              <p>Price: ${(data.current_price as number)?.toFixed(2)}</p>
              <p>RSI: {(data.rsi as number)?.toFixed(1)}</p>
              <Badge>{data.trend as string}</Badge>
            </>
          )}
          {agent === "risk" && (
            <>
              <p>Sector Weight: {((data.portfolio_sector_weight as number) * 100)?.toFixed(1)}%</p>
              {(data.veto as boolean) ? (
                <Badge variant="destructive">VETOED</Badge>
              ) : (
                <Badge variant="default">Approved</Badge>
              )}
            </>
          )}
        </div>
      )}
    </Card>
  );
}
```

**Step 3: Create DecisionCard**

```typescript
// frontend/src/components/DecisionCard.tsx
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Decision } from "../types";

interface Props {
  decision: Decision | null;
  vetoed: boolean;
  vetoReason?: string | null;
}

export function DecisionCard({ decision, vetoed, vetoReason }: Props) {
  if (vetoed) {
    return (
      <Card className="p-6 bg-red-50 border-red-200">
        <h2 className="text-xl font-bold text-red-700">Trade Vetoed</h2>
        <p className="text-red-600 mt-2">{vetoReason}</p>
      </Card>
    );
  }

  if (!decision) return null;

  const actionColors = {
    BUY: "bg-green-500",
    SELL: "bg-red-500",
    HOLD: "bg-yellow-500",
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-4 mb-4">
        <Badge className={`${actionColors[decision.action]} text-white text-lg px-4 py-2`}>
          {decision.action}
        </Badge>
        <span className="text-2xl font-bold">{(decision.confidence * 100).toFixed(0)}% confidence</span>
      </div>
      <p className="text-gray-700">{decision.rationale}</p>
    </Card>
  );
}
```

**Step 4: Create NewsFeed**

```typescript
// frontend/src/components/NewsFeed.tsx
import { Card } from "@/components/ui/card";
import type { NewsItem, SocialMention } from "../types";

interface Props {
  newsItems: NewsItem[];
  socialMentions: SocialMention[];
}

export function NewsFeed({ newsItems, socialMentions }: Props) {
  const allItems = [
    ...newsItems.map((n) => ({ ...n, type: "news" as const })),
    ...socialMentions.map((s) => ({ ...s, type: "social" as const, title: s.content.slice(0, 100) })),
  ];

  if (allItems.length === 0) return null;

  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-3">Recent News & Social</h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {allItems.slice(0, 10).map((item, i) => (
          <a
            key={i}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-2 hover:bg-gray-50 rounded"
          >
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">{item.source}</span>
              <span className="text-sm">{item.title}</span>
            </div>
          </a>
        ))}
      </div>
    </Card>
  );
}
```

**Step 5: Create StockChart**

```typescript
// frontend/src/components/StockChart.tsx
import { useEffect, useRef } from "react";
import { createChart, IChartApi } from "lightweight-charts";
import { Card } from "@/components/ui/card";
import type { PricePoint } from "../types";

interface Props {
  priceHistory: PricePoint[];
  ticker: string;
}

export function StockChart({ priceHistory, ticker }: Props) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current || priceHistory.length === 0) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 300,
      layout: { textColor: "#333" },
      grid: { vertLines: { color: "#eee" }, horzLines: { color: "#eee" } },
    });

    const candlestickSeries = chart.addCandlestickSeries();
    candlestickSeries.setData(
      priceHistory.map((p) => ({
        time: p.date.split("T")[0],
        open: p.open,
        high: p.high,
        low: p.low,
        close: p.close,
      }))
    );

    chartRef.current = chart;

    return () => {
      chart.remove();
    };
  }, [priceHistory]);

  if (priceHistory.length === 0) return null;

  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-2">{ticker} Price Chart</h3>
      <div ref={chartContainerRef} />
    </Card>
  );
}
```

**Step 6: Create Dashboard**

```typescript
// frontend/src/components/Dashboard.tsx
import { TickerInput } from "./TickerInput";
import { AgentPanel } from "./AgentPanel";
import { DecisionCard } from "./DecisionCard";
import { NewsFeed } from "./NewsFeed";
import { StockChart } from "./StockChart";
import { useWebSocket } from "../hooks/useWebSocket";

export function Dashboard() {
  const { state, isConnected, analyze } = useWebSocket();

  const isLoading = state.activeAgents.size > 0;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Boardroom</h1>
          <TickerInput onAnalyze={analyze} isLoading={isLoading} />
        </header>

        {state.ticker && (
          <>
            <div className="grid grid-cols-4 gap-4">
              <AgentPanel
                agent="fundamental"
                title="Fundamental"
                isActive={state.activeAgents.has("fundamental")}
                isCompleted={state.completedAgents.has("fundamental")}
                data={state.fundamental}
              />
              <AgentPanel
                agent="sentiment"
                title="Sentiment"
                isActive={state.activeAgents.has("sentiment")}
                isCompleted={state.completedAgents.has("sentiment")}
                data={state.sentiment}
              />
              <AgentPanel
                agent="technical"
                title="Technical"
                isActive={state.activeAgents.has("technical")}
                isCompleted={state.completedAgents.has("technical")}
                data={state.technical}
              />
              <AgentPanel
                agent="risk"
                title="Risk Manager"
                isActive={state.activeAgents.has("risk")}
                isCompleted={state.completedAgents.has("risk")}
                data={state.risk}
              />
            </div>

            <DecisionCard
              decision={state.decision}
              vetoed={state.vetoed}
              vetoReason={state.risk?.veto_reason}
            />

            <div className="grid grid-cols-2 gap-4">
              {state.technical?.price_history && (
                <StockChart
                  priceHistory={state.technical.price_history}
                  ticker={state.ticker}
                />
              )}
              {state.sentiment && (
                <NewsFeed
                  newsItems={state.sentiment.news_items}
                  socialMentions={state.sentiment.social_mentions}
                />
              )}
            </div>
          </>
        )}

        {state.error && (
          <div className="p-4 bg-red-100 text-red-700 rounded">{state.error}</div>
        )}
      </div>
    </div>
  );
}
```

**Step 7: Update App.tsx**

```typescript
// frontend/src/App.tsx
import { Dashboard } from "./components/Dashboard";

function App() {
  return <Dashboard />;
}

export default App;
```

**Step 8: Commit**

```bash
git add -A
git commit -m "feat: dashboard components"
```

---

## Phase 6: Integration

### Task 18: Final Integration & README

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

**Step 1: Update README**

```markdown
# Boardroom

Multi-agent financial analysis system with React dashboard.

## Quick Start

### Backend
```bash
cd backend
uv sync
cp .env.example .env  # Add your API keys
uv run uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Database
```bash
# Start PostgreSQL
docker run -d --name boardroom-db -e POSTGRES_DB=boardroom -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16

# Or use local PostgreSQL and create database:
createdb boardroom
```

## Environment Variables

```
ANTHROPIC_API_KEY=    # or OPENAI_API_KEY or GEMINI_API_KEY
LLM_PROVIDER=anthropic  # or openai or gemini
EXA_API_KEY=
DATABASE_URL=postgresql+asyncpg://localhost/boardroom
```
```

**Step 2: Update CLAUDE.md with commands**

Add to CLAUDE.md:
```markdown
## Development Commands

```bash
# Backend
uv run uvicorn backend.main:app --reload
uv run pytest tests/ -v
uv run pytest tests/test_specific.py::test_name -v

# Frontend
cd frontend && npm run dev
cd frontend && npm run build
```
```

**Step 3: Commit**

```bash
git add -A
git commit -m "docs: README and development setup"
```

---

## Summary

**Total Tasks:** 18

**Phase 1 (Backend Foundation):** Tasks 1-7
- Project setup, enums, state types
- Market data tool (Yahoo Finance)
- Technical indicators
- Search tool (Exa)
- LLM abstraction
- Database models

**Phase 2 (Agents):** Tasks 8-12
- Fundamental Agent
- Sentiment Agent
- Technical Agent
- Risk Manager Agent
- Chairperson Agent

**Phase 3 (Workflow):** Task 13
- LangGraph workflow with streaming

**Phase 4 (API):** Task 14
- FastAPI + WebSocket

**Phase 5 (Frontend):** Tasks 15-17
- Vite + React setup
- WebSocket hook
- Dashboard components

**Phase 6 (Integration):** Task 18
- Documentation and final setup
