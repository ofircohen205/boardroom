"""API router for backtest HTTP endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.dependencies import get_backtest_service
from backend.domains.analysis.services.backtesting_services import BacktestService
from backend.shared.auth.dependencies import get_current_user
from backend.shared.db.models.user import User

from .schemas import BacktestResultResponse, EquityPointResponse, TradeResponse

router = APIRouter(prefix="/api/backtest", tags=["backtest"])
logger = logging.getLogger(__name__)


@router.get(
    "/results",
    response_model=list[BacktestResultResponse],
    summary="List user's backtest results",
)
async def list_backtest_results(
    limit: int = 50,
    ticker: str | None = None,
    strategy_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    service: BacktestService = Depends(get_backtest_service),
) -> list[BacktestResultResponse]:
    """List backtest results for the current user.

    Args:
        limit: Maximum number of results to return (default: 50)
        ticker: Optional filter by ticker symbol
        strategy_id: Optional filter by strategy ID
        current_user: Currently authenticated user
        service: Backtest service

    Returns:
        List of backtest results ordered by creation date (newest first)
    """
    if ticker:
        results = await service.backtest_dao.get_results_by_ticker(
            current_user.id, ticker.upper(), limit=limit
        )
    elif strategy_id:
        results = await service.backtest_dao.get_results_by_strategy(
            current_user.id, strategy_id, limit=limit
        )
    else:
        results = await service.get_user_results(current_user.id, limit=limit)

    # Convert to response format
    return [
        BacktestResultResponse(
            id=result.id,
            ticker=result.ticker,
            strategy_id=result.strategy_id,
            start_date=result.start_date.isoformat(),
            end_date=result.end_date.isoformat(),
            initial_capital=float(result.initial_capital),
            total_return=float(result.total_return),
            annualized_return=float(result.annualized_return),
            sharpe_ratio=float(result.sharpe_ratio) if result.sharpe_ratio else None,
            max_drawdown=float(result.max_drawdown),
            win_rate=float(result.win_rate),
            total_trades=result.total_trades,
            buy_and_hold_return=float(result.buy_and_hold_return),
            equity_curve=[
                EquityPointResponse(**point) for point in result.equity_curve
            ],
            trades=[TradeResponse(**trade) for trade in result.trades],
            execution_time_seconds=float(result.execution_time_seconds)
            if result.execution_time_seconds
            else None,
        )
        for result in results
    ]


@router.get(
    "/results/{result_id}",
    response_model=BacktestResultResponse,
    summary="Get backtest result details",
)
async def get_backtest_result(
    result_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BacktestService = Depends(get_backtest_service),
) -> BacktestResultResponse:
    """Get details of a specific backtest result.

    Args:
        result_id: Backtest result ID
        current_user: Currently authenticated user
        service: Backtest service

    Returns:
        Backtest result details

    Raises:
        HTTPException: 404 if result not found or doesn't belong to user
    """
    result = await service.get_result(result_id, current_user.id)

    return BacktestResultResponse(
        id=result.id,
        ticker=result.ticker,
        strategy_id=result.strategy_id,
        start_date=result.start_date.isoformat(),
        end_date=result.end_date.isoformat(),
        initial_capital=float(result.initial_capital),
        total_return=float(result.total_return),
        annualized_return=float(result.annualized_return),
        sharpe_ratio=float(result.sharpe_ratio) if result.sharpe_ratio else None,
        max_drawdown=float(result.max_drawdown),
        win_rate=float(result.win_rate),
        total_trades=result.total_trades,
        buy_and_hold_return=float(result.buy_and_hold_return),
        equity_curve=[EquityPointResponse(**point) for point in result.equity_curve],
        trades=[TradeResponse(**trade) for trade in result.trades],
        execution_time_seconds=float(result.execution_time_seconds)
        if result.execution_time_seconds
        else None,
    )


@router.delete(
    "/results/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete backtest result",
)
async def delete_backtest_result(
    result_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BacktestService = Depends(get_backtest_service),
) -> None:
    """Delete a backtest result.

    Args:
        result_id: Backtest result ID
        current_user: Currently authenticated user
        service: Backtest service

    Raises:
        HTTPException: 404 if result not found or doesn't belong to user
    """
    await service.delete_result(result_id, current_user.id)
    logger.info(f"User {current_user.id} deleted backtest result {result_id}")
