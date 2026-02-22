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


def calculate_macd(
    prices: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, float]:
    """Returns MACD line, signal line, and histogram values."""
    if len(prices) < slow + signal:
        return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

    def _ema(data: list[float], period: int) -> list[float]:
        k = 2 / (period + 1)
        seed = sum(data[:period]) / period
        ema = [seed]
        for price in data[period:]:
            ema.append(price * k + ema[-1] * (1 - k))
        return ema

    ema_fast = _ema(prices, fast)
    ema_slow = _ema(prices, slow)

    # Align EMAs: ema_fast starts at t=fast-1, ema_slow starts at t=slow-1
    # Offset ema_fast by (slow - fast) so both series start at t=slow-1
    macd_line = [f - s for f, s in zip(ema_fast[slow - fast :], ema_slow)]
    macd_signal = _ema(macd_line, signal)
    histogram = macd_line[-1] - macd_signal[-1]

    return {
        "macd": round(macd_line[-1], 4),
        "signal": round(macd_signal[-1], 4),
        "histogram": round(histogram, 4),
    }


def calculate_bollinger_bands(
    prices: list[float], period: int = 20, std_dev: float = 2.0
) -> dict[str, float]:
    """Returns upper band, middle band (SMA), lower band, and band width %."""
    if len(prices) < period:
        price = prices[-1] if prices else 0.0
        return {"upper": price, "middle": price, "lower": price, "width_pct": 0.0}

    window = prices[-period:]
    middle = sum(window) / period
    variance = sum((p - middle) ** 2 for p in window) / period
    std = variance**0.5
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    width_pct = ((upper - lower) / middle * 100) if middle else 0.0

    return {
        "upper": round(upper, 4),
        "middle": round(middle, 4),
        "lower": round(lower, 4),
        "width_pct": round(width_pct, 2),
    }


def calculate_atr(price_history: list[dict], period: int = 14) -> float:
    """Average True Range — measures volatility. Expects dicts with high/low/close keys.

    Returns 0.0 if price_history has fewer than 2 entries or if no rows with
    valid high/low/close data are found. Rows missing required keys are skipped.
    """
    if len(price_history) < 2:
        return 0.0

    true_ranges = []
    for i in range(1, len(price_history)):
        high = price_history[i].get("high")
        low = price_history[i].get("low")
        prev_close = price_history[i - 1].get("close")
        if high is None or low is None or prev_close is None:
            continue  # skip rows with missing data
        true_range = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(true_range)

    if not true_ranges:
        return 0.0

    recent = true_ranges[-period:]
    return round(sum(recent) / len(recent), 4)
