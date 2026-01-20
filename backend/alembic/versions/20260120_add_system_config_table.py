"""Add system_config table

Revision ID: 20260120_add_system_config
Revises: 20260120_add_flow_tables
Create Date: 2026-01-20 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260120_add_system_config'
down_revision: Union[str, None] = '20260120_add_flow_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create system_config table."""
    
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'system_config' not in existing_tables:
        # Create system_config table
        op.create_table('system_config',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('config_key', sa.String(length=255), nullable=False),
            sa.Column('config_value', sa.Text(), nullable=False),
            sa.Column('config_type', sa.String(length=50), nullable=False, server_default='string'),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.current_timestamp()),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.current_timestamp()),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('config_key', name='uq_system_config_key'),
            sa.Index('idx_system_config_key', 'config_key'),
            comment='System-wide configuration storage'
        )
        
        # Create trigger function for updated_at
        op.execute("""
            CREATE OR REPLACE FUNCTION update_system_config_updated_at()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Create trigger
        op.execute("""
            CREATE TRIGGER trigger_update_system_config_updated_at
                BEFORE UPDATE ON system_config
                FOR EACH ROW
                EXECUTE FUNCTION update_system_config_updated_at();
        """)
        
        # Insert default embedding model configuration
        op.execute("""
            INSERT INTO system_config (config_key, config_value, config_type, description)
            VALUES 
                ('embedding_model_name', 'jhgan/ko-sroberta-multitask', 'string', 'Current embedding model name'),
                ('embedding_dimension', '768', 'integer', 'Embedding vector dimension')
            ON CONFLICT (config_key) DO NOTHING;
        """)


def downgrade() -> None:
    """Drop system_config table."""
    
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS trigger_update_system_config_updated_at ON system_config;")
    
    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS update_system_config_updated_at();")
    
    # Drop index
    op.drop_index('idx_system_config_key', table_name='system_config')
    
    # Drop table
    op.drop_table('system_config')
