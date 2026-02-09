# backend/api/portfolios/endpoints.py
"""Portfolio endpoints."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.models import User
from backend.auth.dependencies import get_current_user
from backend.services.portfolio_management import (
    get_user_portfolios,
    create_portfolio,
    add_position,
)
from backend.ai.state.enums import Market
from .schemas import PortfolioSchema, PortfolioPositionSchema

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("")
async def list_portfolios(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
) -> list[PortfolioSchema]:
    """Get all portfolios for current user."""
    portfolios = await get_user_portfolios(current_user.id, db)
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
                    sector=pos.sector
                )
                for pos in p.positions
                if pos.closed_at is None
            ]
        )
        for p in portfolios
    ]


@router.post("")
async def create_new_portfolio(
    name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db)
) -> PortfolioSchema:
    """Create a new portfolio."""
    portfolio = await create_portfolio(current_user.id, name, db)
    return PortfolioSchema(
        id=str(portfolio.id),
        name=portfolio.name,
        positions=[]
    )


@router.post("/{portfolio_id}/positions")
async def add_new_position(
    portfolio_id: UUID,
    ticker: str,
    market: str,
    quantity: float,
    entry_price: float,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    sector: str | None = None
) -> PortfolioPositionSchema:
    """Add a position to a portfolio."""
    market_enum = Market.TASE if market == "TASE" else Market.US
    position = await add_position(
        portfolio_id, ticker, market_enum, quantity, entry_price, sector, db
    )
    return PortfolioPositionSchema(
        id=str(position.id),
        ticker=position.ticker,
        quantity=position.quantity,
        avg_entry_price=position.avg_entry_price,
        sector=position.sector
    )
