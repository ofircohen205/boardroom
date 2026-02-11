"""
Integration tests for backtest engine and full flow.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.backtest.schemas import AgentWeights, BacktestConfig, StrategyCreate
from backend.backtest.engine import run_backtest
from backend.dao.backtesting import PaperAccountDAO, StrategyDAO
from backend.data.historical import fetch_and_store_historical_prices, get_price_range
from backend.db.models.backtesting import (
    HistoricalPrice,
)


@pytest.mark.asyncio
class TestHistoricalDataPipeline:
    """Tests for historical data fetching and storage."""

    async def test_fetch_and_store_historical_prices(self, db_session: AsyncSession):
        """Test that historical prices are fetched and stored correctly."""
        ticker = "AAPL"
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        # Fetch and store (will call Yahoo Finance in real test, mock in unit test)
        count = await fetch_and_store_historical_prices(
            db_session, ticker, start_date, end_date
        )

        # Verify data was stored
        assert count > 0, "Should have inserted price data"

        # Query stored prices
        stmt = select(HistoricalPrice).where(
            HistoricalPrice.ticker == ticker,
            HistoricalPrice.date >= start_date,
            HistoricalPrice.date <= end_date,
        )
        result = await db_session.execute(stmt)
        prices = result.scalars().all()

        assert len(prices) > 0, "Prices should be stored in database"
        # Verify structure
        assert all(p.open > 0 for p in prices), "Open prices should be positive"
        assert all(p.close > 0 for p in prices), "Close prices should be positive"
        assert all(p.volume > 0 for p in prices), "Volume should be positive"

    async def test_get_price_range(self, db_session: AsyncSession):
        """Test retrieving price range from database."""
        # First insert some test data
        ticker = "TEST"
        today = date.today()
        prices_to_insert = [
            HistoricalPrice(
                ticker=ticker,
                date=today - timedelta(days=i),
                open=Decimal("100"),
                high=Decimal("105"),
                low=Decimal("95"),
                close=Decimal(str(100 + i)),
                adjusted_close=Decimal(str(100 + i)),
                volume=1000000,
            )
            for i in range(10)
        ]
        db_session.add_all(prices_to_insert)
        await db_session.commit()

        # Retrieve range
        start = today - timedelta(days=9)
        end = today
        prices = await get_price_range(db_session, ticker, start, end)

        assert len(prices) == 10, "Should retrieve all 10 prices"
        assert prices[0].date <= prices[-1].date, (
            "Prices should be in ascending date order"
        )


@pytest.mark.asyncio
class TestBacktestEngine:
    """Tests for backtest engine execution."""

    async def test_backtest_generates_equity_curve(self, db_session: AsyncSession):
        """Test that backtest generates valid equity curve."""
        # Create test strategy
        strategy_dao = StrategyDAO(db_session)
        strategy_data = StrategyCreate(
            name="Test Strategy",
            description="Equal weight strategy",
            weights=AgentWeights(fundamental=0.33, technical=0.33, sentiment=0.34),
        )
        strategy = await strategy_dao.create_strategy(
            user_id="test-user", strategy_data=strategy_data
        )

        # Prepare test historical data (30 days)
        ticker = "BACKTEST"
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        # Insert mock historical data with uptrend
        for i in range(30):
            price = HistoricalPrice(
                ticker=ticker,
                date=start_date + timedelta(days=i),
                open=Decimal(str(100 + i)),
                high=Decimal(str(105 + i)),
                low=Decimal(str(95 + i)),
                close=Decimal(str(100 + i)),
                adjusted_close=Decimal(str(100 + i)),
                volume=1000000,
            )
            db_session.add(price)
        await db_session.commit()

        # Run backtest
        config = BacktestConfig(
            ticker=ticker,
            strategy_id=str(strategy.id),
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
            check_frequency="daily",
            position_size_pct=0.5,
        )

        result = await run_backtest(db_session, config)

        # Verify result structure
        assert result.total_return is not None, "Should calculate total return"
        assert result.annualized_return is not None, (
            "Should calculate annualized return"
        )
        assert result.max_drawdown <= 0, "Max drawdown should be <= 0"
        assert len(result.equity_curve) > 0, "Should generate equity curve"
        assert len(result.trades) >= 0, "Should have trades list"

        # Verify equity curve structure
        for point in result.equity_curve:
            assert point.date is not None
            assert point.equity > 0, "Equity should always be positive"

    async def test_backtest_executes_trades(self, db_session: AsyncSession):
        """Test that backtest executes trades based on signals."""
        # Create aggressive buy strategy (high weights on all factors)
        strategy_dao = StrategyDAO(db_session)
        strategy_data = StrategyCreate(
            name="Aggressive Buy",
            description="High threshold strategy",
            weights=AgentWeights(fundamental=0.4, technical=0.4, sentiment=0.2),
        )
        strategy = await strategy_dao.create_strategy(
            user_id="test-user", strategy_data=strategy_data
        )

        # Create strong uptrend data
        ticker = "TRADE"
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 15)

        for i in range(15):
            price = HistoricalPrice(
                ticker=ticker,
                date=start_date + timedelta(days=i),
                open=Decimal(str(100 + i * 5)),  # Strong uptrend
                high=Decimal(str(105 + i * 5)),
                low=Decimal(str(95 + i * 5)),
                close=Decimal(str(100 + i * 5)),
                adjusted_close=Decimal(str(100 + i * 5)),
                volume=2000000,
            )
            db_session.add(price)
        await db_session.commit()

        # Run backtest
        config = BacktestConfig(
            ticker=ticker,
            strategy_id=str(strategy.id),
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
            check_frequency="daily",
            position_size_pct=0.5,
        )

        result = await run_backtest(db_session, config)

        # Should execute at least one BUY trade in strong uptrend
        assert result.total_trades > 0, "Should execute trades in strong trend"
        buy_trades = [t for t in result.trades if t.type == "BUY"]
        assert len(buy_trades) > 0, "Should have BUY trades in uptrend"

    async def test_backtest_stop_loss_triggers(self, db_session: AsyncSession):
        """Test that stop loss exits position when triggered."""
        # Create strategy
        strategy_dao = StrategyDAO(db_session)
        strategy_data = StrategyCreate(
            name="Stop Loss Test",
            description="Strategy with stop loss",
            weights=AgentWeights(fundamental=0.5, technical=0.5, sentiment=0.0),
        )
        strategy = await strategy_dao.create_strategy(
            user_id="test-user", strategy_data=strategy_data
        )

        # Create data with sharp decline after initial rise
        ticker = "STOPLOSS"
        start_date = date(2024, 1, 1)

        prices_data = []
        # Days 0-5: Rise to 150
        for i in range(5):
            prices_data.append(
                (start_date + timedelta(days=i), Decimal(str(100 + i * 10)))
            )
        # Days 6-10: Sharp drop to 100 (should trigger 10% stop loss)
        for i in range(5, 10):
            prices_data.append(
                (start_date + timedelta(days=i), Decimal(str(150 - (i - 5) * 10)))
            )

        for date_val, price in prices_data:
            db_session.add(
                HistoricalPrice(
                    ticker=ticker,
                    date=date_val,
                    open=price,
                    high=price * Decimal("1.02"),
                    low=price * Decimal("0.98"),
                    close=price,
                    adjusted_close=price,
                    volume=1000000,
                )
            )
        await db_session.commit()

        # Run backtest with 10% stop loss
        config = BacktestConfig(
            ticker=ticker,
            strategy_id=str(strategy.id),
            start_date=start_date,
            end_date=start_date + timedelta(days=9),
            initial_capital=10000.0,
            check_frequency="daily",
            position_size_pct=0.5,
            stop_loss_pct=0.10,  # 10% stop loss
        )

        result = await run_backtest(db_session, config)

        # Should have executed stop loss SELL
        sell_trades = [t for t in result.trades if t.type == "SELL"]
        assert len(sell_trades) > 0, "Stop loss should trigger SELL"

    async def test_backtest_metrics_calculation(self, db_session: AsyncSession):
        """Test that backtest calculates all required metrics."""
        strategy_dao = StrategyDAO(db_session)
        strategy_data = StrategyCreate(
            name="Metrics Test",
            description="Test metrics calculation",
            weights=AgentWeights(fundamental=0.5, technical=0.3, sentiment=0.2),
        )
        strategy = await strategy_dao.create_strategy(
            user_id="test-user", strategy_data=strategy_data
        )

        # Create 60 days of data for meaningful metrics
        ticker = "METRICS"
        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 1)

        for i in range(60):
            price = Decimal(str(100 + (i % 10)))  # Oscillating prices
            db_session.add(
                HistoricalPrice(
                    ticker=ticker,
                    date=start_date + timedelta(days=i),
                    open=price,
                    high=price * Decimal("1.01"),
                    low=price * Decimal("0.99"),
                    close=price,
                    adjusted_close=price,
                    volume=1500000,
                )
            )
        await db_session.commit()

        config = BacktestConfig(
            ticker=ticker,
            strategy_id=str(strategy.id),
            start_date=start_date,
            end_date=end_date,
            initial_capital=10000.0,
            check_frequency="daily",
            position_size_pct=0.5,
        )

        result = await run_backtest(db_session, config)

        # Verify all metrics are calculated
        assert result.total_return is not None
        assert result.annualized_return is not None
        assert result.sharpe_ratio is not None or result.sharpe_ratio == 0.0
        assert result.max_drawdown is not None
        assert result.win_rate is not None
        assert result.buy_and_hold_return is not None


@pytest.mark.asyncio
class TestPaperTradingFlow:
    """Tests for paper trading system."""

    async def test_create_paper_account(self, db_session: AsyncSession):
        """Test creating a new paper trading account."""
        strategy_dao = StrategyDAO(db_session)
        strategy_data = StrategyCreate(
            name="Paper Strategy",
            description="For paper trading",
            weights=AgentWeights(fundamental=0.4, technical=0.4, sentiment=0.2),
        )
        strategy = await strategy_dao.create_strategy(
            user_id="test-user", strategy_data=strategy_data
        )

        # Create paper account
        paper_dao = PaperAccountDAO(db_session)
        account = await paper_dao.create_account(
            user_id="test-user",
            name="Test Account",
            initial_balance=Decimal("10000.00"),
            strategy_id=strategy.id,
        )

        assert account.name == "Test Account"
        assert account.cash_balance == Decimal("10000.00")
        assert account.total_value == Decimal("10000.00")
        assert account.strategy_id == strategy.id

    async def test_execute_paper_trade_buy(self, db_session: AsyncSession):
        """Test executing a paper BUY trade."""
        # Setup account
        strategy_dao = StrategyDAO(db_session)
        strategy = await strategy_dao.create_strategy(
            user_id="test-user",
            strategy_data=StrategyCreate(
                name="Trade Test",
                description="Test",
                weights=AgentWeights(fundamental=0.5, technical=0.5, sentiment=0.0),
            ),
        )

        paper_dao = PaperAccountDAO(db_session)
        account = await paper_dao.create_account(
            user_id="test-user",
            name="Buy Test",
            initial_balance=Decimal("10000.00"),
            strategy_id=strategy.id,
        )

        # Execute BUY trade
        trade = await paper_dao.execute_trade(
            account_id=account.id,
            ticker="AAPL",
            action="BUY",
            quantity=10,
            price=Decimal("150.00"),
        )

        # Verify trade
        assert trade.ticker == "AAPL"
        assert trade.action == "BUY"
        assert trade.quantity == 10
        assert trade.price == Decimal("150.00")
        assert trade.total == Decimal("1500.00")

        # Verify account updated
        await db_session.refresh(account)
        assert account.cash_balance == Decimal("8500.00")  # 10000 - 1500

    async def test_execute_paper_trade_sell(self, db_session: AsyncSession):
        """Test executing a paper SELL trade."""
        # Setup account with existing position
        strategy_dao = StrategyDAO(db_session)
        strategy = await strategy_dao.create_strategy(
            user_id="test-user",
            strategy_data=StrategyCreate(
                name="Sell Test",
                description="Test",
                weights=AgentWeights(fundamental=0.5, technical=0.5, sentiment=0.0),
            ),
        )

        paper_dao = PaperAccountDAO(db_session)
        account = await paper_dao.create_account(
            user_id="test-user",
            name="Sell Test",
            initial_balance=Decimal("10000.00"),
            strategy_id=strategy.id,
        )

        # First BUY to create position
        await paper_dao.execute_trade(
            account_id=account.id,
            ticker="TSLA",
            action="BUY",
            quantity=5,
            price=Decimal("200.00"),
        )

        # Then SELL
        sell_trade = await paper_dao.execute_trade(
            account_id=account.id,
            ticker="TSLA",
            action="SELL",
            quantity=3,
            price=Decimal("220.00"),
        )

        # Verify sell trade
        assert sell_trade.action == "SELL"
        assert sell_trade.quantity == 3
        assert sell_trade.total == Decimal("660.00")

        # Verify cash increased
        await db_session.refresh(account)
        # Started: 10000, bought 5@200=-1000, sold 3@220=+660
        expected_cash = Decimal("9660.00")
        assert account.cash_balance == expected_cash

    async def test_paper_trade_insufficient_funds(self, db_session: AsyncSession):
        """Test that trade fails with insufficient funds."""
        strategy_dao = StrategyDAO(db_session)
        strategy = await strategy_dao.create_strategy(
            user_id="test-user",
            strategy_data=StrategyCreate(
                name="Insufficient Test",
                description="Test",
                weights=AgentWeights(fundamental=0.5, technical=0.5, sentiment=0.0),
            ),
        )

        paper_dao = PaperAccountDAO(db_session)
        account = await paper_dao.create_account(
            user_id="test-user",
            name="Broke Account",
            initial_balance=Decimal("100.00"),
            strategy_id=strategy.id,
        )

        # Try to buy more than balance allows
        with pytest.raises(ValueError, match="Insufficient funds"):
            await paper_dao.execute_trade(
                account_id=account.id,
                ticker="GOOGL",
                action="BUY",
                quantity=10,
                price=Decimal("150.00"),  # Would cost 1500
            )
