"""remove_unused_tables

Revision ID: 264c1fe39bc5
Revises: 762886e12a0a
Create Date: 2025-12-23 23:06:53.722680

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '264c1fe39bc5'
down_revision: Union[str, None] = '762886e12a0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unused database tables that are no longer needed."""
    
    # Use raw SQL to check and drop tables if they exist
    # This avoids transaction issues with Alembic's drop operations
    
    connection = op.get_bind()
    
    # List of tables to remove
    tables_to_remove = [
        'chat_messages',
        'chat_sessions', 
        'file_upload_stats',
        'embedding_stats',
        'hybrid_search_stats', 
        'rag_processing_stats',
        'daily_accuracy_trends',
        'dashboard_widgets',
        'dashboard_layouts'
    ]
    
    for table_name in tables_to_remove:
        try:
            # Check if table exists
            result = connection.execute(sa.text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                );
            """))
            
            table_exists = result.scalar()
            
            if table_exists:
                # Drop table with CASCADE to handle foreign key constraints
                connection.execute(sa.text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
                print(f"Dropped table: {table_name}")
            else:
                print(f"Table {table_name} does not exist, skipping")
                
        except Exception as e:
            print(f"Error dropping table {table_name}: {e}")
            # Continue with other tables
            pass


def downgrade() -> None:
    """Recreate the removed tables if needed (not recommended)."""
    # Note: This is a destructive migration. Downgrade is not fully implemented
    # as these tables were identified as unused and should not be recreated.
    # If you need these tables back, restore from the original migration files:
    # - add_dashboard_chat_tables.py (for dashboard and chat tables)
    # - b667d05f8afb_add_agent_builder_tables_and_models.py (for monitoring tables)
    pass
