"""API endpoints for comparative analysis."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.ai.workflow import create_boardroom_graph
from backend.ai.state.enums import Market
from backend.ai.tools.sector_data import get_sector_tickers, get_all_sectors

router = APIRouter(prefix="/api/compare", tags=["comparison"])


class CompareRequest(BaseModel):
    tickers: list[str] = Field(..., min_length=2, max_length=4, description="2-4 stock tickers to compare")
    market: Market = Field(default=Market.US, description="Market for all tickers")


class SectorAnalysisRequest(BaseModel):
    sector: str = Field(..., description="Sector name (e.g., 'technology', 'finance')")
    limit: int = Field(default=5, ge=2, le=8, description="Number of stocks to analyze")
    market: Market = Field(default=Market.US, description="Market")


@router.post("/stocks")
async def compare_stocks(request: CompareRequest):
    """
    Compare multiple stocks side-by-side.

    This endpoint runs full analysis on 2-4 stocks and returns:
    - Individual analysis results for each stock
    - Comparative rankings
    - Relative strength metrics
    - Best pick recommendation
    """
    if len(request.tickers) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least 2 tickers")

    if len(request.tickers) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 tickers allowed")

    graph = create_boardroom_graph()

    # Run comparison (non-streaming version for REST API)
    all_results = {}
    async for event in graph.run_comparison_streaming(request.tickers, request.market):
        if event["type"].value == "comparison_result":
            return event["data"]

    # If no comparison result was generated
    raise HTTPException(status_code=500, detail="Comparison analysis failed")


@router.post("/sector")
async def analyze_sector(request: SectorAnalysisRequest):
    """
    Analyze top stocks in a sector.

    Runs comparative analysis on the top N stocks in the specified sector.
    Returns rankings and sector-level insights.
    """
    tickers = get_sector_tickers(request.sector, request.limit)

    if not tickers:
        raise HTTPException(status_code=404, detail=f"Sector '{request.sector}' not found")

    graph = create_boardroom_graph()

    # Run comparison on sector stocks
    async for event in graph.run_comparison_streaming(tickers, request.market):
        if event["type"].value == "comparison_result":
            comparison = event["data"]
            comparison["sector"] = request.sector
            return comparison

    raise HTTPException(status_code=500, detail="Sector analysis failed")


@router.get("/sectors")
async def list_sectors():
    """Get list of available sectors for analysis."""
    return {"sectors": get_all_sectors()}
