"""Reset Alembic version table to fix migration issues."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.db.database import engine

def reset_alembic_version():
    """Clear alembic_version table and set to initial migration."""
    with engine.connect() as conn:
        # Clear current version
        conn.execute(text("DELETE FROM alembic_version"))
        conn.commit()
        print("✓ Alembic version table cleared")
        
        # Set to initial migration
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('9ce227b568e8')"))
        conn.commit()
        print("✓ Set to initial migration: 9ce227b568e8_initial_schema")

if __name__ == "__main__":
    try:
        reset_alembic_version()
        print("\n✅ Alembic version reset complete!")
        print("Now run: alembic upgrade head")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
