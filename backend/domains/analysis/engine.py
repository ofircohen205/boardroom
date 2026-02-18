"""
Main backtest engine for running historical simulations.

Executes rules-based backtests on historical data, simulating agent
decisions and trading outcomes without LLM calls.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domains.analysis.scoring import (
    calculate_fundamental_score,
    calculate_sentiment_score,
    calculate_technical_score,
    calculate_weighted_decision,
)
from backend.shared.dao.backtesting import HistoricalFundamentalsDAO, HistoricalPriceDAO
from backend.shared.db.models.backtesting import BacktestFrequency

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for a backtest run."""

    ticker: str
    strategy_id: UUID
    start_date: date
    end_date: date
    initial_capital: Decimal
    check_frequency: BacktestFrequency = BacktestFrequency.DAILY
    position_size_pct: Decimal = Decimal("0.5")  # 50% of capital per trade
    stop_loss_pct: Decimal | None = None  # e.g., 0.10 = 10% stop loss
    take_profit_pct: Decimal | None = None  # e.g., 0.20 = 20% take profit

    # Strategy weights (loaded from Strategy model)
    agent_weights: dict[str, float] = field(default_factory=dict)
    buy_threshold: float = 70.0
    sell_threshold: float = 30.0


@dataclass
class Trade:
    """Record of a simulated trade."""

    date: str
    type: str  # "BUY" or "SELL"
    quantity: int
    price: float
    total: float
    commission: float = 0.0


@dataclass
class EquityPoint:
    """Point on the equity curve."""

    date: str
    equity: float
    cash: float
    position_value: float


@dataclass
class BacktestResult:
    """Results from a completed backtest."""

    config: BacktestConfig
    total_return: float
    annualized_return: float
    sharpe_ratio: float | None
    max_drawdown: float
    win_rate: float
    total_trades: int
    equity_curve: list[EquityPoint]
    trades: list[Trade]
    buy_and_hold_return: float
    execution_time_seconds: float | None = None


