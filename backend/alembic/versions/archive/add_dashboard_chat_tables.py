"""Add dashboard and chat history tables

Revision ID: add_dashboard_chat
Revises: 
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_dashboard_chat'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Dashboard layouts table
    op.create_table(
        'dashboard_layouts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(100), default='Default Dashboard'),
        sa.Column('theme', sa.String(50), default='default'),
        sa.Column('columns', sa.Integer(), default=12),
        sa.Column('row_height', sa.Integer(), default=100),
        sa.Column('is_default', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_dashboard_layouts_user_id', 'dashboard_layouts', ['user_id'])
    
    # Dashboard widgets table
    op.create_table(
        'dashboard_widgets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('layout_id', sa.String(36), sa.ForeignKey('dashboard_layouts.id'), nullable=False),
        sa.Column('widget_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(100), nullable=False),
        sa.Column('x', sa.Integer(), default=0),
        sa.Column('y', sa.Integer(), default=0),
        sa.Column('width', sa.Integer(), default=6),
        sa.Column('height', sa.Integer(), default=2),
        sa.Column('config', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_dashboard_widgets_layout_id', 'dashboard_widgets', ['layout_id'])

    # Chat sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('agent_id', sa.String(36), nullable=True),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('ix_chat_sessions_agent_id', 'chat_sessions', ['agent_id'])
    
    # Chat messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('chat_sessions.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), default=dict),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_created_at', 'chat_messages', ['created_at'])


def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('dashboard_widgets')
    op.drop_table('dashboard_layouts')
