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
