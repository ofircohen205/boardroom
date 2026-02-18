from backend.shared.ai.state.enums import Trend


def calculate_ma(prices: list[float], period: int) -> float:
    if not prices or period == 0:
        return 0.0
    if len(prices) < period:
        return sum(prices) / len(prices)
    return sum(prices[-period:]) / period


def calculate_rsi(prices: list[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return 50.0

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_trend(current_price: float, ma_50: float, ma_200: float) -> Trend:
    # Price above both MAs and 50 > 200 = bullish
    if current_price > ma_50 > ma_200:
        return Trend.BULLISH
    # Price below both MAs and 50 < 200 = bearish
    if current_price < ma_50 < ma_200:
        return Trend.BEARISH
    return Trend.NEUTRAL
