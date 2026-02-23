"""align_market_enum

Revision ID: e2e4e16f8ccd
Revises: d4e52e30ebd3
Create Date: 2026-02-23 15:45:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2e4e16f8ccd"  # pragma: allowlist secret
down_revision: Union[str, Sequence[str], None] = "d4e52e30ebd3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing markets to market enum."""
    # Use DO block for idempotency if running in environments where they might exist
    op.execute(
        """
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'LSE' AND enumtypid = 'market'::regtype) THEN
                ALTER TYPE market ADD VALUE 'LSE';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'TSE' AND enumtypid = 'market'::regtype) THEN
                ALTER TYPE market ADD VALUE 'TSE';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'HKEX' AND enumtypid = 'market'::regtype) THEN
                ALTER TYPE market ADD VALUE 'HKEX';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'XETRA' AND enumtypid = 'market'::regtype) THEN
                ALTER TYPE market ADD VALUE 'XETRA';
            END IF;
        END $$;
    """
    )


def downgrade() -> None:
    """Market enum values cannot be easily removed in PostgreSQL."""
    pass
