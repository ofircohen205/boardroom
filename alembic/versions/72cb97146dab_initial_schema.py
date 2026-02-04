"""initial schema

Revision ID: 72cb97146dab
Revises:
Create Date: 2026-02-04 20:38:25.343165

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '72cb97146dab'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema."""
    # Create Market enum
    market_enum = postgresql.ENUM('US', 'IL', name='market', create_type=False)
    market_enum.create(op.get_bind(), checkfirst=True)

    # Create AgentType enum
    agent_type_enum = postgresql.ENUM(
        'FUNDAMENTAL', 'SENTIMENT', 'TECHNICAL', 'RISK_MANAGER', 'CHAIRPERSON',
        name='agenttype', create_type=False
    )
    agent_type_enum.create(op.get_bind(), checkfirst=True)

    # Create Action enum
    action_enum = postgresql.ENUM('BUY', 'SELL', 'HOLD', name='action', create_type=False)
    action_enum.create(op.get_bind(), checkfirst=True)

    # Create analysis_sessions table
    op.create_table(
        'analysis_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('ticker', sa.String(20), nullable=False),
        sa.Column('market', postgresql.ENUM('US', 'IL', name='market', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    # Create agent_reports table
    op.create_table(
        'agent_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analysis_sessions.id'), nullable=False),
        sa.Column('agent_type', postgresql.ENUM('FUNDAMENTAL', 'SENTIMENT', 'TECHNICAL', 'RISK_MANAGER', 'CHAIRPERSON', name='agenttype', create_type=False), nullable=False),
        sa.Column('report_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Create final_decisions table
    op.create_table(
        'final_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('analysis_sessions.id'), unique=True, nullable=False),
        sa.Column('action', postgresql.ENUM('BUY', 'SELL', 'HOLD', name='action', create_type=False), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('vetoed', sa.Boolean(), default=False, nullable=False),
        sa.Column('veto_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    """Drop all tables and enums."""
    op.drop_table('final_decisions')
    op.drop_table('agent_reports')
    op.drop_table('analysis_sessions')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS action')
    op.execute('DROP TYPE IF EXISTS agenttype')
    op.execute('DROP TYPE IF EXISTS market')
