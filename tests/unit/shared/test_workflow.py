"""Unit tests for backend.shared.ai.workflow (BoardroomGraph)."""

from unittest.mock import AsyncMock, patch

import pytest

from backend.shared.ai.state.enums import AgentType, AnalysisMode, Market, WSMessageType
from backend.shared.ai.workflow import BoardroomGraph, create_boardroom_graph


def _make_fundamental_report(sector="Technology"):
    return {"sector": sector, "summary": "Strong fundamentals", "score": 75}


def _make_sentiment_report():
    return {"summary": "Positive sentiment", "score": 65}


def _make_technical_report(**kwargs):
    return {"summary": "Bullish trend", "score": 70, "price_history": [], **kwargs}


def _make_risk_assessment(veto=False, veto_reason=""):
    return {"veto": veto, "veto_reason": veto_reason, "score": 80}


def _make_decision(action="BUY", confidence=0.85):
    return {
        "action": action,
        "confidence": confidence,
        "rationale": "Strong buy signal",
    }


class TestBoardroomGraphInit:
    def test_init_creates_all_agents(self):
        with (
            patch("backend.shared.ai.workflow.FundamentalAgent"),
            patch("backend.shared.ai.workflow.SentimentAgent"),
            patch("backend.shared.ai.workflow.TechnicalAgent"),
            patch("backend.shared.ai.workflow.RiskManagerAgent"),
            patch("backend.shared.ai.workflow.ChairpersonAgent"),
        ):
            graph = BoardroomGraph()
        assert graph.fundamental is not None
        assert graph.sentiment is not None
        assert graph.technical is not None
        assert graph.risk_manager is not None
        assert graph.chairperson is not None


class TestBoardroomGraphRun:
    @pytest.mark.asyncio
    async def test_run_success_returns_state_with_decision(self):
        with (
            patch("backend.shared.ai.workflow.FundamentalAgent"),
            patch("backend.shared.ai.workflow.SentimentAgent"),
            patch("backend.shared.ai.workflow.TechnicalAgent"),
            patch("backend.shared.ai.workflow.RiskManagerAgent"),
            patch("backend.shared.ai.workflow.ChairpersonAgent"),
        ):
            graph = BoardroomGraph()

        graph.fundamental.analyze = AsyncMock(return_value=_make_fundamental_report())
        graph.sentiment.analyze = AsyncMock(return_value=_make_sentiment_report())
        graph.technical.analyze = AsyncMock(return_value=_make_technical_report())
        graph.risk_manager.assess = AsyncMock(return_value=_make_risk_assessment())
        graph.chairperson.decide = AsyncMock(return_value=_make_decision())

        state = await graph.run("AAPL", Market.US)

        assert state["ticker"] == "AAPL"
        assert state["market"] == Market.US
        assert state["fundamental_report"] is not None
        assert state["final_decision"] is not None
        assert state["audit_id"] != ""

    @pytest.mark.asyncio
    async def test_run_veto_stops_before_chairperson(self):
        with (
            patch("backend.shared.ai.workflow.FundamentalAgent"),
            patch("backend.shared.ai.workflow.SentimentAgent"),
            patch("backend.shared.ai.workflow.TechnicalAgent"),
            patch("backend.shared.ai.workflow.RiskManagerAgent"),
            patch("backend.shared.ai.workflow.ChairpersonAgent"),
        ):
            graph = BoardroomGraph()

        graph.fundamental.analyze = AsyncMock(return_value=_make_fundamental_report())
        graph.sentiment.analyze = AsyncMock(return_value=_make_sentiment_report())
        graph.technical.analyze = AsyncMock(return_value=_make_technical_report())
        graph.risk_manager.assess = AsyncMock(
            return_value=_make_risk_assessment(veto=True, veto_reason="Overexposed")
        )
        graph.chairperson.decide = AsyncMock(return_value=_make_decision())

        state = await graph.run("AAPL", Market.US)

        assert state["final_decision"] is None
        graph.chairperson.decide.assert_not_called()