async def run_backtest(session: AsyncSession, config: BacktestConfig) -> BacktestResult:
    """Run a backtest simulation on historical data.

    Algorithm:
    1. Fetch historical price and fundamental data for date range
    2. Iterate through dates at specified frequency
    3. For each decision point:
       - Calculate technical score (from recent prices)
       - Calculate fundamental score (from most recent quarterly data)
       - Calculate sentiment score (from price momentum)
       - Apply strategy weights to get weighted score
       - Make BUY/SELL/HOLD decision based on thresholds
       - Execute trade if signal generated
       - Check stop loss / take profit if in position
    4. Calculate performance metrics
    5. Return results with equity curve and trade log

    Args:
        session: Database session for fetching historical data
        config: Backtest configuration

    Returns:
        BacktestResult with performance metrics and trade history

    Raises:
        ValueError: If insufficient historical data or invalid config
    """
    start_time = time.time()

    logger.info(
        f"Starting backtest for {config.ticker} from {config.start_date} to {config.end_date}"
    )

    # Fetch historical data
    price_dao = HistoricalPriceDAO(session)
    fundamentals_dao = HistoricalFundamentalsDAO(session)

    # Fetch price data with 50-day buffer for MA calculations
    price_buffer_days = 50
    buffered_start_date = config.start_date - timedelta(days=price_buffer_days + 30)
    all_prices = await price_dao.get_price_range(
        config.ticker, buffered_start_date, config.end_date
    )

    if len(all_prices) < price_buffer_days:
        raise ValueError(
            f"Insufficient price data for {config.ticker}. "
            f"Need at least {price_buffer_days} days, got {len(all_prices)}"
        )

    # Create date -> price mapping
    price_map = {price.date: price for price in all_prices}
    all_dates = sorted(price_map.keys())

    # Filter dates to backtest period
    backtest_dates = [d for d in all_dates if config.start_date <= d <= config.end_date]

    if not backtest_dates:
        raise ValueError(
            f"No trading days found between {config.start_date} and {config.end_date}"
        )

    logger.info(
        f"Loaded {len(all_prices)} price records, backtesting {len(backtest_dates)} days"
    )

    # Initialize portfolio state
    cash = float(config.initial_capital)
    position_shares = 0
    position_entry_price = 0.0

    equity_curve: list[EquityPoint] = []
    trades: list[Trade] = []
    peak_equity = cash

    # Get buy-and-hold benchmark
    buy_and_hold_shares = float(config.initial_capital) / float(
        price_map[backtest_dates[0]].adjusted_close
    )
    buy_and_hold_final_value = buy_and_hold_shares * float(
        price_map[backtest_dates[-1]].adjusted_close
    )
    buy_and_hold_return = (
        buy_and_hold_final_value - float(config.initial_capital)
    ) / float(config.initial_capital)

    # Iterate through backtest dates
    for i, current_date in enumerate(backtest_dates):
        current_price_record = price_map[current_date]
        current_price = float(current_price_record.adjusted_close)

        # Skip if frequency is weekly and not end of week
        if config.check_frequency == BacktestFrequency.WEEKLY:
            # Only make decisions on Fridays (weekday 4) or last day of backtest
            if current_date.weekday() != 4 and i != len(backtest_dates) - 1:
                # Still record equity for visualization
                position_value = position_shares * current_price
                total_equity = cash + position_value
                equity_curve.append(
                    EquityPoint(
                        date=current_date.isoformat(),
                        equity=total_equity,
                        cash=cash,
                        position_value=position_value,
                    )
                )
                continue

        # Check stop loss / take profit if in position
        if position_shares > 0:
            # Calculate current P&L
            current_pnl_pct = (
                current_price - position_entry_price
            ) / position_entry_price

            # Stop loss check
            if config.stop_loss_pct and current_pnl_pct <= -float(config.stop_loss_pct):
                # Execute stop loss sell
                trade_value = position_shares * current_price
                cash += trade_value
                trades.append(
                    Trade(
                        date=current_date.isoformat(),
                        type="SELL",
                        quantity=position_shares,
                        price=current_price,
                        total=trade_value,
                    )
                )
                logger.debug(
                    f"{current_date}: Stop loss triggered at {current_pnl_pct:.2%}. "
                    f"Sold {position_shares} shares @ ${current_price:.2f}"
                )
                position_shares = 0
                position_entry_price = 0.0

            # Take profit check
            elif config.take_profit_pct and current_pnl_pct >= float(
                config.take_profit_pct
            ):
                # Execute take profit sell
                trade_value = position_shares * current_price
                cash += trade_value
                trades.append(
                    Trade(
                        date=current_date.isoformat(),
                        type="SELL",
                        quantity=position_shares,
                        price=current_price,
                        total=trade_value,
                    )
                )
                logger.debug(
                    f"{current_date}: Take profit triggered at {current_pnl_pct:.2%}. "
                    f"Sold {position_shares} shares @ ${current_price:.2f}"
                )
                position_shares = 0
                position_entry_price = 0.0

        # Get price history up to current date (for scoring)
        price_history_end_idx = all_dates.index(current_date)
        price_history = [
            float(price_map[d].adjusted_close)
            for d in all_dates[: price_history_end_idx + 1]
        ]

        # Need at least 50 days for meaningful technical analysis
        if len(price_history) < 50:
            # Skip scoring, just record equity
            position_value = position_shares * current_price
            total_equity = cash + position_value
            equity_curve.append(
                EquityPoint(
                    date=current_date.isoformat(),
                    equity=total_equity,
                    cash=cash,
                    position_value=position_value,
                )
            )
            continue

        # Calculate agent scores
        technical_score = calculate_technical_score(
            [Decimal(str(p)) for p in price_history]
        )
        sentiment_score = calculate_sentiment_score(
            [Decimal(str(p)) for p in price_history]
        )

        # Get fundamental score (use most recent quarterly data as of current_date)
        fundamentals = await fundamentals_dao.get_fundamentals_at_date(
            config.ticker, current_date
        )
        fundamental_score = calculate_fundamental_score(fundamentals)

        # Calculate weighted decision
        scores = {
            "fundamental": fundamental_score,
            "technical": technical_score,
            "sentiment": sentiment_score,
        }
        decision = calculate_weighted_decision(
            scores,
            config.agent_weights,
            config.buy_threshold,
            config.sell_threshold,
        )

        # Execute trade based on decision
        if decision == "BUY" and position_shares == 0:
            # Buy with configured position size
            capital_to_invest = cash * float(config.position_size_pct)
            shares_to_buy = int(capital_to_invest / current_price)

            if shares_to_buy > 0:
                trade_cost = shares_to_buy * current_price
                cash -= trade_cost
                position_shares = shares_to_buy
                position_entry_price = current_price

                trades.append(
                    Trade(
                        date=current_date.isoformat(),
                        type="BUY",
                        quantity=shares_to_buy,
                        price=current_price,
                        total=trade_cost,
                    )
                )
                logger.debug(
                    f"{current_date}: BUY signal. Bought {shares_to_buy} shares @ ${current_price:.2f} "
                    f"(scores: F={fundamental_score:.0f}, T={technical_score:.0f}, S={sentiment_score:.0f})"
                )

        elif decision == "SELL" and position_shares > 0:
            # Sell entire position
            trade_value = position_shares * current_price
            cash += trade_value

            trades.append(
                Trade(
                    date=current_date.isoformat(),
                    type="SELL",
                    quantity=position_shares,
                    price=current_price,
                    total=trade_value,
                )
            )
            logger.debug(
                f"{current_date}: SELL signal. Sold {position_shares} shares @ ${current_price:.2f} "
                f"(scores: F={fundamental_score:.0f}, T={technical_score:.0f}, S={sentiment_score:.0f})"
            )
            position_shares = 0
            position_entry_price = 0.0

        # Record equity
        position_value = position_shares * current_price
        total_equity = cash + position_value
        equity_curve.append(
            EquityPoint(
                date=current_date.isoformat(),
                equity=total_equity,
                cash=cash,
                position_value=position_value,
            )
        )

        # Track peak for drawdown calculation
        if total_equity > peak_equity:
            peak_equity = total_equity

    # Close any open position at end
    if position_shares > 0:
        final_price = float(price_map[backtest_dates[-1]].adjusted_close)
        trade_value = position_shares * final_price
        cash += trade_value
        trades.append(
            Trade(
                date=backtest_dates[-1].isoformat(),
                type="SELL",
                quantity=position_shares,
                price=final_price,
                total=trade_value,
            )
        )
        position_shares = 0

    # Calculate performance metrics
    final_equity = equity_curve[-1].equity
    total_return = (final_equity - float(config.initial_capital)) / float(
        config.initial_capital
    )

    # Annualized return
    days_elapsed = (config.end_date - config.start_date).days
    years_elapsed = days_elapsed / 365.25
    if years_elapsed > 0:
        annualized_return = (1 + total_return) ** (1 / years_elapsed) - 1
    else:
        annualized_return = 0.0

    # Sharpe ratio (simplified: daily returns std)
    daily_returns = [
        (equity_curve[i].equity - equity_curve[i - 1].equity)
        / equity_curve[i - 1].equity
        for i in range(1, len(equity_curve))
    ]
    if daily_returns:
        mean_daily_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_daily_return) ** 2 for r in daily_returns) / len(
            daily_returns
        )
        std_daily_return = variance**0.5
        if std_daily_return > 0:
            sharpe_ratio = (mean_daily_return / std_daily_return) * (252**0.5)
        else:
            sharpe_ratio = 0.0
    else:
        sharpe_ratio = None

    # Max drawdown
    max_drawdown = 0.0
    peak_so_far = float(config.initial_capital)
    for point in equity_curve:
        if point.equity > peak_so_far:
            peak_so_far = point.equity
        drawdown = (point.equity - peak_so_far) / peak_so_far
        if drawdown < max_drawdown:
            max_drawdown = drawdown

    # Win rate (percentage of profitable trades)
    winning_trades = 0
    for i in range(0, len(trades), 2):  # Pairs: BUY then SELL
        if (
            i + 1 < len(trades)
            and trades[i].type == "BUY"
            and trades[i + 1].type == "SELL"
        ):
            profit = trades[i + 1].total - trades[i].total
            if profit > 0:
                winning_trades += 1

    total_trade_pairs = len(trades) // 2
    win_rate = winning_trades / total_trade_pairs if total_trade_pairs > 0 else 0.0

    execution_time = time.time() - start_time

    logger.info(
        f"Backtest complete for {config.ticker}: "
        f"Return={total_return:.2%}, Sharpe={sharpe_ratio:.2f}, "
        f"Max DD={max_drawdown:.2%}, Trades={len(trades)}, Time={execution_time:.1f}s"
    )

    return BacktestResult(
        config=config,
        total_return=total_return,
        annualized_return=annualized_return,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        total_trades=len(trades),
        equity_curve=equity_curve,
        trades=trades,
        buy_and_hold_return=buy_and_hold_return,
        execution_time_seconds=execution_time,
    )
