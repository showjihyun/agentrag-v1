"""add_flows_tables

Revision ID: 009_add_flows_tables
Revises: d7582c3cc7e9
Create Date: 2025-12-13 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '009_add_flows_tables'
down_revision: Union[str, None] = 'd7582c3cc7e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Agentflows table
    op.create_table('agentflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('orchestration_type', sa.String(length=50), nullable=False),
        sa.Column('supervisor_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('communication_protocol', sa.String(length=50), nullable=True),
        sa.Column('graph_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=True),
        sa.Column('last_execution_status', sa.String(length=50), nullable=True),
        sa.Column('last_execution_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("orchestration_type IN ('sequential', 'parallel', 'hierarchical', 'adaptive')", name='check_orchestration_type_valid'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agentflows_user_active', 'agentflows', ['user_id', 'is_active'], unique=False)
    op.create_index('ix_agentflows_user_created', 'agentflows', ['user_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_agentflows_is_active'), 'agentflows', ['is_active'], unique=False)
    op.create_index(op.f('ix_agentflows_is_public'), 'agentflows', ['is_public'], unique=False)
    op.create_index(op.f('ix_agentflows_user_id'), 'agentflows', ['user_id'], unique=False)

    # Create Chatflows table
    op.create_table('chatflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('chat_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('memory_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('rag_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('graph_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('execution_count', sa.Integer(), nullable=True),
        sa.Column('last_execution_status', sa.String(length=50), nullable=True),
        sa.Column('last_execution_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chatflows_user_active', 'chatflows', ['user_id', 'is_active'], unique=False)
    op.create_index('ix_chatflows_user_created', 'chatflows', ['user_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_chatflows_is_active'), 'chatflows', ['is_active'], unique=False)
    op.create_index(op.f('ix_chatflows_is_public'), 'chatflows', ['is_public'], unique=False)
    op.create_index(op.f('ix_chatflows_user_id'), 'chatflows', ['user_id'], unique=False)

    # Create Agentflow Agents table
    op.create_table('agentflow_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agentflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('capabilities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.Column('timeout_seconds', sa.Integer(), nullable=True),
        sa.Column('dependencies', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['agentflow_id'], ['agentflows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agentflow_agents_flow_priority', 'agentflow_agents', ['agentflow_id', 'priority'], unique=False)
    op.create_index(op.f('ix_agentflow_agents_agentflow_id'), 'agentflow_agents', ['agentflow_id'], unique=False)

    # Create Chatflow Tools table
    op.create_table('chatflow_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['chatflow_id'], ['chatflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chatflow_id', 'tool_id', name='uq_chatflow_tool')
    )
    op.create_index(op.f('ix_chatflow_tools_chatflow_id'), 'chatflow_tools', ['chatflow_id'], unique=False)

    # Create Chat Sessions table
    op.create_table('chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_token', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('memory_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['chatflow_id'], ['chatflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_sessions_chatflow_updated', 'chat_sessions', ['chatflow_id', 'updated_at'], unique=False)
    op.create_index(op.f('ix_chat_sessions_chatflow_id'), 'chat_sessions', ['chatflow_id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_session_token'), 'chat_sessions', ['session_token'], unique=True)

    # Create Chat Messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system', 'tool')", name='check_message_role_valid'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_session_created', 'chat_messages', ['session_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_chat_messages_created_at'), 'chat_messages', ['created_at'], unique=False)
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)

    # Create Flow Executions table
    op.create_table('flow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agentflow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_type', sa.String(length=50), nullable=False),
        sa.Column('flow_name', sa.String(length=255), nullable=True),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint("flow_type IN ('agentflow', 'chatflow')", name='check_flow_type_valid'),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'cancelled')", name='check_flow_execution_status_valid'),
        sa.ForeignKeyConstraint(['agentflow_id'], ['agentflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chatflow_id'], ['chatflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_flow_executions_user_status', 'flow_executions', ['user_id', 'status'], unique=False)
    op.create_index(op.f('ix_flow_executions_started_at'), 'flow_executions', ['started_at'], unique=False)
    op.create_index(op.f('ix_flow_executions_status'), 'flow_executions', ['status'], unique=False)
    op.create_index(op.f('ix_flow_executions_user_id'), 'flow_executions', ['user_id'], unique=False)

    # Create Node Executions table
    op.create_table('node_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_id', sa.String(length=255), nullable=False),
        sa.Column('node_type', sa.String(length=100), nullable=False),
        sa.Column('node_label', sa.String(length=255), nullable=True),
        sa.Column('input_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'running', 'completed', 'failed', 'skipped')", name='check_node_execution_status_valid'),
        sa.ForeignKeyConstraint(['flow_execution_id'], ['flow_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_node_executions_flow_status', 'node_executions', ['flow_execution_id', 'status'], unique=False)
    op.create_index(op.f('ix_node_executions_flow_execution_id'), 'node_executions', ['flow_execution_id'], unique=False)

    # Create Execution Logs table
    op.create_table('execution_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('level', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('log_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.CheckConstraint("level IN ('debug', 'info', 'warn', 'error')", name='check_log_level_valid'),
        sa.ForeignKeyConstraint(['flow_execution_id'], ['flow_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_execution_logs_flow_timestamp', 'execution_logs', ['flow_execution_id', 'timestamp'], unique=False)
    op.create_index(op.f('ix_execution_logs_flow_execution_id'), 'execution_logs', ['flow_execution_id'], unique=False)
    op.create_index(op.f('ix_execution_logs_timestamp'), 'execution_logs', ['timestamp'], unique=False)

    # Create Marketplace Items table
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
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=True),
        sa.Column('install_count', sa.Integer(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('is_official', sa.Boolean(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('price', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("item_type IN ('agentflow', 'chatflow', 'workflow', 'tool', 'template')", name='check_marketplace_item_type_valid'),
        sa.CheckConstraint('rating >= 0.0 AND rating <= 5.0', name='check_marketplace_rating_range'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_marketplace_items_featured', 'marketplace_items', ['is_featured', 'is_published'], unique=False)
    op.create_index('ix_marketplace_items_type_category', 'marketplace_items', ['item_type', 'category'], unique=False)
    op.create_index(op.f('ix_marketplace_items_author_id'), 'marketplace_items', ['author_id'], unique=False)
    op.create_index(op.f('ix_marketplace_items_category'), 'marketplace_items', ['category'], unique=False)
    op.create_index(op.f('ix_marketplace_items_created_at'), 'marketplace_items', ['created_at'], unique=False)
    op.create_index(op.f('ix_marketplace_items_is_featured'), 'marketplace_items', ['is_featured'], unique=False)
    op.create_index(op.f('ix_marketplace_items_is_published'), 'marketplace_items', ['is_published'], unique=False)

    # Create Marketplace Reviews table
    op.create_table('marketplace_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_review_rating_range'),
        sa.ForeignKeyConstraint(['item_id'], ['marketplace_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('item_id', 'user_id', name='uq_marketplace_review_user')
    )
    op.create_index('ix_marketplace_reviews_item_created', 'marketplace_reviews', ['item_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_marketplace_reviews_created_at'), 'marketplace_reviews', ['created_at'], unique=False)
    op.create_index(op.f('ix_marketplace_reviews_item_id'), 'marketplace_reviews', ['item_id'], unique=False)
    op.create_index(op.f('ix_marketplace_reviews_user_id'), 'marketplace_reviews', ['user_id'], unique=False)

    # Create Flow Templates table
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
        sa.Column('is_system', sa.Boolean(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('rating_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("flow_type IN ('agentflow', 'chatflow')", name='check_flow_template_type_valid'),
        sa.CheckConstraint('rating >= 0.0 AND rating <= 5.0', name='check_flow_template_rating_range'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_flow_templates_system_published', 'flow_templates', ['is_system', 'is_published'], unique=False)
    op.create_index('ix_flow_templates_type_category', 'flow_templates', ['flow_type', 'category'], unique=False)
    op.create_index(op.f('ix_flow_templates_category'), 'flow_templates', ['category'], unique=False)
    op.create_index(op.f('ix_flow_templates_created_at'), 'flow_templates', ['created_at'], unique=False)
    op.create_index(op.f('ix_flow_templates_is_published'), 'flow_templates', ['is_published'], unique=False)
    op.create_index(op.f('ix_flow_templates_is_system'), 'flow_templates', ['is_system'], unique=False)

    # Create Token Usage table
    op.create_table('token_usages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flow_execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('node_id', sa.String(length=255), nullable=True),
        sa.Column('node_type', sa.String(length=100), nullable=True),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('cost_usd', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['flow_execution_id'], ['flow_executions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_token_usages_user_created', 'token_usages', ['user_id', 'created_at'], unique=False)
    op.create_index('ix_token_usages_user_model', 'token_usages', ['user_id', 'model'], unique=False)
    op.create_index('ix_token_usages_workflow', 'token_usages', ['workflow_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_token_usages_created_at'), 'token_usages', ['created_at'], unique=False)
    op.create_index(op.f('ix_token_usages_flow_execution_id'), 'token_usages', ['flow_execution_id'], unique=False)
    op.create_index(op.f('ix_token_usages_user_id'), 'token_usages', ['user_id'], unique=False)
    op.create_index(op.f('ix_token_usages_workflow_id'), 'token_usages', ['workflow_id'], unique=False)

    # Create Model Pricing table
    op.create_table('model_pricings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('input_price_per_1k', sa.Float(), nullable=False),
        sa.Column('output_price_per_1k', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['provider'], ['llm_providers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'model', name='uq_model_pricing')
    )
    op.create_index('ix_model_pricings_provider_model', 'model_pricings', ['provider', 'model'], unique=False)
    op.create_index(op.f('ix_model_pricings_is_active'), 'model_pricings', ['is_active'], unique=False)

    # Create Embed Config table
    op.create_table('embed_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embed_token', sa.String(length=255), nullable=False),
        sa.Column('theme', sa.String(length=50), nullable=True),
        sa.Column('primary_color', sa.String(length=20), nullable=True),
        sa.Column('position', sa.String(length=50), nullable=True),
        sa.Column('widget_title', sa.String(length=255), nullable=True),
        sa.Column('welcome_message', sa.Text(), nullable=True),
        sa.Column('placeholder_text', sa.String(length=255), nullable=True),
        sa.Column('show_branding', sa.Boolean(), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('allowed_domains', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('rate_limit_per_ip', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['chatflow_id'], ['chatflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_embed_configs_chatflow_active', 'embed_configs', ['chatflow_id', 'is_active'], unique=False)
    op.create_index(op.f('ix_embed_configs_chatflow_id'), 'embed_configs', ['chatflow_id'], unique=False)
    op.create_index(op.f('ix_embed_configs_embed_token'), 'embed_configs', ['embed_token'], unique=True)
    op.create_index(op.f('ix_embed_configs_is_active'), 'embed_configs', ['is_active'], unique=False)
    op.create_index(op.f('ix_embed_configs_user_id'), 'embed_configs', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('embed_configs')
    op.drop_table('model_pricings')
    op.drop_table('token_usages')
    op.drop_table('flow_templates')
    op.drop_table('marketplace_reviews')
    op.drop_table('marketplace_items')
    op.drop_table('execution_logs')
    op.drop_table('node_executions')
    op.drop_table('flow_executions')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('chatflow_tools')
    op.drop_table('agentflow_agents')
    op.drop_table('chatflows')
    op.drop_table('agentflows')