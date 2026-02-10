"""add_alerts_notifications

Revision ID: cc6231cabf3b
Revises: 4389d3063540
Create Date: 2026-02-09 20:02:15.066961

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cc6231cabf3b"
down_revision: Union[str, Sequence[str], None] = "4389d3063540"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create AlertCondition enum
    op.execute(
        """
        CREATE TYPE alertcondition AS ENUM ('above', 'below', 'change_pct')
    """
    )

    # Create NotificationType enum
    op.execute(
        """
        CREATE TYPE notificationtype AS ENUM ('price_alert', 'analysis_complete', 'recommendation_change', 'veto_alert')
    """
    )

    # Update market enum to include TASE if it only has IL
    # This is a conditional update - if TASE already exists, this will fail silently
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'TASE' AND enumtypid = 'market'::regtype) THEN
                ALTER TYPE market ADD VALUE 'TASE';
            END IF;
        END $$;
    """
    )

    # Create price_alerts table
    op.execute(
        """
        CREATE TABLE price_alerts (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            ticker VARCHAR(20) NOT NULL,
            market market NOT NULL,
            condition alertcondition NOT NULL,
            target_value FLOAT NOT NULL,
            triggered BOOLEAN NOT NULL DEFAULT false,
            triggered_at TIMESTAMP,
            cooldown_until TIMESTAMP,
            active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """
    )

    # Create indexes for price_alerts
    op.create_index("ix_price_alerts_ticker", "price_alerts", ["ticker"])
    op.create_index("ix_price_alerts_triggered", "price_alerts", ["triggered"])
    op.create_index("ix_price_alerts_active", "price_alerts", ["active"])
    op.create_index(
        "ix_price_alerts_ticker_active", "price_alerts", ["ticker", "active"]
    )
    op.create_index(
        "ix_price_alerts_triggered_active", "price_alerts", ["triggered", "active"]
    )

    # Create notifications table
    op.execute(
        """
        CREATE TABLE notifications (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            type notificationtype NOT NULL,
            title VARCHAR(255) NOT NULL,
            body TEXT NOT NULL,
            data JSONB NOT NULL DEFAULT '{}',
            read BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """
    )

    # Create indexes for notifications
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_read", "notifications", ["read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read"])
    op.create_index(
        "ix_notifications_user_created", "notifications", ["user_id", "created_at"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables
    op.drop_table("notifications")
    op.drop_table("price_alerts")

    # Drop enums
    op.execute("DROP TYPE notificationtype")
    op.execute("DROP TYPE alertcondition")
