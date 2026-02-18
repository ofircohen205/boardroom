import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from backend.shared.ai.state.enums import Action, AgentType, Market, WSMessageType
from backend.shared.ai.workflow import BoardroomGraph, create_boardroom_graph


@pytest.mark.asyncio
async def test_graph_creation():
    graph = create_boardroom_graph()
    assert graph is not None


def _make_mocks():
    """Return patched agent mocks for all 5 agents."""
    fund_report = {
        "revenue_growth": 0.15,
        "pe_ratio": 20,
        "debt_to_equity": 0.5,
        "market_cap": 1000000000,
        "sector": "Technology",
        "summary": "Good",
    }
    sent_report = {
        "overall_sentiment": 0.7,
        "news_items": [],
        "social_mentions": [],
        "summary": "Positive",
    }
    tech_report = {
        "current_price": 100,
        "ma_50": 95,
        "ma_200": 90,
        "rsi": 55,
        "trend": "bullish",
        "price_history": [{"close": 90 + i} for i in range(30)],
        "summary": "Bullish",
    }
    risk_report = {
        "sector": "Technology",
        "portfolio_sector_weight": 0.1,
        "var_95": 0.02,
        "veto": False,
        "veto_reason": None,
    }
    decision = {"action": Action.BUY, "confidence": 0.8, "rationale": "Strong buy"}

    return fund_report, sent_report, tech_report, risk_report, decision


@pytest.mark.asyncio
async def test_graph_run_no_veto():
    fund_report, sent_report, tech_report, risk_report, decision = _make_mocks()

    with (
        patch("backend.shared.ai.workflow.FundamentalAgent") as mock_fund,
        patch("backend.shared.ai.workflow.SentimentAgent") as mock_sent,
        patch("backend.shared.ai.workflow.TechnicalAgent") as mock_tech,
        patch("backend.shared.ai.workflow.RiskManagerAgent") as mock_risk,
        patch("backend.shared.ai.workflow.ChairpersonAgent") as mock_chair,
    ):
        mock_fund.return_value.analyze = AsyncMock(return_value=fund_report)
        mock_sent.return_value.analyze = AsyncMock(return_value=sent_report)
        mock_tech.return_value.analyze = AsyncMock(return_value=tech_report)
        mock_risk.return_value.assess = AsyncMock(return_value=risk_report)
        mock_chair.return_value.decide = AsyncMock(return_value=decision)

        boardroom = BoardroomGraph()
        result = await boardroom.run("AAPL", Market.US)

        assert result["final_decision"] is not None
        assert result["final_decision"]["action"] == Action.BUY
        assert result["fundamental_report"]["sector"] == "Technology"


@pytest.mark.asyncio
async def test_graph_run_veto():
    fund_report, sent_report, tech_report, _, _ = _make_mocks()
    veto_report = {
        "sector": "Technology",
        "portfolio_sector_weight": 0.4,
        "var_95": 0.05,
        "veto": True,
        "veto_reason": "Portfolio already 40% in Technology",
    }

    with (
        patch("backend.shared.ai.workflow.FundamentalAgent") as mock_fund,
        patch("backend.shared.ai.workflow.SentimentAgent") as mock_sent,
        patch("backend.shared.ai.workflow.TechnicalAgent") as mock_tech,
        patch("backend.shared.ai.workflow.RiskManagerAgent") as mock_risk,
        patch("backend.shared.ai.workflow.ChairpersonAgent") as mock_chair,
    ):
        mock_fund.return_value.analyze = AsyncMock(return_value=fund_report)
        mock_sent.return_value.analyze = AsyncMock(return_value=sent_report)
        mock_tech.return_value.analyze = AsyncMock(return_value=tech_report)
        mock_risk.return_value.assess = AsyncMock(return_value=veto_report)
        mock_chair.return_value.decide = AsyncMock()

        boardroom = BoardroomGraph()
        result = await boardroom.run("AAPL", Market.US)

        assert result["risk_assessment"]["veto"] is True
        assert result["final_decision"] is None
        mock_chair.return_value.decide.assert_not_called()


