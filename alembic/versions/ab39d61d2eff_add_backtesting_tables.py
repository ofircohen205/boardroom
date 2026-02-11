"""add_backtesting_tables

Revision ID: ab39d61d2eff
Revises: 395bbc2d5393
Create Date: 2026-02-11 09:01:02.864144

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ab39d61d2eff"
down_revision: Union[str, Sequence[str], None] = "395bbc2d5393"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enums if they don't exist
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tradetype') THEN
                CREATE TYPE tradetype AS ENUM ('BUY', 'SELL');
            END IF;
        END $$;
    """
    )
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'backtestfrequency') THEN
                CREATE TYPE backtestfrequency AS ENUM ('DAILY', 'WEEKLY');
            END IF;
        END $$;
    """
    )

    # Create historical_prices table
    op.create_table(
        "historical_prices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("high", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("low", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("close", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("adjusted_close", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("volume", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("open > 0", name="ck_historical_prices_open_positive"),
        sa.CheckConstraint("high > 0", name="ck_historical_prices_high_positive"),
        sa.CheckConstraint("low > 0", name="ck_historical_prices_low_positive"),
        sa.CheckConstraint("close > 0", name="ck_historical_prices_close_positive"),
        sa.CheckConstraint(
            "adjusted_close > 0", name="ck_historical_prices_adjusted_close_positive"
        ),
        sa.CheckConstraint(
            "volume >= 0", name="ck_historical_prices_volume_nonnegative"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", "date", name="uq_historical_prices_ticker_date"),
    )
    op.create_index("ix_historical_prices_ticker", "historical_prices", ["ticker"])
    op.create_index("ix_historical_prices_date", "historical_prices", ["date"])
    op.create_index(
        "ix_historical_prices_ticker_date", "historical_prices", ["ticker", "date"]
    )

    # Create historical_fundamentals table
    op.create_table(
        "historical_fundamentals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("quarter_end_date", sa.Date(), nullable=False),
        sa.Column("revenue", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("net_income", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column(
            "earnings_per_share", sa.Numeric(precision=12, scale=4), nullable=True
        ),
        sa.Column("pe_ratio", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("price_to_book", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("price_to_sales", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("total_debt", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("total_equity", sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column("debt_to_equity", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("revenue_growth", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("earnings_growth", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ticker",
            "quarter_end_date",
            name="uq_historical_fundamentals_ticker_quarter",
        ),
    )
    op.create_index(
        "ix_historical_fundamentals_ticker", "historical_fundamentals", ["ticker"]
    )
    op.create_index(
        "ix_historical_fundamentals_quarter_end_date",
        "historical_fundamentals",
        ["quarter_end_date"],
    )
    op.create_index(
        "ix_historical_fundamentals_ticker_quarter",
        "historical_fundamentals",
        ["ticker", "quarter_end_date"],
    )

    # Create strategies table
    op.create_table(
        "strategies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strategies_user_id", "strategies", ["user_id"])

    # Create paper_accounts table
    op.create_table(
        "paper_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("strategy_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("initial_balance", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("current_balance", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "initial_balance > 0", name="ck_paper_accounts_initial_balance_positive"
        ),
        sa.CheckConstraint(
            "current_balance >= 0", name="ck_paper_accounts_current_balance_nonnegative"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_paper_accounts_user_id", "paper_accounts", ["user_id"])
    op.create_index("ix_paper_accounts_strategy_id", "paper_accounts", ["strategy_id"])

    # Create paper_trades table (using raw SQL to avoid enum recreation)
    op.execute(
        """
        CREATE TABLE paper_trades (
            id UUID NOT NULL PRIMARY KEY,
            account_id UUID NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            trade_type tradetype NOT NULL,
            quantity INTEGER NOT NULL,
            price NUMERIC(12, 4) NOT NULL,
            total_value NUMERIC(12, 2) NOT NULL,
            analysis_session_id UUID,
            executed_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT ck_paper_trades_quantity_positive CHECK (quantity > 0),
            CONSTRAINT ck_paper_trades_price_positive CHECK (price > 0),
            CONSTRAINT ck_paper_trades_total_value_positive CHECK (total_value > 0),
            CONSTRAINT fk_paper_trades_account FOREIGN KEY (account_id) REFERENCES paper_accounts(id) ON DELETE CASCADE,
            CONSTRAINT fk_paper_trades_analysis FOREIGN KEY (analysis_session_id) REFERENCES analysis_sessions(id) ON DELETE SET NULL
        )
    """
    )
    # Create indexes for paper_trades
    op.execute("CREATE INDEX ix_paper_trades_account_id ON paper_trades(account_id)")
    op.execute(
        "CREATE INDEX ix_paper_trades_analysis_session_id ON paper_trades(analysis_session_id)"
    )
    op.execute("CREATE INDEX ix_paper_trades_executed_at ON paper_trades(executed_at)")
    op.execute(
        "CREATE INDEX ix_paper_trades_account_executed ON paper_trades(account_id, executed_at)"
    )

    # Create paper_positions table
    op.create_table(
        "paper_positions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "average_entry_price", sa.Numeric(precision=12, scale=4), nullable=False
        ),
        sa.Column("current_price", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("last_price_update", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_paper_positions_quantity_positive"),
        sa.CheckConstraint(
            "average_entry_price > 0", name="ck_paper_positions_entry_price_positive"
        ),
        sa.ForeignKeyConstraint(
            ["account_id"], ["paper_accounts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "account_id", "ticker", name="uq_paper_positions_account_ticker"
        ),
    )
    op.create_index("ix_paper_positions_account_id", "paper_positions", ["account_id"])

    # Create backtest_results table (using raw SQL to avoid enum recreation)
    op.execute(
        """
        CREATE TABLE backtest_results (
            id UUID NOT NULL PRIMARY KEY,
            user_id UUID NOT NULL,
            strategy_id UUID,
            ticker VARCHAR(10) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            initial_capital NUMERIC(12, 2) NOT NULL,
            check_frequency backtestfrequency NOT NULL,
            position_size_pct NUMERIC(4, 3) NOT NULL,
            stop_loss_pct NUMERIC(4, 3),
            take_profit_pct NUMERIC(4, 3),
            total_return NUMERIC(8, 4) NOT NULL,
            annualized_return NUMERIC(8, 4) NOT NULL,
            sharpe_ratio NUMERIC(8, 4),
            max_drawdown NUMERIC(8, 4) NOT NULL,
            win_rate NUMERIC(4, 3) NOT NULL,
            total_trades INTEGER NOT NULL,
            buy_and_hold_return NUMERIC(8, 4) NOT NULL,
            equity_curve JSON NOT NULL,
            trades JSON NOT NULL,
            execution_time_seconds NUMERIC(8, 2),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            CONSTRAINT ck_backtest_results_initial_capital_positive CHECK (initial_capital > 0),
            CONSTRAINT ck_backtest_results_position_size_valid CHECK (position_size_pct > 0 AND position_size_pct <= 1),
            CONSTRAINT ck_backtest_results_trades_valid CHECK (total_trades >= 0),
            CONSTRAINT ck_backtest_results_win_rate_valid CHECK (win_rate >= 0 AND win_rate <= 1),
            CONSTRAINT fk_backtest_results_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            CONSTRAINT fk_backtest_results_strategy FOREIGN KEY (strategy_id) REFERENCES strategies(id) ON DELETE SET NULL
        )
    """
    )
    # Create indexes for backtest_results
    op.execute("CREATE INDEX ix_backtest_results_user_id ON backtest_results(user_id)")
    op.execute(
        "CREATE INDEX ix_backtest_results_strategy_id ON backtest_results(strategy_id)"
    )
    op.execute(
        "CREATE INDEX ix_backtest_results_created_at ON backtest_results(created_at)"
    )
    op.execute(
        "CREATE INDEX ix_backtest_results_user_created ON backtest_results(user_id, created_at)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index("ix_backtest_results_user_created", table_name="backtest_results")
    op.drop_index("ix_backtest_results_created_at", table_name="backtest_results")
    op.drop_index("ix_backtest_results_strategy_id", table_name="backtest_results")
    op.drop_index("ix_backtest_results_user_id", table_name="backtest_results")
    op.drop_table("backtest_results")

    op.drop_index("ix_paper_positions_account_id", table_name="paper_positions")
    op.drop_table("paper_positions")

    op.drop_index("ix_paper_trades_account_executed", table_name="paper_trades")
    op.drop_index("ix_paper_trades_executed_at", table_name="paper_trades")
    op.drop_index("ix_paper_trades_analysis_session_id", table_name="paper_trades")
    op.drop_index("ix_paper_trades_account_id", table_name="paper_trades")
    op.drop_table("paper_trades")

    op.drop_index("ix_paper_accounts_strategy_id", table_name="paper_accounts")
    op.drop_index("ix_paper_accounts_user_id", table_name="paper_accounts")
    op.drop_table("paper_accounts")

    op.drop_index("ix_strategies_user_id", table_name="strategies")
    op.drop_table("strategies")

    op.drop_index(
        "ix_historical_fundamentals_ticker_quarter",
        table_name="historical_fundamentals",
    )
    op.drop_index(
        "ix_historical_fundamentals_quarter_end_date",
        table_name="historical_fundamentals",
    )
    op.drop_index(
        "ix_historical_fundamentals_ticker", table_name="historical_fundamentals"
    )
    op.drop_table("historical_fundamentals")

    op.drop_index("ix_historical_prices_ticker_date", table_name="historical_prices")
    op.drop_index("ix_historical_prices_date", table_name="historical_prices")
    op.drop_index("ix_historical_prices_ticker", table_name="historical_prices")
    op.drop_table("historical_prices")

    # Drop enums
    op.execute("DROP TYPE backtestfrequency")
    op.execute("DROP TYPE tradetype")
