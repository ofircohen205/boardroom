"""Sector to stock mappings for sector analysis."""

from typing import TypedDict


class SectorData(TypedDict):
    name: str
    tickers: list[str]
    description: str


SECTORS: dict[str, SectorData] = {
    "technology": {
        "name": "Technology",
        "tickers": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "TSLA", "AMD", "INTC"],
        "description": "Technology and software companies"
    },
    "finance": {
        "name": "Financial Services",
        "tickers": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "AXP"],
        "description": "Banks, investment firms, and financial services"
    },
    "healthcare": {
        "name": "Healthcare",
        "tickers": ["UNH", "JNJ", "PFE", "ABBV", "TMO", "MRK", "ABT", "LLY"],
        "description": "Pharmaceuticals, biotech, and healthcare services"
    },
    "energy": {
        "name": "Energy",
        "tickers": ["XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "VLO"],
        "description": "Oil, gas, and renewable energy companies"
    },
    "consumer": {
        "name": "Consumer Goods",
        "tickers": ["AMZN", "WMT", "HD", "MCD", "NKE", "SBUX", "TGT", "COST"],
        "description": "Retail and consumer products"
    },
    "industrial": {
        "name": "Industrial",
        "tickers": ["BA", "CAT", "GE", "HON", "UPS", "LMT", "MMM", "DE"],
        "description": "Manufacturing, aerospace, and industrial equipment"
    },
    "telecommunications": {
        "name": "Telecommunications",
        "tickers": ["VZ", "T", "TMUS", "CMCSA", "DIS", "NFLX", "CHTR"],
        "description": "Telecom and media companies"
    },
    "realestate": {
        "name": "Real Estate",
        "tickers": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "O", "WELL"],
        "description": "REITs and real estate companies"
    }
}


def get_sector_tickers(sector: str, limit: int = 5) -> list[str]:
    """Get top N tickers for a given sector."""
    sector_key = sector.lower().replace(" ", "").replace("-", "")

    if sector_key in SECTORS:
        return SECTORS[sector_key]["tickers"][:limit]

    # Fallback: return tech stocks
    return SECTORS["technology"]["tickers"][:limit]


def get_all_sectors() -> list[dict]:
    """Get list of all available sectors."""
    return [
        {
            "key": key,
            "name": data["name"],
            "description": data["description"],
            "ticker_count": len(data["tickers"])
        }
        for key, data in SECTORS.items()
    ]
