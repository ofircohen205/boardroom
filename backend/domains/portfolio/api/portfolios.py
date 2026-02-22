# backend/api/portfolios/endpoints.py
"""Portfolio endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_portfolio_service
from backend.domains.portfolio.services import PortfolioService
from backend.shared.ai.state.enums import Market
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.models import User

from .portfolios_schemas import PortfolioPositionSchema, PortfolioSchema

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("")
async def list_portfolios(
    current_user: Annotated[User, Depends(get_current_user)],
    service: PortfolioService = Depends(get_portfolio_service),
) -> list[PortfolioSchema]:
    """Get all portfolios for current user."""
    portfolios = await service.get_user_portfolios(current_user.id)
    return [
        PortfolioSchema(
            id=str(p.id),
            name=p.name,
            positions=[
                PortfolioPositionSchema(
                    id=str(pos.id),
                    ticker=pos.ticker,
                    quantity=pos.quantity,
                    avg_entry_price=pos.avg_entry_price,
                    sector=pos.sector or "Unknown",
                )
                for pos in p.positions
                if pos.closed_at is None
            ],
        )
        for p in portfolios
    ]


@router.post("")
async def create_new_portfolio(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioSchema:
    """Create a new portfolio."""
    portfolio = await service.create_portfolio(
        current_user.id, name, service.portfolio_dao.session
    )
    return PortfolioSchema(id=str(portfolio.id), name=portfolio.name, positions=[])


@router.post("/{portfolio_id}/positions")
async def add_new_position(
    portfolio_id: UUID,
    ticker: str,
    market: str,
    quantity: float,
    entry_price: float,
    current_user: Annotated[User, Depends(get_current_user)],
    service: PortfolioService = Depends(get_portfolio_service),
    sector: str | None = None,
) -> PortfolioPositionSchema:
    """Add a position to a portfolio."""
    try:
        market_enum = Market(market)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid market: {market}")
    position = await service.add_position(
        portfolio_id,
        ticker,
        market_enum,
        quantity,
        entry_price,
        sector,
        service.portfolio_dao.session,
    )
    return PortfolioPositionSchema(
        id=str(position.id),
        ticker=position.ticker,
        quantity=position.quantity,
        avg_entry_price=position.avg_entry_price,
        sector=position.sector or "Unknown",
    )
