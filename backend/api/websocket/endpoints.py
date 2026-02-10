# backend/api/websocket/endpoints.py
"""WebSocket endpoint for real-time analysis streaming."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.ai.state.enums import Action, AnalysisMode, Market, WSMessageType
from backend.ai.tools.market_data import get_market_data_client
from backend.ai.workflow import BoardroomGraph
from backend.core.logging import get_logger
from backend.core.settings import settings
from backend.db.database import get_db
from backend.db.models import (
    AgentReport,
    AnalysisSession,
    FinalDecision,
    Portfolio,
    User,
)
from backend.services.performance_tracking.service import create_analysis_outcome

from .connection_manager import connection_manager

logger = get_logger(__name__)

router = APIRouter(tags=["websocket"])


async def get_current_user_ws(token: str, db: AsyncSession) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def _calculate_portfolio_sector_weight(
    db: AsyncSession, user: User, ticker: str, market: Market
) -> float:
    """Calculates the portfolio weight of the sector the given ticker belongs to."""
    try:
        # 1. Get the sector for the ticker being analyzed
        market_data_client = get_market_data_client()
        analyzed_stock_data = await market_data_client.get_stock_data(ticker, market)
        target_sector = analyzed_stock_data.get("sector")

        if not target_sector:
            logger.warning(
                f"Could not determine sector for ticker {ticker}. Defaulting to 0 weight."
            )
            return 0.0

        # 2. Get user's portfolio with all positions
        portfolio_result = await db.execute(
            select(Portfolio)
            .where(Portfolio.user_id == user.id)
            .options(selectinload(Portfolio.positions))
        )
        portfolio = portfolio_result.scalars().first()

        if not portfolio or not portfolio.positions:
            return 0.0

        # 3. Calculate total portfolio value and sector-specific value
        total_portfolio_value = 0.0
        sector_portfolio_value = 0.0

        for position in portfolio.positions:
            try:
                position_data = await market_data_client.get_stock_data(
                    position.ticker, position.market
                )
                position_value = position.quantity * position_data["current_price"]
                total_portfolio_value += position_value

                if position_data.get("sector") == target_sector:
                    sector_portfolio_value += position_value
            except Exception as e:
                logger.error(
                    f"Failed to get market data for portfolio position {position.ticker}: {e}"
                )
                # If we can't get price, we can't value the portfolio accurately. Skip this position.
                continue

        # 4. Calculate weight
        if total_portfolio_value == 0:
            return 0.0

        weight = sector_portfolio_value / total_portfolio_value
        logger.info(
            f"Calculated portfolio sector weight for user {user.id} and sector '{target_sector}': {weight:.2f}"
        )
        return weight

    except Exception as e:
        logger.error(
            f"Failed to calculate portfolio sector weight for user {user.id} and ticker {ticker}: {e}"
        )
        return 0.0


@router.websocket("/analyze")
async def websocket_endpoint(
    websocket: WebSocket, token: str = Query(None), db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time stock analysis streaming."""
    await websocket.accept()

    user = await get_current_user_ws(token, db)
    # Allow anonymous access for now, but with limited functionality
    # if not user:
    #     await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    #     return

    # Register connection for authenticated users (for notifications)
    if user:
        await connection_manager.connect(user.id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            request_type = data.get("type", "analyze")  # "analyze" or "compare"

            # Handle comparison requests
            if request_type == "compare":
                tickers = data.get("tickers", [])
                market_str = data.get("market", "US")
                market = Market(market_str)

                if not tickers or len(tickers) < 2:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "agent": None,
                            "data": {
                                "message": "At least 2 tickers required for comparison"
                            },
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    continue

                graph = BoardroomGraph()
                async for event in graph.run_comparison_streaming(tickers, market):
                    await websocket.send_json(
                        {
                            "type": event["type"].value,
                            "agent": event["agent"].value if event["agent"] else None,
                            "data": _serialize(event["data"]),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                continue

            # Handle single stock analysis
            ticker = data.get("ticker")
            market_str = data.get("market", "US")
            market = Market(market_str)
            mode_str = data.get("mode", "standard")
            analysis_mode = AnalysisMode(mode_str)

            portfolio_sector_weight = 0.0
            if user:
                portfolio_sector_weight = await _calculate_portfolio_sector_weight(
                    db, user, ticker, market
                )
            else:
                # For anonymous users, we can't calculate weight
                logger.info("Anonymous user analysis, portfolio weight is 0.")

            graph = BoardroomGraph()

            # Variables to hold session execution data for persistence
            current_session_id = None

            async for event in graph.run_streaming(
                ticker, market, portfolio_sector_weight, analysis_mode
            ):
                # Send to client
                await websocket.send_json(
                    {
                        "type": event["type"].value,
                        "agent": event["agent"].value if event["agent"] else None,
                        "data": _serialize(event["data"]),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # Persistence logic (only for logged-in users)
                if not user:
                    continue

                evt_type = event["type"]
                evt_data = event["data"]

                if evt_type == WSMessageType.ANALYSIS_STARTED:
                    current_session_id = uuid.UUID(evt_data["audit_id"])
                    new_session = AnalysisSession(
                        id=current_session_id,
                        user_id=user.id,
                        ticker=ticker,
                        market=market,
                        created_at=datetime.now(),
                    )
                    db.add(new_session)
                    await db.commit()

                elif evt_type == WSMessageType.AGENT_COMPLETED and current_session_id:
                    agent_type = event["agent"]
                    report = AgentReport(
                        session_id=current_session_id,
                        agent_type=agent_type,
                        report_data=_serialize(evt_data),
                    )
                    db.add(report)
                    await db.commit()

                elif evt_type == WSMessageType.DECISION and current_session_id:
                    action = Action(evt_data.get("action"))
                    decision = FinalDecision(
                        session_id=current_session_id,
                        action=action,
                        confidence=evt_data.get("confidence", 0.0),
                        rationale=evt_data.get("reasoning", ""),
                        vetoed=False,
                    )
                    db.add(decision)

                    session = await db.get(AnalysisSession, current_session_id)
                    if session:
                        session.completed_at = datetime.now()

                    await db.commit()
                    await create_analysis_outcome(db, current_session_id)

                elif evt_type == WSMessageType.VETO and current_session_id:
                    decision = FinalDecision(
                        session_id=current_session_id,
                        action=Action.HOLD,
                        confidence=0.0,
                        rationale=evt_data.get("reason", "Risk Management Veto"),
                        vetoed=True,
                        veto_reason=evt_data.get("reason"),
                    )
                    db.add(decision)

                    session = await db.get(AnalysisSession, current_session_id)
                    if session:
                        session.completed_at = datetime.now()

                    await db.commit()
                    await create_analysis_outcome(db, current_session_id)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
        if user:
            connection_manager.disconnect(user.id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        if user:
            connection_manager.disconnect(user.id, websocket)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass


def _serialize(data):
    """Convert data to JSON-serializable format."""
    if isinstance(data, dict):
        return {k: _serialize(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_serialize(v) for v in data]
    if hasattr(data, "value"):  # Enum
        return data.value
    if isinstance(data, uuid.UUID):
        return str(data)
    if hasattr(data, "isoformat"):  # datetime
        return data.isoformat()
    return data
