"""rename knowledge_base_id to knowledgebase_id in agent_knowledgebases

Revision ID: 20260127_rename_kb_col
Revises: 20260127_add_kg_tables
Create Date: 2026-01-27 15:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260127_rename_kb_col'
down_revision = '20260127_add_kg_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Check if the old column exists and rename it
    op.execute("""
        DO $$
        BEGIN
            -- Check if knowledge_base_id exists and knowledgebase_id doesn't
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='agent_knowledgebases' AND column_name='knowledge_base_id'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='agent_knowledgebases' AND column_name='knowledgebase_id'
            ) THEN
                -- Rename the column
                ALTER TABLE agent_knowledgebases 
                RENAME COLUMN knowledge_base_id TO knowledgebase_id;
                
                -- Update the unique constraint name if it exists
                IF EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'uq_agent_kb' 
                    AND conrelid = 'agent_knowledgebases'::regclass
                ) THEN
                    ALTER TABLE agent_knowledgebases 
                    DROP CONSTRAINT uq_agent_kb;
                    
                    ALTER TABLE agent_knowledgebases 
                    ADD CONSTRAINT uq_agent_kb UNIQUE (agent_id, knowledgebase_id);
                END IF;
            END IF;
        END $$;
    """)
    
    # Ensure the foreign key constraint uses the correct column name
    op.execute("""
        DO $$
        BEGIN
            -- Drop old foreign key if it exists
            IF EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname LIKE '%knowledge_base_id%' 
                AND conrelid = 'agent_knowledgebases'::regclass
            ) THEN
                ALTER TABLE agent_knowledgebases 
                DROP CONSTRAINT IF EXISTS agent_knowledgebases_knowledge_base_id_fkey;
            END IF;
            
            -- Add new foreign key if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'agent_knowledgebases_knowledgebase_id_fkey'
                AND conrelid = 'agent_knowledgebases'::regclass
            ) THEN
                ALTER TABLE agent_knowledgebases 
                ADD CONSTRAINT agent_knowledgebases_knowledgebase_id_fkey 
                FOREIGN KEY (knowledgebase_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE;
            END IF;
        END $$;
    """)
    
    # Update indexes
    op.execute("""
        DO $$
        BEGIN
            -- Drop old index if exists
            DROP INDEX IF EXISTS idx_agent_kb_kb_id;
            
            -- Create new index if not exists
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename='agent_knowledgebases' 
                AND indexname='ix_agent_knowledgebases_knowledgebase_id'
            ) THEN
                CREATE INDEX ix_agent_knowledgebases_knowledgebase_id 
                ON agent_knowledgebases(knowledgebase_id);
            END IF;
        END $$;
    """)


def downgrade():
    # Rename back to knowledge_base_id
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='agent_knowledgebases' AND column_name='knowledgebase_id'
            ) THEN
                ALTER TABLE agent_knowledgebases 
                RENAME COLUMN knowledgebase_id TO knowledge_base_id;
            END IF;
        END $$;
    """)
