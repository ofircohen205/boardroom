"""Unit tests for backend.shared.ai.tools.relative_strength."""

import pytest

from backend.shared.ai.tools.relative_strength import (
    calculate_correlation_matrix,
    calculate_relative_performance,
    calculate_relative_strength,
    calculate_valuation_comparison,
)

# ---------------------------------------------------------------------------
# Sample price histories
# ---------------------------------------------------------------------------

AAPL_HISTORY = [{"close": 150.0 + i} for i in range(10)]  # trending up
MSFT_HISTORY = [{"close": 300.0 + i * 2} for i in range(10)]  # trending up faster
TSLA_HISTORY = [{"close": 200.0 - i} for i in range(10)]  # trending down

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fundamental(
    pe_ratio: float = 25.0,
    revenue_growth: float = 0.15,
    debt_to_equity: float = 1.5,
    market_cap: float = 3e12,
) -> dict:
    """Return a minimal FundamentalReport dict."""
    return {
        "pe_ratio": pe_ratio,
        "revenue_growth": revenue_growth,
        "debt_to_equity": debt_to_equity,
        "market_cap": market_cap,
        "sector": "Technology",
        "summary": "Test summary",
    }


# ===========================================================================
# calculate_correlation_matrix
# ===========================================================================


class TestCalculateCorrelationMatrix:
    def test_two_stocks_both_trending_up_positive_correlation(self):
        histories = {"AAPL": AAPL_HISTORY, "MSFT": MSFT_HISTORY}
        result = calculate_correlation_matrix(histories)

        assert "AAPL" in result
        assert "MSFT" in result
        # Both trends are monotonically increasing → near-perfect correlation
        assert result["AAPL"]["MSFT"] > 0.9
        assert result["MSFT"]["AAPL"] > 0.9

    def test_self_correlation_is_one(self):
        histories = {"AAPL": AAPL_HISTORY, "MSFT": MSFT_HISTORY}
        result = calculate_correlation_matrix(histories)

        assert result["AAPL"]["AAPL"] == pytest.approx(1.0)
        assert result["MSFT"]["MSFT"] == pytest.approx(1.0)

    def test_one_up_one_down_negative_correlation(self):
        # Correlation is computed on returns (daily % changes), not raw prices.
        # Monotone up vs monotone down series still have positive correlation on returns
        # (both return series have near-constant magnitude).
        # Use alternating/zigzag prices so returns oscillate in opposite directions:
        # zigzag_up:   100, 110, 100, 110, ... → returns [+10%, -9.1%, +10%, ...]
        # zigzag_down: 200, 190, 200, 190, ... → returns [-5%,  +5.3%, -5%, ...]
        zigzag_up = [{"close": 100.0 if i % 2 == 0 else 110.0} for i in range(10)]
        zigzag_down = [{"close": 200.0 if i % 2 == 0 else 190.0} for i in range(10)]
        histories = {"UP": zigzag_up, "DOWN": zigzag_down}
        result = calculate_correlation_matrix(histories)

        # Alternating up/down vs alternating down/up → strong negative correlation
        assert result["UP"]["DOWN"] < 0

    def test_single_stock_returns_empty(self):
        histories = {"AAPL": AAPL_HISTORY}
        result = calculate_correlation_matrix(histories)

        assert result == {}

    def test_empty_input_returns_empty(self):
        result = calculate_correlation_matrix({})
        assert result == {}

    def test_different_length_histories_trimmed_no_crash(self):
        short_history = [{"close": 100.0 + i} for i in range(5)]
        long_history = [{"close": 200.0 + i} for i in range(20)]

        histories = {"SHORT": short_history, "LONG": long_history}
        # Should not raise; result should contain both tickers
        result = calculate_correlation_matrix(histories)

        assert "SHORT" in result
        assert "LONG" in result
        assert "SHORT" in result["LONG"]
        assert "LONG" in result["SHORT"]

    def test_three_stocks_full_matrix(self):
        histories = {
            "AAPL": AAPL_HISTORY,
            "MSFT": MSFT_HISTORY,
            "TSLA": TSLA_HISTORY,
        }
        result = calculate_correlation_matrix(histories)

        # All three tickers appear as rows and columns
        for ticker in ("AAPL", "MSFT", "TSLA"):
            assert ticker in result
            for other in ("AAPL", "MSFT", "TSLA"):
                assert other in result[ticker]


# ===========================================================================
# calculate_relative_performance
# ===========================================================================


class TestCalculateRelativePerformance:
    def test_stock_going_up_positive_return(self):
        # 150 → 159: (9/150)*100 = 6%
        history = [{"close": 150.0 + i} for i in range(10)]
        result = calculate_relative_performance({"AAPL": history})

        assert result["AAPL"] == pytest.approx(6.0, abs=0.01)

    def test_stock_going_down_negative_return(self):
        # 200 → 191: (-9/200)*100 = -4.5%
        history = [{"close": 200.0 - i} for i in range(10)]
        result = calculate_relative_performance({"TSLA": history})

        assert result["TSLA"] < 0
        assert result["TSLA"] == pytest.approx(-4.5, abs=0.01)

    def test_single_price_entry_returns_zero(self):
        history = [{"close": 100.0}]
        result = calculate_relative_performance({"X": history})

        assert result["X"] == 0.0

    def test_zero_first_price_returns_zero(self):
        history = [{"close": 0.0}, {"close": 50.0}]
        result = calculate_relative_performance({"X": history})

        assert result["X"] == 0.0

    def test_multiple_stocks_in_one_call(self):
        histories = {
            "AAPL": AAPL_HISTORY,
            "MSFT": MSFT_HISTORY,
            "TSLA": TSLA_HISTORY,
        }
        result = calculate_relative_performance(histories)

        assert "AAPL" in result
        assert "MSFT" in result
        assert "TSLA" in result
        # AAPL and MSFT positive, TSLA negative
        assert result["AAPL"] > 0
        assert result["MSFT"] > 0
        assert result["TSLA"] < 0

    def test_empty_history_dict_returns_empty(self):
        result = calculate_relative_performance({})
        assert result == {}

    def test_flat_price_returns_zero(self):
        history = [{"close": 100.0}] * 10
        result = calculate_relative_performance({"FLAT": history})

        assert result["FLAT"] == pytest.approx(0.0)


