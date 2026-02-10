from pydantic import BaseModel, Field

from backend.ai.state.enums import Market


class CompareRequest(BaseModel):
    tickers: list[str] = Field(
        ..., min_length=2, max_length=4, description="2-4 stock tickers to compare"
    )
    market: Market = Field(default=Market.US, description="Market for all tickers")


class SectorAnalysisRequest(BaseModel):
    sector: str = Field(..., description="Sector name (e.g., 'technology', 'finance')")
    limit: int = Field(default=5, ge=2, le=8, description="Number of stocks to analyze")
    market: Market = Field(default=Market.US, description="Market")
