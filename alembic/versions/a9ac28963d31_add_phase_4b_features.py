"""add_phase_4b_features

Revision ID: a9ac28963d31
Revises: cc6231cabf3b
Create Date: 2026-02-09 23:31:57.479348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'a9ac28963d31'
down_revision: Union[str, Sequence[str], None] = 'cc6231cabf3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create AlertFrequency enum
    op.execute("""
        CREATE TYPE alertfrequency AS ENUM ('daily', 'weekly', 'on_change')
    """)

    # Add baseline_price column to price_alerts
    op.execute("""
        ALTER TABLE price_alerts ADD COLUMN baseline_price FLOAT
    """)

    # Add email column to users (for SendGrid foundation)
    op.execute("""
        ALTER TABLE users ADD COLUMN notification_email VARCHAR(255)
    """)

    # Create scheduled_analyses table
    op.execute("""
        CREATE TABLE scheduled_analyses (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            ticker VARCHAR(20) NOT NULL,
            market market NOT NULL,
            frequency alertfrequency NOT NULL,
            last_run TIMESTAMP,
            next_run TIMESTAMP,
            active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    # Create indexes for scheduled_analyses
    op.create_index('ix_scheduled_analyses_next_run', 'scheduled_analyses', ['next_run'])
    op.create_index('ix_scheduled_analyses_active', 'scheduled_analyses', ['active'])
    op.create_index('ix_scheduled_analyses_next_run_active', 'scheduled_analyses', ['next_run', 'active'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop table and indexes
    op.drop_table('scheduled_analyses')

    # Remove columns
    op.execute('ALTER TABLE users DROP COLUMN notification_email')
    op.execute('ALTER TABLE price_alerts DROP COLUMN baseline_price')

    # Drop enum
    op.execute('DROP TYPE alertfrequency')
