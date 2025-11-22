"""Add comprehensive performance indexes

Revision ID: add_comprehensive_indexes
Revises: add_performance_indexes
Create Date: 2025-11-21

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_comprehensive_indexes'
down_revision = 'add_performance_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Add comprehensive indexes for query optimization."""
    
    # ========================================================================
    # AGENT EXECUTIONS - Additional indexes for common queries
    # ========================================================================
    
    # Status + Started time for filtering and sorting
    op.create_index(
        'idx_agent_executions_status_started',
        'agent_executions',
        ['status', sa.text('started_at DESC')],
        postgresql_using='btree'
    )
    
    # Agent + Status for filtering by agent and status
    op.create_index(
        'idx_agent_executions_agent_status',
        'agent_executions',
        ['agent_id', 'status'],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # TOOL EXECUTIONS - Additional indexes
    # ========================================================================
    
    # Tool + Status for filtering
    op.create_index(
        'idx_tool_executions_tool_status',
        'tool_executions',
        ['tool_id', 'status'],
        postgresql_using='btree'
    )
    
    # User + Tool for user-specific tool queries
    op.create_index(
        'idx_tool_executions_user_tool',
        'tool_executions',
        ['user_id', 'tool_id'],
        postgresql_using='btree'
    )
    
    # Status + Started for filtering and sorting
    op.create_index(
        'idx_tool_executions_status_started',
        'tool_executions',
        ['status', sa.text('started_at DESC')],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # WORKFLOW EXECUTIONS - Additional indexes
    # ========================================================================
    
    # Workflow + Status for filtering
    op.create_index(
        'idx_workflow_executions_workflow_status',
        'workflow_executions',
        ['workflow_id', 'status'],
        postgresql_using='btree'
    )
    
    # User + Workflow for user-specific workflow queries
    op.create_index(
        'idx_workflow_executions_user_workflow',
        'workflow_executions',
        ['user_id', 'workflow_id'],
        postgresql_using='btree'
    )
    
    # Status + Started for filtering and sorting
    op.create_index(
        'idx_workflow_executions_status_started',
        'workflow_executions',
        ['status', sa.text('started_at DESC')],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # BLOCKS - Additional indexes
    # ========================================================================
    
    # User + Type + Public for filtering
    op.create_index(
        'idx_blocks_user_type_public',
        'blocks',
        ['user_id', 'block_type', 'is_public'],
        postgresql_using='btree'
    )
    
    # Type + Public for public block queries
    op.create_index(
        'idx_blocks_type_public',
        'blocks',
        ['block_type', 'is_public'],
        postgresql_using='btree',
        postgresql_where=sa.text('is_public = true')
    )
    
    # ========================================================================
    # AGENT TOOLS - Additional indexes
    # ========================================================================
    
    # Tool + Agent for reverse lookups
    op.create_index(
        'idx_agent_tools_tool_agent',
        'agent_tools',
        ['tool_id', 'agent_id'],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # AGENT KNOWLEDGEBASES - Additional indexes
    # ========================================================================
    
    # Agent + Knowledgebase for lookups
    op.create_index(
        'idx_agent_knowledgebases_agent_kb',
        'agent_knowledgebases',
        ['agent_id', 'knowledgebase_id'],
        postgresql_using='btree'
    )
    
    # Knowledgebase + Agent for reverse lookups
    op.create_index(
        'idx_agent_knowledgebases_kb_agent',
        'agent_knowledgebases',
        ['knowledgebase_id', 'agent_id'],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # WORKFLOW NODES - Additional indexes
    # ========================================================================
    
    # Workflow + Type for filtering by node type
    op.create_index(
        'idx_workflow_nodes_workflow_type',
        'workflow_nodes',
        ['workflow_id', 'node_type'],
        postgresql_using='btree'
    )
    
    # Node ref for lookups by referenced entity
    op.create_index(
        'idx_workflow_nodes_node_ref',
        'workflow_nodes',
        ['node_ref_id'],
        postgresql_using='btree',
        postgresql_where=sa.text('node_ref_id IS NOT NULL')
    )
    
    # ========================================================================
    # AGENT BLOCKS - Additional indexes
    # ========================================================================
    
    # Workflow + Enabled for active blocks
    op.create_index(
        'idx_agent_blocks_workflow_enabled_type',
        'agent_blocks',
        ['workflow_id', 'enabled', 'type'],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # WORKFLOW SCHEDULES - Additional indexes
    # ========================================================================
    
    # Active + Next execution for scheduler queries
    op.create_index(
        'idx_workflow_schedules_active_next',
        'workflow_schedules',
        ['is_active', sa.text('next_execution_at ASC')],
        postgresql_using='btree',
        postgresql_where=sa.text('is_active = true AND next_execution_at IS NOT NULL')
    )
    
    # ========================================================================
    # PROMPT TEMPLATES - Additional indexes
    # ========================================================================
    
    # System + Category for system template queries
    op.create_index(
        'idx_prompt_templates_system_category',
        'prompt_templates',
        ['is_system', 'category'],
        postgresql_using='btree'
    )
    
    # User + Category for user template queries
    op.create_index(
        'idx_prompt_templates_user_category',
        'prompt_templates',
        ['user_id', 'category'],
        postgresql_using='btree',
        postgresql_where=sa.text('user_id IS NOT NULL')
    )


def downgrade():
    """Remove comprehensive indexes."""
    
    # Drop indexes in reverse order
    op.drop_index('idx_prompt_templates_user_category', 'prompt_templates')
    op.drop_index('idx_prompt_templates_system_category', 'prompt_templates')
    op.drop_index('idx_workflow_schedules_active_next', 'workflow_schedules')
    op.drop_index('idx_agent_blocks_workflow_enabled_type', 'agent_blocks')
    op.drop_index('idx_workflow_nodes_node_ref', 'workflow_nodes')
    op.drop_index('idx_workflow_nodes_workflow_type', 'workflow_nodes')
    op.drop_index('idx_agent_knowledgebases_kb_agent', 'agent_knowledgebases')
    op.drop_index('idx_agent_knowledgebases_agent_kb', 'agent_knowledgebases')
    op.drop_index('idx_agent_tools_tool_agent', 'agent_tools')
    op.drop_index('idx_blocks_type_public', 'blocks')
    op.drop_index('idx_blocks_user_type_public', 'blocks')
    op.drop_index('idx_workflow_executions_status_started', 'workflow_executions')
    op.drop_index('idx_workflow_executions_user_workflow', 'workflow_executions')
    op.drop_index('idx_workflow_executions_workflow_status', 'workflow_executions')
    op.drop_index('idx_tool_executions_status_started', 'tool_executions')
    op.drop_index('idx_tool_executions_user_tool', 'tool_executions')
    op.drop_index('idx_tool_executions_tool_status', 'tool_executions')
    op.drop_index('idx_agent_executions_agent_status', 'agent_executions')
    op.drop_index('idx_agent_executions_status_started', 'agent_executions')
