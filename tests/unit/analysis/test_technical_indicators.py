import pytest

from backend.shared.ai.state.enums import Trend
from backend.shared.ai.tools.technical_indicators import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ma,
    calculate_macd,
    calculate_rsi,
    calculate_trend,
)

# --- Moving Average tests ---


def test_calculate_ma():
    prices = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109]
    ma = calculate_ma(prices, period=5)
    assert ma == pytest.approx(108.0, rel=0.01)


def test_calculate_ma_empty():
    assert calculate_ma([], 5) == 0.0


def test_calculate_ma_zero_period():
    assert calculate_ma([100, 200], 0) == 0.0


def test_calculate_ma_short_list():
    """When list is shorter than period, average all available prices."""
    prices = [100, 200, 300]
    ma = calculate_ma(prices, period=10)
    assert ma == pytest.approx(200.0)


def test_calculate_ma_exact_period():
    prices = [10, 20, 30]
    ma = calculate_ma(prices, period=3)
    assert ma == pytest.approx(20.0)


def test_calculate_ma_period_1():
    prices = [10, 20, 30, 40]
    ma = calculate_ma(prices, period=1)
    assert ma == pytest.approx(40.0)  # Last 1 element


# --- RSI tests ---


def test_calculate_rsi_overbought():
    prices = [100 + i * 2 for i in range(20)]
    rsi = calculate_rsi(prices)
    assert rsi > 70


def test_calculate_rsi_oversold():
    prices = [100 - i * 2 for i in range(20)]
    rsi = calculate_rsi(prices)
    assert rsi < 30


def test_calculate_rsi_insufficient_data():
    """Returns 50 when there isn't enough data."""
    prices = [100, 102, 104]
    rsi = calculate_rsi(prices, period=14)
    assert rsi == 50.0


def test_calculate_rsi_all_gains():
    """All gains should produce RSI of 100."""
    prices = [100 + i for i in range(20)]
    rsi = calculate_rsi(prices)
    assert rsi == 100.0


def test_calculate_rsi_mixed():
    """Mixed price movement should produce RSI between 0 and 100."""
    prices = [
        100,
        105,
        102,
        108,
        103,
        110,
        107,
        112,
        108,
        115,
        110,
        118,
        113,
        120,
        115,
        122,
    ]
    rsi = calculate_rsi(prices)
    assert 0 < rsi < 100


# --- Trend tests ---


def test_calculate_trend_bullish():
    trend = calculate_trend(current_price=110, ma_50=100, ma_200=95)
    assert trend == Trend.BULLISH


def test_calculate_trend_bearish():
    trend = calculate_trend(current_price=90, ma_50=100, ma_200=105)
    assert trend == Trend.BEARISH


def test_calculate_trend_neutral():
    trend = calculate_trend(current_price=100, ma_50=100, ma_200=100)
    assert trend == Trend.NEUTRAL


def test_calculate_trend_price_between_mas():
    """Price between MAs is neutral (not clearly bullish or bearish)."""
    trend = calculate_trend(current_price=97, ma_50=95, ma_200=100)
    assert trend == Trend.NEUTRAL


def test_calculate_trend_death_cross_above():
    """Price above both MAs but 50 < 200 (death cross) is neutral."""
    trend = calculate_trend(current_price=110, ma_50=100, ma_200=105)
    assert trend == Trend.NEUTRAL


# --- MACD tests ---


def test_calculate_macd_returns_all_keys():
    prices = list(range(1, 50))  # 49 prices
    result = calculate_macd(prices)
    assert "macd" in result
    assert "signal" in result
    assert "histogram" in result


def test_calculate_macd_insufficient_data_returns_zeros():
    result = calculate_macd([100.0, 101.0])
    assert result == {"macd": 0.0, "signal": 0.0, "histogram": 0.0}


# --- Bollinger Bands tests ---


def test_calculate_bollinger_bands_returns_all_keys():
    prices = [100.0 + i for i in range(25)]
    result = calculate_bollinger_bands(prices)
    assert "upper" in result and "lower" in result and "middle" in result
    assert result["upper"] > result["middle"] > result["lower"]


def test_calculate_bollinger_bands_insufficient_data():
    result = calculate_bollinger_bands([100.0])
    assert result["upper"] == result["middle"] == result["lower"] == 100.0


# --- ATR tests ---


def test_calculate_atr_returns_float():
    history = [
        {"high": 105.0, "low": 98.0, "close": 102.0},
        {"high": 107.0, "low": 100.0, "close": 104.0},
        {"high": 103.0, "low": 97.0, "close": 100.0},
    ]
    result = calculate_atr(history)
    assert isinstance(result, float)
    assert result > 0


def test_calculate_atr_insufficient_data():
    result = calculate_atr([{"high": 100.0, "low": 98.0, "close": 99.0}])
    assert result == 0.0
