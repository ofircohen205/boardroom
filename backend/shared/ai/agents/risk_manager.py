import re
from typing import Optional

import numpy as np

from backend.shared.ai.agents.base import get_llm_client
from backend.shared.ai.state.agent_state import (
    FundamentalReport,
    RiskAssessment,
    SentimentReport,
    TechnicalReport,
)


def calculate_var_95(price_history: list[dict]) -> float:
    """Calculate 95% parametric Value at Risk from price history."""
    if not price_history or len(price_history) < 2:
        return 0.0
    prices = np.array([p["close"] for p in price_history])
    log_returns = np.diff(np.log(prices))
    mean = np.mean(log_returns)
    std = np.std(log_returns)
    var = -(mean + (-1.645) * std)  # 95% parametric VaR
    return max(0.0, float(var))


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
        var_95 = calculate_var_95(technical["price_history"]) if technical else 0.0

        # Rule-based veto: sector overweight
        if portfolio_tech_weight > self.MAX_SECTOR_WEIGHT:
            return RiskAssessment(
                sector=sector,
                portfolio_sector_weight=portfolio_tech_weight,
                var_95=var_95,
                veto=True,
                veto_reason=f"Portfolio already {portfolio_tech_weight * 100:.0f}% in {sector}, exceeds {self.MAX_SECTOR_WEIGHT * 100:.0f}% limit",
            )

        # LLM-based risk assessment
        prompt = f"""As a risk manager, assess whether to VETO this trade for {ticker} ({sector}):

Portfolio {sector} weight: {portfolio_tech_weight * 100:.1f}%
Max allowed: {self.MAX_SECTOR_WEIGHT * 100:.0f}%
95% Value at Risk (daily): {var_95 * 100:.2f}%

Fundamental summary: {fundamental["summary"] if fundamental else "N/A"}
Sentiment: {sentiment["overall_sentiment"] if sentiment else "N/A"}
Technical trend: {technical["trend"].value if technical else "N/A"}

Consider:
1. Concentration risk
2. Fundamental red flags (high debt, negative growth)
3. Extreme sentiment (might indicate bubble or panic)
4. Technical overbought/oversold
5. Value at Risk level (high VaR indicates elevated downside risk)

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
            var_95=var_95,
            veto=veto,
            veto_reason=veto_reason,
        )
