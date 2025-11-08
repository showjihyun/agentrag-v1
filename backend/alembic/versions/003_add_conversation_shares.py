"""Add conversation shares table

Revision ID: 003_conversation_shares
Revises: 002_notifications
Create Date: 2025-10-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_conversation_shares'
down_revision = '002_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create share_role enum
    share_role = postgresql.ENUM('viewer', 'editor', 'admin', name='sharerole')
    share_role.create(op.get_bind())
    
    # Create conversation_shares table
    op.create_table(
        'conversation_shares',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', share_role, nullable=False),
        sa.Column('shared_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_conversation_shares_conversation_id', 'conversation_shares', ['conversation_id'])
    op.create_index('idx_conversation_shares_user_id', 'conversation_shares', ['user_id'])
    op.create_index('idx_conversation_shares_conversation_user', 'conversation_shares', ['conversation_id', 'user_id'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_conversation_shares_conversation_user', table_name='conversation_shares')
    op.drop_index('idx_conversation_shares_user_id', table_name='conversation_shares')
    op.drop_index('idx_conversation_shares_conversation_id', table_name='conversation_shares')
    
    # Drop table
    op.drop_table('conversation_shares')
    
    # Drop enum
    share_role = postgresql.ENUM('viewer', 'editor', 'admin', name='sharerole')
    share_role.drop(op.get_bind())
