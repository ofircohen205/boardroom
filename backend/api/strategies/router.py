"""API router for strategy management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.dao.backtesting import StrategyDAO
from backend.db.database import get_db
from backend.db.models.backtesting import Strategy
from backend.db.models.user import User

from .schemas import StrategyCreate, StrategyResponse, StrategyUpdate

router = APIRouter(prefix="/api/strategies", tags=["strategies"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=StrategyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new strategy",
)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Strategy:
    """Create a new trading strategy with custom agent weights.

    Args:
        strategy_data: Strategy configuration (name, description, weights, thresholds, risk params)
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created strategy

    Example:
        ```json
        {
          "name": "Balanced Growth",
          "description": "Equal weight to all agents with moderate thresholds",
          "config": {
            "weights": {"fundamental": 0.4, "technical": 0.4, "sentiment": 0.2},
            "thresholds": {"buy": 70, "sell": 30},
            "risk_params": {"max_position_size": 0.5, "stop_loss": 0.1}
          }
        }
        ```
    """
    dao = StrategyDAO(db)

    strategy = Strategy(
        user_id=current_user.id,
        name=strategy_data.name,
        description=strategy_data.description,
        config=strategy_data.config.model_dump(),
        is_active=True,
    )

    created = await dao.create(strategy)
    await db.commit()
    await db.refresh(created)

    logger.info(f"User {current_user.id} created strategy {created.id}: {created.name}")
    return created


@router.get(
    "",
    response_model=list[StrategyResponse],
    summary="List user's strategies",
)
async def list_strategies(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Strategy]:
    """List all strategies for the current user.

    Args:
        active_only: If True, only return active strategies (default: True)
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of user's strategies, ordered by creation date (newest first)
    """
    dao = StrategyDAO(db)
    strategies = await dao.get_user_strategies(current_user.id, active_only=active_only)
    return strategies


@router.get(
    "/{strategy_id}",
    response_model=StrategyResponse,
    summary="Get strategy details",
)
async def get_strategy(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Strategy:
    """Get details of a specific strategy.

    Args:
        strategy_id: Strategy ID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Strategy details

    Raises:
        HTTPException: 404 if strategy not found or doesn't belong to user
    """
    dao = StrategyDAO(db)
    strategy = await dao.get_by_id_and_user(strategy_id, current_user.id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_id} not found",
        )

    return strategy


@router.put(
    "/{strategy_id}",
    response_model=StrategyResponse,
    summary="Update strategy",
)
async def update_strategy(
    strategy_id: UUID,
    strategy_data: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Strategy:
    """Update an existing strategy.

    Args:
        strategy_id: Strategy ID
        strategy_data: Updated strategy data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Updated strategy

    Raises:
        HTTPException: 404 if strategy not found or doesn't belong to user
    """
    dao = StrategyDAO(db)
    strategy = await dao.get_by_id_and_user(strategy_id, current_user.id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_id} not found",
        )

    # Update fields
    if strategy_data.name is not None:
        strategy.name = strategy_data.name
    if strategy_data.description is not None:
        strategy.description = strategy_data.description
    if strategy_data.config is not None:
        strategy.config = strategy_data.config.model_dump()
    if strategy_data.is_active is not None:
        strategy.is_active = strategy_data.is_active

    await db.commit()
    await db.refresh(strategy)

    logger.info(f"User {current_user.id} updated strategy {strategy_id}")
    return strategy


@router.delete(
    "/{strategy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete strategy",
)
async def delete_strategy(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a strategy.

    Note: This will cascade delete all associated paper accounts and backtest results.

    Args:
        strategy_id: Strategy ID
        current_user: Currently authenticated user
        db: Database session

    Raises:
        HTTPException: 404 if strategy not found or doesn't belong to user
    """
    dao = StrategyDAO(db)
    strategy = await dao.get_by_id_and_user(strategy_id, current_user.id)

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_id} not found",
        )

    await dao.delete(strategy_id)
    await db.commit()

    logger.info(f"User {current_user.id} deleted strategy {strategy_id}")
