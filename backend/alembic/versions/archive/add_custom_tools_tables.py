"""Add custom tools tables

Revision ID: add_custom_tools_001
Revises: add_memory_cost_branch_collab_models
Create Date: 2025-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'add_custom_tools_001'
down_revision = 'add_memory_cost_models'
branch_labels = None
depends_on = None


def upgrade():
    # Create custom_tools table
    op.create_table(
        'custom_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(50), nullable=False, server_default='custom'),
        sa.Column('icon', sa.String(50), server_default='🔧'),
        sa.Column('method', sa.String(10), nullable=False, server_default='GET'),
        sa.Column('url', sa.Text, nullable=False),
        sa.Column('headers', postgresql.JSON, server_default='{}'),
        sa.Column('query_params', postgresql.JSON, server_default='{}'),
        sa.Column('body_template', postgresql.JSON, server_default='{}'),
        sa.Column('parameters', postgresql.JSON, server_default='[]'),
        sa.Column('outputs', postgresql.JSON, server_default='[]'),
        sa.Column('requires_auth', sa.Boolean, server_default='false'),
        sa.Column('auth_type', sa.String(20)),
        sa.Column('auth_config', postgresql.JSON, server_default='{}'),
        sa.Column('is_public', sa.Boolean, server_default='false'),
        sa.Column('is_marketplace', sa.Boolean, server_default='false'),
        sa.Column('test_data', postgresql.JSON, server_default='{}'),
        sa.Column('last_test_result', postgresql.JSON),
        sa.Column('last_test_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
        sa.Column('usage_count', sa.Integer, server_default='0'),
    )
    
    # Create indexes
    op.create_index('idx_custom_tools_user_id', 'custom_tools', ['user_id'])
    op.create_index('idx_custom_tools_category', 'custom_tools', ['category'])
    op.create_index('idx_custom_tools_public', 'custom_tools', ['is_public'])
    op.create_index('idx_custom_tools_marketplace', 'custom_tools', ['is_marketplace'])
    
    # Create custom_tool_usage table
    op.create_table(
        'custom_tool_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('custom_tools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='SET NULL')),
        sa.Column('input_data', postgresql.JSON),
        sa.Column('output_data', postgresql.JSON),
        sa.Column('success', sa.Boolean, server_default='true'),
        sa.Column('error_message', sa.Text),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('executed_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
    )
    
    # Create indexes
    op.create_index('idx_custom_tool_usage_tool_id', 'custom_tool_usage', ['tool_id'])
    op.create_index('idx_custom_tool_usage_user_id', 'custom_tool_usage', ['user_id'])
    op.create_index('idx_custom_tool_usage_executed_at', 'custom_tool_usage', ['executed_at'])
    
    # Create custom_tool_ratings table
    op.create_table(
        'custom_tool_ratings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tool_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('custom_tools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('review', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()')),
    )
    
    # Create indexes
    op.create_index('idx_custom_tool_ratings_tool_id', 'custom_tool_ratings', ['tool_id'])
    op.create_index('idx_custom_tool_ratings_user_id', 'custom_tool_ratings', ['user_id'])


def downgrade():
    op.drop_table('custom_tool_ratings')
    op.drop_table('custom_tool_usage')
    op.drop_table('custom_tools')
