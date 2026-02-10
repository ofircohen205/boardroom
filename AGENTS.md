# AGENTS.md

This document provides a comprehensive guide to the Boardroom agent system architecture.

## Repository Information

**Git Repository:** https://github.com/ofircohen205/boardroom

> **Important:** When adding new agents or modifying agent behavior, update this file to document the changes and prevent knowledge loss between sessions.

## Table of Contents

1. [Repository Information](#repository-information)
2. [Overview](#overview)
3. [Agent Hierarchy](#agent-hierarchy)
4. [Token of Authority Pattern](#token-of-authority-pattern)
5. [State Flow](#state-flow)
6. [Individual Agents](#individual-agents)
7. [Workflow Execution](#workflow-execution)
8. [Adding New Agents](#adding-new-agents)
9. [Testing Agents](#testing-agents)
10. [Agent Development Standards](#agent-development-standards)

---

## Overview

Boardroom uses a **multi-agent system** where specialized AI agents collaborate to analyze stocks and make trading decisions. The system is built on [LangGraph](https://langchain-ai.github.io/langgraph/), which provides the orchestration framework.

**Key Principles:**

- **Separation of Concerns:** Each agent has a focused responsibility
- **Parallel Execution:** Analyst agents run concurrently for speed
- **Veto Power:** Risk manager can block unsafe trades
- **Consensus Building:** Chairperson weighs all inputs before deciding
- **Auditability:** All decisions are logged with full reasoning

### Architecture Diagram

```
User Input (ticker)
       ↓
┌──────────────────────────────────┐
│   LangGraph Workflow             │
│   (BoardroomGraph)               │
└──────────────────────────────────┘
       ↓
┌──────────────────────────────────┐
│   PARALLEL EXECUTION             │
│                                  │
│  ┌────────────────┐              │
│  │ Fundamental    │→ Revenue,    │
│  │ Agent          │  P/E, etc.   │
│  └────────────────┘              │
│                                  │
│  ┌────────────────┐              │
│  │ Sentiment      │→ News,       │
│  │ Agent          │  Social      │
│  └────────────────┘              │
│                                  │
│  ┌────────────────┐              │
│  │ Technical      │→ MA, RSI,    │
│  │ Agent          │  Trend       │
│  └────────────────┘              │
└──────────────────────────────────┘
       ↓ (All 3 complete)
┌──────────────────────────────────┐
│   SEQUENTIAL EXECUTION           │
│                                  │
│  ┌────────────────┐              │
│  │ Risk Manager   │→ VaR,        │
│  │ Agent          │  Veto?       │
│  └────────────────┘              │
│         ↓                        │
│    [If not vetoed]               │
│         ↓                        │
│  ┌────────────────┐              │
│  │ Chairperson    │→ BUY/SELL/   │
│  │ Agent          │  HOLD        │
│  └────────────────┘              │
└──────────────────────────────────┘
       ↓
  Final Decision
```

---

## Agent Hierarchy

### 1. Analyst Agents (Workers)

These agents gather and analyze data. They run **in parallel** for maximum speed.

#### **Fundamental Agent**

- **Role:** Financial health analyst
- **Data Sources:** Yahoo Finance API
- **Output:** Revenue growth, P/E ratio, debt-to-equity, market cap, sector
- **Location:** `backend/agents/fundamental.py`

#### **Sentiment Agent**

- **Role:** News and social media analyst
- **Data Sources:** Exa search API (news + social)
- **Output:** Overall sentiment score (-1 to +1), news items, social mentions
- **Location:** `backend/agents/sentiment.py`

#### **Technical Agent**

- **Role:** Price action and trend analyst
- **Data Sources:** Yahoo Finance (historical prices)
- **Output:** Current price, MA50, MA200, RSI, trend (bullish/bearish/neutral)
- **Location:** `backend/agents/technical.py`

### 2. Risk Manager (Brake)

- **Role:** Risk assessment and trade veto authority
- **Runs:** After analysts complete (sequential)
- **Checks:**
  - Portfolio sector concentration (max 30% per sector)
  - Value at Risk (VaR) calculation
  - Overall risk profile
- **Veto Power:** Can block trades deemed too risky
- **Location:** `backend/agents/risk_manager.py`

### 3. Chairperson (Closer)

- **Role:** Final decision maker
- **Runs:** After risk approval (sequential)
- **Process:**
  - Weighs all analyst reports
  - Considers risk assessment
  - Makes BUY/SELL/HOLD decision
  - Assigns confidence score (0-100)
  - Provides detailed rationale
- **Location:** `backend/agents/chairperson.py`

---

## Token of Authority Pattern

The **Token of Authority** is a conceptual pattern (not literal token passing) where agents have different levels of decision-making power:

### Authority Levels

1. **Analysts (No Authority):** Gather data and provide opinions, but cannot make decisions
2. **Risk Manager (Veto Authority):** Can block decisions but cannot make BUY/SELL/HOLD calls
3. **Chairperson (Full Authority):** Makes the final binding decision

### State-Based Token Passing

The "token" is represented by the `AgentState` object that flows through the workflow:

```python
AgentState = {
    "ticker": "AAPL",
    "market": Market.US,
    "fundamental_report": {...},      # Analyst input
    "sentiment_report": {...},        # Analyst input
    "technical_report": {...},        # Analyst input
    "risk_assessment": {...},         # Risk veto checkpoint
    "final_decision": {...},          # Chairperson output
    "consensus_score": 0.0,
    "audit_id": "uuid-here",
}
```

Each agent receives the current state, adds its contribution, and passes it forward.

### Workflow Control Flow

```python
# Parallel: Analysts add reports to state
state["fundamental_report"] = await fundamental_agent.analyze(...)
state["sentiment_report"] = await sentiment_agent.analyze(...)
state["technical_report"] = await technical_agent.analyze(...)

# Sequential: Risk manager checks state
state["risk_assessment"] = await risk_manager.assess(...)

# Control flow: Veto stops the workflow
if state["risk_assessment"]["veto"]:
    return state  # No final decision

# Sequential: Chairperson makes decision
state["final_decision"] = await chairperson.decide(...)

return state
```

---

## State Flow

### State Schema

Defined in `backend/state/agent_state.py`:

```python
from typing import Optional, TypedDict
from backend.state.enums import Action, Market, Trend

class FundamentalReport(TypedDict):
    revenue_growth: float
    pe_ratio: float
    debt_to_equity: float
    market_cap: float
    sector: Optional[str]
    summary: str  # LLM-generated analysis

class SentimentReport(TypedDict):
    overall_sentiment: float  # -1 to +1
    news_items: list[NewsItem]
    social_mentions: list[SocialMention]
    summary: str  # LLM-generated analysis

class TechnicalReport(TypedDict):
    current_price: float
    ma_50: float
    ma_200: float
    rsi: float
    trend: Trend  # BULLISH, BEARISH, NEUTRAL
    price_history: list[dict]
    summary: str  # LLM-generated analysis

class RiskAssessment(TypedDict):
    sector: str
    portfolio_sector_weight: float
    var_95: float
    veto: bool
    veto_reason: Optional[str]

class Decision(TypedDict):
    action: Action  # BUY, SELL, HOLD
    confidence: float  # 0-100
    rationale: str
```

### State Lifecycle

1. **Initialization:** Empty state created with ticker, market, audit_id
2. **Analyst Phase:** Reports added in parallel
3. **Risk Phase:** Assessment added, veto may stop workflow
4. **Decision Phase:** Final decision added
5. **Persistence:** Complete state saved to PostgreSQL
6. **Streaming:** Each state update streamed to frontend via WebSocket

---

## Individual Agents

### Fundamental Agent

**File:** `backend/agents/fundamental.py`

**Purpose:** Analyze financial health using company fundamentals.

**Tools Used:**

- `backend/tools/market_data.py` → `get_stock_data(ticker, market)`

**LLM Prompt:**

```
Analyze the fundamental data for {ticker}:
- P/E Ratio: {pe_ratio}
- Revenue Growth: {revenue_growth}
- Debt to Equity: {debt_to_equity}
- Market Cap: {market_cap}
- Sector: {sector}

Provide a brief fundamental analysis summary (2-3 sentences).
```

**Output:**

```python
FundamentalReport(
    revenue_growth=0.082,  # 8.2%
    pe_ratio=28.5,
    debt_to_equity=1.73,
    market_cap=2.8e12,     # $2.8T
    sector="Technology",
    summary="Apple shows strong revenue growth of 8.2%..."
)
```

**Key Logic:**

- Fetches stock data from Yahoo Finance
- Extracts key fundamental metrics
- Uses LLM to generate human-readable summary
- Returns structured report

---

### Sentiment Agent

**File:** `backend/agents/sentiment.py`

**Purpose:** Gauge market sentiment from news and social media.

**Tools Used:**

- `backend/tools/search.py` → `search_news()`, `search_social()`

**LLM Prompt:**

```
Analyze the sentiment for {ticker} based on recent news and social media:

News Items:
{news_items}

Social Mentions:
{social_mentions}

Provide an overall sentiment score (-1 to +1) and a brief summary.
```

**Output:**

```python
SentimentReport(
    overall_sentiment=0.65,  # Positive
    news_items=[
        NewsItem(
            source=SentimentSource.NEWS,
            title="Apple announces new product line",
            url="https://...",
            published_at=datetime.now(),
            sentiment=0.8,
            snippet="..."
        ),
        ...
    ],
    social_mentions=[...],
    summary="Sentiment is strongly positive with..."
)
```

**Sentiment Calculation:**

- Weighted average of news sentiment scores
- Social mentions contribute to overall score
- LLM provides qualitative analysis

---

### Technical Agent

**File:** `backend/agents/technical.py`

**Purpose:** Analyze price trends and technical indicators.

**Tools Used:**

- `backend/tools/technical_indicators.py` → `calculate_ma()`, `calculate_rsi()`, `detect_trend()`

**LLM Prompt:**

```
Analyze the technical indicators for {ticker}:
- Current Price: ${current_price}
- MA50: ${ma_50}
- MA200: ${ma_200}
- RSI: {rsi}
- Trend: {trend}

Provide a brief technical analysis summary (2-3 sentences).
```

**Output:**

```python
TechnicalReport(
    current_price=175.43,
    ma_50=172.30,
    ma_200=168.50,
    rsi=62.5,
    trend=Trend.BULLISH,
    price_history=[...],
    summary="Price is above both moving averages..."
)
```

**Technical Indicators:**

- **MA50/MA200:** Moving averages for trend detection
- **RSI:** Relative Strength Index (overbought/oversold)
- **Trend:** Detected from price action and MA crossovers

---

### Risk Manager Agent

**File:** `backend/agents/risk_manager.py`

**Purpose:** Assess risk and veto unsafe trades.

**Tools Used:**

- Value at Risk (VaR) calculation from price volatility
- Portfolio sector weight checks

**LLM Prompt:**

```
Assess the risk for trading {ticker} in the {sector} sector:
- Current portfolio weight in {sector}: {weight}%
- Value at Risk (95% confidence): {var}
- Fundamental data: {fundamental}
- Sentiment: {sentiment}
- Technical trend: {technical}

Should this trade be vetoed? Provide reasoning.
```

**Output:**

```python
RiskAssessment(
    sector="Technology",
    portfolio_sector_weight=0.28,  # 28%
    var_95=0.032,  # 3.2% potential loss
    veto=False,
    veto_reason=None
)
```

**Veto Conditions:**

- Portfolio sector concentration > 30%
- Excessive volatility (VaR > threshold)
- Conflicting signals from analysts

**Current Limitation:** `portfolio_sector_weight` is hardcoded to 0.0 until Phase 1 (Portfolio Tracking) is implemented.

---

### Chairperson Agent

**File:** `backend/agents/chairperson.py`

**Purpose:** Make the final BUY/SELL/HOLD decision.

**LLM Prompt:**

```
You are the Chairperson of the Boardroom investment committee.

Review the analyst reports for {ticker}:

FUNDAMENTAL ANALYSIS:
{fundamental_summary}

SENTIMENT ANALYSIS:
{sentiment_summary}

TECHNICAL ANALYSIS:
{technical_summary}

Based on all reports, make a decision:
- Action: BUY, SELL, or HOLD
- Confidence: 0-100
- Rationale: Explain your reasoning

Respond in JSON format.
```

**Output:**

```python
Decision(
    action=Action.BUY,
    confidence=78.0,
    rationale="Strong fundamentals (8.2% revenue growth, P/E of 28.5), positive sentiment (0.65), and bullish technical trend. Price above MA50 and MA200. Confidence tempered by slightly elevated RSI (62.5)."
)
```

**Decision Logic:**

- Weighs all three analyst reports
- Considers consensus vs. divergence
- Assigns confidence based on signal strength
- Provides detailed rationale

---

## Workflow Execution

### Non-Streaming Workflow

**File:** `backend/graph/workflow.py` → `BoardroomGraph.run()`

```python
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

    # Run analysts in parallel
    fundamental, sentiment, technical = await asyncio.gather(
        self.fundamental.analyze(ticker, market),
        self.sentiment.analyze(ticker, market),
        self.technical.analyze(ticker, market),
    )
    state["fundamental_report"] = fundamental
    state["sentiment_report"] = sentiment
    state["technical_report"] = technical

    # Risk assessment
    sector = fundamental.get("sector") or "Unknown"
    state["risk_assessment"] = await self.risk_manager.assess(
        ticker=ticker,
        sector=sector,
        portfolio_tech_weight=portfolio_sector_weight,
        fundamental=fundamental,
        sentiment=sentiment,
        technical=technical,
    )

    # Veto check
    if state["risk_assessment"]["veto"]:
        return state

    # Chairperson decision
    state["final_decision"] = await self.chairperson.decide(
        ticker=ticker,
        fundamental=fundamental,
        sentiment=sentiment,
        technical=technical,
    )

    return state
```

### Streaming Workflow

**File:** `backend/graph/workflow.py` → `BoardroomGraph.run_streaming()`

Used for real-time WebSocket updates to the frontend.

**Key Features:**

- Yields WebSocket messages after each agent completion
- Uses `asyncio.Queue` to stream results as they arrive
- Supports partial state updates

**Message Types:**

```python
WSMessageType.ANALYSIS_STARTED   # Workflow begins
WSMessageType.AGENT_STARTED      # Agent starts execution
WSMessageType.AGENT_COMPLETED    # Agent finishes, data available
WSMessageType.VETO               # Risk manager vetoes
WSMessageType.DECISION           # Chairperson makes final call
```

**Example Stream:**

```python
async for message in graph.run_streaming("AAPL", Market.US):
    # message = {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.TECHNICAL, "data": {...}}
    await websocket.send_json(message)
```

---

## Adding New Agents

### Step-by-Step Guide

#### 1. Define the Report Type

Add to `backend/state/agent_state.py`:

```python
class MyNewReport(TypedDict):
    metric_a: float
    metric_b: str
    summary: str
```

#### 2. Update AgentState

Add to `backend/state/agent_state.py`:

```python
class AgentState(TypedDict):
    # ... existing fields
    my_new_report: Optional[MyNewReport]
```

#### 3. Create the Agent Class

Create `backend/agents/my_new_agent.py`:

```python
from backend.agents.base import get_llm_client
from backend.state.agent_state import MyNewReport
from backend.state.enums import Market
from backend.tools.some_tool import get_data

class MyNewAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def analyze(self, ticker: str, market: Market) -> MyNewReport:
        # 1. Fetch data using tools
        data = await get_data(ticker, market)

        # 2. Build LLM prompt
        prompt = f"Analyze {ticker} with data: {data}"

        # 3. Get LLM analysis
        summary = await self.llm.complete([{"role": "user", "content": prompt}])

        # 4. Return structured report
        return MyNewReport(
            metric_a=data["metric_a"],
            metric_b=data["metric_b"],
            summary=summary,
        )
```

#### 4. Add Agent to Workflow

Update `backend/graph/workflow.py`:

```python
class BoardroomGraph:
    def __init__(self):
        # ... existing agents
        self.my_new_agent = MyNewAgent()

    async def run_streaming(self, ticker: str, market: Market, ...) -> AsyncGenerator[dict, None]:
        # ... existing code

        # Option A: Run in parallel with other analysts
        tasks = [
            asyncio.create_task(_run_agent(AgentType.FUNDAMENTAL, self.fundamental.analyze(ticker, market))),
            asyncio.create_task(_run_agent(AgentType.MY_NEW_AGENT, self.my_new_agent.analyze(ticker, market))),
            # ...
        ]

        # Option B: Run sequentially after other agents
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.MY_NEW_AGENT, "data": {}}
        my_report = await self.my_new_agent.analyze(ticker, market)
        yield {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.MY_NEW_AGENT, "data": my_report}
```

#### 5. Add Agent Type Enum

Update `backend/state/enums.py`:

```python
class AgentType(str, Enum):
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    TECHNICAL = "technical"
    RISK = "risk"
    CHAIRPERSON = "chairperson"
    MY_NEW_AGENT = "my_new_agent"  # Add this
```

#### 6. Update Frontend

**TypeScript Types** (`frontend/src/types/analysis.ts`):

```typescript
export interface MyNewReport {
  metric_a: number;
  metric_b: string;
  summary: string;
}

export interface AnalysisState {
  // ... existing
  my_new_report: MyNewReport | null;
}
```

**Display Component** (`frontend/src/components/MyNewAgentPanel.tsx`):

```tsx
export function MyNewAgentPanel({ report }: { report: MyNewReport | null }) {
  if (!report) return <Skeleton />;

  return (
    <Card>
      <CardHeader>My New Agent</CardHeader>
      <CardContent>
        <p>Metric A: {report.metric_a}</p>
        <p>Metric B: {report.metric_b}</p>
        <p>{report.summary}</p>
      </CardContent>
    </Card>
  );
}
```

**Add to Dashboard** (`frontend/src/components/Dashboard.tsx`):

```tsx
<MyNewAgentPanel report={analysisState.my_new_report} />
```

#### 7. Write Tests

Create `tests/test_my_new_agent.py`:

```python
import pytest
from backend.agents.my_new_agent import MyNewAgent
from backend.state.enums import Market

@pytest.mark.asyncio
async def test_my_new_agent_analyze(mocker):
    # Mock tools
    mock_get_data = mocker.patch("backend.tools.some_tool.get_data")
    mock_get_data.return_value = {"metric_a": 42, "metric_b": "test"}

    # Mock LLM
    mock_llm = mocker.patch("backend.agents.base.get_llm_client")
    mock_llm.return_value.complete = mocker.AsyncMock(return_value="Summary text")

    # Test
    agent = MyNewAgent()
    report = await agent.analyze("AAPL", Market.US)

    assert report["metric_a"] == 42
    assert report["metric_b"] == "test"
    assert "Summary" in report["summary"]
```

---

## Testing Agents

### Unit Testing Strategy

**Test agents in isolation** by mocking their dependencies:

```python
import pytest
from unittest.mock import AsyncMock
from backend.agents.fundamental import FundamentalAgent
from backend.state.enums import Market

@pytest.mark.asyncio
async def test_fundamental_agent_analyze(mocker):
    # Mock the market data tool
    mock_market_data = mocker.patch("backend.agents.fundamental.get_market_data_client")
    mock_market_data.return_value.get_stock_data = AsyncMock(return_value={
        "pe_ratio": 28.5,
        "revenue_growth": 0.082,
        "debt_to_equity": 1.73,
        "market_cap": 2.8e12,
        "sector": "Technology",
    })

    # Mock the LLM
    mock_llm = mocker.patch("backend.agents.fundamental.get_llm_client")
    mock_llm.return_value.complete = AsyncMock(return_value="Strong fundamentals")

    # Create agent and test
    agent = FundamentalAgent()
    report = await agent.analyze("AAPL", Market.US)

    # Assertions
    assert report["pe_ratio"] == 28.5
    assert report["revenue_growth"] == 0.082
    assert report["sector"] == "Technology"
    assert "Strong fundamentals" in report["summary"]
```

### Integration Testing

**Test the full workflow** with mocked external APIs:

```python
import pytest
from backend.graph.workflow import create_boardroom_graph
from backend.state.enums import Market, Action

@pytest.mark.asyncio
async def test_full_workflow(mocker):
    # Mock all external APIs
    mocker.patch("backend.tools.market_data.yfinance.Ticker")
    mocker.patch("backend.tools.search.exa_client.search_and_contents")

    # Mock LLM responses
    mock_llm = mocker.patch("backend.agents.base.get_llm_client")
    mock_llm.return_value.complete = AsyncMock(return_value="Test summary")

    # Run workflow
    graph = create_boardroom_graph()
    state = await graph.run("AAPL", Market.US)

    # Assertions
    assert state["fundamental_report"] is not None
    assert state["sentiment_report"] is not None
    assert state["technical_report"] is not None
    assert state["risk_assessment"] is not None
    assert state["final_decision"] is not None
    assert state["final_decision"]["action"] in [Action.BUY, Action.SELL, Action.HOLD]
```

### Testing Checklist

- [ ] Agent returns correct report structure
- [ ] Agent handles missing data gracefully
- [ ] Agent calls tools with correct parameters
- [ ] LLM prompt is well-formatted
- [ ] Edge cases handled (no data, API errors)
- [ ] Integration with workflow works
- [ ] WebSocket streaming works
- [ ] Frontend receives and displays data

---

## Advanced Topics

### Multi-LLM Support

All agents use the `get_llm_client()` abstraction from `backend/agents/base.py`:

```python
from backend.agents.base import get_llm_client

llm = get_llm_client()  # Uses LLM_PROVIDER from env
summary = await llm.complete([{"role": "user", "content": prompt}])
```

**Supported Providers:**

- Anthropic Claude (default)
- OpenAI GPT-4
- Google Gemini

Set via `LLM_PROVIDER` environment variable.

### Tool Calling

Some agents may need tool-calling capabilities (e.g., for complex data fetching):

```python
async def analyze_with_tools(self, ticker: str) -> Report:
    tools = [
        {
            "name": "get_earnings_data",
            "description": "Fetch earnings history",
            "parameters": {"ticker": {"type": "string"}},
        }
    ]

    result = await self.llm.complete_with_tools(messages, tools)

    if result.get("tool"):
        # Handle tool call
        tool_result = await self.execute_tool(result["tool"], result["args"])
        # Continue conversation with tool result
```

### Caching

Expensive operations (market data, LLM calls) are cached:

```python
from backend.cache import cached

@cached(ttl=3600)  # Cache for 1 hour
async def get_stock_data(ticker: str, market: Market):
    # Expensive operation
    return data
```

### Error Handling

Agents should handle errors gracefully:

```python
async def analyze(self, ticker: str, market: Market) -> Report:
    try:
        data = await self.get_data(ticker, market)
    except Exception as e:
        # Log error
        logger.error(f"Failed to fetch data for {ticker}: {e}")
        # Return default report
        return Report(
            metric=0.0,
            summary="Data unavailable",
        )
```

---

## Agent Development Standards

### Code Quality for Agents

1. **Clean Code Principles:**
   - Each agent should have a single, well-defined responsibility
   - Extract complex logic into helper methods
   - Remove orphaned code (unused imports, commented-out functions)
   - Refactor duplicated code into shared utilities

2. **Logging Requirements:**
   - Log agent start and completion times
   - Log all tool calls and their results
   - Log LLM prompts and responses (at DEBUG level)
   - Include ticker symbol and agent name in all logs
   - Example:
     ```python
     logger.info(f"[{self.__class__.__name__}] Analyzing {ticker}")
     logger.debug(f"[{self.__class__.__name__}] LLM prompt: {prompt}")
     logger.info(f"[{self.__class__.__name__}] Analysis complete for {ticker}")
     ```

3. **Error Handling:**
   - Always handle tool failures gracefully
   - Return meaningful error reports instead of crashing
   - Log errors with full context
   - Example:
     ```python
     try:
         data = await self.fetch_data(ticker)
     except Exception as e:
         logger.error(f"[{self.__class__.__name__}] Failed to fetch data for {ticker}: {e}")
         return self._create_error_report(ticker, str(e))
     ```

4. **Testing:**
   - Write unit tests for each agent
   - Mock external APIs and LLM calls
   - Test error scenarios (missing data, API failures)
   - Maintain >80% test coverage

### Numerical Accuracy in Agents

> **Critical for Financial Analysis:**

Agents analyze financial data where precision matters:

1. **Calculations:**
   - Verify formulas before implementation (RSI, moving averages, ratios)
   - Use proper data types (Decimal for currency, float for percentages)
   - Handle division by zero
   - Round appropriately (2 decimals for currency, 4 for ratios)

2. **Thresholds:**
   - Document threshold rationale ("RSI > 70 indicates overbought")
   - Don't hardcode arbitrary thresholds without explanation
   - Consider context (e.g., P/E ratio varies by sector)

3. **Comparisons:**
   - Be explicit about "good" vs "bad" (high P/E can be good or bad)
   - Consider relative comparisons (vs sector average, vs historical)
   - Validate sign/direction of changes (growth is positive, decline is negative)

### Agent-Specific Best Practices

1. **Fundamental Agent:**
   - Always validate financial metrics before using them
   - Handle missing data (not all stocks have all metrics)
   - Consider market capitalization when interpreting ratios

2. **Sentiment Agent:**
   - Weight recent news more heavily than old news
   - Normalize sentiment scores to -1 to +1 range
   - Handle cases with no news/social data

3. **Technical Agent:**
   - Ensure sufficient historical data before calculating indicators
   - Handle edge cases (IPOs, recent stock splits)
   - Validate indicator calculations match standard formulas

4. **Risk Manager:**
   - Never skip risk checks (even for "obvious" safe trades)
   - Document veto rationale clearly
   - Consider correlation between holdings (not just sector weight)

5. **Chairperson:**
   - Explain decision rationale in detail
   - Weight analyst inputs appropriately (don't ignore dissenting views)
   - Assign confidence scores based on signal quality, not arbitrary values

### Performance Optimization

1. **Caching:**
   - Cache expensive market data calls (TTL: 1 hour for static data)
   - Don't cache real-time price data
   - Consider cache invalidation strategy

2. **Parallel Execution:**
   - Analysts should run in parallel (already implemented)
   - Don't add sequential dependencies between analysts
   - Only sequential operations: Risk Manager → Chairperson

3. **LLM Optimization:**
   - Keep prompts concise but complete
   - Use async LLM calls
   - Consider streaming responses for real-time updates

---

## Future Enhancements

### Planned Agent Additions

- **Options Agent:** Analyze options chains for volatility signals (Phase 3+)
- **Macro Agent:** Assess macroeconomic conditions (interest rates, inflation) (Phase 3+)
- **Insider Trading Agent:** Track insider buying/selling activity (Phase 3+)

### Planned Agent Improvements

- **Fundamental Agent:** Quarterly earnings call transcripts analysis
- **Sentiment Agent:** Reddit sentiment analysis (r/wallstreetbets)
- **Technical Agent:** More indicators (MACD, Bollinger Bands, Fibonacci)
- **Risk Manager:** Portfolio optimization suggestions
- **Chairperson:** Position sizing recommendations

See [docs/plans/roadmap.md](./docs/plans/roadmap.md) for full roadmap.

---

## References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Yahoo Finance API](https://python-yahoofinance.readthedocs.io/)
- [Exa Search API](https://docs.exa.ai/)

---

**Last Updated:** 2026-02-10
**Version:** 2.0.0
