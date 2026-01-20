"""add context and mcp to agents

Revision ID: 20260115220929
Revises: 9ce227b568e8
Create Date: 2026-01-15 22:09:29.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260115220929'
down_revision = '9ce227b568e8'  # Changed from 6d5699fcf270
branch_labels = None
depends_on = None


def upgrade():
    """Add context_items and mcp_servers columns to agents table."""
    # Check if columns exist before adding
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('agents')]
    
    # Add context_items column if it doesn't exist
    if 'context_items' not in columns:
        op.add_column('agents', sa.Column('context_items', postgresql.JSONB(), nullable=True))
        op.execute("UPDATE agents SET context_items = '[]'::jsonb WHERE context_items IS NULL")
    
    # Add mcp_servers column if it doesn't exist
    if 'mcp_servers' not in columns:
        op.add_column('agents', sa.Column('mcp_servers', postgresql.JSONB(), nullable=True))
        op.execute("UPDATE agents SET mcp_servers = '[]'::jsonb WHERE mcp_servers IS NULL")


def downgrade():
    """Remove context_items and mcp_servers columns from agents table."""
    op.drop_column('agents', 'mcp_servers')
    op.drop_column('agents', 'context_items')
