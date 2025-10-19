"""Add query_logs table for monitoring

Revision ID: add_query_logs_001
Revises: 3cf740d85320
Create Date: 2025-01-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_query_logs_001'
down_revision = '3cf740d85320'
branch_labels = None
depends_on = None


def upgrade():
    # Create query_logs table
    op.create_table(
        'query_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_mode', sa.String(length=50), nullable=True),
        sa.Column('response_time_ms', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_query_logs_created_at', 'query_logs', ['created_at'])
    op.create_index('ix_query_logs_query_mode', 'query_logs', ['query_mode'])
    op.create_index('ix_query_logs_confidence_score', 'query_logs', ['confidence_score'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_query_logs_confidence_score', table_name='query_logs')
    op.drop_index('ix_query_logs_query_mode', table_name='query_logs')
    op.drop_index('ix_query_logs_created_at', table_name='query_logs')
    
    # Drop table
    op.drop_table('query_logs')
