"""add memory cost branch collaboration models

Revision ID: add_memory_cost_models
Revises: previous_revision
Create Date: 2025-11-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_memory_cost_models'
down_revision = None  # Update this to your latest revision
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_memories table
    op.create_table(
        'agent_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSON, default={}),
        sa.Column('importance', sa.String(10), default='medium'),
        sa.Column('access_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_accessed_at', sa.DateTime),
        sa.CheckConstraint("type IN ('short_term', 'long_term', 'episodic', 'semantic')", name='ck_memory_type'),
        sa.CheckConstraint("importance IN ('low', 'medium', 'high')", name='ck_memory_importance'),
    )
    
    op.create_index('ix_agent_memory_type', 'agent_memories', ['agent_id', 'type'])
    op.create_index('ix_agent_memory_importance', 'agent_memories', ['agent_id', 'importance'])
    op.create_index('ix_agent_memory_created', 'agent_memories', ['agent_id', 'created_at'])

    # Create memory_settings table
    op.create_table(
        'memory_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('short_term_retention_hours', sa.Integer, default=24),
        sa.Column('auto_cleanup', sa.Boolean, default=True),
        sa.Column('auto_consolidation', sa.Boolean, default=True),
        sa.Column('consolidation_threshold', sa.Integer, default=100),
        sa.Column('enable_compression', sa.Boolean, default=True),
        sa.Column('max_memory_size_mb', sa.Integer, default=1000),
        sa.Column('importance_threshold', sa.String(10), default='low'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # Create cost_records table
    op.create_table(
        'cost_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE')),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True)),
        sa.Column('model', sa.String(50), nullable=False),
        sa.Column('tokens', sa.Integer, nullable=False),
        sa.Column('cost', sa.Float, nullable=False),
        sa.Column('metadata', postgresql.JSON, default={}),
        sa.Column('timestamp', sa.DateTime, nullable=False),
    )
    
    op.create_index('ix_cost_agent_timestamp', 'cost_records', ['agent_id', 'timestamp'])
    op.create_index('ix_cost_model_timestamp', 'cost_records', ['model', 'timestamp'])
    op.create_index('ix_cost_execution', 'cost_records', ['execution_id'])

    # Create budget_settings table
    op.create_table(
        'budget_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='CASCADE'), unique=True),
        sa.Column('monthly_budget', sa.Float, default=1000.0),
        sa.Column('alert_threshold_percentage', sa.Integer, default=80),
        sa.Column('enable_email_alerts', sa.Boolean, default=True),
        sa.Column('enable_auto_stop', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # Create workflow_branches table
    op.create_table(
        'workflow_branches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('is_main', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=False),
        sa.Column('commit_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.UniqueConstraint('workflow_id', 'name', name='uq_workflow_branch_name'),
    )
    
    op.create_index('ix_workflow_branch_workflow', 'workflow_branches', ['workflow_id'])

    # Create branch_commits table
    op.create_table(
        'branch_commits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflow_branches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('snapshot', postgresql.JSON, nullable=False),
        sa.Column('changes_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    
    op.create_index('ix_branch_commit_branch', 'branch_commits', ['branch_id', 'created_at'])

    # Create collaboration_sessions table
    op.create_table(
        'collaboration_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resource_type', sa.String(20), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('color', sa.String(7)),
        sa.Column('cursor_position', postgresql.JSON),
        sa.Column('selection', postgresql.JSON),
        sa.Column('joined_at', sa.DateTime, nullable=False),
        sa.Column('last_seen', sa.DateTime, nullable=False),
    )
    
    op.create_index('ix_collab_resource', 'collaboration_sessions', ['resource_type', 'resource_id'])
    op.create_index('ix_collab_user', 'collaboration_sessions', ['user_id'])
    op.create_index('ix_collab_last_seen', 'collaboration_sessions', ['last_seen'])

    # Create resource_locks table
    op.create_table(
        'resource_locks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resource_type', sa.String(20), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('locked_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('resource_type', 'resource_id', name='uq_resource_lock'),
    )
    
    op.create_index('ix_resource_lock_expires', 'resource_locks', ['expires_at'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('resource_locks')
    op.drop_table('collaboration_sessions')
    op.drop_table('branch_commits')
    op.drop_table('workflow_branches')
    op.drop_table('budget_settings')
    op.drop_table('cost_records')
    op.drop_table('memory_settings')
    op.drop_table('agent_memories')
