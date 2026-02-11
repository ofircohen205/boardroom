"""API router for paper trading."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.dao.backtesting import (
    PaperAccountDAO,
    PaperPositionDAO,
    PaperTradeDAO,
    StrategyDAO,
)
from backend.data.historical import get_latest_price
from backend.db.database import get_db
from backend.db.models.backtesting import PaperAccount, PaperTrade, TradeType
from backend.db.models.user import User

from .schemas import (
    PaperAccountCreate,
    PaperAccountResponse,
    PaperAccountUpdate,
    PaperPerformanceResponse,
    PaperPositionResponse,
    PaperTradeRequest,
    PaperTradeResponse,
)

router = APIRouter(prefix="/api/paper", tags=["paper-trading"])
logger = logging.getLogger(__name__)


@router.post(
    "/accounts",
    response_model=PaperAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a paper trading account",
)
async def create_paper_account(
    account_data: PaperAccountCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaperAccount:
    """Create a new paper trading account.

    Args:
        account_data: Account configuration (name, strategy, initial balance)
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Created paper account

    Raises:
        HTTPException: 404 if strategy not found
    """
    # Validate strategy belongs to user
    strategy_dao = StrategyDAO(db)
    strategy = await strategy_dao.get_by_id_and_user(
        account_data.strategy_id, current_user.id
    )
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {account_data.strategy_id} not found",
        )

    # Create account
    account_dao = PaperAccountDAO(db)
    account = PaperAccount(
        user_id=current_user.id,
        strategy_id=account_data.strategy_id,
        name=account_data.name,
        initial_balance=account_data.initial_balance,
        current_balance=account_data.initial_balance,
        is_active=True,
    )

    created = await account_dao.create(account)
    await db.commit()
    await db.refresh(created)

    logger.info(
        f"User {current_user.id} created paper account {created.id}: {created.name}"
    )
    return created


@router.get(
    "/accounts",
    response_model=list[PaperAccountResponse],
    summary="List user's paper trading accounts",
)
async def list_paper_accounts(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PaperAccount]:
    """List all paper trading accounts for the current user.

    Args:
        active_only: If True, only return active accounts (default: True)
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of user's paper accounts
    """
    dao = PaperAccountDAO(db)
    accounts = await dao.get_user_accounts(current_user.id, active_only=active_only)
    return accounts


@router.get(
    "/accounts/{account_id}",
    response_model=PaperAccountResponse,
    summary="Get paper account details",
)
async def get_paper_account(
    account_id: UUID,
    include_positions: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get details of a specific paper trading account.

    Args:
        account_id: Account ID
        include_positions: If True, include current positions (default: True)
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Account details with optional positions

    Raises:
        HTTPException: 404 if account not found
    """
    account_dao = PaperAccountDAO(db)
    account = await account_dao.get_by_id_and_user(account_id, current_user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper account {account_id} not found",
        )

    # Calculate total value
    positions_value = 0.0
    positions_list = []

    if include_positions:
        position_dao = PaperPositionDAO(db)
        positions = await position_dao.get_account_positions(account_id)

        for position in positions:
            # Get current price
            current_price = await get_latest_price(db, position.ticker)
            if current_price:
                position.current_price = current_price
                position.last_price_update = datetime.utcnow()
                market_value = float(current_price) * position.quantity
                positions_value += market_value

                # Calculate unrealized P&L
                cost_basis = float(position.average_entry_price) * position.quantity
                unrealized_pnl = market_value - cost_basis
                unrealized_pnl_pct = (
                    unrealized_pnl / cost_basis if cost_basis > 0 else 0
                )

                positions_list.append(
                    {
                        "id": position.id,
                        "ticker": position.ticker,
                        "quantity": position.quantity,
                        "average_entry_price": float(position.average_entry_price),
                        "current_price": float(current_price)
                        if current_price
                        else None,
                        "market_value": market_value,
                        "unrealized_pnl": unrealized_pnl,
                        "unrealized_pnl_pct": unrealized_pnl_pct,
                        "created_at": position.created_at,
                        "updated_at": position.updated_at,
                    }
                )

        # Save updated prices
        await db.commit()

    total_value = float(account.current_balance) + positions_value
    total_pnl = total_value - float(account.initial_balance)
    total_pnl_pct = total_pnl / float(account.initial_balance)

    return {
        "id": account.id,
        "user_id": account.user_id,
        "strategy_id": account.strategy_id,
        "name": account.name,
        "initial_balance": float(account.initial_balance),
        "current_balance": float(account.current_balance),
        "total_value": total_value,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "is_active": account.is_active,
        "created_at": account.created_at,
        "updated_at": account.updated_at,
        "positions": positions_list if include_positions else None,
    }


