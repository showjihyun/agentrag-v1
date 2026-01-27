"""Check for missing tables in the database."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect
from db.database import engine
from db.models.agent_builder import Base
import db.models.agent_builder  # Import to register all models

def check_missing_tables():
    """Check which tables are defined in models but missing from database."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    # Get all tables defined in SQLAlchemy models
    model_tables = set()
    for table_name, table in Base.metadata.tables.items():
        model_tables.add(table_name)
    
    # Find missing tables
    missing_tables = model_tables - existing_tables
    
    print(f"Total tables in models: {len(model_tables)}")
    print(f"Total tables in database: {len(existing_tables)}")
    print(f"Missing tables: {len(missing_tables)}")
    
    if missing_tables:
        print("\nMissing tables:")
        for table in sorted(missing_tables):
            print(f"  - {table}")
        return list(sorted(missing_tables))
    else:
        print("\n✓ All model tables exist in database!")
        return []

if __name__ == "__main__":
    missing = check_missing_tables()
    sys.exit(1 if missing else 0)