# ===========================================================================
# calculate_valuation_comparison
# ===========================================================================


class TestCalculateValuationComparison:
    def test_with_real_report_values_preserved(self):
        fund = _make_fundamental(
            pe_ratio=25.0, revenue_growth=0.15, debt_to_equity=1.5, market_cap=3e12
        )
        result = calculate_valuation_comparison({"AAPL": fund})

        assert result["AAPL"]["pe_ratio"] == pytest.approx(25.0)
        assert result["AAPL"]["debt_to_equity"] == pytest.approx(1.5)
        assert result["AAPL"]["market_cap"] == pytest.approx(3e12)

    def test_revenue_growth_converted_to_percentage(self):
        fund = _make_fundamental(revenue_growth=0.15)
        result = calculate_valuation_comparison({"AAPL": fund})

        # 0.15 → 15.0
        assert result["AAPL"]["revenue_growth"] == pytest.approx(15.0)

    def test_none_report_all_zeros(self):
        result = calculate_valuation_comparison({"TSLA": None})

        assert result["TSLA"]["pe_ratio"] == 0.0
        assert result["TSLA"]["revenue_growth"] == 0.0
        assert result["TSLA"]["debt_to_equity"] == 0.0
        assert result["TSLA"]["market_cap"] == 0.0

    def test_mixed_one_real_one_none(self):
        fund = _make_fundamental(pe_ratio=30.0, revenue_growth=0.20)
        result = calculate_valuation_comparison({"AAPL": fund, "TSLA": None})

        assert result["AAPL"]["pe_ratio"] == pytest.approx(30.0)
        assert result["AAPL"]["revenue_growth"] == pytest.approx(20.0)
        assert result["TSLA"]["pe_ratio"] == 0.0
        assert result["TSLA"]["revenue_growth"] == 0.0

    def test_empty_fundamentals_returns_empty(self):
        result = calculate_valuation_comparison({})
        assert result == {}

    def test_negative_revenue_growth_converted_correctly(self):
        fund = _make_fundamental(revenue_growth=-0.05)
        result = calculate_valuation_comparison({"X": fund})

        assert result["X"]["revenue_growth"] == pytest.approx(-5.0)


# ===========================================================================
# calculate_relative_strength (integration of all three sub-functions)
# ===========================================================================


class TestCalculateRelativeStrength:
    def test_returns_relative_strength_typed_dict(self):
        histories = {"AAPL": AAPL_HISTORY, "MSFT": MSFT_HISTORY}
        fundamentals = {
            "AAPL": _make_fundamental(pe_ratio=28.0),
            "MSFT": _make_fundamental(pe_ratio=32.0),
        }
        result = calculate_relative_strength(histories, fundamentals)

        # TypedDict keys
        assert "correlation_matrix" in result
        assert "relative_performance" in result
        assert "valuation_comparison" in result

    def test_correlation_matrix_field_populated(self):
        histories = {"AAPL": AAPL_HISTORY, "MSFT": MSFT_HISTORY}
        fundamentals = {"AAPL": _make_fundamental(), "MSFT": _make_fundamental()}
        result = calculate_relative_strength(histories, fundamentals)

        assert "AAPL" in result["correlation_matrix"]
        assert "MSFT" in result["correlation_matrix"]

    def test_relative_performance_field_populated(self):
        histories = {"AAPL": AAPL_HISTORY, "TSLA": TSLA_HISTORY}
        fundamentals = {"AAPL": _make_fundamental(), "TSLA": None}
        result = calculate_relative_strength(histories, fundamentals)

        assert "AAPL" in result["relative_performance"]
        assert "TSLA" in result["relative_performance"]
        assert result["relative_performance"]["AAPL"] > 0
        assert result["relative_performance"]["TSLA"] < 0

    def test_valuation_comparison_field_populated(self):
        histories = {"AAPL": AAPL_HISTORY, "MSFT": MSFT_HISTORY}
        fund_aapl = _make_fundamental(pe_ratio=25.0, revenue_growth=0.15)
        fund_msft = _make_fundamental(pe_ratio=35.0, revenue_growth=0.10)
        fundamentals = {"AAPL": fund_aapl, "MSFT": fund_msft}
        result = calculate_relative_strength(histories, fundamentals)

        assert result["valuation_comparison"]["AAPL"]["pe_ratio"] == pytest.approx(25.0)
        assert result["valuation_comparison"]["MSFT"]["pe_ratio"] == pytest.approx(35.0)
        assert result["valuation_comparison"]["AAPL"][
            "revenue_growth"
        ] == pytest.approx(15.0)

    def test_single_stock_correlation_matrix_empty(self):
        histories = {"AAPL": AAPL_HISTORY}
        fundamentals = {"AAPL": _make_fundamental()}
        result = calculate_relative_strength(histories, fundamentals)

        # Single stock → correlation matrix empty (requires >= 2)
        assert result["correlation_matrix"] == {}
        # But relative performance and valuation still computed
        assert "AAPL" in result["relative_performance"]
        assert "AAPL" in result["valuation_comparison"]
