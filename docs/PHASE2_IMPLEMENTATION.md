# Phase 2: Performance Tracking - Implementation Summary

## Overview
Phase 2 adds comprehensive performance tracking to The Boardroom, allowing users to see how accurate the system's recommendations have been over time and which agents provide the most reliable signals.

## ✅ Completed Components

### 1. Database Models (`backend/dao/models.py`)

#### `AnalysisOutcome` Table
Tracks what actually happened after each recommendation:
- Price at recommendation
- Follow-up prices at 1d, 7d, 30d, 90d intervals
- Whether the recommendation was correct
- Links to original analysis session

#### `AgentAccuracy` Table
Tracks accuracy metrics for each agent type:
- Total signals generated
- Correct signals
- Accuracy percentage
- Tracked across 7d, 30d, 90d periods

### 2. Background Job System

#### Outcome Tracker (`backend/jobs/outcome_tracker.py`)
- Updates follow-up prices for past recommendations
- Calculates whether recommendations were correct
- Uses attribution logic to determine which agents made good calls
- Runs automatically every hour

#### Job Scheduler (`backend/jobs/scheduler.py`)
- Manages periodic execution of background jobs
- Starts/stops with FastAPI lifecycle
- Handles errors gracefully
- Can be triggered manually for testing

#### Attribution Logic
```python
# If agent agreed with final decision and outcome was correct → credit agent
# If agent disagreed with final decision and outcome was incorrect → credit agent
# This rewards both good calls AND good contrarian analysis
```

### 3. Outcome Service (`backend/services/outcome_service.py`)
- Creates outcome records when analysis completes
- Fetches performance summaries
- Gets recent outcomes with returns
- Calculates statistics

### 4. API Endpoints (`backend/api/performance.py`)

| Endpoint | Description |
|----------|-------------|
| `GET /api/performance/summary` | Overall accuracy statistics |
| `GET /api/performance/recent` | Recent recommendations with returns |
| `GET /api/performance/agents` | Accuracy by agent and time period |
| `GET /api/performance/agent/{type}` | Detailed agent performance |
| `GET /api/performance/ticker/{ticker}` | History for specific stock |
| `POST /api/performance/trigger-update` | Manual job trigger |

### 5. Integration

- **WebSocket** (`backend/api/websocket.py`): Creates outcome record when decision is made
- **Main App** (`backend/main.py`): Starts scheduler on application startup
- **Database Migration** (`alembic/versions/1e04e15e9cbb_*.py`): Adds new tables

## How It Works

### 1. Outcome Creation Flow
```
Analysis Completes → Decision Made → Create AnalysisOutcome Record
                                    ↓
                            Record initial price
```

### 2. Background Update Flow
```
Every Hour → Fetch all pending outcomes
          ↓
     Check time elapsed since recommendation
          ↓
     Fetch current price for each ticker
          ↓
     Update 1d/7d/30d/90d prices as they become available
          ↓
     Calculate if recommendation was correct (using 30d as primary)
          ↓
     Update agent accuracy metrics with attribution
```

### 3. Correctness Calculation
- **BUY**: Correct if price went up (any increase)
- **SELL**: Correct if price went down (any decrease)
- **HOLD**: Correct if price stayed stable (±2% threshold)

## API Examples

### Get Overall Performance
```bash
curl http://localhost:8000/api/performance/summary
```
```json
{
  "total_recommendations": 42,
  "correct_count": 29,
  "accuracy": 0.69,
  "by_action": {
    "BUY": {"total": 20, "correct": 15, "accuracy": 0.75},
    "SELL": {"total": 12, "correct": 8, "accuracy": 0.67},
    "HOLD": {"total": 10, "correct": 6, "accuracy": 0.60}
  }
}
```

### Get Agent Accuracy
```bash
curl http://localhost:8000/api/performance/agents
```
```json
{
  "agents": {
    "fundamental": {
      "7d": {"total_signals": 50, "correct_signals": 38, "accuracy": 0.76},
      "30d": {"total_signals": 45, "correct_signals": 32, "accuracy": 0.71},
      "90d": {"total_signals": 30, "correct_signals": 20, "accuracy": 0.67}
    },
    "sentiment": {...},
    "technical": {...}
  }
}
```

### Get Recent Outcomes
```bash
curl http://localhost:8000/api/performance/recent?limit=5
```
```json
{
  "outcomes": [
    {
      "ticker": "AAPL",
      "action": "BUY",
      "price_at_recommendation": 150.00,
      "confidence": 0.82,
      "outcome_correct": true,
      "returns": {
        "1d": 0.013,
        "7d": 0.047,
        "30d": 0.095
      },
      "created_at": "2026-02-01T10:30:00"
    },
    ...
  ]
}
```

### Trigger Manual Update
```bash
curl -X POST http://localhost:8000/api/performance/trigger-update
```

## Testing

### 1. Verify Scheduler is Running
```bash
uv run uvicorn backend.main:app --reload
# Check logs for: "Job scheduler started"
```

### 2. Create Analysis
Use the frontend to analyze a stock. An `AnalysisOutcome` record will be created automatically.

### 3. Trigger Manual Update
```bash
curl -X POST http://localhost:8000/api/performance/trigger-update
```

### 4. Check Performance Data
```bash
curl http://localhost:8000/api/performance/summary
curl http://localhost:8000/api/performance/recent
```

## Next Steps (Frontend Dashboard)

To complete Phase 2, implement frontend components:

1. **Performance Dashboard Page**
   - Overall accuracy chart
   - Agent performance comparison
   - Recent outcomes table

2. **Agent Performance Cards**
   - Accuracy metrics by time period
   - Visual indicators (badges, charts)
   - Trend over time

3. **Outcome Timeline**
   - Historical recommendations
   - Price movement visualization
   - Filter by action, ticker, date

4. **Integration with Existing Views**
   - Show historical accuracy on agent panels
   - Display past performance for ticker in AnalysisHistory
   - Add performance badge to agent reports

## Configuration

The outcome tracker job runs every hour by default. To adjust:

```python
# backend/jobs/scheduler.py
await asyncio.sleep(3600)  # Change interval (in seconds)
```

## Database Schema

```sql
-- AnalysisOutcome: tracks recommendation outcomes
CREATE TABLE analysis_outcomes (
    id UUID PRIMARY KEY,
    session_id UUID UNIQUE REFERENCES analysis_sessions(id),
    ticker VARCHAR(20),
    action_recommended action,  -- BUY/SELL/HOLD
    price_at_recommendation FLOAT,
    price_after_1d FLOAT,
    price_after_7d FLOAT,
    price_after_30d FLOAT,
    price_after_90d FLOAT,
    outcome_correct BOOLEAN,
    created_at TIMESTAMP,
    last_updated TIMESTAMP
);

-- AgentAccuracy: tracks agent performance
CREATE TABLE agent_accuracy (
    id UUID PRIMARY KEY,
    agent_type agenttype,  -- FUNDAMENTAL/SENTIMENT/TECHNICAL/RISK/CHAIRPERSON
    period VARCHAR(10),    -- "7d", "30d", "90d"
    total_signals INTEGER,
    correct_signals INTEGER,
    accuracy FLOAT,
    last_calculated TIMESTAMP
);
```

## Notes

- Outcomes are evaluated using the 30-day price as the primary timeframe
- Agent attribution considers both alignment and contrarian positions
- The risk manager doesn't make buy/sell recommendations, only vetos
- Background job continues running even if individual updates fail
- All timestamps are stored in UTC
