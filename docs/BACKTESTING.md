# Backtesting & Paper Trading Guide

## Overview

Phase 5 introduces **backtesting**, **strategy customization**, and **paper trading** to the Boardroom platform. These features allow you to:

1. **Test trading strategies on historical data** - Validate how the multi-agent system would have performed in the past
2. **Customize agent weights** - Create custom strategies by adjusting the influence of each agent
3. **Practice with virtual money** - Execute simulated trades in a risk-free environment

## Table of Contents

- [Strategy Builder](#strategy-builder)
- [Backtesting](#backtesting)
- [Paper Trading](#paper-trading)
- [Important Disclaimers](#important-disclaimers)
- [API Reference](#api-reference)

---

## Strategy Builder

### Creating a Strategy

Strategies define how the three analyst agents (Fundamental, Technical, Sentiment) are weighted when making trading decisions.

**Web UI:**
1. Navigate to `/strategies`
2. Click "Create New Strategy"
3. Adjust agent weight sliders (must sum to 1.0):
   - **Fundamental:** Yahoo Finance data (P/E ratio, revenue growth, profit margins, debt)
   - **Technical:** Price action indicators (moving averages, RSI, trend direction)
   - **Sentiment:** Price momentum analysis (5-day return as proxy for market sentiment)
4. Optionally add risk limits (stop loss, take profit percentages)
5. Save your strategy

**API:**
```bash
curl -X POST http://localhost:8000/api/strategies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conservative Value",
    "description": "Heavy fundamental, light technical",
    "weights": {
      "fundamental": 0.6,
      "technical": 0.3,
      "sentiment": 0.1
    }
  }'
```

### Agent Weight Guidelines

**Fundamental-Heavy (0.5-0.7):**
- Best for: Long-term investing, value stocks
- Focuses on: P/E ratios, revenue growth, profit margins, debt levels
- Risk: May miss short-term opportunities

**Technical-Heavy (0.5-0.7):**
- Best for: Active trading, momentum plays
- Focuses on: Moving averages, RSI, price trends
- Risk: May ignore underlying company health

**Balanced (0.33/0.33/0.34):**
- Best for: General-purpose analysis
- Considers all factors equally
- Risk: May be indecisive in mixed signals

---

## Backtesting

### Running a Backtest

Backtesting simulates how your strategy would have performed on historical data.

**Configuration Parameters:**

| Parameter | Description | Example |
|-----------|-------------|---------|
| `ticker` | Stock symbol to test | `AAPL` |
| `strategy_id` | ID of saved strategy | `uuid-here` |
| `start_date` | Backtest start date | `2023-01-01` |
| `end_date` | Backtest end date | `2023-12-31` |
| `initial_capital` | Starting cash ($) | `10000` |
| `check_frequency` | Daily or weekly checks | `daily` |
| `position_size_pct` | % of capital per trade | `0.5` (50%) |
| `stop_loss_pct` | Auto-sell on loss % | `0.10` (10%) |
| `take_profit_pct` | Auto-sell on gain % | `0.20` (20%) |

**Web UI:**
1. Navigate to `/backtest`
2. Fill out configuration form
3. Click "Run Backtest"
4. Watch real-time progress bar as historical data is processed
5. View results: equity curve, trade log, performance metrics

**WebSocket API:**
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/backtest?token=${token}`);

ws.onopen = () => {
  ws.send(JSON.stringify({
    ticker: "NVDA",
    strategy_id: "your-strategy-id",
    start_date: "2023-01-01",
    end_date: "2023-12-31",
    initial_capital: 10000,
    check_frequency: "daily",
    position_size_pct: 0.5,
    stop_loss_pct: 0.10,
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // message.type: backtest_started | backtest_progress | backtest_completed | backtest_error
};
```

### Understanding Results

**Metrics Explained:**

- **Total Return:** Overall % gain/loss (e.g., +15.5% = turned $10k into $11,550)
- **Annualized Return:** Return extrapolated to one year (useful for comparing different time periods)
- **Sharpe Ratio:** Risk-adjusted return (> 1.0 is good, > 2.0 is excellent)
- **Max Drawdown:** Largest peak-to-trough decline (e.g., -12% = worst drop from any high point)
- **Win Rate:** % of profitable trades (> 50% means more winners than losers)
- **Buy & Hold Return:** Passive strategy return for comparison (what if you just bought and held?)

**Interpreting Results:**

✅ **Good Backtest:**
- Total return > Buy & Hold
- Sharpe ratio > 1.0
- Max drawdown < -20%
- Win rate > 50%

⚠️ **Caution Flags:**
- Very high win rate (> 90%) may indicate overfitting
- Very low max drawdown (< -5%) may lack sufficient testing periods
- Total return << Buy & Hold means strategy underperformed passive investing

---

## Paper Trading

### Creating a Paper Account

Paper trading lets you execute virtual trades based on real-time prices.

**Web UI:**
1. Navigate to `/paper-trading`
2. Click "Create Account"
3. Enter account name and starting balance
4. Select a strategy (trades can be manual or strategy-based)

**API:**
```bash
curl -X POST http://localhost:8000/api/paper/accounts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Practice Account",
    "initial_balance": 10000.00,
    "strategy_id": "your-strategy-id"
  }'
```

### Executing Trades

**Manual Trades (Web UI):**
1. Select your paper account
2. Click "Execute Trade"
3. Enter ticker, action (BUY/SELL), quantity
4. Confirm trade (uses current market price)

**Manual Trades (API):**
```bash
curl -X POST http://localhost:8000/api/paper/accounts/{account_id}/trades \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "TSLA",
    "action": "BUY",
    "quantity": 5
  }'
```

### Monitoring Performance

**Account Overview:**
- Total Value = Cash + (Positions × Current Prices)
- Unrealized P&L = (Current Price - Entry Price) × Quantity
- Total Return % = (Total Value - Initial Balance) / Initial Balance

**Position Tracking:**
- Each position shows: ticker, quantity, entry price, current price, P&L, return %
- Real-time updates based on latest market prices

---

## Important Disclaimers

### ⚠️ Backtest Limitations

**Please read carefully before making any investment decisions:**

#### 1. **Simplified Scoring - Not Live AI Analysis**

Backtests use **rules-based scoring**, not the full LLM-powered multi-agent system you see in live analysis.

- **Fundamental score:** Based on P/E ratio, revenue growth, profit margins, debt ratios
- **Technical score:** Moving averages, RSI, price trends
- **Sentiment score:** Price momentum (5-day returns) - **NOT real news/social media analysis**

**What this means:** Backtest results are approximations. The live system analyzes actual news articles, earnings calls, and social sentiment. Historical backtests cannot replay these data sources.

#### 2. **Historical Sentiment Data Unavailable**

Real sentiment analysis uses:
- Recent news articles (via Exa search)
- Social media mentions
- Analyst reports

**In backtests:** We use price momentum as a proxy. This is less accurate than real-time sentiment analysis.

#### 3. **Look-Ahead Bias**

Technical indicators like moving averages need a "warmup period":
- MA50 (50-day moving average) requires 50 days of prior data
- Early trades in a backtest may use incomplete indicators

**Impact:** First month of backtest may have inaccurate signals.

#### 4. **Survivorship Bias**

Backtests only test stocks that **still exist today**.

- Delisted companies (bankruptcies, acquisitions) are not included
- This makes historical results appear better than they would have been in real-time

#### 5. **No Slippage or Commissions**

Backtests assume:
- Perfect execution at closing prices
- No bid-ask spreads
- No transaction fees

**Real trading:** Has costs (commissions, spreads, slippage) that reduce returns.

#### 6. **Past Performance ≠ Future Results**

**This is critical:** Historical performance is for **educational purposes only**.

- Markets change
- Strategies that worked in the past may not work in the future
- Economic conditions, regulations, and market structure evolve

**Do not** make investment decisions based solely on backtest results.

### ⚠️ Paper Trading Limitations

Paper trading uses **current market prices** but does not account for:

- Order execution delays
- Liquidity constraints (can you actually buy/sell that quantity?)
- Market impact (large orders move prices)
- Emotional factors (real money feels different)

**Paper trading is practice, not prediction.** Real trading performance may differ significantly.

---

## Best Practices

### For Backtesting

1. **Test multiple time periods** - A strategy that works in 2023 may fail in 2024
2. **Compare to buy-and-hold** - If your strategy underperforms passive investing, reconsider it
3. **Check max drawdown** - Can you tolerate a -30% decline?
4. **Avoid overfitting** - Don't optimize until results look perfect (won't work in real markets)
5. **Use realistic position sizes** - 100% allocation per trade is unrealistic

### For Paper Trading

1. **Start small** - Practice position sizing and risk management
2. **Track why you make trades** - Build a trading journal
3. **Test your emotional reactions** - How do you feel when positions move against you?
4. **Experiment with strategies** - Try different agent weights and see what fits your style
5. **Don't skip paper trading** - Moving from backtest → live trading skips crucial learning

---

## API Reference

### Strategy Endpoints

```bash
# Create strategy
POST /api/strategies
Body: { name, description, weights: {fundamental, technical, sentiment} }

# List strategies
GET /api/strategies

# Get strategy details
GET /api/strategies/{id}

# Update strategy
PUT /api/strategies/{id}
Body: { name?, description?, weights? }

# Delete strategy
DELETE /api/strategies/{id}
```

### Backtest Endpoints

```bash
# Run backtest (WebSocket)
WS /ws/backtest?token={jwt_token}
Send: BacktestConfig
Receive: backtest_started | backtest_progress | backtest_completed | backtest_error

# List past backtest results
GET /api/backtest/results

# Get specific backtest result
GET /api/backtest/results/{id}
```

### Paper Trading Endpoints

```bash
# Create account
POST /api/paper/accounts
Body: { name, initial_balance, strategy_id }

# List accounts
GET /api/paper/accounts

# Get account details
GET /api/paper/accounts/{id}

# Execute trade
POST /api/paper/accounts/{id}/trades
Body: { ticker, action: "BUY"|"SELL", quantity }

# Get trade history
GET /api/paper/accounts/{id}/trades

# Get performance metrics
GET /api/paper/accounts/{id}/performance
```

---

## Troubleshooting

### "Historical data not found"

**Solution:** The system automatically fetches historical data from Yahoo Finance on first backtest. If data is unavailable, the ticker may not have sufficient history or may be delisted.

### "Backtest taking too long"

**Solution:**
- Use weekly frequency instead of daily for long time periods
- Reduce date range (max 5 years recommended)
- Check your API rate limits (Yahoo Finance has restrictions)

### "Paper trade failed - insufficient funds"

**Solution:** Check your account cash balance. You cannot buy more than your available cash.

### "Paper trade failed - insufficient shares"

**Solution:** You're trying to sell more shares than you own. Check your positions.

---

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/ofircohen205/boardroom/issues
- Documentation: https://github.com/ofircohen205/boardroom/tree/main/docs

**Remember:** Backtesting and paper trading are learning tools, not guarantees of future performance. Always do your own research and consult with a financial advisor before making real investment decisions.
