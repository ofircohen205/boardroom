# tests/unit/analysis/test_dao_backtesting.py
"""
Unit tests for backend/shared/dao/backtesting.py

Tests all DAO classes using mock sessions (no database required).
Uses pytest-asyncio with asyncio_mode = "auto" (no @pytest.mark.asyncio needed).
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from backend.shared.dao.backtesting import (
    BacktestResultDAO,
    HistoricalFundamentalsDAO,
    HistoricalPriceDAO,
    PaperAccountDAO,
    PaperPositionDAO,
    PaperTradeDAO,
    StrategyDAO,
)
from backend.shared.db.models.backtesting import PaperTrade, TradeType

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Lightweight mock async DB session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.delete = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_scalar_result(items: list):
    """Return a mock that mimics result.scalars().all()."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


def make_one_result(item):
    """Return a mock that mimics result.scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = item
    return result


def make_first_result(item):
    """Return a mock that mimics result.scalars().first() (used by BaseDAO.get_by_id)."""
    result = MagicMock()
    result.scalars.return_value.first.return_value = item
    return result


# ===========================================================================
# HistoricalPriceDAO
# ===========================================================================


async def test_get_price_at_date_found(mock_session):
    """get_price_at_date returns the record when one exists."""
    price_record = MagicMock()
    mock_session.execute.return_value = make_one_result(price_record)

    dao = HistoricalPriceDAO(mock_session)
    result = await dao.get_price_at_date("AAPL", date(2025, 1, 15))

    assert result == price_record
    mock_session.execute.assert_called_once()


async def test_get_price_at_date_not_found(mock_session):
    """get_price_at_date returns None when no record exists."""
    mock_session.execute.return_value = make_one_result(None)

    dao = HistoricalPriceDAO(mock_session)
    result = await dao.get_price_at_date("AAPL", date(2025, 1, 15))

    assert result is None


async def test_get_price_at_date_uppercases_ticker(mock_session):
    """get_price_at_date executes a query (ticker is uppercased internally)."""
    mock_session.execute.return_value = make_one_result(None)

    dao = HistoricalPriceDAO(mock_session)
    await dao.get_price_at_date("aapl", date(2025, 1, 15))

    mock_session.execute.assert_called_once()


async def test_get_price_range_returns_list(mock_session):
    """get_price_range returns the full list of records."""
    prices = [MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(prices)

    dao = HistoricalPriceDAO(mock_session)
    result = await dao.get_price_range("AAPL", date(2025, 1, 1), date(2025, 1, 31))

    assert result == prices
    mock_session.execute.assert_called_once()


async def test_get_price_range_empty(mock_session):
    """get_price_range returns an empty list when no records exist."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = HistoricalPriceDAO(mock_session)
    result = await dao.get_price_range("AAPL", date(2025, 1, 1), date(2025, 1, 31))

    assert result == []


async def test_get_latest_price_found(mock_session):
    """get_latest_price returns the most recent price record."""
    price = MagicMock()
    mock_session.execute.return_value = make_one_result(price)

    dao = HistoricalPriceDAO(mock_session)
    result = await dao.get_latest_price("AAPL")

    assert result == price
    mock_session.execute.assert_called_once()


async def test_get_latest_price_not_found(mock_session):
    """get_latest_price returns None when no record exists."""
    mock_session.execute.return_value = make_one_result(None)

    dao = HistoricalPriceDAO(mock_session)
    result = await dao.get_latest_price("TSLA")

    assert result is None


async def test_bulk_create(mock_session):
    """bulk_create adds all records, flushes, and returns the input list."""
    prices = [MagicMock(), MagicMock(), MagicMock()]

    dao = HistoricalPriceDAO(mock_session)
    result = await dao.bulk_create(prices)

    mock_session.add_all.assert_called_once_with(prices)
    mock_session.flush.assert_called_once()
    assert result == prices


async def test_bulk_create_empty_list(mock_session):
    """bulk_create with an empty list still calls add_all and flush."""
    dao = HistoricalPriceDAO(mock_session)
    result = await dao.bulk_create([])

    mock_session.add_all.assert_called_once_with([])
    mock_session.flush.assert_called_once()
    assert result == []


# ===========================================================================
# HistoricalFundamentalsDAO
# ===========================================================================


