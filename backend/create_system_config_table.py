"""Create system_config table manually"""
import asyncio
import asyncpg
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import settings

async def create_system_config_table():
    """Create system_config table if it doesn't exist"""
    conn = await asyncpg.connect(settings.DATABASE_URL)
    
    try:
        # Read the SQL file
        with open('migrations/add_system_config_table.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Execute the SQL
        await conn.execute(sql)
        print("✓ system_config table created successfully")
        
    except Exception as e:
        print(f"Error creating system_config table: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_system_config_table())
