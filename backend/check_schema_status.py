#!/usr/bin/env python
"""Check current database schema status against latest migrations."""

import sys
import os
from pathlib import Path
import dotenv

# Load environment variables
dotenv.load_dotenv('.env')

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/agentrag')

def check_schema_status():
    """Check if DB schema is up to date with latest migrations."""
    
    print("=" * 60)
    print("DATABASE SCHEMA STATUS CHECK")
    print("=" * 60)
    
    # Get latest migration revision
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), 'alembic.ini'))
    alembic_cfg.set_main_option('script_location', os.path.join(os.path.dirname(__file__), 'alembic'))
    script = ScriptDirectory.from_config(alembic_cfg)
    latest_revision = script.get_current_head()
    
    print(f"\n✓ Latest Migration Revision: {latest_revision}")
    
    # Connect to database
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            # Get current DB revision
            result = connection.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"))
            current_revision = result.scalar()
            
            print(f"✓ Current DB Revision: {current_revision}")
            
            if current_revision == latest_revision:
                print("\n✅ DATABASE SCHEMA IS UP TO DATE")
            else:
                print(f"\n⚠️  DATABASE SCHEMA IS OUT OF DATE")
                print(f"   Need to run migrations from {current_revision} to {latest_revision}")
            
            # Check agents table structure
            print("\n" + "=" * 60)
            print("AGENTS TABLE STRUCTURE")
            print("=" * 60)
            
            inspector = inspect(engine)
            columns = inspector.get_columns('agents')
            
            required_columns = {
                'id', 'user_id', 'name', 'agent_type', 'llm_provider', 
                'llm_model', 'configuration', 'context_items', 'mcp_servers',
                'created_at', 'updated_at', 'deleted_at'
            }
            
            existing_columns = {col['name'] for col in columns}
            
            print(f"\nTotal columns: {len(columns)}")
            print("\nColumn Details:")
            for col in columns:
                col_type = str(col['type'])
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  • {col['name']:<20} {col_type:<20} {nullable}")
            
            missing = required_columns - existing_columns
            if missing:
                print(f"\n⚠️  Missing columns: {missing}")
            else:
                print(f"\n✅ All required columns present")
            
            # Check for context_items and mcp_servers
            print("\n" + "=" * 60)
            print("MCP & CONTEXT SUPPORT")
            print("=" * 60)
            
            has_context = 'context_items' in existing_columns
            has_mcp = 'mcp_servers' in existing_columns
            
            print(f"  • context_items column: {'✅ Present' if has_context else '❌ Missing'}")
            print(f"  • mcp_servers column: {'✅ Present' if has_mcp else '❌ Missing'}")
            
            if has_context and has_mcp:
                print("\n✅ MCP and Context support is enabled")
            else:
                print("\n⚠️  MCP and Context support needs to be added")
            
    except Exception as e:
        print(f"\n❌ Error connecting to database: {e}")
        print("Make sure the database is running and DATABASE_URL is correct")
        return False
    
    return True

if __name__ == "__main__":
    check_schema_status()
