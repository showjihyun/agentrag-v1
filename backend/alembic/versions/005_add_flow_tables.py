"""Add flow tables for Agentflow and Chatflow

Revision ID: 005_add_flow_tables
Revises: 004_add_workflow_blocks_and_triggers
Create Date: 2024-12-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_flow_tables'
down_revision = '004_add_workflow_blocks_and_triggers'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create agentflows table
    op.create_table(
        'agentflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('orchestration_type', sa.String(50), nullable=False, default='sequential'),
        sa.Column('supervisor_config', postgresql.JSONB, default=dict),
        sa.Column('communication_protocol', sa.String(50), default='direct'),
        sa.Column('graph_definition', postgresql.JSONB, nullable=False, default=dict),
        sa.Column('version', sa.String(50), default='1.0.0'),
        sa.Column('tags', postgresql.JSONB, default=list),
        sa.Column('category', sa.String(100)),
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('execution_count', sa.Integer, default=0),
        sa.Column('last_execution_status', sa.String(50)),
        sa.Column('last_execution_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime),
        sa.CheckConstraint(
            "orchestration_type IN ('sequential', 'parallel', 'hierarchical', 'adaptive')",
            name='check_orchestration_type_valid'
        ),
    )
    
    op.create_index('ix_agentflows_user_id', 'agentflows', ['user_id'])
    op.create_index('ix_agentflows_is_public', 'agentflows', ['is_public'])
    op.create_index('ix_agentflows_is_active', 'agentflows', ['is_active'])
    op.create_index('ix_agentflows_created_at', 'agentflows', ['created_at'])
    op.create_index('ix_agentflows_user_active', 'agentflows', ['user_id', 'is_active'])
    op.create_index('ix_agentflows_user_created', 'agentflows', ['user_id', 'created_at'])

    # Create agentflow_agents table
    op.create_table(
        'agentflow_agents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agentflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agentflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agents.id', ondelete='SET NULL')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('capabilities', postgresql.JSONB, default=list),
        sa.Column('priority', sa.Integer, default=1),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('timeout_seconds', sa.Integer, default=60),
        sa.Column('dependencies', postgresql.JSONB, default=list),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('ix_agentflow_agents_agentflow_id', 'agentflow_agents', ['agentflow_id'])
    op.create_index('ix_agentflow_agents_flow_priority', 'agentflow_agents', ['agentflow_id', 'priority'])

    # Create chatflows table
    op.create_table(
        'chatflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('chat_config', postgresql.JSONB, nullable=False, default=dict),
        sa.Column('memory_config', postgresql.JSONB, default=dict),
        sa.Column('rag_config', postgresql.JSONB, default=dict),
        sa.Column('graph_definition', postgresql.JSONB, nullable=False, default=dict),
        sa.Column('version', sa.String(50), default='1.0.0'),
        sa.Column('tags', postgresql.JSONB, default=list),
        sa.Column('category', sa.String(100)),
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('execution_count', sa.Integer, default=0),
        sa.Column('last_execution_status', sa.String(50)),
        sa.Column('last_execution_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime),
    )
    
    op.create_index('ix_chatflows_user_id', 'chatflows', ['user_id'])
    op.create_index('ix_chatflows_is_public', 'chatflows', ['is_public'])
    op.create_index('ix_chatflows_is_active', 'chatflows', ['is_active'])
    op.create_index('ix_chatflows_created_at', 'chatflows', ['created_at'])
    op.create_index('ix_chatflows_user_active', 'chatflows', ['user_id', 'is_active'])
    op.create_index('ix_chatflows_user_created', 'chatflows', ['user_id', 'created_at'])

    # Create chatflow_tools table
    op.create_table(
        'chatflow_tools',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chatflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tool_id', sa.String(100), sa.ForeignKey('tools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('configuration', postgresql.JSONB, default=dict),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('chatflow_id', 'tool_id', name='uq_chatflow_tool'),
    )
    
    op.create_index('ix_chatflow_tools_chatflow_id', 'chatflow_tools', ['chatflow_id'])

    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chatflows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('session_token', sa.String(255), unique=True),
        sa.Column('title', sa.String(255)),
        sa.Column('memory_state', postgresql.JSONB, default=dict),
        sa.Column('message_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime),
    )
    
    op.create_index('ix_chat_sessions_chatflow_id', 'chat_sessions', ['chatflow_id'])
    op.create_index('ix_chat_sessions_session_token', 'chat_sessions', ['session_token'])
    op.create_index('ix_chat_sessions_chatflow_updated', 'chat_sessions', ['chatflow_id', 'updated_at'])

    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSONB, default=dict),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system', 'tool')",
            name='check_message_role_valid'
        ),
    )
    
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'])
    op.create_index('ix_chat_messages_session_created', 'chat_messages', ['session_id', 'created_at'])


    # Create flow_executions table
    op.create_table(
        'flow_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agentflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agentflows.id', ondelete='CASCADE')),
        sa.Column('chatflow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('chatflows.id', ondelete='CASCADE')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('flow_type', sa.String(50), nullable=False),
        sa.Column('flow_name', sa.String(255)),
        sa.Column('input_data', postgresql.JSONB),
        sa.Column('output_data', postgresql.JSONB),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text),
        sa.Column('started_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_ms', sa.Integer),
        sa.Column('metrics', postgresql.JSONB, default=dict),
        sa.CheckConstraint(
            "flow_type IN ('agentflow', 'chatflow')",
            name='check_flow_type_valid'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name='check_flow_execution_status_valid'
        ),
    )
    
    op.create_index('ix_flow_executions_agentflow_id', 'flow_executions', ['agentflow_id'])
    op.create_index('ix_flow_executions_chatflow_id', 'flow_executions', ['chatflow_id'])
    op.create_index('ix_flow_executions_user_id', 'flow_executions', ['user_id'])
    op.create_index('ix_flow_executions_status', 'flow_executions', ['status'])
    op.create_index('ix_flow_executions_started_at', 'flow_executions', ['started_at'])
    op.create_index('ix_flow_executions_user_status', 'flow_executions', ['user_id', 'status'])

    # Create node_executions table
    op.create_table(
        'node_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('flow_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('flow_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', sa.String(255), nullable=False),
        sa.Column('node_type', sa.String(100), nullable=False),
        sa.Column('node_label', sa.String(255)),
        sa.Column('input_data', postgresql.JSONB),
        sa.Column('output_data', postgresql.JSONB),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_ms', sa.Integer),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'skipped')",
            name='check_node_execution_status_valid'
        ),
    )
    
    op.create_index('ix_node_executions_flow_execution_id', 'node_executions', ['flow_execution_id'])
    op.create_index('ix_node_executions_flow_status', 'node_executions', ['flow_execution_id', 'status'])

    # Create execution_logs table
    op.create_table(
        'execution_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('flow_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('flow_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('level', sa.String(20), nullable=False, default='info'),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('metadata', postgresql.JSONB, default=dict),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "level IN ('debug', 'info', 'warn', 'error')",
            name='check_log_level_valid'
        ),
    )
    
    op.create_index('ix_execution_logs_flow_execution_id', 'execution_logs', ['flow_execution_id'])
    op.create_index('ix_execution_logs_timestamp', 'execution_logs', ['timestamp'])
    op.create_index('ix_execution_logs_flow_timestamp', 'execution_logs', ['flow_execution_id', 'timestamp'])

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('key_prefix', sa.String(20), nullable=False),
        sa.Column('permissions', postgresql.JSONB, default=list),
        sa.Column('rate_limit', sa.Integer, default=1000),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('usage_count', sa.Integer, default=0),
        sa.Column('last_used_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'])
    op.create_index('ix_api_keys_key_prefix', 'api_keys', ['key_prefix'])
    op.create_index('ix_api_keys_user_active', 'api_keys', ['user_id', 'is_active'])

    # Create marketplace_items table
    op.create_table(
        'marketplace_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('item_type', sa.String(50), nullable=False),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reference_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('tags', postgresql.JSONB, default=list),
        sa.Column('preview_image', sa.String(500)),
        sa.Column('rating', sa.Float, default=0.0),
        sa.Column('rating_count', sa.Integer, default=0),
        sa.Column('install_count', sa.Integer, default=0),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('is_official', sa.Boolean, default=False),
        sa.Column('is_published', sa.Boolean, default=True),
        sa.Column('price', sa.String(20), default='free'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.CheckConstraint(
            "item_type IN ('agentflow', 'chatflow', 'workflow', 'tool', 'template')",
            name='check_marketplace_item_type_valid'
        ),
        sa.CheckConstraint('rating >= 0.0 AND rating <= 5.0', name='check_marketplace_rating_range'),
    )
    
    op.create_index('ix_marketplace_items_author_id', 'marketplace_items', ['author_id'])
    op.create_index('ix_marketplace_items_category', 'marketplace_items', ['category'])
    op.create_index('ix_marketplace_items_is_featured', 'marketplace_items', ['is_featured'])
    op.create_index('ix_marketplace_items_is_published', 'marketplace_items', ['is_published'])
    op.create_index('ix_marketplace_items_created_at', 'marketplace_items', ['created_at'])
    op.create_index('ix_marketplace_items_type_category', 'marketplace_items', ['item_type', 'category'])
    op.create_index('ix_marketplace_items_featured', 'marketplace_items', ['is_featured', 'is_published'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('marketplace_items')
    op.drop_table('api_keys')
    op.drop_table('execution_logs')
    op.drop_table('node_executions')
    op.drop_table('flow_executions')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('chatflow_tools')
    op.drop_table('chatflows')
    op.drop_table('agentflow_agents')
    op.drop_table('agentflows')
