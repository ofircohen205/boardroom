"""API router for strategy management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.dependencies import get_strategy_service
from backend.domains.analysis.services.backtesting_services import StrategyService
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.models.backtesting import Strategy
from backend.shared.db.models.user import User

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
    service: StrategyService = Depends(get_strategy_service),
) -> Strategy:
    """Create a new trading strategy with custom agent weights.

    Args:
        strategy_data: Strategy configuration (name, description, weights, thresholds, risk params)
        current_user: Currently authenticated user
        service: Strategy service injected

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
    created = await service.create_strategy(current_user.id, strategy_data)
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
    service: StrategyService = Depends(get_strategy_service),
) -> list[Strategy]:
    """List all strategies for the current user.

    Args:
        active_only: If True, only return active strategies (default: True)
        current_user: Currently authenticated user
        service: Strategy service injected

    Returns:
        List of user's strategies, ordered by creation date (newest first)
    """
    strategies = await service.get_user_strategies(
        current_user.id, active_only=active_only
    )
    return strategies


@router.get(
    "/{strategy_id}",
    response_model=StrategyResponse,
    summary="Get strategy details",
)
async def get_strategy(
    strategy_id: UUID,
    current_user: User = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service),
) -> Strategy:
    """Get details of a specific strategy.

    Args:
        strategy_id: Strategy ID
        current_user: Currently authenticated user
        service: Strategy service injected

    Returns:
        Strategy details

    Raises:
        HTTPException: 404 if strategy not found or doesn't belong to user
    """
    return await service.get_strategy(strategy_id, current_user.id)


@router.put(
    "/{strategy_id}",
    response_model=StrategyResponse,
    summary="Update strategy",
)
async def update_strategy(
    strategy_id: UUID,
    strategy_data: StrategyUpdate,
    current_user: User = Depends(get_current_user),
    service: StrategyService = Depends(get_strategy_service),
) -> Strategy:
    """Update an existing strategy.

    Args:
        strategy_id: Strategy ID
        strategy_data: Updated strategy data
        current_user: Currently authenticated user
        service: Strategy service injected

    Returns:
        Updated strategy

    Raises:
        HTTPException: 404 if strategy not found or doesn't belong to user
    """
    strategy = await service.update_strategy(
        strategy_id, current_user.id, strategy_data
    )
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
    service: StrategyService = Depends(get_strategy_service),
) -> None:
    """Delete a strategy.

    Note: This will cascade delete all associated paper accounts and backtest results.

    Args:
        strategy_id: Strategy ID
        current_user: Currently authenticated user
        service: Strategy service injected

    Raises:
        HTTPException: 404 if strategy not found or doesn't belong to user
    """
    await service.delete_strategy(strategy_id, current_user.id)
    logger.info(f"User {current_user.id} deleted strategy {strategy_id}")
