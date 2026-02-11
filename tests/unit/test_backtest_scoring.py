"""
Unit tests for backtest scoring modules.
"""

from decimal import Decimal

from backend.api.backtest.schemas import AgentWeights
from backend.backtest.scoring.chairperson_scorer import (
    calculate_weighted_score,
    generate_trade_decision,
)
from backend.backtest.scoring.fundamental_scorer import calculate_fundamental_score
from backend.backtest.scoring.sentiment_scorer import calculate_sentiment_score
from backend.backtest.scoring.technical_scorer import calculate_technical_score


class TestTechnicalScorer:
    """Tests for technical scoring logic."""

    def test_uptrend_scores_high(self):
        """Test that strong uptrend generates high score (70+)."""
        # Simulated uptrend: prices increasing over time
        prices = [Decimal(str(100 + i * 2)) for i in range(50)]
        score = calculate_technical_score(prices)
        assert 70 <= score <= 100, f"Uptrend should score 70+, got {score}"

    def test_downtrend_scores_low(self):
        """Test that strong downtrend generates low score (< 30)."""
        # Simulated downtrend: prices decreasing over time
        prices = [Decimal(str(100 - i * 2)) for i in range(50)]
        score = calculate_technical_score(prices)
        assert 0 <= score <= 30, f"Downtrend should score < 30, got {score}"

    def test_sideways_scores_neutral(self):
        """Test that sideways movement scores near neutral (40-60)."""
        # Simulated sideways: prices oscillating around mean
        prices = [
            Decimal("100"),
            Decimal("102"),
            Decimal("98"),
            Decimal("101"),
            Decimal("99"),
        ] * 10
        score = calculate_technical_score(prices)
        assert 40 <= score <= 60, f"Sideways should score 40-60, got {score}"

    def test_overbought_rsi_scores_lower(self):
        """Test that overbought RSI (> 70) reduces score."""
        # Sharp rally should push RSI overbought
        prices = [Decimal(str(100 + i * 5)) for i in range(20)]
        score = calculate_technical_score(prices)
        # Even in uptrend, overbought RSI should moderate the score
        assert score < 90, f"Overbought RSI should moderate score, got {score}"

    def test_insufficient_data_returns_neutral(self):
        """Test that insufficient data returns neutral score."""
        prices = [Decimal("100"), Decimal("101")]  # < 14 days for RSI
        score = calculate_technical_score(prices)
        assert 45 <= score <= 55, (
            f"Insufficient data should return neutral ~50, got {score}"
        )

    def test_empty_prices_returns_neutral(self):
        """Test that empty price list returns neutral score."""
        score = calculate_technical_score([])
        assert score == 50.0


class TestFundamentalScorer:
    """Tests for fundamental scoring logic."""

    def test_strong_fundamentals_score_high(self):
        """Test that strong fundamentals generate high score (70+)."""
        score = calculate_fundamental_score(
            pe_ratio=Decimal("15.0"),
            revenue_growth=Decimal("0.25"),  # 25% growth
            profit_margin=Decimal("0.20"),  # 20% margin
            debt_to_equity=Decimal("0.3"),  # Low debt
        )
        assert 70 <= score <= 100, f"Strong fundamentals should score 70+, got {score}"

    def test_weak_fundamentals_score_low(self):
        """Test that weak fundamentals generate low score (< 40)."""
        score = calculate_fundamental_score(
            pe_ratio=Decimal("100.0"),  # Overvalued
            revenue_growth=Decimal("-0.10"),  # Declining revenue
            profit_margin=Decimal("0.02"),  # Low margin
            debt_to_equity=Decimal("2.5"),  # High debt
        )
        assert 0 <= score <= 40, f"Weak fundamentals should score < 40, got {score}"

    def test_moderate_fundamentals_score_neutral(self):
        """Test that moderate fundamentals score near neutral (40-60)."""
        score = calculate_fundamental_score(
            pe_ratio=Decimal("20.0"),
            revenue_growth=Decimal("0.05"),  # 5% growth
            profit_margin=Decimal("0.10"),
            debt_to_equity=Decimal("0.8"),
        )
        assert 40 <= score <= 60, (
            f"Moderate fundamentals should score 40-60, got {score}"
        )

    def test_missing_data_returns_neutral(self):
        """Test that missing fundamental data returns neutral score."""
        score = calculate_fundamental_score(
            pe_ratio=None,
            revenue_growth=None,
            profit_margin=None,
            debt_to_equity=None,
        )
        assert score == 50.0


