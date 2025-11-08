"""
Run database migration for system_config table.
"""

import asyncio
import asyncpg
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    """Run the system_config table migration."""
    try:
        # Read migration SQL
        migration_file = Path(__file__).parent.parent / "migrations" / "add_system_config_table.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Connect to database
        # Update these with your actual database credentials
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='agenticrag'
        )
        
        try:
            # Execute migration
            logger.info("Running migration...")
            await conn.execute(migration_sql)
            logger.info("Migration completed successfully!")
            
            # Verify table was created
            result = await conn.fetchval(
                "SELECT COUNT(*) FROM system_config"
            )
            logger.info(f"system_config table has {result} rows")
            
            return True
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(run_migration())
    exit(0 if success else 1)
