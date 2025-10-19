"""
Create monitoring statistics tables in PostgreSQL.

Run this script to create the necessary tables for monitoring statistics.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import text
from backend.db.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_monitoring_tables():
    """Create monitoring statistics tables"""
    
    sql_file = os.path.join(
        os.path.dirname(__file__),
        '../db/migrations/create_monitoring_tables.sql'
    )
    
    try:
        # Read SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute SQL
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            for statement in statements:
                if statement:
                    logger.info(f"Executing: {statement[:100]}...")
                    conn.execute(text(statement))
                    conn.commit()
        
        logger.info("✅ Successfully created monitoring tables!")
        
        # Verify tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%_stats' OR table_name LIKE '%_trends'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            
            logger.info(f"\n📊 Created tables:")
            for table in tables:
                logger.info(f"   - {table}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create monitoring tables: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = create_monitoring_tables()
    sys.exit(0 if success else 1)
