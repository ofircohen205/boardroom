import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.graph.workflow import create_boardroom_graph, BoardroomGraph
from backend.state.enums import Market, Action


@pytest.mark.asyncio
async def test_graph_creation():
    graph = create_boardroom_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_graph_run_no_veto():
    with patch("backend.graph.workflow.FundamentalAgent") as mock_fund:
        with patch("backend.graph.workflow.SentimentAgent") as mock_sent:
            with patch("backend.graph.workflow.TechnicalAgent") as mock_tech:
                with patch("backend.graph.workflow.RiskManagerAgent") as mock_risk:
                    with patch("backend.graph.workflow.ChairpersonAgent") as mock_chair:
                        # Setup mocks
                        mock_fund.return_value.analyze = AsyncMock(return_value={
                            "revenue_growth": 0.15, "pe_ratio": 20, "debt_to_equity": 0.5,
                            "market_cap": 1000000000, "summary": "Good"
                        })
                        mock_sent.return_value.analyze = AsyncMock(return_value={
                            "overall_sentiment": 0.7, "news_items": [], "social_mentions": [], "summary": "Positive"
                        })
                        mock_tech.return_value.analyze = AsyncMock(return_value={
                            "current_price": 100, "ma_50": 95, "ma_200": 90, "rsi": 55,
                            "trend": "bullish", "price_history": [], "summary": "Bullish"
                        })
                        mock_risk.return_value.assess = AsyncMock(return_value={
                            "sector": "Tech", "portfolio_sector_weight": 0.1, "var_95": 0.05,
                            "veto": False, "veto_reason": None
                        })
                        mock_chair.return_value.decide = AsyncMock(return_value={
                            "action": Action.BUY, "confidence": 0.8, "rationale": "Strong buy"
                        })

                        boardroom = BoardroomGraph()
                        result = await boardroom.run("AAPL", Market.US)

                        assert result["final_decision"] is not None
                        assert result["final_decision"]["action"] == Action.BUY