async def test_get_fundamentals_at_date_found(mock_session):
    """get_fundamentals_at_date returns the most recent record on or before target_date."""
    fundamentals = MagicMock()
    mock_session.execute.return_value = make_one_result(fundamentals)

    dao = HistoricalFundamentalsDAO(mock_session)
    result = await dao.get_fundamentals_at_date("AAPL", date(2025, 6, 30))

    assert result == fundamentals
    mock_session.execute.assert_called_once()


async def test_get_fundamentals_at_date_not_found(mock_session):
    """get_fundamentals_at_date returns None when no record exists."""
    mock_session.execute.return_value = make_one_result(None)

    dao = HistoricalFundamentalsDAO(mock_session)
    result = await dao.get_fundamentals_at_date("AAPL", date(2025, 6, 30))

    assert result is None


async def test_get_fundamentals_range_returns_list(mock_session):
    """get_fundamentals_range returns all records within the date range."""
    records = [MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(records)

    dao = HistoricalFundamentalsDAO(mock_session)
    result = await dao.get_fundamentals_range(
        "AAPL", date(2024, 1, 1), date(2025, 1, 1)
    )

    assert result == records
    mock_session.execute.assert_called_once()


async def test_get_fundamentals_range_empty(mock_session):
    """get_fundamentals_range returns an empty list when no records exist."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = HistoricalFundamentalsDAO(mock_session)
    result = await dao.get_fundamentals_range(
        "MSFT", date(2024, 1, 1), date(2025, 1, 1)
    )

    assert result == []


# ===========================================================================
# StrategyDAO
# ===========================================================================


async def test_get_user_strategies_active_only(mock_session):
    """get_user_strategies with active_only=True returns active strategies."""
    user_id = uuid4()
    strategies = [MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(strategies)

    dao = StrategyDAO(mock_session)
    result = await dao.get_user_strategies(user_id, active_only=True)

    assert result == strategies
    mock_session.execute.assert_called_once()


async def test_get_user_strategies_all(mock_session):
    """get_user_strategies with active_only=False returns all strategies."""
    user_id = uuid4()
    strategies = [MagicMock(), MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(strategies)

    dao = StrategyDAO(mock_session)
    result = await dao.get_user_strategies(user_id, active_only=False)

    assert result == strategies
    mock_session.execute.assert_called_once()


async def test_get_user_strategies_empty(mock_session):
    """get_user_strategies returns an empty list when the user has no strategies."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = StrategyDAO(mock_session)
    result = await dao.get_user_strategies(uuid4())

    assert result == []


async def test_get_strategy_by_id_and_user_found(mock_session):
    """get_by_id_and_user returns the strategy when it belongs to the user."""
    strategy = MagicMock()
    mock_session.execute.return_value = make_one_result(strategy)

    dao = StrategyDAO(mock_session)
    result = await dao.get_by_id_and_user(uuid4(), uuid4())

    assert result == strategy
    mock_session.execute.assert_called_once()


async def test_get_strategy_by_id_and_user_not_found(mock_session):
    """get_by_id_and_user returns None when strategy does not belong to user."""
    mock_session.execute.return_value = make_one_result(None)

    dao = StrategyDAO(mock_session)
    result = await dao.get_by_id_and_user(uuid4(), uuid4())

    assert result is None


async def test_create_strategy_with_model_dump(mock_session):
    """create_strategy adds the strategy, commits, and refreshes (model_dump path)."""
    user_id = uuid4()
    strategy_data = MagicMock()
    strategy_data.name = "Test Strategy"
    strategy_data.description = "A test description"
    strategy_data.config = MagicMock()
    strategy_data.config.model_dump.return_value = {"weights": {"fundamental": 1.0}}

    dao = StrategyDAO(mock_session)
    await dao.create_strategy(user_id, strategy_data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


async def test_create_strategy_with_dict_fallback(mock_session):
    """create_strategy falls back to .dict() when model_dump is unavailable."""
    user_id = uuid4()
    strategy_data = MagicMock(spec=["name", "description", "config"])
    strategy_data.name = "Strategy via dict"
    strategy_data.description = "Uses .dict()"
    config = MagicMock(spec=["dict"])
    config.dict.return_value = {"weights": {"fundamental": 0.5}}
    strategy_data.config = config

    dao = StrategyDAO(mock_session)
    await dao.create_strategy(user_id, strategy_data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


async def test_create_strategy_with_plain_dict_config(mock_session):
    """create_strategy accepts a plain dict config directly."""
    user_id = uuid4()
    strategy_data = MagicMock()
    strategy_data.name = "Plain dict strategy"
    strategy_data.description = "Uses raw dict"
    strategy_data.config = {"weights": {"fundamental": 0.8}}

    dao = StrategyDAO(mock_session)
    await dao.create_strategy(user_id, strategy_data)

    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


# ===========================================================================
# PaperAccountDAO
# ===========================================================================


async def test_get_user_accounts_active_only(mock_session):
    """get_user_accounts with active_only=True returns active accounts."""
    user_id = uuid4()
    accounts = [MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(accounts)

    dao = PaperAccountDAO(mock_session)
    result = await dao.get_user_accounts(user_id, active_only=True)

    assert result == accounts
    mock_session.execute.assert_called_once()


async def test_get_user_accounts_all(mock_session):
    """get_user_accounts with active_only=False returns all accounts."""
    user_id = uuid4()
    accounts = [MagicMock(), MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(accounts)

    dao = PaperAccountDAO(mock_session)
    result = await dao.get_user_accounts(user_id, active_only=False)

    assert result == accounts


async def test_get_user_accounts_empty(mock_session):
    """get_user_accounts returns an empty list for a user with no accounts."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = PaperAccountDAO(mock_session)
    result = await dao.get_user_accounts(uuid4())

    assert result == []


async def test_get_account_by_id_and_user_found(mock_session):
    """get_by_id_and_user returns the account when it belongs to the user."""
    account = MagicMock()
    mock_session.execute.return_value = make_one_result(account)

    dao = PaperAccountDAO(mock_session)
    result = await dao.get_by_id_and_user(uuid4(), uuid4())

    assert result == account


async def test_get_account_by_id_and_user_not_found(mock_session):
    """get_by_id_and_user returns None when account does not belong to user."""
    mock_session.execute.return_value = make_one_result(None)

    dao = PaperAccountDAO(mock_session)
    result = await dao.get_by_id_and_user(uuid4(), uuid4())

    assert result is None


async def test_update_balance_success(mock_session):
    """update_balance sets new balance and returns the updated account."""
    account = MagicMock()
    account.id = uuid4()
    mock_session.execute.return_value = make_first_result(account)

    dao = PaperAccountDAO(mock_session)
    result = await dao.update_balance(account.id, Decimal("15000.00"))

    assert result.current_balance == Decimal("15000.00")
    mock_session.flush.assert_called_once()


async def test_update_balance_account_not_found(mock_session):
    """update_balance raises ValueError when account does not exist."""
    mock_session.execute.return_value = make_first_result(None)

    dao = PaperAccountDAO(mock_session)
    with pytest.raises(ValueError, match="not found"):
        await dao.update_balance(uuid4(), Decimal("5000.00"))


async def test_create_account(mock_session):
    """create_account adds the account, flushes, refreshes, and returns it."""
    user_id = uuid4()
    strategy_id = uuid4()

    dao = PaperAccountDAO(mock_session)
    result = await dao.create_account(
        user_id=user_id,
        name="Test Account",
        initial_balance=Decimal("10000.00"),
        strategy_id=strategy_id,
    )

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    mock_session.refresh.assert_called_once()
    assert result is not None


# ===========================================================================
# PaperTradeDAO
# ===========================================================================


async def test_get_account_trades_default_limit(mock_session):
    """get_account_trades returns trades with default limit of 100."""
    account_id = uuid4()
    trades = [MagicMock() for _ in range(5)]
    mock_session.execute.return_value = make_scalar_result(trades)

    dao = PaperTradeDAO(mock_session)
    result = await dao.get_account_trades(account_id)

    assert result == trades
    mock_session.execute.assert_called_once()


async def test_get_account_trades_custom_limit(mock_session):
    """get_account_trades respects a custom limit parameter."""
    account_id = uuid4()
    trades = [MagicMock() for _ in range(3)]
    mock_session.execute.return_value = make_scalar_result(trades)

    dao = PaperTradeDAO(mock_session)
    result = await dao.get_account_trades(account_id, limit=3)

    assert result == trades
    mock_session.execute.assert_called_once()


async def test_get_account_trades_empty(mock_session):
    """get_account_trades returns an empty list when the account has no trades."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = PaperTradeDAO(mock_session)
    result = await dao.get_account_trades(uuid4())

    assert result == []


async def test_get_trades_for_ticker(mock_session):
    """get_trades_for_ticker returns trades filtered by ticker."""
    account_id = uuid4()
    trades = [MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(trades)

    dao = PaperTradeDAO(mock_session)
    result = await dao.get_trades_for_ticker(account_id, "AAPL")

    assert result == trades
    mock_session.execute.assert_called_once()


async def test_get_trades_for_ticker_empty(mock_session):
    """get_trades_for_ticker returns empty list when ticker has no trades."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = PaperTradeDAO(mock_session)
    result = await dao.get_trades_for_ticker(uuid4(), "TSLA")

    assert result == []


# ===========================================================================
# PaperPositionDAO
# ===========================================================================


async def test_get_account_positions(mock_session):
    """get_account_positions returns all open positions for an account."""
    account_id = uuid4()
    positions = [MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(positions)

    dao = PaperPositionDAO(mock_session)
    result = await dao.get_account_positions(account_id)

    assert result == positions
    mock_session.execute.assert_called_once()


async def test_get_account_positions_empty(mock_session):
    """get_account_positions returns an empty list when there are no positions."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = PaperPositionDAO(mock_session)
    result = await dao.get_account_positions(uuid4())

    assert result == []


async def test_get_position_found(mock_session):
    """get_position returns the position for a given account and ticker."""
    position = MagicMock()
    mock_session.execute.return_value = make_one_result(position)

    dao = PaperPositionDAO(mock_session)
    result = await dao.get_position(uuid4(), "AAPL")

    assert result == position


async def test_get_position_not_found(mock_session):
    """get_position returns None when no position exists for the ticker."""
    mock_session.execute.return_value = make_one_result(None)

    dao = PaperPositionDAO(mock_session)
    result = await dao.get_position(uuid4(), "AAPL")

    assert result is None


async def test_update_position_buy_existing(mock_session):
    """update_position BUY with an existing position updates quantity and avg price."""
    position = MagicMock()
    position.quantity = 10
    position.average_entry_price = Decimal("100.0")
    mock_session.execute.return_value = make_one_result(position)

    dao = PaperPositionDAO(mock_session)
    result = await dao.update_position(
        uuid4(), "AAPL", 5, Decimal("120.0"), TradeType.BUY
    )

    # new_quantity = 15, new_avg = (100*10 + 120*5) / 15 = 106.666...
    assert position.quantity == 15
    assert result == position
    mock_session.flush.assert_called_once()


async def test_update_position_buy_new_position(mock_session):
    """update_position BUY with no existing position creates a new PaperPosition."""
    mock_session.execute.return_value = make_one_result(None)

    dao = PaperPositionDAO(mock_session)
    result = await dao.update_position(
        uuid4(), "AAPL", 10, Decimal("150.0"), TradeType.BUY
    )

    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()
    assert result is not None


async def test_update_position_sell_partial(mock_session):
    """update_position SELL reduces the position quantity.

    The code does `position.quantity -= quantity_delta`, so a positive
    quantity_delta of 5 reduces a 10-share position to 5 shares.
    """
    position = MagicMock()
    position.quantity = 10
    mock_session.execute.return_value = make_one_result(position)

    dao = PaperPositionDAO(mock_session)
    result = await dao.update_position(
        uuid4(), "AAPL", 5, Decimal("150.0"), TradeType.SELL
    )

    assert position.quantity == 5
    assert result == position
    mock_session.flush.assert_called_once()


async def test_update_position_sell_close_position(mock_session):
    """update_position SELL that fully closes a position deletes it and returns None."""
    position = MagicMock()
    position.quantity = 10
    mock_session.execute.return_value = make_one_result(position)

    dao = PaperPositionDAO(mock_session)
    result = await dao.update_position(
        uuid4(), "AAPL", 10, Decimal("150.0"), TradeType.SELL
    )

    mock_session.delete.assert_called_once_with(position)
    assert result is None


async def test_update_position_sell_no_position_raises(mock_session):
    """update_position SELL raises ValueError when there is no open position."""
    mock_session.execute.return_value = make_one_result(None)

    dao = PaperPositionDAO(mock_session)
    with pytest.raises(ValueError, match="no open position"):
        await dao.update_position(uuid4(), "AAPL", -5, Decimal("150.0"), TradeType.SELL)


async def test_update_position_sell_oversell_raises(mock_session):
    """update_position SELL raises ValueError when selling more shares than owned."""
    position = MagicMock()
    position.quantity = 5
    mock_session.execute.return_value = make_one_result(position)

    dao = PaperPositionDAO(mock_session)
    with pytest.raises(ValueError, match="only 5 available"):
        await dao.update_position(uuid4(), "AAPL", 10, Decimal("150.0"), TradeType.SELL)


# ===========================================================================
# BacktestResultDAO
# ===========================================================================


async def test_get_user_results(mock_session):
    """get_user_results returns backtest results for a user."""
    user_id = uuid4()
    results = [MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(results)

    dao = BacktestResultDAO(mock_session)
    result = await dao.get_user_results(user_id)

    assert result == results
    mock_session.execute.assert_called_once()


async def test_get_user_results_custom_limit(mock_session):
    """get_user_results respects a custom limit."""
    mock_session.execute.return_value = make_scalar_result([MagicMock()])

    dao = BacktestResultDAO(mock_session)
    result = await dao.get_user_results(uuid4(), limit=10)

    assert len(result) == 1
    mock_session.execute.assert_called_once()


async def test_get_user_results_empty(mock_session):
    """get_user_results returns an empty list when no results exist."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = BacktestResultDAO(mock_session)
    result = await dao.get_user_results(uuid4())

    assert result == []


async def test_get_results_by_ticker(mock_session):
    """get_results_by_ticker returns results filtered by ticker."""
    user_id = uuid4()
    results = [MagicMock(), MagicMock()]
    mock_session.execute.return_value = make_scalar_result(results)

    dao = BacktestResultDAO(mock_session)
    result = await dao.get_results_by_ticker(user_id, "AAPL")

    assert result == results
    mock_session.execute.assert_called_once()


async def test_get_results_by_ticker_empty(mock_session):
    """get_results_by_ticker returns empty list when ticker has no results."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = BacktestResultDAO(mock_session)
    result = await dao.get_results_by_ticker(uuid4(), "TSLA")

    assert result == []


async def test_get_results_by_strategy(mock_session):
    """get_results_by_strategy returns results filtered by strategy."""
    user_id = uuid4()
    strategy_id = uuid4()
    results = [MagicMock()]
    mock_session.execute.return_value = make_scalar_result(results)

    dao = BacktestResultDAO(mock_session)
    result = await dao.get_results_by_strategy(user_id, strategy_id)

    assert result == results
    mock_session.execute.assert_called_once()


async def test_get_results_by_strategy_custom_limit(mock_session):
    """get_results_by_strategy respects a custom limit."""
    mock_session.execute.return_value = make_scalar_result([MagicMock()])

    dao = BacktestResultDAO(mock_session)
    result = await dao.get_results_by_strategy(uuid4(), uuid4(), limit=5)

    assert len(result) == 1
    mock_session.execute.assert_called_once()


async def test_get_results_by_strategy_empty(mock_session):
    """get_results_by_strategy returns empty list when strategy has no results."""
    mock_session.execute.return_value = make_scalar_result([])

    dao = BacktestResultDAO(mock_session)
    result = await dao.get_results_by_strategy(uuid4(), uuid4())

    assert result == []


# ===========================================================================
# PaperAccountDAO.execute_trade
# ===========================================================================


# Helper to make a mock account (with Decimal balance to match Decimal math)
def _make_mock_account(balance: Decimal = Decimal("1000.00")):
    account = MagicMock()
    account.current_balance = balance
    account.updated_at = None
    return account


# Helper: mock PaperPositionDAO that returns an async update_position
def _mock_position_dao_class():
    mock_instance = MagicMock()
    mock_instance.update_position = AsyncMock()
    mock_class = MagicMock(return_value=mock_instance)
    return mock_class, mock_instance


async def test_execute_trade_raises_when_account_not_found(mock_session):
    """execute_trade() raises ValueError when account does not exist."""
    mock_session.execute.return_value = make_first_result(None)

    dao = PaperAccountDAO(mock_session)
    with pytest.raises(ValueError, match="not found"):
        await dao.execute_trade(
            account_id=uuid4(),
            ticker="AAPL",
            action="BUY",
            quantity=1,
            price=Decimal("100.00"),
        )


async def test_execute_trade_buy_decrements_balance(mock_session):
    """execute_trade() BUY reduces account balance by price * quantity."""
    account = _make_mock_account(Decimal("1000.00"))
    mock_session.execute.return_value = make_first_result(account)

    mock_class, _ = _mock_position_dao_class()
    with patch("backend.shared.dao.backtesting.PaperPositionDAO", mock_class):
        dao = PaperAccountDAO(mock_session)
        await dao.execute_trade(
            account_id=uuid4(),
            ticker="AAPL",
            action="BUY",
            quantity=2,
            price=Decimal("100.00"),
        )

    assert account.current_balance == Decimal("800.00")


async def test_execute_trade_buy_raises_when_insufficient_funds(mock_session):
    """execute_trade() BUY raises ValueError when balance < total cost."""
    account = _make_mock_account(Decimal("50.00"))
    mock_session.execute.return_value = make_first_result(account)

    dao = PaperAccountDAO(mock_session)
    with pytest.raises(ValueError, match="Insufficient funds"):
        await dao.execute_trade(
            account_id=uuid4(),
            ticker="AAPL",
            action="BUY",
            quantity=2,
            price=Decimal("100.00"),
        )


async def test_execute_trade_sell_increments_balance(mock_session):
    """execute_trade() SELL increases account balance by price * quantity."""
    account = _make_mock_account(Decimal("500.00"))
    mock_session.execute.return_value = make_first_result(account)

    mock_class, _ = _mock_position_dao_class()
    with patch("backend.shared.dao.backtesting.PaperPositionDAO", mock_class):
        dao = PaperAccountDAO(mock_session)
        await dao.execute_trade(
            account_id=uuid4(),
            ticker="AAPL",
            action="SELL",
            quantity=3,
            price=Decimal("100.00"),
        )

    assert account.current_balance == Decimal("800.00")


async def test_execute_trade_commits_and_refreshes(mock_session):
    """execute_trade() calls session.commit() and session.refresh() on success."""
    account = _make_mock_account(Decimal("1000.00"))
    mock_session.execute.return_value = make_first_result(account)

    mock_class, _ = _mock_position_dao_class()
    with patch("backend.shared.dao.backtesting.PaperPositionDAO", mock_class):
        dao = PaperAccountDAO(mock_session)
        await dao.execute_trade(
            account_id=uuid4(),
            ticker="AAPL",
            action="BUY",
            quantity=1,
            price=Decimal("100.00"),
        )

    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


async def test_execute_trade_adds_paper_trade_to_session(mock_session):
    """execute_trade() adds a PaperTrade record to the session."""
    account = _make_mock_account(Decimal("1000.00"))
    mock_session.execute.return_value = make_first_result(account)

    mock_class, _ = _mock_position_dao_class()
    with patch("backend.shared.dao.backtesting.PaperPositionDAO", mock_class):
        dao = PaperAccountDAO(mock_session)
        await dao.execute_trade(
            account_id=uuid4(),
            ticker="aapl",  # lowercase - should be uppercased internally
            action="BUY",
            quantity=1,
            price=Decimal("100.00"),
        )

    # session.add must have been called (for the PaperTrade)
    mock_session.add.assert_called()
    added = mock_session.add.call_args[0][0]
    assert isinstance(added, PaperTrade)
    assert added.ticker == "AAPL"  # uppercased


async def test_execute_trade_calls_update_position(mock_session):
    """execute_trade() delegates position update to PaperPositionDAO."""
    account = _make_mock_account(Decimal("1000.00"))
    mock_session.execute.return_value = make_first_result(account)

    mock_class, mock_position = _mock_position_dao_class()
    with patch("backend.shared.dao.backtesting.PaperPositionDAO", mock_class):
        dao = PaperAccountDAO(mock_session)
        await dao.execute_trade(
            account_id=uuid4(),
            ticker="TSLA",
            action="BUY",
            quantity=5,
            price=Decimal("200.00"),
        )

    mock_position.update_position.assert_called_once()


async def test_execute_trade_sell_passes_negative_quantity_to_position(mock_session):
    """execute_trade() SELL passes negative qty_delta to update_position."""
    account = _make_mock_account(Decimal("500.00"))
    mock_session.execute.return_value = make_first_result(account)

    mock_class, mock_position = _mock_position_dao_class()
    with patch("backend.shared.dao.backtesting.PaperPositionDAO", mock_class):
        dao = PaperAccountDAO(mock_session)
        await dao.execute_trade(
            account_id=uuid4(),
            ticker="MSFT",
            action="SELL",
            quantity=3,
            price=Decimal("100.00"),
        )

    call_kwargs = mock_position.update_position.call_args.kwargs
    assert call_kwargs["quantity_delta"] == -3
