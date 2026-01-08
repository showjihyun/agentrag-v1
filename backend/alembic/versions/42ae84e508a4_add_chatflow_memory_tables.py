"""Add chatflow memory tables

Revision ID: 42ae84e508a4
Revises: a0511f45fcf7
Create Date: 2025-12-30 21:58:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '42ae84e508a4'
down_revision: Union[str, None] = 'a0511f45fcf7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('chatflow_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('session_token', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('memory_type', sa.String(length=50), nullable=False),
        sa.Column('memory_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('memory_state', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('total_tokens_used', sa.Integer(), nullable=True),
        sa.Column('avg_response_time', sa.Float(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('auto_archive_after_days', sa.Integer(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("memory_type IN ('buffer', 'summary', 'vector', 'hybrid')", name='check_memory_type_valid'),
        sa.CheckConstraint("status IN ('active', 'archived', 'deleted')", name='check_session_status_valid'),
        sa.ForeignKeyConstraint(['chatflow_id'], ['chatflows.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_chatflow_id'), 'chat_sessions', ['chatflow_id'], unique=False)
    op.create_index('ix_chat_sessions_chatflow_updated', 'chat_sessions', ['chatflow_id', 'updated_at'], unique=False)
    op.create_index('ix_chat_sessions_last_activity', 'chat_sessions', ['last_activity_at'], unique=False)
    op.create_index('ix_chat_sessions_memory_type', 'chat_sessions', ['memory_type'], unique=False)
    op.create_index(op.f('ix_chat_sessions_session_token'), 'chat_sessions', ['session_token'], unique=True)
    op.create_index('ix_chat_sessions_user_status', 'chat_sessions', ['user_id', 'status'], unique=False)

    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('is_summarized', sa.Boolean(), nullable=True),
        sa.Column('is_archived', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system', 'tool')", name='check_message_role_valid'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_created_at'), 'chat_messages', ['created_at'], unique=False)
    op.create_index('ix_chat_messages_embedding', 'chat_messages', ['embedding_id'], unique=False)
    op.create_index('ix_chat_messages_importance', 'chat_messages', ['message_metadata'], unique=False, postgresql_using='gin')
    op.create_index('ix_chat_messages_session_created', 'chat_messages', ['session_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)

    # Create chat_summaries table
    op.create_table('chat_summaries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('summary_type', sa.String(length=50), nullable=True),
        sa.Column('start_message_id', sa.UUID(), nullable=True),
        sa.Column('end_message_id', sa.UUID(), nullable=True),
        sa.Column('message_count', sa.Integer(), nullable=False),
        sa.Column('topics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('key_points', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('decisions_made', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("summary_type IN ('conversation', 'topic', 'decision')", name='check_summary_type_valid'),
        sa.ForeignKeyConstraint(['end_message_id'], ['chat_messages.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['start_message_id'], ['chat_messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_summaries_embedding', 'chat_summaries', ['embedding_id'], unique=False)
    op.create_index('ix_chat_summaries_session_created', 'chat_summaries', ['session_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_chat_summaries_session_id'), 'chat_summaries', ['session_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('chat_summaries')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')