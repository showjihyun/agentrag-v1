"""Add event store table

Revision ID: 008_add_event_store
Revises: 007_add_api_keys
Create Date: 2024-12-06

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_event_store'
down_revision = '007_add_api_keys'
branch_labels = None
depends_on = None


def upgrade():
    """Create event_store table."""
    op.create_table(
        'event_store',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aggregate_id', sa.String(), nullable=False),
        sa.Column('aggregate_type', sa.String(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('event_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_event_store_id', 'event_store', ['id'])
    op.create_index('ix_event_store_aggregate_id', 'event_store', ['aggregate_id'])
    op.create_index('ix_event_store_aggregate_type', 'event_store', ['aggregate_type'])
    op.create_index('ix_event_store_event_type', 'event_store', ['event_type'])
    op.create_index('ix_event_store_user_id', 'event_store', ['user_id'])
    op.create_index('ix_event_store_timestamp', 'event_store', ['timestamp'])
    
    # Composite indexes for common queries
    op.create_index('idx_aggregate_version', 'event_store', ['aggregate_id', 'version'])
    op.create_index('idx_aggregate_type_timestamp', 'event_store', ['aggregate_type', 'timestamp'])
    op.create_index('idx_user_timestamp', 'event_store', ['user_id', 'timestamp'])


def downgrade():
    """Drop event_store table."""
    op.drop_index('idx_user_timestamp', table_name='event_store')
    op.drop_index('idx_aggregate_type_timestamp', table_name='event_store')
    op.drop_index('idx_aggregate_version', table_name='event_store')
    op.drop_index('ix_event_store_timestamp', table_name='event_store')
    op.drop_index('ix_event_store_user_id', table_name='event_store')
    op.drop_index('ix_event_store_event_type', table_name='event_store')
    op.drop_index('ix_event_store_aggregate_type', table_name='event_store')
    op.drop_index('ix_event_store_aggregate_id', table_name='event_store')
    op.drop_index('ix_event_store_id', table_name='event_store')
    op.drop_table('event_store')
