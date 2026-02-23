"""WebSocket endpoint for backtest execution."""

import json
import logging
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.analysis.engine import BacktestConfig, run_backtest
from backend.shared.core.settings import settings
from backend.shared.dao.backtesting import BacktestResultDAO, StrategyDAO
from backend.shared.dao.user import UserDAO
from backend.shared.data.historical import fetch_and_store_historical_prices
from backend.shared.db.database import get_db
from backend.shared.db.models.backtesting import BacktestFrequency, BacktestResult
from backend.shared.db.models.user import User

router = APIRouter(tags=["backtest-websocket"])
logger = logging.getLogger(__name__)


async def get_current_user_ws(token: str, db: AsyncSession) -> User | None:
    """Get current user from WebSocket token."""
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.algorithm],
        )
        email: str = str(payload.get("sub"))
        if email is None:
            return None
    except JWTError:
        return None

    user_dao = UserDAO(db)
    return await user_dao.find_by_email(email)


@router.websocket("/backtest")
async def backtest_websocket(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket endpoint for running backtests with real-time progress updates.

    Protocol:
    1. Client connects with JWT token
    2. Client sends BacktestConfigRequest as JSON
    3. Server streams progress updates:
       - backtest_started: Backtest initiated
       - backtest_progress: Periodic updates (every N days processed)
       - backtest_completed: Final results
       - backtest_error: Error occurred
    4. Connection closes after completion or error

    Example client message:
    ```json
    {
      "ticker": "AAPL",
      "strategy_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "initial_capital": 10000.00,
      "check_frequency": "daily"
    }
    ```

    Example server messages:
    ```json
    {"type": "backtest_started", "data": {"ticker": "AAPL"}}
    {"type": "backtest_progress", "data": {"progress_pct": 45.5}}
    {"type": "backtest_completed", "data": {...results...}}
    ```
    """
    await websocket.accept()

    # Authenticate user
    user = await get_current_user_ws(token, db)
    if not user:
        await websocket.send_json(
            {"type": "backtest_error", "data": {"error": "Authentication failed"}}
        )
        await websocket.close()
        return

    logger.info(f"User {user.id} connected to backtest WebSocket")

    try:
        # Receive backtest configuration
        raw_message = await websocket.receive_text()
        config_data = json.loads(raw_message)

        ticker = config_data["ticker"].upper()
        strategy_id = UUID(config_data["strategy_id"])
        start_date_str = config_data["start_date"]
        end_date_str = config_data["end_date"]
        initial_capital = Decimal(str(config_data.get("initial_capital", 10000)))
        check_frequency = config_data.get("check_frequency", "daily")
        position_size_pct = Decimal(str(config_data.get("position_size_pct", 0.5)))
        stop_loss_pct = config_data.get("stop_loss_pct")
        take_profit_pct = config_data.get("take_profit_pct")

        # Parse dates
        from datetime import date

        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)

        # Validate strategy belongs to user
        strategy_dao = StrategyDAO(db)
        strategy = await strategy_dao.get_by_id_and_user(strategy_id, user.id)
        if not strategy:
            await websocket.send_json(
                {
                    "type": "backtest_error",
                    "data": {"error": f"Strategy {strategy_id} not found"},
                }
            )
            await websocket.close()
            return

        # Send started message
        await websocket.send_json(
            {
                "type": "backtest_started",
                "data": {
                    "ticker": ticker,
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "strategy": strategy.name,
                },
            }
        )

        # Fetch historical data if needed
        logger.info(
            f"Fetching historical data for {ticker} from {start_date} to {end_date}"
        )
        await websocket.send_json(
            {
                "type": "backtest_progress",
                "data": {
                    "status": "fetching_data",
                    "message": f"Fetching historical data for {ticker}...",
                },
            }
        )

        try:
            new_records = await fetch_and_store_historical_prices(
                db, ticker, start_date, end_date
            )
            logger.info(f"Fetched {new_records} new price records for {ticker}")
        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            await websocket.send_json(
                {
                    "type": "backtest_error",
                    "data": {"error": f"Failed to fetch historical data: {e!s}"},
                }
            )
            await websocket.close()
            return

        # Send progress update
        await websocket.send_json(
            {
                "type": "backtest_progress",
                "data": {
                    "status": "running_backtest",
                    "message": "Running backtest simulation...",
                },
            }
        )

        # Build backtest config
        backtest_config = BacktestConfig(
            ticker=ticker,
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            check_frequency=BacktestFrequency.DAILY
            if check_frequency == "daily"
            else BacktestFrequency.WEEKLY,
            position_size_pct=position_size_pct,
            stop_loss_pct=Decimal(str(stop_loss_pct)) if stop_loss_pct else None,
            take_profit_pct=Decimal(str(take_profit_pct)) if take_profit_pct else None,
            agent_weights=strategy.config.get(
                "weights", {"fundamental": 0.33, "technical": 0.33, "sentiment": 0.34}
            ),
            buy_threshold=strategy.config.get("thresholds", {}).get("buy", 70.0),
            sell_threshold=strategy.config.get("thresholds", {}).get("sell", 30.0),
        )

        # Run backtest
        logger.info(f"Running backtest for {ticker} with strategy {strategy.name}")
        result = await run_backtest(db, backtest_config)

        # Save result to database
        backtest_result = BacktestResult(
            user_id=user.id,
            strategy_id=strategy_id,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            check_frequency=backtest_config.check_frequency,
            position_size_pct=position_size_pct,
            stop_loss_pct=backtest_config.stop_loss_pct,
            take_profit_pct=backtest_config.take_profit_pct,
            total_return=Decimal(str(result.total_return)),
            annualized_return=Decimal(str(result.annualized_return)),
            sharpe_ratio=Decimal(str(result.sharpe_ratio))
            if result.sharpe_ratio
            else None,
            max_drawdown=Decimal(str(result.max_drawdown)),
            win_rate=Decimal(str(result.win_rate)),
            total_trades=result.total_trades,
            buy_and_hold_return=Decimal(str(result.buy_and_hold_return)),
            equity_curve=[
                {
                    "date": point.date,
                    "equity": point.equity,
                    "cash": point.cash,
                    "position_value": point.position_value,
                }
                for point in result.equity_curve
            ],
            trades=[
                {
                    "date": trade.date,
                    "type": trade.type,
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "total": trade.total,
                    "commission": trade.commission,
                }
                for trade in result.trades
            ],
            execution_time_seconds=Decimal(str(result.execution_time_seconds))
            if result.execution_time_seconds
            else None,
            created_at=datetime.utcnow(),
        )

        result_dao = BacktestResultDAO(db)
        saved_result = await result_dao.save(backtest_result)
        await db.commit()
        await db.refresh(saved_result)

        # Send completion message with full results
        await websocket.send_json(
            {
                "type": "backtest_completed",
                "data": {
                    "id": str(saved_result.id),
                    "ticker": ticker,
                    "strategy_id": str(strategy_id),
                    "start_date": start_date_str,
                    "end_date": end_date_str,
                    "initial_capital": float(initial_capital),
                    "total_return": result.total_return,
                    "annualized_return": result.annualized_return,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "total_trades": result.total_trades,
                    "buy_and_hold_return": result.buy_and_hold_return,
                    "equity_curve": [
                        {
                            "date": point.date,
                            "equity": point.equity,
                            "cash": point.cash,
                            "position_value": point.position_value,
                        }
                        for point in result.equity_curve
                    ],
                    "trades": [
                        {
                            "date": trade.date,
                            "type": trade.type,
                            "quantity": trade.quantity,
                            "price": trade.price,
                            "total": trade.total,
                            "commission": trade.commission,
                        }
                        for trade in result.trades
                    ],
                    "execution_time_seconds": result.execution_time_seconds,
                },
            }
        )

        logger.info(
            f"Backtest completed for {ticker}: "
            f"Return={result.total_return:.2%}, Trades={result.total_trades}"
        )

    except WebSocketDisconnect:
        logger.info(f"User {user.id} disconnected from backtest WebSocket")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON received: {e}")
        await websocket.send_json(
            {"type": "backtest_error", "data": {"error": "Invalid JSON format"}}
        )
    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        await websocket.send_json(
            {
                "type": "backtest_error",
                "data": {"error": f"Missing required field: {e!s}"},
            }
        )
    except ValueError as e:
        logger.error(f"Backtest failed: {e}")
        await websocket.send_json({"type": "backtest_error", "data": {"error": str(e)}})
    except Exception as e:
        logger.exception(f"Unexpected error in backtest WebSocket: {e}")
        await websocket.send_json(
            {
                "type": "backtest_error",
                "data": {"error": f"Internal server error: {e!s}"},
            }
        )
    finally:
        try:
            await websocket.close()
        except Exception:
            pass  # Already closed
