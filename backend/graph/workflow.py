import uuid
from typing import AsyncGenerator

from backend.agents.fundamental import FundamentalAgent
from backend.agents.sentiment import SentimentAgent
from backend.agents.technical import TechnicalAgent
from backend.agents.risk_manager import RiskManagerAgent
from backend.agents.chairperson import ChairpersonAgent
from backend.state.agent_state import AgentState
from backend.state.enums import Market, AgentType, WSMessageType


class BoardroomGraph:
    def __init__(self):
        self.fundamental = FundamentalAgent()
        self.sentiment = SentimentAgent()
        self.technical = TechnicalAgent()
        self.risk_manager = RiskManagerAgent()
        self.chairperson = ChairpersonAgent()

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

        # Run analysts in parallel (simulated)
        state["fundamental_report"] = await self.fundamental.analyze(ticker, market)
        state["sentiment_report"] = await self.sentiment.analyze(ticker, market)
        state["technical_report"] = await self.technical.analyze(ticker, market)

        # Get sector from fundamental report
        sector = "Technology"  # Default, would come from market data

        # Risk assessment
        state["risk_assessment"] = await self.risk_manager.assess(
            ticker=ticker,
            sector=sector,
            portfolio_tech_weight=portfolio_sector_weight,
            fundamental=state["fundamental_report"],
            sentiment=state["sentiment_report"],
            technical=state["technical_report"],
        )

        # If vetoed, stop here
        if state["risk_assessment"]["veto"]:
            return state

        # Chairperson decision
        state["final_decision"] = await self.chairperson.decide(
            ticker=ticker,
            fundamental=state["fundamental_report"],
            sentiment=state["sentiment_report"],
            technical=state["technical_report"],
        )

        return state

    async def run_streaming(
        self, ticker: str, market: Market, portfolio_sector_weight: float = 0.0
    ) -> AsyncGenerator[dict, None]:
        audit_id = str(uuid.uuid4())

        yield {"type": WSMessageType.ANALYSIS_STARTED, "agent": None, "data": {"ticker": ticker, "audit_id": audit_id}}

        # Fundamental
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.FUNDAMENTAL, "data": {}}
        fundamental = await self.fundamental.analyze(ticker, market)
        yield {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.FUNDAMENTAL, "data": fundamental}

        # Sentiment
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.SENTIMENT, "data": {}}
        sentiment = await self.sentiment.analyze(ticker, market)
        yield {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.SENTIMENT, "data": sentiment}

        # Technical
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.TECHNICAL, "data": {}}
        technical = await self.technical.analyze(ticker, market)
        yield {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.TECHNICAL, "data": technical}

        # Risk
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.RISK, "data": {}}
        risk = await self.risk_manager.assess(
            ticker=ticker,
            sector="Technology",
            portfolio_tech_weight=portfolio_sector_weight,
            fundamental=fundamental,
            sentiment=sentiment,
            technical=technical,
        )
        yield {"type": WSMessageType.AGENT_COMPLETED, "agent": AgentType.RISK, "data": risk}

        if risk["veto"]:
            yield {"type": WSMessageType.VETO, "agent": AgentType.RISK, "data": {"reason": risk["veto_reason"]}}
            return

        # Chairperson
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.CHAIRPERSON, "data": {}}
        decision = await self.chairperson.decide(ticker, fundamental, sentiment, technical)
        yield {"type": WSMessageType.DECISION, "agent": AgentType.CHAIRPERSON, "data": decision}


def create_boardroom_graph() -> BoardroomGraph:
    return BoardroomGraph()