@pytest.mark.asyncio
async def test_parallel_execution_timing():
    """Verify that analyst agents actually run in parallel."""
    delay = 0.1

    async def slow_analyze(ticker, market):
        await asyncio.sleep(delay)
        return {
            "revenue_growth": 0.1,
            "pe_ratio": 15,
            "debt_to_equity": 0.3,
            "market_cap": 500000000,
            "sector": "Tech",
            "summary": "OK",
        }

    async def slow_sentiment(ticker, market):
        await asyncio.sleep(delay)
        return {
            "overall_sentiment": 0.5,
            "news_items": [],
            "social_mentions": [],
            "summary": "Neutral",
        }

    async def slow_technical(ticker, market):
        await asyncio.sleep(delay)
        return {
            "current_price": 100,
            "ma_50": 95,
            "ma_200": 90,
            "rsi": 50,
            "trend": "neutral",
            "price_history": [{"close": 100}],
            "summary": "Flat",
        }

    with (
        patch("backend.shared.ai.workflow.FundamentalAgent") as mock_fund,
        patch("backend.shared.ai.workflow.SentimentAgent") as mock_sent,
        patch("backend.shared.ai.workflow.TechnicalAgent") as mock_tech,
        patch("backend.shared.ai.workflow.RiskManagerAgent") as mock_risk,
        patch("backend.shared.ai.workflow.ChairpersonAgent") as mock_chair,
    ):
        mock_fund.return_value.analyze = slow_analyze
        mock_sent.return_value.analyze = slow_sentiment
        mock_tech.return_value.analyze = slow_technical
        mock_risk.return_value.assess = AsyncMock(
            return_value={
                "sector": "Tech",
                "portfolio_sector_weight": 0.1,
                "var_95": 0.01,
                "veto": False,
                "veto_reason": None,
            }
        )
        mock_chair.return_value.decide = AsyncMock(
            return_value={
                "action": Action.HOLD,
                "confidence": 0.5,
                "rationale": "Neutral",
            }
        )

        boardroom = BoardroomGraph()
        start = time.monotonic()
        await boardroom.run("AAPL", Market.US)
        elapsed = time.monotonic() - start

        # If sequential, would take ~0.3s. Parallel should be ~0.1s.
        assert elapsed < 0.25, (
            f"Expected parallel execution (<0.25s), took {elapsed:.2f}s"
        )


@pytest.mark.asyncio
async def test_streaming_event_order():
    """Verify streaming yields correct event types in order."""
    fund_report, sent_report, tech_report, risk_report, decision = _make_mocks()

    with (
        patch("backend.shared.ai.workflow.FundamentalAgent") as mock_fund,
        patch("backend.shared.ai.workflow.SentimentAgent") as mock_sent,
        patch("backend.shared.ai.workflow.TechnicalAgent") as mock_tech,
        patch("backend.shared.ai.workflow.RiskManagerAgent") as mock_risk,
        patch("backend.shared.ai.workflow.ChairpersonAgent") as mock_chair,
    ):
        mock_fund.return_value.analyze = AsyncMock(return_value=fund_report)
        mock_sent.return_value.analyze = AsyncMock(return_value=sent_report)
        mock_tech.return_value.analyze = AsyncMock(return_value=tech_report)
        mock_risk.return_value.assess = AsyncMock(return_value=risk_report)
        mock_chair.return_value.decide = AsyncMock(return_value=decision)

        boardroom = BoardroomGraph()
        events = []
        async for event in boardroom.run_streaming("AAPL", Market.US):
            events.append(event)

        event_types = [e["type"] for e in events]

        # First event: analysis started
        assert event_types[0] == WSMessageType.ANALYSIS_STARTED

        # Next 3: all analyst agents started
        started = event_types[1:4]
        assert all(t == WSMessageType.AGENT_STARTED for t in started)
        started_agents = {events[i]["agent"] for i in range(1, 4)}
        assert started_agents == {
            AgentType.FUNDAMENTAL,
            AgentType.SENTIMENT,
            AgentType.TECHNICAL,
        }

        # Next 3: all analyst agents completed
        completed = event_types[4:7]
        assert all(t == WSMessageType.AGENT_COMPLETED for t in completed)

        # Then risk started + completed
        assert event_types[7] == WSMessageType.AGENT_STARTED
        assert events[7]["agent"] == AgentType.RISK
        assert event_types[8] == WSMessageType.AGENT_COMPLETED
        assert events[8]["agent"] == AgentType.RISK

        # Then chairperson started + decision
        assert event_types[9] == WSMessageType.AGENT_STARTED
        assert events[9]["agent"] == AgentType.CHAIRPERSON
        assert event_types[10] == WSMessageType.DECISION


