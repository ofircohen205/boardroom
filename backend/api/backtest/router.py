"""API router for backtest HTTP endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.dao.backtesting import BacktestResultDAO
from backend.db.database import get_db
from backend.db.models.backtesting import BacktestResult
from backend.db.models.user import User

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
    db: AsyncSession = Depends(get_db),
) -> list[BacktestResult]:
    """List backtest results for the current user.

    Args:
        limit: Maximum number of results to return (default: 50)
        ticker: Optional filter by ticker symbol
        strategy_id: Optional filter by strategy ID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of backtest results ordered by creation date (newest first)
    """
    dao = BacktestResultDAO(db)

    if ticker:
        results = await dao.get_results_by_ticker(
            current_user.id, ticker.upper(), limit=limit
        )
    elif strategy_id:
        results = await dao.get_results_by_strategy(
            current_user.id, strategy_id, limit=limit
        )
    else:
        results = await dao.get_user_results(current_user.id, limit=limit)

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
    db: AsyncSession = Depends(get_db),
) -> BacktestResultResponse:
    """Get details of a specific backtest result.

    Args:
        result_id: Backtest result ID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Backtest result details

    Raises:
        HTTPException: 404 if result not found or doesn't belong to user
    """
    dao = BacktestResultDAO(db)
    result = await dao.get(result_id)

    if not result or result.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest result {result_id} not found",
        )

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
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a backtest result.

    Args:
        result_id: Backtest result ID
        current_user: Currently authenticated user
        db: Database session

    Raises:
        HTTPException: 404 if result not found or doesn't belong to user
    """
    dao = BacktestResultDAO(db)
    result = await dao.get(result_id)

    if not result or result.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backtest result {result_id} not found",
        )

    await dao.delete(result_id)
    await db.commit()

    logger.info(f"User {current_user.id} deleted backtest result {result_id}")
