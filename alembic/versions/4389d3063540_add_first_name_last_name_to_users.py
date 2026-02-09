"""add_first_name_last_name_to_users

Revision ID: 4389d3063540
Revises: 5f691480b773
Create Date: 2026-02-09 18:50:35.817664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4389d3063540'
down_revision: Union[str, Sequence[str], None] = '5f691480b773'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add first_name, last_name, and is_active columns to users table
    op.add_column('users', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True))

    # Update existing users with default values
    op.execute("UPDATE users SET first_name = 'User', last_name = 'Name', is_active = TRUE WHERE first_name IS NULL")

    # Make columns non-nullable after setting defaults
    op.alter_column('users', 'first_name', nullable=False)
    op.alter_column('users', 'last_name', nullable=False)
    op.alter_column('users', 'is_active', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove first_name, last_name, and is_active columns
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
