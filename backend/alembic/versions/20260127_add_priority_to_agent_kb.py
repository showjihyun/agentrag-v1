"""add priority column to agent_knowledgebases

Revision ID: 20260127_add_priority
Revises: 20260127_rename_kb_col
Create Date: 2026-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260127_add_priority'
down_revision = '20260127_rename_kb_col'
branch_labels = None
depends_on = None


def upgrade():
    """Add priority column to agent_knowledgebases table."""
    
    # Add priority column if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='agent_knowledgebases' AND column_name='priority'
            ) THEN
                ALTER TABLE agent_knowledgebases 
                ADD COLUMN priority INTEGER DEFAULT 0;
            END IF;
        END $$;
    """)
    
    # Create index on agent_id and priority if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes 
                WHERE tablename='agent_knowledgebases' 
                AND indexname='ix_agent_kb_agent_priority'
            ) THEN
                CREATE INDEX ix_agent_kb_agent_priority 
                ON agent_knowledgebases(agent_id, priority);
            END IF;
        END $$;
    """)


def downgrade():
    """Remove priority column from agent_knowledgebases table."""
    
    # Drop index
    op.execute("""
        DROP INDEX IF EXISTS ix_agent_kb_agent_priority;
    """)
    
    # Drop column
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='agent_knowledgebases' AND column_name='priority'
            ) THEN
                ALTER TABLE agent_knowledgebases 
                DROP COLUMN priority;
            END IF;
        END $$;
    """)
