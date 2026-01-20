"""Add missing columns to knowledge_bases table

Revision ID: 20260120_add_missing_kb_cols
Revises: 20260120_add_kb_type
Create Date: 2026-01-20 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260120_add_missing_kb_cols'
down_revision: Union[str, None] = '20260120_add_kb_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add missing columns to knowledge_bases table."""
    
    # Check if columns exist before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('knowledge_bases')]
    
    # Add milvus_collection_name column if it doesn't exist
    if 'milvus_collection_name' not in columns:
        op.add_column('knowledge_bases', 
            sa.Column('milvus_collection_name', sa.String(length=255), nullable=True)
        )
        op.create_index(op.f('ix_knowledge_bases_milvus_collection_name'), 
                       'knowledge_bases', ['milvus_collection_name'], unique=True)
    
    # Add embedding_model column if it doesn't exist
    if 'embedding_model' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('embedding_model', sa.String(length=100), nullable=True)
        )
    
    # Add chunk_size column if it doesn't exist
    if 'chunk_size' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('chunk_size', sa.Integer(), nullable=True, server_default='500')
        )
        
        # Add check constraint for chunk_size
        op.create_check_constraint(
            'check_chunk_size_positive',
            'knowledge_bases',
            "chunk_size > 0"
        )
    
    # Add chunk_overlap column if it doesn't exist
    if 'chunk_overlap' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('chunk_overlap', sa.Integer(), nullable=True, server_default='50')
        )
        
        # Add check constraint for chunk_overlap
        op.create_check_constraint(
            'check_chunk_overlap_positive',
            'knowledge_bases',
            "chunk_overlap >= 0"
        )
    
    # Add constraint to ensure vector configuration is present for vector/hybrid types
    # This constraint is defined in the model but may not exist in the database
    try:
        op.create_check_constraint(
            'check_vector_config_required',
            'knowledge_bases',
            "(kb_type = 'graph') OR (milvus_collection_name IS NOT NULL AND embedding_model IS NOT NULL)"
        )
    except Exception:
        # Constraint may already exist
        pass


def downgrade() -> None:
    """Remove added columns from knowledge_bases table."""
    
    # Drop constraints first
    try:
        op.drop_constraint('check_vector_config_required', 'knowledge_bases', type_='check')
    except Exception:
        pass
    
    op.drop_constraint('check_chunk_overlap_positive', 'knowledge_bases', type_='check')
    op.drop_constraint('check_chunk_size_positive', 'knowledge_bases', type_='check')
    
    # Drop index
    op.drop_index(op.f('ix_knowledge_bases_milvus_collection_name'), table_name='knowledge_bases')
    
    # Drop columns
    op.drop_column('knowledge_bases', 'chunk_overlap')
    op.drop_column('knowledge_bases', 'chunk_size')
    op.drop_column('knowledge_bases', 'embedding_model')
    op.drop_column('knowledge_bases', 'milvus_collection_name')
