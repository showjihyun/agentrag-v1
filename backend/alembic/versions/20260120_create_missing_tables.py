"""Create missing tables for complete schema

Revision ID: 20260120_create_missing_tables
Revises: 20260115220929
Create Date: 2026-01-20 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260120_create_missing_tables'
down_revision: Union[str, None] = '20260115220929'  # Changed from 004_rate_limit_config
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create missing tables."""
    
    # ==========================================
    # 1. Conversations Table
    # ==========================================
    op.create_table('conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_conversations_user_id', 'user_id'),
        sa.Index('idx_conversations_created_at', 'created_at'),
        sa.Index('idx_conversations_user_created', 'user_id', 'created_at'),
    )
    
    # Skip messages table - already exists
    
    # ==========================================
    # 2. Feedback Table
    # ==========================================
    op.create_table('feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),  # 1-5
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('feedback_type', sa.String(length=50), nullable=True),  # quality, accuracy, relevance
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_feedback_conversation_id', 'conversation_id'),
        sa.Index('idx_feedback_user_id', 'user_id'),
        sa.Index('idx_feedback_agent_id', 'agent_id'),
        sa.Index('idx_feedback_rating', 'rating'),
    )
    
    # ==========================================
    # 4. Agent Versions Table
    # ==========================================
    op.create_table('agent_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('context_items', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('mcp_servers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'version_number', name='uq_agent_version'),
        sa.Index('idx_agent_versions_agent_id', 'agent_id'),
        sa.Index('idx_agent_versions_created_at', 'created_at'),
    )
    
    # ==========================================
    # 5. Agent Tools Table
    # ==========================================
    op.create_table('agent_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', sa.String(length=100), nullable=False),  # tools.id is VARCHAR(100)
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'tool_id', name='uq_agent_tool'),
        sa.Index('idx_agent_tools_agent_id', 'agent_id'),
        sa.Index('idx_agent_tools_tool_id', 'tool_id'),
    )
    
    # ==========================================
    # 6. Agent Knowledgebases Table
    # ==========================================
    op.create_table('agent_knowledgebases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledge_base_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id', 'knowledge_base_id', name='uq_agent_kb'),
        sa.Index('idx_agent_kb_agent_id', 'agent_id'),
        sa.Index('idx_agent_kb_kb_id', 'knowledge_base_id'),
    )
    
    # ==========================================
    # 7. Agent Executions Table
    # ==========================================
    op.create_table('agent_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),  # pending, running, completed, failed
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_agent_executions_agent_id', 'agent_id'),
        sa.Index('idx_agent_executions_user_id', 'user_id'),
        sa.Index('idx_agent_executions_status', 'status'),
        sa.Index('idx_agent_executions_created_at', 'created_at'),
    )
    
    # ==========================================
    # 8. Agent Memories Table
    # ==========================================
    op.create_table('agent_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('memory_type', sa.String(length=50), nullable=False),  # stm, ltm, episodic, semantic
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_agent_memories_agent_id', 'agent_id'),
        sa.Index('idx_agent_memories_type', 'memory_type'),
        sa.Index('idx_agent_memories_created_at', 'created_at'),
    )
    
    # ==========================================
    # 9. Organizations Table
    # ==========================================
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_organizations_owner_id', 'owner_id'),
        sa.Index('idx_organizations_created_at', 'created_at'),
    )
    
    # ==========================================
    # 10. Teams Table
    # ==========================================
    op.create_table('teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'name', name='uq_team_org_name'),
        sa.Index('idx_teams_organization_id', 'organization_id'),
    )
    
    # ==========================================
    # 11. Bookmarks Table
    # ==========================================
    op.create_table('bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'conversation_id', name='uq_bookmark_user_conv'),
        sa.Index('idx_bookmarks_user_id', 'user_id'),
        sa.Index('idx_bookmarks_conversation_id', 'conversation_id'),
    )
    
    # ==========================================
    # 12. Notifications Table
    # ==========================================
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=True),  # info, warning, error, success
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_notifications_user_id', 'user_id'),
        sa.Index('idx_notifications_is_read', 'is_read'),
        sa.Index('idx_notifications_created_at', 'created_at'),
    )
    
    # ==========================================
    # 13. Conversation Shares Table
    # ==========================================
    op.create_table('conversation_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shared_with_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_level', sa.String(length=50), nullable=True, server_default='view'),  # view, edit
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_by_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['shared_with_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'shared_with_user_id', name='uq_share_conv_user'),
        sa.Index('idx_conversation_shares_conversation_id', 'conversation_id'),
        sa.Index('idx_conversation_shares_shared_with_user_id', 'shared_with_user_id'),
    )
    
    # ==========================================
    # 14. API Keys Table
    # ==========================================
    op.create_table('api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash', name='uq_api_key_hash'),
        sa.Index('idx_api_keys_user_id', 'user_id'),
        sa.Index('idx_api_keys_is_active', 'is_active'),
    )
    
    # ==========================================
    # 15. Event Store Table
    # ==========================================
    op.create_table('event_store',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('aggregate_type', sa.String(length=100), nullable=True),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_event_store_event_type', 'event_type'),
        sa.Index('idx_event_store_aggregate_id', 'aggregate_id'),
        sa.Index('idx_event_store_created_at', 'created_at'),
        sa.Index('idx_event_store_user_id', 'user_id'),
    )
    
    # ==========================================
    # 16. Agentflow Agents Table
    # ==========================================
    op.create_table('agentflow_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agentflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('position_x', sa.Float(), nullable=True),
        sa.Column('position_y', sa.Float(), nullable=True),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agentflow_id'], ['agentflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agentflow_id', 'agent_id', name='uq_agentflow_agent'),
        sa.Index('idx_agentflow_agents_agentflow_id', 'agentflow_id'),
        sa.Index('idx_agentflow_agents_agent_id', 'agent_id'),
    )
    
    # ==========================================
    # 17. Agentflow Edges Table
    # ==========================================
    op.create_table('agentflow_edges',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agentflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('edge_type', sa.String(length=50), nullable=True),  # sequential, conditional, parallel
        sa.Column('condition', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agentflow_id'], ['agentflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_agentflow_edges_agentflow_id', 'agentflow_id'),
        sa.Index('idx_agentflow_edges_source_agent_id', 'source_agent_id'),
        sa.Index('idx_agentflow_edges_target_agent_id', 'target_agent_id'),
    )
    
    # ==========================================
    # 18. Knowledge Graphs Table
    # ==========================================
    op.create_table('knowledge_graphs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('graph_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_knowledge_graphs_user_id', 'user_id'),
        sa.Index('idx_knowledge_graphs_created_at', 'created_at'),
    )
    
    # ==========================================
    # 19. Tool Executions Table
    # ==========================================
    op.create_table('tool_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', sa.String(length=100), nullable=False),  # tools.id is VARCHAR(100)
        sa.Column('tool_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),  # pending, running, completed, failed
        sa.Column('input_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_tool_executions_agent_id', 'agent_id'),
        sa.Index('idx_tool_executions_tool_id', 'tool_id'),
        sa.Index('idx_tool_executions_status', 'status'),
        sa.Index('idx_tool_executions_created_at', 'created_at'),
    )
    
    # ==========================================
    # 20. Query Logs Table
    # ==========================================
    op.create_table('query_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('query_type', sa.String(length=50), nullable=True),  # search, filter, aggregate
        sa.Column('results_count', sa.Integer(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_query_logs_user_id', 'user_id'),
        sa.Index('idx_query_logs_created_at', 'created_at'),
        sa.Index('idx_query_logs_query_type', 'query_type'),
    )
    
    # ==========================================
    # 21. User Settings Table
    # ==========================================
    op.create_table('user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('theme', sa.String(length=50), nullable=True, server_default='light'),
        sa.Column('language', sa.String(length=10), nullable=True, server_default='en'),
        sa.Column('notifications_enabled', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_settings_user_id'),
    )


def downgrade() -> None:
    """Drop all created tables."""
    op.drop_table('user_settings')
    op.drop_table('query_logs')
    op.drop_table('tool_executions')
    op.drop_table('knowledge_graphs')
    op.drop_table('agentflow_edges')
    op.drop_table('agentflow_agents')
    op.drop_table('event_store')
    op.drop_table('api_keys')
    op.drop_table('conversation_shares')
    op.drop_table('notifications')
    op.drop_table('bookmarks')
    op.drop_table('teams')
    op.drop_table('organizations')
    op.drop_table('agent_memories')
    op.drop_table('agent_executions')
    op.drop_table('agent_knowledgebases')
    op.drop_table('agent_tools')
    op.drop_table('agent_versions')
    op.drop_table('feedback')
    # Skip messages - already exists
    op.drop_table('conversations')
