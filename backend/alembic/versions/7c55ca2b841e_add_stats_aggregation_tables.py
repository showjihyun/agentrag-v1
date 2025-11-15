"""add_stats_aggregation_tables

Revision ID: 7c55ca2b841e
Revises: 1a7037582536
Create Date: 2025-11-15 15:29:00.879697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c55ca2b841e'
down_revision: Union[str, None] = '1a7037582536'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add statistics aggregation tables for dashboard performance"""
    
    # AgentExecutionStats 테이블 생성
    op.create_table(
        'agent_execution_stats',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), index=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True),
        sa.Column('date', sa.DateTime, nullable=False, index=True),
        sa.Column('execution_count', sa.Integer, default=0),
        sa.Column('success_count', sa.Integer, default=0),
        sa.Column('failed_count', sa.Integer, default=0),
        sa.Column('cancelled_count', sa.Integer, default=0),
        sa.Column('avg_duration_ms', sa.Integer),
        sa.Column('min_duration_ms', sa.Integer),
        sa.Column('max_duration_ms', sa.Integer),
        sa.Column('total_tokens', sa.BigInteger, default=0),
        sa.Column('total_llm_calls', sa.Integer, default=0),
        sa.Column('total_cost', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.UniqueConstraint('agent_id', 'user_id', 'date', name='uq_agent_stats_date'),
        sa.Index('ix_agent_stats_user_date', 'user_id', 'date'),
        sa.Index('ix_agent_stats_agent_date', 'agent_id', 'date')
    )
    
    # WorkflowExecutionStats 테이블 생성
    op.create_table(
        'workflow_execution_stats',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('workflows.id', ondelete='CASCADE'), index=True),
        sa.Column('user_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), index=True),
        sa.Column('date', sa.DateTime, nullable=False, index=True),
        sa.Column('execution_count', sa.Integer, default=0),
        sa.Column('success_count', sa.Integer, default=0),
        sa.Column('failed_count', sa.Integer, default=0),
        sa.Column('avg_duration_ms', sa.Integer),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.UniqueConstraint('workflow_id', 'user_id', 'date', name='uq_workflow_stats_date'),
        sa.Index('ix_workflow_stats_user_date', 'user_id', 'date')
    )


def downgrade() -> None:
    """Remove statistics aggregation tables"""
    op.drop_table('workflow_execution_stats')
    op.drop_table('agent_execution_stats')