@router.put(
    "/accounts/{account_id}",
    response_model=PaperAccountResponse,
    summary="Update paper account",
)
async def update_paper_account(
    account_id: UUID,
    account_data: PaperAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaperAccount:
    """Update a paper trading account.

    Args:
        account_id: Account ID
        account_data: Updated account data
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Updated account

    Raises:
        HTTPException: 404 if account not found
    """
    dao = PaperAccountDAO(db)
    account = await dao.get_by_id_and_user(account_id, current_user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper account {account_id} not found",
        )

    # Update fields
    if account_data.name is not None:
        account.name = account_data.name
    if account_data.is_active is not None:
        account.is_active = account_data.is_active

    account.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(account)

    logger.info(f"User {current_user.id} updated paper account {account_id}")
    return account


@router.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete paper account",
)
async def delete_paper_account(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a paper trading account.

    Note: This will cascade delete all associated trades and positions.

    Args:
        account_id: Account ID
        current_user: Currently authenticated user
        db: Database session

    Raises:
        HTTPException: 404 if account not found
    """
    dao = PaperAccountDAO(db)
    account = await dao.get_by_id_and_user(account_id, current_user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper account {account_id} not found",
        )

    await dao.delete(account_id)
    await db.commit()

    logger.info(f"User {current_user.id} deleted paper account {account_id}")


@router.post(
    "/accounts/{account_id}/trades",
    response_model=PaperTradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute a paper trade",
)
async def execute_paper_trade(
    account_id: UUID,
    trade_data: PaperTradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaperTrade:
    """Execute a paper trade (buy or sell).

    Args:
        account_id: Account ID
        trade_data: Trade details (ticker, type, quantity, optional price)
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Executed trade record

    Raises:
        HTTPException: 404 if account not found, 400 if insufficient funds/shares
    """
    # Verify account belongs to user
    account_dao = PaperAccountDAO(db)
    account = await account_dao.get_by_id_and_user(account_id, current_user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper account {account_id} not found",
        )

    # Get current price if not provided
    price = trade_data.price
    if not price:
        price = await get_latest_price(db, trade_data.ticker)
        if not price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot get current price for {trade_data.ticker}",
            )

    trade_type = TradeType.BUY if trade_data.trade_type == "BUY" else TradeType.SELL
    total_value = price * trade_data.quantity

    # Validate trade
    position_dao = PaperPositionDAO(db)

    if trade_type == TradeType.BUY:
        # Check if enough cash
        if account.current_balance < total_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient funds: need ${total_value:.2f}, have ${account.current_balance:.2f}",
            )
    else:  # SELL
        # Check if enough shares
        position = await position_dao.get_position(account_id, trade_data.ticker)
        if not position or position.quantity < trade_data.quantity:
            available = position.quantity if position else 0
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient shares: trying to sell {trade_data.quantity}, have {available}",
            )

    # Create trade record
    trade_dao = PaperTradeDAO(db)
    trade = PaperTrade(
        account_id=account_id,
        ticker=trade_data.ticker.upper(),
        trade_type=trade_type,
        quantity=trade_data.quantity,
        price=price,
        total_value=total_value,
        analysis_session_id=trade_data.analysis_session_id,
        executed_at=datetime.utcnow(),
    )

    created_trade = await trade_dao.create(trade)

    # Update account balance and position
    if trade_type == TradeType.BUY:
        new_balance = account.current_balance - total_value
    else:
        new_balance = account.current_balance + total_value

    await account_dao.update_balance(account_id, new_balance)

    # Update position
    await position_dao.update_position(
        account_id,
        trade_data.ticker.upper(),
        trade_data.quantity if trade_type == TradeType.BUY else -trade_data.quantity,
        price,
        trade_type,
    )

    await db.commit()
    await db.refresh(created_trade)

    logger.info(
        f"User {current_user.id} executed paper trade: {trade_type.value} {trade_data.quantity} "
        f"{trade_data.ticker} @ ${price:.2f} in account {account_id}"
    )

    return created_trade


@router.get(
    "/accounts/{account_id}/trades",
    response_model=list[PaperTradeResponse],
    summary="Get trade history",
)
async def get_trade_history(
    account_id: UUID,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PaperTrade]:
    """Get trade history for a paper account.

    Args:
        account_id: Account ID
        limit: Maximum number of trades to return (default: 100)
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of trades ordered by execution time (newest first)

    Raises:
        HTTPException: 404 if account not found
    """
    # Verify account belongs to user
    account_dao = PaperAccountDAO(db)
    account = await account_dao.get_by_id_and_user(account_id, current_user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper account {account_id} not found",
        )

    trade_dao = PaperTradeDAO(db)
    trades = await trade_dao.get_account_trades(account_id, limit=limit)
    return trades


@router.get(
    "/accounts/{account_id}/positions",
    response_model=list[PaperPositionResponse],
    summary="Get current positions",
)
async def get_positions(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get all current positions for a paper account.

    Args:
        account_id: Account ID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        List of open positions with current prices and P&L

    Raises:
        HTTPException: 404 if account not found
    """
    # Verify account belongs to user
    account_dao = PaperAccountDAO(db)
    account = await account_dao.get_by_id_and_user(account_id, current_user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper account {account_id} not found",
        )

    position_dao = PaperPositionDAO(db)
    positions = await position_dao.get_account_positions(account_id)

    positions_list = []
    for position in positions:
        # Get current price
        current_price = await get_latest_price(db, position.ticker)
        if current_price:
            position.current_price = current_price
            position.last_price_update = datetime.utcnow()

        market_value = (
            float(current_price) * position.quantity if current_price else None
        )
        cost_basis = float(position.average_entry_price) * position.quantity
        unrealized_pnl = market_value - cost_basis if market_value else None
        unrealized_pnl_pct = (
            unrealized_pnl / cost_basis if unrealized_pnl and cost_basis > 0 else None
        )

        positions_list.append(
            {
                "id": position.id,
                "ticker": position.ticker,
                "quantity": position.quantity,
                "average_entry_price": float(position.average_entry_price),
                "current_price": float(current_price) if current_price else None,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_pct": unrealized_pnl_pct,
                "created_at": position.created_at,
                "updated_at": position.updated_at,
            }
        )

    # Save updated prices
    await db.commit()

    return positions_list


@router.get(
    "/accounts/{account_id}/performance",
    response_model=PaperPerformanceResponse,
    summary="Get account performance metrics",
)
async def get_performance(
    account_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get performance metrics for a paper account.

    Args:
        account_id: Account ID
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Performance metrics including returns, win rate, and trade statistics

    Raises:
        HTTPException: 404 if account not found
    """
    # Verify account belongs to user
    account_dao = PaperAccountDAO(db)
    account = await account_dao.get_by_id_and_user(account_id, current_user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper account {account_id} not found",
        )

    # Get all trades
    trade_dao = PaperTradeDAO(db)
    trades = await trade_dao.get_account_trades(account_id, limit=10000)

    # Calculate current value
    position_dao = PaperPositionDAO(db)
    positions = await position_dao.get_account_positions(account_id)

    positions_value = 0.0
    for position in positions:
        current_price = await get_latest_price(db, position.ticker)
        if current_price:
            positions_value += float(current_price) * position.quantity

    current_value = float(account.current_balance) + positions_value
    total_return = (current_value - float(account.initial_balance)) / float(
        account.initial_balance
    )
    total_pnl = current_value - float(account.initial_balance)

    # Analyze trades
    winning_trades = 0
    losing_trades = 0
    wins = []
    losses = []

    # Pair BUY and SELL trades
    for i in range(0, len(trades) - 1, 2):
        if (
            i + 1 < len(trades)
            and trades[i].trade_type == TradeType.SELL
            and trades[i + 1].trade_type == TradeType.BUY
        ):
            # Reversed order (newest first), so SELL comes before BUY
            sell_trade = trades[i]
            buy_trade = trades[i + 1]
            profit = float(sell_trade.total_value) - float(buy_trade.total_value)

            if profit > 0:
                winning_trades += 1
                wins.append(profit)
            elif profit < 0:
                losing_trades += 1
                losses.append(profit)

    total_trade_pairs = winning_trades + losing_trades
    win_rate = winning_trades / total_trade_pairs if total_trade_pairs > 0 else 0.0

    avg_win = sum(wins) / len(wins) if wins else None
    avg_loss = sum(losses) / len(losses) if losses else None
    largest_win = max(wins) if wins else None
    largest_loss = min(losses) if losses else None

    return {
        "account_id": account_id,
        "initial_balance": float(account.initial_balance),
        "current_value": current_value,
        "total_return": total_return,
        "total_pnl": total_pnl,
        "total_trades": len(trades),
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "equity_curve": None,  # TODO: Implement equity curve calculation
    }
