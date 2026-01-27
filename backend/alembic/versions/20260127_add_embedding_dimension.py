"""add embedding_dimension to knowledge_bases

Revision ID: 20260127_add_emb_dim
Revises: 20260127_add_priority
Create Date: 2026-01-27 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260127_add_emb_dim'
down_revision = '20260127_add_priority'
branch_labels = None
depends_on = None


def upgrade():
    """Add embedding_dimension column to knowledge_bases table."""
    
    # Add embedding_dimension column if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='knowledge_bases' AND column_name='embedding_dimension'
            ) THEN
                ALTER TABLE knowledge_bases 
                ADD COLUMN embedding_dimension INTEGER;
                
                -- Set default value based on common models
                -- jhgan/ko-sroberta-multitask = 768
                -- sentence-transformers/all-MiniLM-L6-v2 = 384
                UPDATE knowledge_bases 
                SET embedding_dimension = CASE 
                    WHEN embedding_model LIKE '%MiniLM%' THEN 384
                    WHEN embedding_model LIKE '%distiluse%' THEN 512
                    WHEN embedding_model LIKE '%text-embedding-3-small%' THEN 1536
                    WHEN embedding_model LIKE '%text-embedding-3-large%' THEN 3072
                    WHEN embedding_model LIKE '%text-embedding-ada%' THEN 1536
                    ELSE 768  -- Default for most Korean and multilingual models
                END
                WHERE embedding_dimension IS NULL;
            END IF;
        END $$;
    """)
    
    # Add index on embedding_dimension for query optimization
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename='knowledge_bases' 
                AND indexname='ix_knowledge_bases_embedding_dimension'
            ) THEN
                CREATE INDEX ix_knowledge_bases_embedding_dimension 
                ON knowledge_bases(embedding_dimension);
            END IF;
        END $$;
    """)


def downgrade():
    """Remove embedding_dimension column from knowledge_bases table."""
    
    # Drop index
    op.execute("""
        DROP INDEX IF EXISTS ix_knowledge_bases_embedding_dimension;
    """)
    
    # Drop column
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='knowledge_bases' AND column_name='embedding_dimension'
            ) THEN
                ALTER TABLE knowledge_bases 
                DROP COLUMN embedding_dimension;
            END IF;
        END $$;
    """)
