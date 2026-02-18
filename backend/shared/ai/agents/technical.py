from backend.shared.ai.agents.base import get_llm_client
from backend.shared.ai.state.agent_state import TechnicalReport
from backend.shared.ai.state.enums import Market
from backend.shared.ai.tools.market_data import get_market_data_client
from backend.shared.ai.tools.technical_indicators import (
    calculate_ma,
    calculate_rsi,
    calculate_trend,
)


class TechnicalAgent:
    def __init__(self):
        self.llm = get_llm_client()
        self.market_data = get_market_data_client()

    async def analyze(self, ticker: str, market: Market) -> TechnicalReport:
        stock_data = await self.market_data.get_stock_data(ticker, market)

        prices = [p["close"] for p in stock_data["price_history"]]
        current_price = stock_data["current_price"]

        ma_50 = (
            calculate_ma(prices, 50)
            if len(prices) >= 50
            else calculate_ma(prices, len(prices))
        )
        ma_200 = (
            calculate_ma(prices, 200)
            if len(prices) >= 200
            else calculate_ma(prices, len(prices))
        )
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
