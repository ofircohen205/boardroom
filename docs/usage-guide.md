# Usage Guide

Learn how to use Boardroom's multi-agent financial analysis system to get investment insights.

## Overview

Boardroom uses AI agents to analyze stocks and provide comprehensive investment recommendations. The system combines:

- **Market Data Analysis**: Real-time stock prices and historical data
- **News Analysis**: Latest news and sentiment analysis
- **AI-Powered Insights**: Multiple AI agents providing different perspectives

## Dashboard Components

### Ticker Input

Enter a stock ticker symbol (e.g., `AAPL`, `GOOGL`, `MSFT`) to begin analysis.

1. Type the ticker symbol in the input field
2. Press Enter or click the Analyze button
3. The system will start gathering data and running analysis

### Stock Chart

Displays historical price data for the selected stock:

- Price trends over time
- Volume indicators
- Interactive zoom and pan

### Agent Panel

Shows the AI agents working on your analysis:

- Real-time status updates as agents process data
- Each agent focuses on different aspects (fundamentals, technicals, sentiment)
- Results stream in as they become available

### Decision Card

Displays the final investment recommendation:

- **Buy/Hold/Sell** verdict
- Confidence score
- Key reasons for the recommendation
- Risk factors to consider

### News Feed

Shows recent news articles related to the stock:

- Headlines with timestamps
- Source attribution
- Sentiment indicators (positive/negative/neutral)

## Running an Analysis

### Step 1: Enter a Stock Ticker

Type a valid stock ticker symbol into the search bar. Examples:

- `AAPL` - Apple Inc.
- `MSFT` - Microsoft Corporation
- `GOOGL` - Alphabet Inc.
- `TSLA` - Tesla Inc.

### Step 2: Wait for Analysis

The multi-agent system will:

1. Fetch current market data
2. Retrieve recent news articles
3. Analyze fundamentals
4. Evaluate technical indicators
5. Assess market sentiment

Analysis typically takes 15-45 seconds depending on data availability.

### Step 3: Review Results

The dashboard will populate with:

- A stock chart showing price history
- Agent status and intermediate findings
- Final investment recommendation
- Supporting news articles

## Understanding the Output

### Confidence Scores

Each recommendation includes a confidence score from 0-100%:

- **80-100%**: High confidence - strong signals align
- **60-79%**: Moderate confidence - mixed signals
- **Below 60%**: Low confidence - significant uncertainty

### Agent Perspectives

Multiple AI agents analyze different aspects:

| Agent              | Focus Area                                   |
| ------------------ | -------------------------------------------- |
| Fundamentals Agent | Financial statements, earnings, valuation    |
| Technical Agent    | Price patterns, momentum, support/resistance |
| Sentiment Agent    | News sentiment, social media, market mood    |
| Risk Agent         | Volatility, market conditions, sector risks  |

### Risk Factors

Every analysis includes potential risk factors:

- Market volatility
- Company-specific risks
- Sector headwinds
- Macroeconomic factors

## Tips for Best Results

### Use Valid Tickers

Ensure you're using the correct exchange ticker:

- US stocks typically use standard symbols (AAPL, MSFT)
- Include exchange prefix for international stocks if needed

### Consider Multiple Analyses

For important investment decisions:

- Run analysis at different times for varying market conditions
- Compare results across similar companies in the same sector

### Review News Context

The news feed provides important context:

- Recent events that may affect the stock
- Industry trends
- Regulatory changes

## API Access

For programmatic access, the backend exposes a REST API:

### Health Check

```bash
curl http://localhost:8000/health
```

### WebSocket Connection

For real-time analysis updates, connect to:

```
ws://localhost:8000/ws/analyze
```

## Keyboard Shortcuts

| Shortcut | Action                     |
| -------- | -------------------------- |
| `Enter`  | Submit ticker for analysis |
| `Esc`    | Clear input field          |

## Limitations

- Analysis is for informational purposes only
- Not financial advice - always do your own research
- Data may have delays (typically 15 minutes for free market data)
- Historical performance doesn't guarantee future results

## Getting Help

If you encounter issues:

1. Check the [Getting Started Guide](./getting-started.md) for setup issues
2. Review container logs: `make logs`
3. Ensure your API keys are correctly configured in `.env`
