"""Quick test to verify variables and secrets tables exist."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import inspect, text
from db.database import engine

def test_tables():
    """Test that variables and secrets tables exist."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("Checking for variables and secrets tables...")
    print(f"Total tables in database: {len(tables)}")
    
    # Check variables table
    if 'variables' in tables:
        print("\n✓ 'variables' table exists")
        columns = inspector.get_columns('variables')
        print(f"  Columns ({len(columns)}):")
        for col in columns:
            print(f"    - {col['name']}: {col['type']}")
        
        # Check indexes
        indexes = inspector.get_indexes('variables')
        print(f"  Indexes ({len(indexes)}):")
        for idx in indexes:
            print(f"    - {idx['name']}: {idx['column_names']}")
    else:
        print("\n✗ 'variables' table NOT FOUND")
        return False
    
    # Check secrets table
    if 'secrets' in tables:
        print("\n✓ 'secrets' table exists")
        columns = inspector.get_columns('secrets')
        print(f"  Columns ({len(columns)}):")
        for col in columns:
            print(f"    - {col['name']}: {col['type']}")
    else:
        print("\n✗ 'secrets' table NOT FOUND")
        return False
    
    # Test a simple query
    print("\n\nTesting query on variables table...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM variables"))
            count = result.scalar()
            print(f"✓ Query successful! Current variable count: {count}")
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False
    
    print("\n✓ All checks passed!")
    return True

if __name__ == "__main__":
    success = test_tables()
    sys.exit(0 if success else 1)
