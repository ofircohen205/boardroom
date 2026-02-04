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
