"""Add missing flow-related tables

Revision ID: 20260120_add_flow_tables
Revises: 20260120_add_missing_kb_cols
Create Date: 2026-01-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260120_add_flow_tables'
down_revision: Union[str, None] = '20260120_add_missing_kb_cols'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create missing flow-related tables."""
    
    # Get existing tables
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # ==========================================
    # 1. ChatflowTool Table
    # ==========================================
    if 'chatflow_tools' not in existing_tables:
        op.create_table('chatflow_tools',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('tool_id', sa.String(length=100), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('enabled', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['chatflow_id'], ['chatflows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('chatflow_id', 'tool_id', name='uq_chatflow_tool'),
            sa.Index('ix_chatflow_tools_chatflow_id', 'chatflow_id'),
        )
    
    # ==========================================
    # 2. ChatSession Table
    # ==========================================
    if 'chat_sessions' not in existing_tables:
        op.create_table('chat_sessions',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('session_token', sa.String(length=255), nullable=True),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('memory_type', sa.String(length=50), nullable=False, server_default='buffer'),
            sa.Column('memory_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
            sa.Column('memory_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('total_tokens_used', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('avg_response_time', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('last_activity_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('auto_archive_after_days', sa.Integer(), nullable=True, server_default='30'),
            sa.Column('message_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('last_message_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['chatflow_id'], ['chatflows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('session_token', name='uq_chat_session_token'),
            sa.Index('ix_chat_sessions_chatflow_updated', 'chatflow_id', 'updated_at'),
            sa.Index('ix_chat_sessions_user_status', 'user_id', 'status'),
            sa.Index('ix_chat_sessions_memory_type', 'memory_type'),
            sa.Index('ix_chat_sessions_last_activity', 'last_activity_at'),
            sa.CheckConstraint(
                "memory_type IN ('buffer', 'summary', 'vector', 'hybrid')",
                name='check_memory_type_valid'
            ),
            sa.CheckConstraint(
                "status IN ('active', 'archived', 'deleted')",
                name='check_session_status_valid'
            ),
        )
    
    # ==========================================
    # 3. ChatMessage Table
    # ==========================================
    if 'chat_messages' not in existing_tables:
        op.create_table('chat_messages',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('role', sa.String(length=50), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('message_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('embedding_id', sa.String(length=255), nullable=True),
            sa.Column('is_summarized', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('is_archived', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.Index('ix_chat_messages_session_created', 'session_id', 'created_at'),
            sa.Index('ix_chat_messages_embedding', 'embedding_id'),
            sa.CheckConstraint(
                "role IN ('user', 'assistant', 'system', 'tool')",
                name='check_message_role_valid'
            ),
        )
    
    # ==========================================
    # 4. ChatSummary Table
    # ==========================================
    if 'chat_summaries' not in existing_tables:
        op.create_table('chat_summaries',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('summary_text', sa.Text(), nullable=False),
            sa.Column('summary_type', sa.String(length=50), nullable=True, server_default='conversation'),
            sa.Column('start_message_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('end_message_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('message_count', sa.Integer(), nullable=False),
            sa.Column('topics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('key_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('decisions_made', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('embedding_id', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['start_message_id'], ['chat_messages.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['end_message_id'], ['chat_messages.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.Index('ix_chat_summaries_session_created', 'session_id', 'created_at'),
            sa.Index('ix_chat_summaries_embedding', 'embedding_id'),
            sa.CheckConstraint(
                "summary_type IN ('conversation', 'topic', 'decision')",
                name='check_summary_type_valid'
            ),
        )
    
    # ==========================================
    # 5. NodeExecution Table
    # ==========================================
    if 'node_executions' not in existing_tables:
        op.create_table('node_executions',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('flow_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('node_id', sa.String(length=255), nullable=False),
            sa.Column('node_type', sa.String(length=100), nullable=False),
            sa.Column('node_label', sa.String(length=255), nullable=True),
            sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('duration_ms', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['flow_execution_id'], ['flow_executions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.Index('ix_node_executions_flow_status', 'flow_execution_id', 'status'),
            sa.CheckConstraint(
                "status IN ('pending', 'running', 'completed', 'failed', 'skipped')",
                name='check_node_execution_status_valid'
            ),
        )
    
    # ==========================================
    # 6. ExecutionLog Table
    # ==========================================
    if 'execution_logs' not in existing_tables:
        op.create_table('execution_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('flow_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('level', sa.String(length=20), nullable=False, server_default='info'),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('log_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['flow_execution_id'], ['flow_executions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.Index('ix_execution_logs_flow_timestamp', 'flow_execution_id', 'timestamp'),
            sa.CheckConstraint(
                "level IN ('debug', 'info', 'warn', 'error')",
                name='check_log_level_valid'
            ),
        )
    
    # ==========================================
    # 7. MarketplaceItem Table
    # ==========================================
    if 'marketplace_items' not in existing_tables:
        op.create_table('marketplace_items',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('item_type', sa.String(length=50), nullable=False),
            sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('reference_type', sa.String(length=50), nullable=False),
            sa.Column('category', sa.String(length=100), nullable=True),
            sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('preview_image', sa.String(length=500), nullable=True),
            sa.Column('rating', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('rating_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('install_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('is_featured', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('is_official', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('is_published', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('price', sa.String(length=20), nullable=True, server_default='free'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.Index('ix_marketplace_items_author_id', 'author_id'),
            sa.Index('ix_marketplace_items_category', 'category'),
            sa.Index('ix_marketplace_items_type_category', 'item_type', 'category'),
            sa.Index('ix_marketplace_items_featured', 'is_featured', 'is_published'),
            sa.Index('ix_marketplace_items_created_at', 'created_at'),
            sa.CheckConstraint(
                "item_type IN ('agentflow', 'chatflow', 'workflow', 'tool', 'template')",
                name='check_marketplace_item_type_valid'
            ),
            sa.CheckConstraint(
                "rating >= 0.0 AND rating <= 5.0",
                name='check_marketplace_rating_range'
            ),
        )
    
    # ==========================================
    # 8. FlowTemplate Table
    # ==========================================
    if 'flow_templates' not in existing_tables:
        op.create_table('flow_templates',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('flow_type', sa.String(length=50), nullable=False),
            sa.Column('category', sa.String(length=100), nullable=True),
            sa.Column('icon', sa.String(length=50), nullable=True),
            sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('use_case_examples', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('is_system', sa.Boolean(), nullable=True, server_default='false'),
            sa.Column('is_published', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('usage_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('rating', sa.Float(), nullable=True, server_default='0.0'),
            sa.Column('rating_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.Index('ix_flow_templates_author_id', 'author_id'),
            sa.Index('ix_flow_templates_category', 'category'),
            sa.Index('ix_flow_templates_type_category', 'flow_type', 'category'),
            sa.Index('ix_flow_templates_system_published', 'is_system', 'is_published'),
            sa.Index('ix_flow_templates_created_at', 'created_at'),
            sa.CheckConstraint(
                "flow_type IN ('agentflow', 'chatflow')",
                name='check_flow_template_type_valid'
            ),
            sa.CheckConstraint(
                "rating >= 0.0 AND rating <= 5.0",
                name='check_flow_template_rating_range'
            ),
        )
    
    # ==========================================
    # 9. TokenUsage Table
    # ==========================================
    if 'token_usages' not in existing_tables:
        op.create_table('token_usages',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('flow_execution_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('node_id', sa.String(length=255), nullable=True),
            sa.Column('node_type', sa.String(length=100), nullable=True),
            sa.Column('provider', sa.String(length=100), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('cost_usd', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['flow_execution_id'], ['flow_executions.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
            sa.Index('ix_token_usages_user_id', 'user_id'),
            sa.Index('ix_token_usages_flow_execution_id', 'flow_execution_id'),
            sa.Index('ix_token_usages_user_created', 'user_id', 'created_at'),
            sa.Index('ix_token_usages_user_model', 'user_id', 'model'),
            sa.Index('ix_token_usages_workflow', 'workflow_id', 'created_at'),
            sa.Index('ix_token_usages_created_at', 'created_at'),
        )
    
    # ==========================================
    # 10. ModelPricing Table
    # ==========================================
    if 'model_pricings' not in existing_tables:
        op.create_table('model_pricings',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('provider', sa.String(length=100), nullable=False),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('input_price_per_1k', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('output_price_per_1k', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('currency', sa.String(length=10), nullable=True, server_default='USD'),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('provider', 'model', name='uq_model_pricing'),
            sa.Index('ix_model_pricings_provider_model', 'provider', 'model'),
            sa.Index('ix_model_pricings_is_active', 'is_active'),
        )
    
    # ==========================================
    # 11. EmbedConfig Table
    # ==========================================
    if 'embed_configs' not in existing_tables:
        op.create_table('embed_configs',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('embed_token', sa.String(length=255), nullable=False),
            sa.Column('theme', sa.String(length=50), nullable=True, server_default='light'),
            sa.Column('primary_color', sa.String(length=20), nullable=True, server_default='#6366f1'),
            sa.Column('position', sa.String(length=50), nullable=True, server_default='bottom-right'),
            sa.Column('widget_title', sa.String(length=255), nullable=True),
            sa.Column('welcome_message', sa.Text(), nullable=True),
            sa.Column('placeholder_text', sa.String(length=255), nullable=True, server_default='메시지를 입력하세요...'),
            sa.Column('show_branding', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('custom_css', sa.Text(), nullable=True),
            sa.Column('allowed_domains', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('rate_limit_per_ip', sa.Integer(), nullable=True, server_default='100'),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(['chatflow_id'], ['chatflows.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('embed_token', name='uq_embed_token'),
            sa.Index('ix_embed_configs_chatflow_id', 'chatflow_id'),
            sa.Index('ix_embed_configs_user_id', 'user_id'),
            sa.Index('ix_embed_configs_chatflow_active', 'chatflow_id', 'is_active'),
            sa.Index('ix_embed_configs_token', 'embed_token'),
            sa.Index('ix_embed_configs_is_active', 'is_active'),
        )


def downgrade() -> None:
    """Drop all created tables."""
    op.drop_table('embed_configs')
    op.drop_table('model_pricings')
    op.drop_table('token_usages')
    op.drop_table('flow_templates')
    op.drop_table('marketplace_items')
    op.drop_table('execution_logs')
    op.drop_table('node_executions')
    op.drop_table('chat_summaries')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('chatflow_tools')
