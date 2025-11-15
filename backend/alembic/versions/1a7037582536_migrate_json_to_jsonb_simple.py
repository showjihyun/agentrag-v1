"""migrate_json_to_jsonb_simple

Revision ID: 1a7037582536
Revises: 7a0086db5e15
Create Date: 2025-11-15 15:22:49.617284

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a7037582536'
down_revision: Union[str, None] = '7a0086db5e15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate JSON columns to JSONB and add GIN indexes for performance"""
    
    # Note: This migration converts JSON to JSONB for PostgreSQL performance
    # JSONB provides better indexing and query performance
    
    # High priority tables with GIN indexes
    tables_with_gin = [
        ('agents', 'configuration'),
        ('workflows', 'graph_definition'),
        ('agent_blocks', 'config'),
    ]
    
    for table, column in tables_with_gin:
        # Convert to JSONB
        op.execute(f"""
            ALTER TABLE {table} 
            ALTER COLUMN {column} TYPE JSONB USING {column}::JSONB
        """)
        # Add GIN index
        op.execute(f"""
            CREATE INDEX IF NOT EXISTS ix_{table}_{column}_gin 
            ON {table} USING GIN ({column})
        """)
    
    # Add specific indexes for frequently searched fields
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_agents_llm_provider 
        ON agents ((configuration->>'llm_provider'))
    """)


def downgrade() -> None:
    """Revert JSONB back to JSON"""
    
    # Remove GIN indexes
    op.drop_index('ix_agents_configuration_gin', table_name='agents')
    op.drop_index('ix_workflows_graph_definition_gin', table_name='workflows')
    op.drop_index('ix_agent_blocks_config_gin', table_name='agent_blocks')
    op.drop_index('ix_agents_llm_provider', table_name='agents')
    
    # Revert to JSON
    op.execute("ALTER TABLE agents ALTER COLUMN configuration TYPE JSON")
    op.execute("ALTER TABLE workflows ALTER COLUMN graph_definition TYPE JSON")
    op.execute("ALTER TABLE agent_blocks ALTER COLUMN config TYPE JSON")