class TestBoardroomGraphRunStreaming:
    async def _collect(
        self, graph, ticker, market, mode=AnalysisMode.STANDARD, weight=0.0
    ):
        messages = []
        async for msg in graph.run_streaming(ticker, market, weight, mode):
            messages.append(msg)
        return messages

    def _make_graph(self):
        with (
            patch("backend.shared.ai.workflow.FundamentalAgent"),
            patch("backend.shared.ai.workflow.SentimentAgent"),
            patch("backend.shared.ai.workflow.TechnicalAgent"),
            patch("backend.shared.ai.workflow.RiskManagerAgent"),
            patch("backend.shared.ai.workflow.ChairpersonAgent"),
        ):
            return BoardroomGraph()

    @pytest.mark.asyncio
    async def test_streaming_standard_mode_emits_started(self):
        graph = self._make_graph()
        graph.fundamental.analyze = AsyncMock(return_value=_make_fundamental_report())
        graph.sentiment.analyze = AsyncMock(return_value=_make_sentiment_report())
        graph.technical.analyze = AsyncMock(return_value=_make_technical_report())
        graph.risk_manager.assess = AsyncMock(return_value=_make_risk_assessment())
        graph.chairperson.decide = AsyncMock(return_value=_make_decision())

        messages = await self._collect(graph, "AAPL", Market.US)

        types = [m["type"] for m in messages]
        assert WSMessageType.ANALYSIS_STARTED in types
        assert WSMessageType.AGENT_STARTED in types
        assert WSMessageType.DECISION in types

    @pytest.mark.asyncio
    async def test_streaming_quick_mode_only_runs_technical(self):
        graph = self._make_graph()
        graph.technical.analyze = AsyncMock(return_value=_make_technical_report())
        graph.risk_manager.assess = AsyncMock(return_value=_make_risk_assessment())
        graph.chairperson.decide = AsyncMock(return_value=_make_decision())

        messages = await self._collect(
            graph, "AAPL", Market.US, mode=AnalysisMode.QUICK
        )

        # fundamental and sentiment should not be called in quick mode
        graph.fundamental.analyze.assert_not_called()
        graph.sentiment.analyze.assert_not_called()
        started = [
            m["agent"] for m in messages if m["type"] == WSMessageType.AGENT_STARTED
        ]
        assert AgentType.TECHNICAL in started
        assert AgentType.FUNDAMENTAL not in started

    @pytest.mark.asyncio
    async def test_streaming_all_agents_fail_emits_error(self):
        graph = self._make_graph()
        graph.fundamental.analyze = AsyncMock(side_effect=Exception("fail"))
        graph.sentiment.analyze = AsyncMock(side_effect=Exception("fail"))
        graph.technical.analyze = AsyncMock(side_effect=Exception("fail"))

        messages = await self._collect(graph, "AAPL", Market.US)

        types = [m["type"] for m in messages]
        assert WSMessageType.ERROR in types

    @pytest.mark.asyncio
    async def test_streaming_one_agent_fails_emits_agent_error_continues(self):
        graph = self._make_graph()
        graph.fundamental.analyze = AsyncMock(return_value=_make_fundamental_report())
        graph.sentiment.analyze = AsyncMock(side_effect=Exception("sentiment fail"))
        graph.technical.analyze = AsyncMock(return_value=_make_technical_report())
        graph.risk_manager.assess = AsyncMock(return_value=_make_risk_assessment())
        graph.chairperson.decide = AsyncMock(return_value=_make_decision())

        messages = await self._collect(graph, "AAPL", Market.US)

        types = [m["type"] for m in messages]
        assert WSMessageType.AGENT_ERROR in types
        assert WSMessageType.DECISION in types

    @pytest.mark.asyncio
    async def test_streaming_veto_emits_veto_and_stops(self):
        graph = self._make_graph()
        graph.fundamental.analyze = AsyncMock(return_value=_make_fundamental_report())
        graph.sentiment.analyze = AsyncMock(return_value=_make_sentiment_report())
        graph.technical.analyze = AsyncMock(return_value=_make_technical_report())
        graph.risk_manager.assess = AsyncMock(
            return_value=_make_risk_assessment(veto=True, veto_reason="Too risky")
        )
        graph.chairperson.decide = AsyncMock(return_value=_make_decision())

        messages = await self._collect(graph, "AAPL", Market.US)

        types = [m["type"] for m in messages]
        assert WSMessageType.VETO in types
        assert WSMessageType.DECISION not in types
        graph.chairperson.decide.assert_not_called()

    @pytest.mark.asyncio
    async def test_streaming_risk_failure_continues_to_chairperson(self):
        graph = self._make_graph()
        graph.fundamental.analyze = AsyncMock(return_value=_make_fundamental_report())
        graph.sentiment.analyze = AsyncMock(return_value=_make_sentiment_report())
        graph.technical.analyze = AsyncMock(return_value=_make_technical_report())
        graph.risk_manager.assess = AsyncMock(side_effect=Exception("risk fail"))
        graph.chairperson.decide = AsyncMock(return_value=_make_decision())

        messages = await self._collect(graph, "AAPL", Market.US)

        types = [m["type"] for m in messages]
        # Risk errors but chairperson still runs
        assert WSMessageType.DECISION in types

    @pytest.mark.asyncio
    async def test_streaming_chairperson_failure_emits_agent_error(self):
        graph = self._make_graph()
        graph.fundamental.analyze = AsyncMock(return_value=_make_fundamental_report())
        graph.sentiment.analyze = AsyncMock(return_value=_make_sentiment_report())
        graph.technical.analyze = AsyncMock(return_value=_make_technical_report())
        graph.risk_manager.assess = AsyncMock(return_value=_make_risk_assessment())
        graph.chairperson.decide = AsyncMock(side_effect=Exception("chairperson fail"))

        messages = await self._collect(graph, "AAPL", Market.US)

        agent_errors = [m for m in messages if m["type"] == WSMessageType.AGENT_ERROR]
        chairperson_errors = [
            m for m in agent_errors if m["agent"] == AgentType.CHAIRPERSON
        ]
        assert len(chairperson_errors) == 1


class TestCreateBoardroomGraphFactory:
    def test_factory_returns_boardroom_graph(self):
        with (
            patch("backend.shared.ai.workflow.FundamentalAgent"),
            patch("backend.shared.ai.workflow.SentimentAgent"),
            patch("backend.shared.ai.workflow.TechnicalAgent"),
            patch("backend.shared.ai.workflow.RiskManagerAgent"),
            patch("backend.shared.ai.workflow.ChairpersonAgent"),
        ):
            graph = create_boardroom_graph()

        assert isinstance(graph, BoardroomGraph)
