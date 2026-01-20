"""Add kb_type column to knowledge_bases table

Revision ID: 20260120_add_kb_type
Revises: 20260120_create_missing_tables
Create Date: 2026-01-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260120_add_kb_type'
down_revision: Union[str, None] = '20260120_plugin_marketplace'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add kb_type column and related fields to knowledge_bases table."""
    
    # Check if column exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('knowledge_bases')]
    
    # Add kb_type column if it doesn't exist
    if 'kb_type' not in columns:
        op.add_column('knowledge_bases', 
            sa.Column('kb_type', sa.String(length=50), nullable=False, server_default='vector')
        )
        op.create_index(op.f('ix_knowledge_bases_kb_type'), 'knowledge_bases', ['kb_type'], unique=False)
        
        # Add check constraint for kb_type
        op.create_check_constraint(
            'check_kb_type_valid',
            'knowledge_bases',
            "kb_type IN ('vector', 'graph', 'hybrid')"
        )
    
    # Add kg_enabled column if it doesn't exist
    if 'kg_enabled' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('kg_enabled', sa.Boolean(), nullable=True, server_default='false')
        )
        op.create_index(op.f('ix_knowledge_bases_kg_enabled'), 'knowledge_bases', ['kg_enabled'], unique=False)
    
    # Add kg_auto_extraction column if it doesn't exist
    if 'kg_auto_extraction' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('kg_auto_extraction', sa.Boolean(), nullable=True, server_default='true')
        )
    
    # Add kg_entity_extraction_model column if it doesn't exist
    if 'kg_entity_extraction_model' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('kg_entity_extraction_model', sa.String(length=100), nullable=True, server_default='spacy_en_core_web_sm')
        )
    
    # Add kg_relation_extraction_model column if it doesn't exist
    if 'kg_relation_extraction_model' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('kg_relation_extraction_model', sa.String(length=100), nullable=True, server_default='rebel_large')
        )
    
    # Add search_strategy column if it doesn't exist
    if 'search_strategy' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('search_strategy', sa.String(length=50), nullable=True, server_default='vector')
        )
        
        # Add check constraint for search_strategy
        op.create_check_constraint(
            'check_search_strategy_valid',
            'knowledge_bases',
            "search_strategy IN ('vector', 'graph', 'hybrid')"
        )
    
    # Add hybrid_weight_vector column if it doesn't exist
    if 'hybrid_weight_vector' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('hybrid_weight_vector', sa.Float(), nullable=True, server_default='0.7')
        )
        
        # Add check constraint for hybrid_weight_vector
        op.create_check_constraint(
            'check_hybrid_weight_vector_range',
            'knowledge_bases',
            "hybrid_weight_vector >= 0.0 AND hybrid_weight_vector <= 1.0"
        )
    
    # Add hybrid_weight_graph column if it doesn't exist
    if 'hybrid_weight_graph' not in columns:
        op.add_column('knowledge_bases',
            sa.Column('hybrid_weight_graph', sa.Float(), nullable=True, server_default='0.3')
        )
        
        # Add check constraint for hybrid_weight_graph
        op.create_check_constraint(
            'check_hybrid_weight_graph_range',
            'knowledge_bases',
            "hybrid_weight_graph >= 0.0 AND hybrid_weight_graph <= 1.0"
        )


def downgrade() -> None:
    """Remove kb_type column and related fields from knowledge_bases table."""
    
    # Drop constraints first
    op.drop_constraint('check_hybrid_weight_graph_range', 'knowledge_bases', type_='check')
    op.drop_constraint('check_hybrid_weight_vector_range', 'knowledge_bases', type_='check')
    op.drop_constraint('check_search_strategy_valid', 'knowledge_bases', type_='check')
    op.drop_constraint('check_kb_type_valid', 'knowledge_bases', type_='check')
    
    # Drop indexes
    op.drop_index(op.f('ix_knowledge_bases_kg_enabled'), table_name='knowledge_bases')
    op.drop_index(op.f('ix_knowledge_bases_kb_type'), table_name='knowledge_bases')
    
    # Drop columns
    op.drop_column('knowledge_bases', 'hybrid_weight_graph')
    op.drop_column('knowledge_bases', 'hybrid_weight_vector')
    op.drop_column('knowledge_bases', 'search_strategy')
    op.drop_column('knowledge_bases', 'kg_relation_extraction_model')
    op.drop_column('knowledge_bases', 'kg_entity_extraction_model')
    op.drop_column('knowledge_bases', 'kg_auto_extraction')
    op.drop_column('knowledge_bases', 'kg_enabled')
    op.drop_column('knowledge_bases', 'kb_type')
