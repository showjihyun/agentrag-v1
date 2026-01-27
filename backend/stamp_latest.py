"""Stamp database with latest migration without running migrations."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.db.database import engine

def stamp_latest():
    """Stamp database with latest migration revision."""
    with engine.connect() as conn:
        # Clear current version
        conn.execute(text("DELETE FROM alembic_version"))
        conn.commit()
        print("✓ Alembic version table cleared")
        
        # Set to latest migration (rename knowledgebases)
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('20260120_rename_kb')"))
        conn.commit()
        print("✓ Set to latest migration: 20260120_rename_kb")

if __name__ == "__main__":
    try:
        stamp_latest()
        print("\n✅ Database stamped with latest migration!")
        print("Now you can run the rename migration: alembic upgrade head")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
