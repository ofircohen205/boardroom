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
