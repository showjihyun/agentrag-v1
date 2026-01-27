"""add knowledgebase_versions table

Revision ID: 20260127_add_kb_versions
Revises: 20260127_add_kb_docs
Create Date: 2026-01-27 14:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260127_add_kb_versions'
down_revision = '20260127_add_kb_docs'
branch_labels = None
depends_on = None


def upgrade():
    # Create knowledgebase_versions table
    op.create_table(
        'knowledgebase_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledgebase_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('document_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('version_number > 0', name='check_kb_version_positive'),
        sa.ForeignKeyConstraint(['knowledgebase_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_knowledgebase_versions_knowledgebase_id', 'knowledgebase_versions', ['knowledgebase_id'])
    op.create_index('ix_knowledgebase_versions_created_at', 'knowledgebase_versions', ['created_at'])
    op.create_index('ix_kb_versions_kb_created', 'knowledgebase_versions', ['knowledgebase_id', 'created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_kb_versions_kb_created', table_name='knowledgebase_versions')
    op.drop_index('ix_knowledgebase_versions_created_at', table_name='knowledgebase_versions')
    op.drop_index('ix_knowledgebase_versions_knowledgebase_id', table_name='knowledgebase_versions')
    
    # Drop table
    op.drop_table('knowledgebase_versions')
