import asyncio
import uuid
from typing import AsyncGenerator

from backend.agents.fundamental import FundamentalAgent
from backend.agents.sentiment import SentimentAgent
from backend.agents.technical import TechnicalAgent
from backend.agents.risk_manager import RiskManagerAgent
from backend.agents.chairperson import ChairpersonAgent
from backend.state.agent_state import AgentState, ComparisonResult, StockRanking
from backend.state.enums import Market, AgentType, WSMessageType, AnalysisMode, Action
from backend.tools.relative_strength import calculate_relative_strength


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
        self,
        ticker: str,
        market: Market,
        portfolio_sector_weight: float = 0.0,
        analysis_mode: AnalysisMode = AnalysisMode.STANDARD
    ) -> AsyncGenerator[dict, None]:
        audit_id = str(uuid.uuid4())

        yield {"type": WSMessageType.ANALYSIS_STARTED, "agent": None, "data": {"ticker": ticker, "audit_id": audit_id, "mode": analysis_mode.value}}

        # Determine which agents to run based on mode
        agents_to_run = []
        if analysis_mode == AnalysisMode.QUICK:
            # Quick mode: Technical only
            agents_to_run = [AgentType.TECHNICAL]
        else:
            # Standard and Deep modes: All agents
            agents_to_run = [AgentType.FUNDAMENTAL, AgentType.SENTIMENT, AgentType.TECHNICAL]

        # Emit started events for agents that will run
        for agent_type in agents_to_run:
            yield {"type": WSMessageType.AGENT_STARTED, "agent": agent_type, "data": {}}

        # Run analysts in parallel, streaming completions as they finish
        completion_queue: asyncio.Queue[tuple[AgentType, dict | None, str | None]] = asyncio.Queue()

        async def _run_agent(agent_type: AgentType, coro):
            try:
                result = await coro
                await completion_queue.put((agent_type, result, None))
                return result
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                await completion_queue.put((agent_type, None, error_msg))
                return None

        # Create tasks only for agents to run
        tasks = []
        if AgentType.FUNDAMENTAL in agents_to_run:
            tasks.append(asyncio.create_task(_run_agent(AgentType.FUNDAMENTAL, self.fundamental.analyze(ticker, market))))
        if AgentType.SENTIMENT in agents_to_run:
            tasks.append(asyncio.create_task(_run_agent(AgentType.SENTIMENT, self.sentiment.analyze(ticker, market))))
        if AgentType.TECHNICAL in agents_to_run:
            tasks.append(asyncio.create_task(_run_agent(AgentType.TECHNICAL, self.technical.analyze(ticker, market))))

        results: dict[AgentType, dict | None] = {}
        errors: dict[AgentType, str] = {}

        # Collect results for agents that were run
        for _ in range(len(agents_to_run)):
            agent_type, result, error = await completion_queue.get()
            if error:
                errors[agent_type] = error
                results[agent_type] = None
                yield {"type": WSMessageType.AGENT_ERROR, "agent": agent_type, "data": {"error": error}}
            else:
                results[agent_type] = result
                yield {"type": WSMessageType.AGENT_COMPLETED, "agent": agent_type, "data": result}

        # Ensure no exceptions are lost
        await asyncio.gather(*tasks)

        # Set None for agents that were skipped
        if AgentType.FUNDAMENTAL not in agents_to_run:
            results[AgentType.FUNDAMENTAL] = None
        if AgentType.SENTIMENT not in agents_to_run:
            results[AgentType.SENTIMENT] = None
        if AgentType.TECHNICAL not in agents_to_run:
            results[AgentType.TECHNICAL] = None

        fundamental = results.get(AgentType.FUNDAMENTAL)
        sentiment = results.get(AgentType.SENTIMENT)
        technical = results.get(AgentType.TECHNICAL)

        # Check if we have enough data to continue
        successful_agents = sum(1 for r in [fundamental, sentiment, technical] if r is not None)
        if successful_agents == 0:
            # All analysts failed - cannot continue
            yield {
                "type": WSMessageType.ERROR,
                "agent": None,
                "data": {"error": "All analyst agents failed. Cannot proceed with analysis."}
            }
            return

        sector = fundamental.get("sector") if fundamental else "Unknown"

        # Risk - only if we have at least one successful agent
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.RISK, "data": {}}
        try:
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
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            yield {"type": WSMessageType.AGENT_ERROR, "agent": AgentType.RISK, "data": {"error": error_msg}}
            # Continue to chairperson even if risk assessment fails
            risk = None

        # Chairperson - proceed with whatever data we have
        yield {"type": WSMessageType.AGENT_STARTED, "agent": AgentType.CHAIRPERSON, "data": {}}
        try:
            decision = await self.chairperson.decide(ticker, fundamental, sentiment, technical)
            yield {"type": WSMessageType.DECISION, "agent": AgentType.CHAIRPERSON, "data": decision}
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            yield {"type": WSMessageType.AGENT_ERROR, "agent": AgentType.CHAIRPERSON, "data": {"error": error_msg}}


    async def run_comparison_streaming(
        self,
        tickers: list[str],
        market: Market,
        portfolio_sector_weight: float = 0.0
    ) -> AsyncGenerator[dict, None]:
        """Run comparative analysis on multiple stocks."""
        comparison_id = str(uuid.uuid4())

        yield {
            "type": WSMessageType.ANALYSIS_STARTED,
            "agent": None,
            "data": {"tickers": tickers, "comparison_id": comparison_id, "mode": "comparison"}
        }

        # Run analysis for each ticker in parallel
        all_results: dict[str, dict] = {}

        for ticker in tickers:
            all_results[ticker] = {
                "ticker": ticker,
                "fundamental": None,
                "sentiment": None,
                "technical": None,
                "risk": None,
                "decision": None,
            }

        # Emit started events for all tickers
        for ticker in tickers:
            for agent_type in [AgentType.FUNDAMENTAL, AgentType.SENTIMENT, AgentType.TECHNICAL]:
                yield {
                    "type": WSMessageType.AGENT_STARTED,
                    "agent": agent_type,
                    "data": {"ticker": ticker}
                }

        # Run all analyst agents for all tickers in parallel
        completion_queue: asyncio.Queue[tuple[str, AgentType, dict | None, str | None]] = asyncio.Queue()

        async def _run_ticker_agent(ticker: str, agent_type: AgentType, coro):
            try:
                result = await coro
                await completion_queue.put((ticker, agent_type, result, None))
                return result
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                await completion_queue.put((ticker, agent_type, None, error_msg))
                return None

        # Create tasks for all tickers × all agents
        tasks = []
        for ticker in tickers:
            tasks.append(asyncio.create_task(_run_ticker_agent(
                ticker, AgentType.FUNDAMENTAL, self.fundamental.analyze(ticker, market)
            )))
            tasks.append(asyncio.create_task(_run_ticker_agent(
                ticker, AgentType.SENTIMENT, self.sentiment.analyze(ticker, market)
            )))
            tasks.append(asyncio.create_task(_run_ticker_agent(
                ticker, AgentType.TECHNICAL, self.technical.analyze(ticker, market)
            )))

        # Collect results as they complete
        total_tasks = len(tickers) * 3
        for _ in range(total_tasks):
            ticker, agent_type, result, error = await completion_queue.get()

            if error:
                yield {
                    "type": WSMessageType.AGENT_ERROR,
                    "agent": agent_type,
                    "data": {"ticker": ticker, "error": error}
                }
            else:
                all_results[ticker][agent_type.value] = result
                yield {
                    "type": WSMessageType.AGENT_COMPLETED,
                    "agent": agent_type,
                    "data": {"ticker": ticker, **result}
                }

        await asyncio.gather(*tasks)

        # Run risk assessment and decision for each ticker
        for ticker in tickers:
            fundamental = all_results[ticker]["fundamental"]
            sentiment = all_results[ticker]["sentiment"]
            technical = all_results[ticker]["technical"]

            # Skip if all agents failed
            if not any([fundamental, sentiment, technical]):
                continue

            sector = fundamental.get("sector") if fundamental else "Unknown"

            # Risk assessment
            try:
                risk = await self.risk_manager.assess(
                    ticker=ticker,
                    sector=sector,
                    portfolio_tech_weight=portfolio_sector_weight,
                    fundamental=fundamental,
                    sentiment=sentiment,
                    technical=technical,
                )
                all_results[ticker]["risk"] = risk

                if risk["veto"]:
                    # Create HOLD decision for vetoed stocks
                    all_results[ticker]["decision"] = {
                        "action": Action.HOLD,
                        "confidence": 0.0,
                        "rationale": f"Risk Manager Veto: {risk['veto_reason']}"
                    }
                    continue

            except Exception:
                pass

            # Chairperson decision
            try:
                decision = await self.chairperson.decide(ticker, fundamental, sentiment, technical)
                all_results[ticker]["decision"] = decision
            except Exception:
                pass

        # Generate comparison and ranking
        comparison = await self._generate_comparison(tickers, all_results, market)

        yield {
            "type": WSMessageType.COMPARISON_RESULT,
            "agent": AgentType.CHAIRPERSON,
            "data": comparison
        }

    async def _generate_comparison(
        self,
        tickers: list[str],
        all_results: dict[str, dict],
        market: Market
    ) -> ComparisonResult:
        """Generate comparison summary and rankings."""
        # Build comparison prompt for LLM
        comparison_data = []
        for ticker in tickers:
            result = all_results[ticker]
            decision = result.get("decision")
            if decision:
                comparison_data.append({
                    "ticker": ticker,
                    "action": decision["action"],
                    "confidence": decision["confidence"],
                    "fundamental_summary": result.get("fundamental", {}).get("summary", "N/A"),
                    "sentiment_summary": result.get("sentiment", {}).get("summary", "N/A"),
                    "technical_summary": result.get("technical", {}).get("summary", "N/A"),
                })

        prompt = f"""Compare and rank these {len(tickers)} stocks:

"""
        for i, data in enumerate(comparison_data, 1):
            prompt += f"""
{i}. {data['ticker']}
   Recommendation: {data['action']} (confidence: {data['confidence']:.0%})
   Fundamental: {data['fundamental_summary']}
   Sentiment: {data['sentiment_summary']}
   Technical: {data['technical_summary']}
"""

        prompt += """
Provide:
1. A ranking (1 = best investment right now)
2. A score (0-100) for each stock
3. Brief rationale for the ranking
4. Overall comparison summary (2-3 sentences)
5. Which is the best pick overall

Format as:
RANKING:
1. TICKER - Score: XX - Rationale
2. TICKER - Score: XX - Rationale
...

BEST_PICK: TICKER
SUMMARY: Overall comparison analysis
"""

        response = await self.chairperson.llm.complete([{"role": "user", "content": prompt}])

        # Parse response (simplified - in production would use structured output)
        rankings = []
        best_pick = tickers[0] if tickers else ""
        summary = response

        # Extract best pick
        import re
        best_match = re.search(r"BEST_PICK:\s*(\w+)", response, re.IGNORECASE)
        if best_match:
            best_pick = best_match.group(1)

        # Create rankings
        for i, ticker in enumerate(tickers, 1):
            decision = all_results[ticker].get("decision")
            if decision:
                rankings.append(StockRanking(
                    ticker=ticker,
                    rank=i,
                    score=decision["confidence"] * 100,
                    rationale=f"Ranked #{i} - {decision['rationale'][:100]}...",
                    decision=decision
                ))

        # Calculate relative strength metrics
        price_histories = {
            ticker: all_results[ticker].get("technical", {}).get("price_history", [])
            for ticker in tickers
            if all_results[ticker].get("technical")
        }

        fundamentals = {
            ticker: all_results[ticker].get("fundamental")
            for ticker in tickers
        }

        relative_strength = calculate_relative_strength(price_histories, fundamentals)

        return ComparisonResult(
            tickers=tickers,
            rankings=sorted(rankings, key=lambda x: x["rank"]),
            best_pick=best_pick,
            comparison_summary=summary,
            relative_strength=relative_strength,
            price_histories=price_histories,
            stock_data=all_results
        )


def create_boardroom_graph() -> BoardroomGraph:
    return BoardroomGraph()
