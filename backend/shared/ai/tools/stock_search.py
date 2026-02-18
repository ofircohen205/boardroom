"""Stock symbol search utility using yfinance."""

from dataclasses import dataclass

import yfinance as yf

from backend.shared.ai.state.enums import Market


@dataclass
class StockSuggestion:
    """A stock suggestion returned from search."""

    symbol: str
    name: str
    exchange: str
    market: Market


# Common stocks for quick lookups - reduces API calls for frequent searches
POPULAR_US_STOCKS = {
    "AAPL": ("Apple Inc.", "NASDAQ"),
    "MSFT": ("Microsoft Corporation", "NASDAQ"),
    "GOOGL": ("Alphabet Inc.", "NASDAQ"),
    "AMZN": ("Amazon.com Inc.", "NASDAQ"),
    "META": ("Meta Platforms Inc.", "NASDAQ"),
    "TSLA": ("Tesla Inc.", "NASDAQ"),
    "NVDA": ("NVIDIA Corporation", "NASDAQ"),
    "JPM": ("JPMorgan Chase & Co.", "NYSE"),
    "V": ("Visa Inc.", "NYSE"),
    "JNJ": ("Johnson & Johnson", "NYSE"),
    "WMT": ("Walmart Inc.", "NYSE"),
    "PG": ("Procter & Gamble Co.", "NYSE"),
    "MA": ("Mastercard Inc.", "NYSE"),
    "UNH": ("UnitedHealth Group Inc.", "NYSE"),
    "HD": ("Home Depot Inc.", "NYSE"),
    "DIS": ("The Walt Disney Company", "NYSE"),
    "BAC": ("Bank of America Corp.", "NYSE"),
    "XOM": ("Exxon Mobil Corporation", "NYSE"),
    "PFE": ("Pfizer Inc.", "NYSE"),
    "KO": ("The Coca-Cola Company", "NYSE"),
    "NFLX": ("Netflix Inc.", "NASDAQ"),
    "INTC": ("Intel Corporation", "NASDAQ"),
    "AMD": ("Advanced Micro Devices Inc.", "NASDAQ"),
    "CSCO": ("Cisco Systems Inc.", "NASDAQ"),
    "ADBE": ("Adobe Inc.", "NASDAQ"),
    "CRM": ("Salesforce Inc.", "NYSE"),
    "ORCL": ("Oracle Corporation", "NYSE"),
    "PYPL": ("PayPal Holdings Inc.", "NASDAQ"),
    "UBER": ("Uber Technologies Inc.", "NYSE"),
    "ABNB": ("Airbnb Inc.", "NASDAQ"),
}

POPULAR_TASE_STOCKS = {
    "TEVA": ("Teva Pharmaceutical Industries", "TASE"),
    "NICE": ("NICE Ltd.", "TASE"),
    "LUMI": ("Bank Leumi", "TASE"),
    "POLI": ("Bank Hapoalim", "TASE"),
    "ICL": ("ICL Group Ltd.", "TASE"),
    "BEZQ": ("Bezeq", "TASE"),
    "ELCO": ("Elco Holdings", "TASE"),
    "AZRG": ("Azrieli Group", "TASE"),
    "MZTF": ("Mizrahi Tefahot Bank", "TASE"),
    "PHOE": ("Phoenix Holdings", "TASE"),
}


async def search_stocks(
    query: str, market: Market, limit: int = 8
) -> list[StockSuggestion]:
    """
    Search for stock symbols matching the query.

    Args:
        query: Search query (partial or full ticker/company name)
        market: Market to search in (US or TASE)
        limit: Maximum number of results to return

    Returns:
        List of matching stock suggestions
    """
    if not query or len(query) < 1:
        return []

    query_upper = query.upper().strip()
    results: list[StockSuggestion] = []

    # First check popular stocks cache for fast response
    popular_stocks = POPULAR_US_STOCKS if market == Market.US else POPULAR_TASE_STOCKS

    for symbol, (name, exchange) in popular_stocks.items():
        if query_upper in symbol or query_upper.lower() in name.lower():
            results.append(
                StockSuggestion(
                    symbol=symbol,
                    name=name,
                    exchange=exchange,
                    market=market,
                )
            )
            if len(results) >= limit:
                return results

    # If we have few results, try yfinance lookup for the exact symbol
    if len(results) < limit and len(query_upper) >= 1:
        try:
            # Format ticker for the market
            if market == Market.TASE:
                ticker_symbol = f"{query_upper}.TA"
            else:
                ticker_symbol = query_upper

            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            # Check if we got valid data
            if (info and info.get("shortName")) or info.get("longName"):
                name = info.get("shortName") or info.get("longName") or query_upper
                exchange = info.get("exchange") or (
                    "TASE" if market == Market.TASE else "US"
                )

                # Avoid duplicates
                if not any(r.symbol == query_upper for r in results):
                    results.append(
                        StockSuggestion(
                            symbol=query_upper,
                            name=name,
                            exchange=exchange,
                            market=market,
                        )
                    )
        except Exception:
            # yfinance lookup failed, just return cached results
            pass

    return results[:limit]