@pytest.mark.asyncio
async def test_streaming_veto_stops_early():
    """Verify streaming stops after veto (no chairperson)."""
    fund_report, sent_report, tech_report, _, _ = _make_mocks()
    veto_report = {
        "sector": "Technology",
        "portfolio_sector_weight": 0.4,
        "var_95": 0.05,
        "veto": True,
        "veto_reason": "Over sector limit",
    }

    with (
        patch("backend.shared.ai.workflow.FundamentalAgent") as mock_fund,
        patch("backend.shared.ai.workflow.SentimentAgent") as mock_sent,
        patch("backend.shared.ai.workflow.TechnicalAgent") as mock_tech,
        patch("backend.shared.ai.workflow.RiskManagerAgent") as mock_risk,
        patch("backend.shared.ai.workflow.ChairpersonAgent") as mock_chair,
    ):
        mock_fund.return_value.analyze = AsyncMock(return_value=fund_report)
        mock_sent.return_value.analyze = AsyncMock(return_value=sent_report)
        mock_tech.return_value.analyze = AsyncMock(return_value=tech_report)
        mock_risk.return_value.assess = AsyncMock(return_value=veto_report)
        mock_chair.return_value.decide = AsyncMock()

        boardroom = BoardroomGraph()
        events = []
        async for event in boardroom.run_streaming("AAPL", Market.US):
            events.append(event)

        event_types = [e["type"] for e in events]
        assert WSMessageType.VETO in event_types
        assert WSMessageType.DECISION not in event_types
        mock_chair.return_value.decide.assert_not_called()


@pytest.mark.asyncio
async def test_sector_from_fundamental_report():
    """Verify sector is passed from fundamental report to risk manager."""
    fund_report, sent_report, tech_report, risk_report, decision = _make_mocks()
    fund_report["sector"] = "Healthcare"

    with (
        patch("backend.shared.ai.workflow.FundamentalAgent") as mock_fund,
        patch("backend.shared.ai.workflow.SentimentAgent") as mock_sent,
        patch("backend.shared.ai.workflow.TechnicalAgent") as mock_tech,
        patch("backend.shared.ai.workflow.RiskManagerAgent") as mock_risk,
        patch("backend.shared.ai.workflow.ChairpersonAgent") as mock_chair,
    ):
        mock_fund.return_value.analyze = AsyncMock(return_value=fund_report)
        mock_sent.return_value.analyze = AsyncMock(return_value=sent_report)
        mock_tech.return_value.analyze = AsyncMock(return_value=tech_report)
        mock_risk.return_value.assess = AsyncMock(return_value=risk_report)
        mock_chair.return_value.decide = AsyncMock(return_value=decision)

        boardroom = BoardroomGraph()
        await boardroom.run("AAPL", Market.US)

        # Verify risk manager was called with "Healthcare" sector
        call_kwargs = mock_risk.return_value.assess.call_args
        assert call_kwargs.kwargs["sector"] == "Healthcare"
