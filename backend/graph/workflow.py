import asyncio
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

        # Run analysts in parallel
        fundamental, sentiment, technical = await asyncio.gather(
            self.fundamental.analyze(ticker, market),
            self.sentiment.analyze(ticker, market),
            self.technical.analyze(ticker, market),
        )
        state["fundamental_report"] = fundamental
        state["sentiment_report"] = sentiment
        state["technical_report"] = technical

        sector = fundamental.get("sector") or "Unknown"

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

        # Emit all 3 analyst started events
        for agent_type in [AgentType.FUNDAMENTAL, AgentType.SENTIMENT, AgentType.TECHNICAL]:
            yield {"type": WSMessageType.AGENT_STARTED, "agent": agent_type, "data": {}}

        # Run analysts in parallel, streaming completions as they finish
        completion_queue: asyncio.Queue[tuple[AgentType, dict]] = asyncio.Queue()

        async def _run_agent(agent_type: AgentType, coro):
            result = await coro
            await completion_queue.put((agent_type, result))
            return result

        tasks = [
            asyncio.create_task(_run_agent(AgentType.FUNDAMENTAL, self.fundamental.analyze(ticker, market))),
            asyncio.create_task(_run_agent(AgentType.SENTIMENT, self.sentiment.analyze(ticker, market))),
            asyncio.create_task(_run_agent(AgentType.TECHNICAL, self.technical.analyze(ticker, market))),
        ]

        results: dict[AgentType, dict] = {}
        for _ in range(3):
            agent_type, result = await completion_queue.get()
            results[agent_type] = result
            yield {"type": WSMessageType.AGENT_COMPLETED, "agent": agent_type, "data": result}

        # Ensure no exceptions are lost
        await asyncio.gather(*tasks)

        fundamental = results[AgentType.FUNDAMENTAL]
        sentiment = results[AgentType.SENTIMENT]
        technical = results[AgentType.TECHNICAL]

        sector = fundamental.get("sector") or "Unknown"

        # Risk
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.RISK, "data": {}}
        risk = await self.risk_manager.assess(
            ticker=ticker,
            sector=sector,
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
