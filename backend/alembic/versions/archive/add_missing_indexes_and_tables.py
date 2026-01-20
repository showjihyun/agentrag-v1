"""Add missing indexes and tables for performance and tracking

Revision ID: add_missing_indexes_and_tables
Revises: add_comprehensive_indexes
Create Date: 2025-11-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = 'add_missing_indexes_and_tables'
down_revision = 'add_comprehensive_indexes'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing tables and indexes."""
    
    # ========================================================================
    # 1. Tool Credentials Table
    # ========================================================================
    op.create_table(
        'tool_credentials',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('tool_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('credentials', sa.Text, nullable=False),  # Encrypted
        sa.Column('is_active', sa.Boolean, server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'tool_id', 'name', name='uq_tool_credential')
    )
    
    op.create_index(
        'idx_tool_credentials_user_tool',
        'tool_credentials',
        ['user_id', 'tool_id'],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_tool_credentials_user_active',
        'tool_credentials',
        ['user_id', 'is_active'],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # 2. Tool Executions Table
    # ========================================================================
    op.create_table(
        'tool_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tool_id', sa.String(100), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', UUID(as_uuid=True)),
        sa.Column('execution_id', UUID(as_uuid=True)),
        sa.Column('credential_id', UUID(as_uuid=True)),
        sa.Column('parameters', JSONB),
        sa.Column('result', JSONB),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text),
        sa.Column('started_at', sa.DateTime, server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_ms', sa.Integer),
        sa.ForeignKeyConstraint(['tool_id'], ['tools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['execution_id'], ['agent_executions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['credential_id'], ['tool_credentials.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'timeout', 'cancelled')",
            name='check_tool_execution_status_valid'
        ),
        sa.CheckConstraint('duration_ms >= 0', name='check_tool_duration_positive')
    )
    
    op.create_index(
        'idx_tool_executions_tool_started_desc',
        'tool_executions',
        ['tool_id', sa.text('started_at DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_tool_executions_user_started_desc',
        'tool_executions',
        ['user_id', sa.text('started_at DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_tool_executions_status_started',
        'tool_executions',
        ['status', sa.text('started_at DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_tool_executions_agent_started',
        'tool_executions',
        ['agent_id', sa.text('started_at DESC')],
        postgresql_using='btree',
        postgresql_where=sa.text('agent_id IS NOT NULL')
    )
    
    # ========================================================================
    # 3. Messages Table Indexes
    # ========================================================================
    op.create_index(
        'idx_messages_session_created_desc',
        'messages',
        ['session_id', sa.text('created_at DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_messages_user_created_desc',
        'messages',
        ['user_id', sa.text('created_at DESC')],
        postgresql_using='btree',
        postgresql_where=sa.text('user_id IS NOT NULL')
    )
    
    # ========================================================================
    # 4. Documents Table Indexes
    # ========================================================================
    op.create_index(
        'idx_documents_user_created_desc',
        'documents',
        ['user_id', sa.text('created_at DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_documents_status_created',
        'documents',
        ['status', sa.text('created_at DESC')],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # 5. Audit Logs Table Indexes
    # ========================================================================
    op.create_index(
        'idx_audit_logs_user_timestamp_desc',
        'audit_logs',
        ['user_id', sa.text('timestamp DESC')],
        postgresql_using='btree',
        postgresql_where=sa.text('user_id IS NOT NULL')
    )
    
    op.create_index(
        'idx_audit_logs_action_timestamp',
        'audit_logs',
        ['action', sa.text('timestamp DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_audit_logs_resource',
        'audit_logs',
        ['resource_type', 'resource_id', sa.text('timestamp DESC')],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # 6. Usage Logs Table Indexes
    # ========================================================================
    op.create_index(
        'idx_usage_logs_user_timestamp_desc',
        'usage_logs',
        ['user_id', sa.text('timestamp DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_usage_logs_resource_timestamp',
        'usage_logs',
        ['resource_type', sa.text('timestamp DESC')],
        postgresql_using='btree'
    )
    
    # ========================================================================
    # 7. Sessions Table Indexes
    # ========================================================================
    op.create_index(
        'idx_sessions_user_created_desc',
        'sessions',
        ['user_id', sa.text('created_at DESC')],
        postgresql_using='btree'
    )
    
    op.create_index(
        'idx_sessions_expires_at',
        'sessions',
        ['expires_at'],
        postgresql_using='btree'
    )


def downgrade():
    """Remove added tables and indexes."""
    
    # Drop indexes
    op.drop_index('idx_sessions_expires_at', 'sessions')
    op.drop_index('idx_sessions_user_created_desc', 'sessions')
    op.drop_index('idx_usage_logs_resource_timestamp', 'usage_logs')
    op.drop_index('idx_usage_logs_user_timestamp_desc', 'usage_logs')
    op.drop_index('idx_audit_logs_resource', 'audit_logs')
    op.drop_index('idx_audit_logs_action_timestamp', 'audit_logs')
    op.drop_index('idx_audit_logs_user_timestamp_desc', 'audit_logs')
    op.drop_index('idx_documents_status_created', 'documents')
    op.drop_index('idx_documents_user_created_desc', 'documents')
    op.drop_index('idx_messages_user_created_desc', 'messages')
    op.drop_index('idx_messages_session_created_desc', 'messages')
    
    # Drop tool_executions indexes and table
    op.drop_index('idx_tool_executions_agent_started', 'tool_executions')
    op.drop_index('idx_tool_executions_status_started', 'tool_executions')
    op.drop_index('idx_tool_executions_user_started_desc', 'tool_executions')
    op.drop_index('idx_tool_executions_tool_started_desc', 'tool_executions')
    op.drop_table('tool_executions')
    
    # Drop tool_credentials indexes and table
    op.drop_index('idx_tool_credentials_user_active', 'tool_credentials')
    op.drop_index('idx_tool_credentials_user_tool', 'tool_credentials')
    op.drop_table('tool_credentials')
