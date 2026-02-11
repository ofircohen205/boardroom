import re
from typing import Optional

from backend.ai.agents.base import get_llm_client
from backend.ai.state.agent_state import (
    Decision,
    FundamentalReport,
    SentimentReport,
    TechnicalReport,
)
from backend.ai.state.enums import Action


class ChairpersonAgent:
    def __init__(self):
        self.llm = get_llm_client()

    async def decide(
        self,
        ticker: str,
        fundamental: Optional[FundamentalReport],
        sentiment: Optional[SentimentReport],
        technical: Optional[TechnicalReport],
    ) -> Decision:
        # Build prompt with available data
        available_reports = []

        if fundamental:
            available_reports.append(
                f"""FUNDAMENTAL ANALYSIS:
{fundamental["summary"]}
- P/E: {fundamental["pe_ratio"]}, Revenue Growth: {fundamental["revenue_growth"] * 100:.1f}%, D/E: {fundamental["debt_to_equity"]}"""
            )
        else:
            available_reports.append("FUNDAMENTAL ANALYSIS: [Data unavailable]")

        if sentiment:
            available_reports.append(
                f"""SENTIMENT ANALYSIS:
{sentiment["summary"]}
- Overall sentiment: {sentiment["overall_sentiment"]:.2f} (-1 to 1 scale)"""
            )
        else:
            available_reports.append("SENTIMENT ANALYSIS: [Data unavailable]")

        if technical:
            available_reports.append(
                f"""TECHNICAL ANALYSIS:
{technical["summary"]}
- Trend: {technical["trend"].value}, RSI: {technical["rsi"]:.1f}"""
            )
        else:
            available_reports.append("TECHNICAL ANALYSIS: [Data unavailable]")

        # Count available reports for confidence adjustment
        available_count = sum(
            1 for r in [fundamental, sentiment, technical] if r is not None
        )

        prompt = f"""As the Chairperson of the investment committee, make a final decision for {ticker}:

{chr(10).join(available_reports)}

NOTE: {available_count} of 3 analyst reports are available. Base your decision on the available data.

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

        # Adjust confidence based on data availability
        if available_count < 3:
            confidence *= 0.8  # Reduce confidence when data is incomplete
            if available_count == 1:
                confidence *= 0.8  # Further reduce if only 1 report available

        # Add note about missing data if any
        missing_reports = []
        if not fundamental:
            missing_reports.append("fundamental")
        if not sentiment:
            missing_reports.append("sentiment")
        if not technical:
            missing_reports.append("technical")

        if missing_reports:
            rationale = f"[Note: Decision made with limited data - missing {', '.join(missing_reports)} analysis] {rationale}"

        return Decision(
            action=action,
            confidence=min(1.0, max(0.0, confidence)),
            rationale=rationale,
        )
