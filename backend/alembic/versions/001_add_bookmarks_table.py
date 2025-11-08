"""Add bookmarks table

Revision ID: 001_bookmarks
Revises: 
Create Date: 2025-10-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_bookmarks'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bookmarks table
    op.create_table(
        'bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('item_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('is_favorite', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Create indexes
    op.create_index('idx_bookmarks_user_id', 'bookmarks', ['user_id'])
    op.create_index('idx_bookmarks_type', 'bookmarks', ['type'])
    op.create_index('idx_bookmarks_item_id', 'bookmarks', ['item_id'])
    op.create_index('idx_bookmarks_user_type', 'bookmarks', ['user_id', 'type'])
    op.create_index('idx_bookmarks_is_favorite', 'bookmarks', ['is_favorite'])
    op.create_index('idx_bookmarks_created_at', 'bookmarks', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_bookmarks_created_at', table_name='bookmarks')
    op.drop_index('idx_bookmarks_is_favorite', table_name='bookmarks')
    op.drop_index('idx_bookmarks_user_type', table_name='bookmarks')
    op.drop_index('idx_bookmarks_item_id', table_name='bookmarks')
    op.drop_index('idx_bookmarks_type', table_name='bookmarks')
    op.drop_index('idx_bookmarks_user_id', table_name='bookmarks')
    
    # Drop table
    op.drop_table('bookmarks')
