"""Add tool execution tracking

Revision ID: add_tool_execution_tracking
Revises: 
Create Date: 2025-11-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_tool_execution_tracking'
down_revision = None  # Update this with the latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Create tool_executions table
    op.create_table(
        'tool_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', sa.String(100), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parameters', postgresql.JSONB, default=dict),
        sa.Column('credentials_used', sa.Boolean, default=False),
        sa.Column('success', sa.Boolean, nullable=False),
        sa.Column('output', postgresql.JSONB),
        sa.Column('error', sa.Text),
        sa.Column('execution_time', sa.Float),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('session_id', sa.String(255)),
        sa.Column('workflow_execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workflow_execution_id'], ['workflow_executions.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for tool_executions
    op.create_index('ix_tool_executions_tool_id', 'tool_executions', ['tool_id'])
    op.create_index('ix_tool_executions_agent_id', 'tool_executions', ['agent_id'])
    op.create_index('ix_tool_executions_user_id', 'tool_executions', ['user_id'])
    op.create_index('ix_tool_executions_success', 'tool_executions', ['success'])
    op.create_index('ix_tool_executions_started_at', 'tool_executions', ['started_at'])
    op.create_index('ix_tool_executions_session_id', 'tool_executions', ['session_id'])
    op.create_index('ix_tool_executions_tool_user', 'tool_executions', ['tool_id', 'user_id'])
    op.create_index('ix_tool_executions_started_at_desc', 'tool_executions', [sa.text('started_at DESC')])
    op.create_index('ix_tool_executions_success_started', 'tool_executions', ['success', 'started_at'])
    
    # Create tool_credentials table
    op.create_table(
        'tool_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('credentials', postgresql.JSONB, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_used_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'tool_id', 'name', name='uq_user_tool_credential_name'),
    )
    
    # Create indexes for tool_credentials
    op.create_index('ix_tool_credentials_user_id', 'tool_credentials', ['user_id'])
    op.create_index('ix_tool_credentials_tool_id', 'tool_credentials', ['tool_id'])
    op.create_index('ix_tool_credentials_is_active', 'tool_credentials', ['is_active'])
    op.create_index('ix_tool_credentials_user_tool', 'tool_credentials', ['user_id', 'tool_id'])
    
    # Create tool_usage_metrics table
    op.create_table(
        'tool_usage_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', sa.String(100), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('date', sa.DateTime, nullable=False),
        sa.Column('execution_count', sa.Integer, default=0),
        sa.Column('success_count', sa.Integer, default=0),
        sa.Column('failure_count', sa.Integer, default=0),
        sa.Column('avg_execution_time', sa.Float),
        sa.Column('total_execution_time', sa.Float),
        sa.Column('min_execution_time', sa.Float),
        sa.Column('max_execution_time', sa.Float),
        sa.Column('estimated_cost', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tool_id', 'user_id', 'date', name='uq_tool_user_date_metric'),
    )
    
    # Create indexes for tool_usage_metrics
    op.create_index('ix_tool_usage_metrics_tool_id', 'tool_usage_metrics', ['tool_id'])
    op.create_index('ix_tool_usage_metrics_user_id', 'tool_usage_metrics', ['user_id'])
    op.create_index('ix_tool_usage_metrics_date', 'tool_usage_metrics', ['date'])
    op.create_index('ix_tool_usage_metrics_date_desc', 'tool_usage_metrics', [sa.text('date DESC')])
    op.create_index('ix_tool_usage_metrics_tool_date', 'tool_usage_metrics', ['tool_id', 'date'])


def downgrade():
    # Drop tool_usage_metrics table
    op.drop_index('ix_tool_usage_metrics_tool_date', 'tool_usage_metrics')
    op.drop_index('ix_tool_usage_metrics_date_desc', 'tool_usage_metrics')
    op.drop_index('ix_tool_usage_metrics_date', 'tool_usage_metrics')
    op.drop_index('ix_tool_usage_metrics_user_id', 'tool_usage_metrics')
    op.drop_index('ix_tool_usage_metrics_tool_id', 'tool_usage_metrics')
    op.drop_table('tool_usage_metrics')
    
    # Drop tool_credentials table
    op.drop_index('ix_tool_credentials_user_tool', 'tool_credentials')
    op.drop_index('ix_tool_credentials_is_active', 'tool_credentials')
    op.drop_index('ix_tool_credentials_tool_id', 'tool_credentials')
    op.drop_index('ix_tool_credentials_user_id', 'tool_credentials')
    op.drop_table('tool_credentials')
    
    # Drop tool_executions table
    op.drop_index('ix_tool_executions_success_started', 'tool_executions')
    op.drop_index('ix_tool_executions_started_at_desc', 'tool_executions')
    op.drop_index('ix_tool_executions_tool_user', 'tool_executions')
    op.drop_index('ix_tool_executions_session_id', 'tool_executions')
    op.drop_index('ix_tool_executions_started_at', 'tool_executions')
    op.drop_index('ix_tool_executions_success', 'tool_executions')
    op.drop_index('ix_tool_executions_user_id', 'tool_executions')
    op.drop_index('ix_tool_executions_agent_id', 'tool_executions')
    op.drop_index('ix_tool_executions_tool_id', 'tool_executions')
    op.drop_table('tool_executions')