class TestSentimentScorer:
    """Tests for sentiment scoring logic."""

    def test_strong_positive_momentum_scores_high(self):
        """Test that strong positive momentum generates high score (70+)."""
        # Recent prices show strong upward momentum
        prices = [Decimal(str(100 + i * 3)) for i in range(10)]
        score = calculate_sentiment_score(prices)
        assert 70 <= score <= 100, (
            f"Strong positive momentum should score 70+, got {score}"
        )

    def test_strong_negative_momentum_scores_low(self):
        """Test that strong negative momentum generates low score (< 30)."""
        # Recent prices show strong downward momentum
        prices = [Decimal(str(100 - i * 3)) for i in range(10)]
        score = calculate_sentiment_score(prices)
        assert 0 <= score <= 30, (
            f"Strong negative momentum should score < 30, got {score}"
        )

    def test_flat_momentum_scores_neutral(self):
        """Test that flat momentum scores near neutral (45-55)."""
        prices = [Decimal("100")] * 10
        score = calculate_sentiment_score(prices)
        assert 45 <= score <= 55, f"Flat momentum should score 45-55, got {score}"

    def test_insufficient_data_returns_neutral(self):
        """Test that insufficient data returns neutral score."""
        prices = [Decimal("100"), Decimal("101")]
        score = calculate_sentiment_score(prices)
        assert score == 50.0


class TestChairpersonScorer:
    """Tests for chairperson weighted scoring and decision logic."""

    def test_weighted_score_calculation(self):
        """Test that weighted score is calculated correctly."""
        weights = AgentWeights(
            fundamental=0.5,
            technical=0.3,
            sentiment=0.2,
        )
        scores = {
            "fundamental": 80.0,
            "technical": 60.0,
            "sentiment": 50.0,
        }
        # Expected: 0.5*80 + 0.3*60 + 0.2*50 = 40 + 18 + 10 = 68
        weighted = calculate_weighted_score(scores, weights)
        assert weighted == 68.0

    def test_all_scores_high_generates_buy(self):
        """Test that high weighted score (> 70) generates BUY decision."""
        weights = AgentWeights(
            fundamental=0.33,
            technical=0.33,
            sentiment=0.34,
        )
        scores = {"fundamental": 85.0, "technical": 80.0, "sentiment": 75.0}
        decision = generate_trade_decision(scores, weights)
        assert decision == "BUY", f"High score should BUY, got {decision}"

    def test_all_scores_low_generates_sell(self):
        """Test that low weighted score (< 30) generates SELL decision."""
        weights = AgentWeights(
            fundamental=0.33,
            technical=0.33,
            sentiment=0.34,
        )
        scores = {"fundamental": 20.0, "technical": 25.0, "sentiment": 15.0}
        decision = generate_trade_decision(scores, weights)
        assert decision == "SELL", f"Low score should SELL, got {decision}"

    def test_neutral_scores_generate_hold(self):
        """Test that neutral weighted score (30-70) generates HOLD decision."""
        weights = AgentWeights(
            fundamental=0.33,
            technical=0.33,
            sentiment=0.34,
        )
        scores = {"fundamental": 50.0, "technical": 55.0, "sentiment": 45.0}
        decision = generate_trade_decision(scores, weights)
        assert decision == "HOLD", f"Neutral score should HOLD, got {decision}"

    def test_custom_weights_affect_decision(self):
        """Test that changing weights changes the decision."""
        scores = {"fundamental": 80.0, "technical": 30.0, "sentiment": 30.0}

        # Heavy fundamental weight should BUY
        fundamental_heavy = AgentWeights(fundamental=0.8, technical=0.1, sentiment=0.1)
        decision1 = generate_trade_decision(scores, fundamental_heavy)
        # 0.8*80 + 0.1*30 + 0.1*30 = 64 + 3 + 3 = 70 → BUY

        # Heavy technical weight should SELL or HOLD
        technical_heavy = AgentWeights(fundamental=0.1, technical=0.8, sentiment=0.1)
        decision2 = generate_trade_decision(scores, technical_heavy)
        # 0.1*80 + 0.8*30 + 0.1*30 = 8 + 24 + 3 = 35 → HOLD or SELL

        assert decision1 != decision2, (
            "Different weights should produce different decisions"
        )

    def test_edge_case_threshold_buy(self):
        """Test that score exactly at 70 threshold generates BUY."""
        weights = AgentWeights(fundamental=1.0, technical=0.0, sentiment=0.0)
        scores = {"fundamental": 70.0, "technical": 0.0, "sentiment": 0.0}
        decision = generate_trade_decision(scores, weights)
        assert decision == "BUY"

    def test_edge_case_threshold_sell(self):
        """Test that score exactly at 30 threshold generates SELL."""
        weights = AgentWeights(fundamental=1.0, technical=0.0, sentiment=0.0)
        scores = {"fundamental": 30.0, "technical": 0.0, "sentiment": 0.0}
        decision = generate_trade_decision(scores, weights)
        assert decision == "SELL"
