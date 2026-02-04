import pytest
from backend.tools.technical_indicators import calculate_rsi, calculate_ma, calculate_trend
from backend.state.enums import Trend


def test_calculate_ma():
    prices = [100, 102, 104, 103, 105, 107, 106, 108, 110, 109]
    ma = calculate_ma(prices, period=5)
    assert ma == pytest.approx(108.0, rel=0.01)


def test_calculate_rsi_overbought():
    # Consistently rising prices = high RSI
    prices = [100 + i * 2 for i in range(20)]
    rsi = calculate_rsi(prices)
    assert rsi > 70


def test_calculate_rsi_oversold():
    # Consistently falling prices = low RSI
    prices = [100 - i * 2 for i in range(20)]
    rsi = calculate_rsi(prices)
    assert rsi < 30


def test_calculate_trend_bullish():
    trend = calculate_trend(current_price=110, ma_50=100, ma_200=95)
    assert trend == Trend.BULLISH


def test_calculate_trend_bearish():
    trend = calculate_trend(current_price=90, ma_50=100, ma_200=105)
    assert trend == Trend.BEARISH


def test_calculate_trend_neutral():
    trend = calculate_trend(current_price=100, ma_50=100, ma_200=100)
    assert trend == Trend.NEUTRAL
