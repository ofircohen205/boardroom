"""Stock symbol search utility using yfinance."""

from dataclasses import dataclass

import yfinance as yf

from backend.shared.ai.state.enums import Market
from backend.shared.ai.tools.market_data import _MARKET_SUFFIX


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

POPULAR_LSE_STOCKS = {
    "HSBA": ("HSBC Holdings", "LSE"),
    "BP": ("BP plc", "LSE"),
    "SHEL": ("Shell plc", "LSE"),
    "AZN": ("AstraZeneca plc", "LSE"),
    "LLOY": ("Lloyds Banking Group", "LSE"),
    "RIO": ("Rio Tinto plc", "LSE"),
    "GSK": ("GSK plc", "LSE"),
    "ULVR": ("Unilever plc", "LSE"),
}

POPULAR_TSE_STOCKS = {
    "7203": ("Toyota Motor Corporation", "TSE"),
    "6758": ("Sony Group Corporation", "TSE"),
    "9984": ("SoftBank Group Corp.", "TSE"),
    "6861": ("Keyence Corporation", "TSE"),
    "8306": ("Mitsubishi UFJ Financial Group", "TSE"),
    "7267": ("Honda Motor Co.", "TSE"),
    "6501": ("Hitachi Ltd.", "TSE"),
    "4063": ("Shin-Etsu Chemical Co.", "TSE"),
}

POPULAR_HKEX_STOCKS = {
    "0700": ("Tencent Holdings", "HKEX"),
    "0005": ("HSBC Holdings", "HKEX"),
    "0939": ("China Construction Bank", "HKEX"),
    "0941": ("China Mobile", "HKEX"),
    "0175": ("Geely Automobile", "HKEX"),
    "1299": ("AIA Group", "HKEX"),
    "2318": ("Ping An Insurance", "HKEX"),
    "3690": ("Meituan", "HKEX"),
}

POPULAR_XETRA_STOCKS = {
    "SAP": ("SAP SE", "XETRA"),
    "BMW": ("BMW AG", "XETRA"),
    "SIE": ("Siemens AG", "XETRA"),
    "VOW3": ("Volkswagen AG", "XETRA"),
    "ALV": ("Allianz SE", "XETRA"),
    "DTE": ("Deutsche Telekom AG", "XETRA"),
    "BAS": ("BASF SE", "XETRA"),
    "MBG": ("Mercedes-Benz Group AG", "XETRA"),
}

_POPULAR_STOCKS: dict[Market, dict[str, tuple[str, str]]] = {
    Market.US: POPULAR_US_STOCKS,
    Market.TASE: POPULAR_TASE_STOCKS,
    Market.LSE: POPULAR_LSE_STOCKS,
    Market.TSE: POPULAR_TSE_STOCKS,
    Market.HKEX: POPULAR_HKEX_STOCKS,
    Market.XETRA: POPULAR_XETRA_STOCKS,
}


async def search_stocks(
    query: str, market: Market, limit: int = 8
) -> list[StockSuggestion]:
    """
    Search for stock symbols matching the query.

    Args:
        query: Search query (partial or full ticker/company name)
        market: Market to search in (US, TASE, LSE, TSE, HKEX, or XETRA)
        limit: Maximum number of results to return

    Returns:
        List of matching stock suggestions
    """
    if not query or len(query) < 1:
        return []

    query_upper = query.upper().strip()
    results: list[StockSuggestion] = []

    # First check popular stocks cache for fast response
    popular_stocks = _POPULAR_STOCKS.get(market, {})

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
            ticker_symbol = f"{query_upper}{_MARKET_SUFFIX.get(market, '')}"

            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info

            # Check if we got valid data
            if (info and info.get("shortName")) or info.get("longName"):
                name = info.get("shortName") or info.get("longName") or query_upper
                exchange = info.get("exchange") or market.value

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
