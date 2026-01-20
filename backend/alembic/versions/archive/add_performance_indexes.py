"""Add performance indexes

Revision ID: add_performance_indexes
Revises: add_tool_execution_tracking
Create Date: 2025-11-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = 'add_tool_execution_tracking'
branch_labels = None
depends_on = None


def upgrade():
    # Tool Executions - Performance indexes
    op.create_index(
        'idx_tool_executions_user_started_desc',
        'tool_executions',
        ['user_id', sa.text('started_at DESC')],
        postgresql_using='btree'
    )
    
    # Agents - Performance indexes
    op.create_index(
        'idx_agents_user_updated_desc',
        'agents',
        ['user_id', sa.text('updated_at DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_agents_user_created_desc',
        'agents',
        ['user_id', sa.text('created_at DESC')],
        postgresql_using='btree'
    )
    
    # Agent Executions - Performance indexes
    op.create_index(
        'idx_agent_executions_agent_started_desc',
        'agent_executions',
        ['agent_id', sa.text('started_at DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_agent_executions_user_started_desc',
        'agent_executions',
        ['user_id', sa.text('started_at DESC')],
        postgresql_using='btree'
    )
    
    # Workflows - Performance indexes
    op.create_index(
        'idx_workflows_user_updated_desc',
        'workflows',
        ['user_id', sa.text('updated_at DESC')],
        postgresql_using='btree'
    )
    
    # Tool Credentials - Performance indexes
    op.create_index(
        'idx_tool_credentials_user_tool_active',
        'tool_credentials',
        ['user_id', 'tool_id', 'is_active'],
        postgresql_using='btree'
    )
    
    # Knowledgebases - Performance indexes
    op.create_index(
        'idx_knowledgebases_user_updated_desc',
        'knowledgebases',
        ['user_id', sa.text('updated_at DESC')],
        postgresql_using='btree'
    )


def downgrade():
    # Drop indexes in reverse order
    op.drop_index('idx_knowledgebases_user_updated_desc', 'knowledgebases')
    op.drop_index('idx_tool_credentials_user_tool_active', 'tool_credentials')
    op.drop_index('idx_workflows_user_updated_desc', 'workflows')
    op.drop_index('idx_agent_executions_user_started_desc', 'agent_executions')
    op.drop_index('idx_agent_executions_agent_started_desc', 'agent_executions')
    op.drop_index('idx_agents_user_created_desc', 'agents')
    op.drop_index('idx_agents_user_updated_desc', 'agents')
    op.drop_index('idx_tool_executions_user_started_desc', 'tool_executions')
