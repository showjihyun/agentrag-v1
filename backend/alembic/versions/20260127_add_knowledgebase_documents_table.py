"""add knowledgebase_documents table

Revision ID: 20260127_add_kb_docs
Revises: 20260127_add_variables
Create Date: 2026-01-27 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260127_add_kb_docs'
down_revision = '20260127_add_variables'
branch_labels = None
depends_on = None


def upgrade():
    # Create knowledgebase_documents table
    op.create_table(
        'knowledgebase_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('knowledgebase_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('removed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['knowledgebase_id'], ['knowledge_bases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('knowledgebase_id', 'document_id', name='uq_kb_document')
    )
    
    # Create indexes
    op.create_index('ix_knowledgebase_documents_knowledgebase_id', 'knowledgebase_documents', ['knowledgebase_id'])
    op.create_index('ix_knowledgebase_documents_document_id', 'knowledgebase_documents', ['document_id'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_knowledgebase_documents_document_id', table_name='knowledgebase_documents')
    op.drop_index('ix_knowledgebase_documents_knowledgebase_id', table_name='knowledgebase_documents')
    
    # Drop table
    op.drop_table('knowledgebase_documents')
