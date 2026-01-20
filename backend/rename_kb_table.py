"""Rename knowledgebases table to knowledge_bases."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.db.database import engine

def rename_table():
    """Rename knowledgebases table to knowledge_bases."""
    with engine.connect() as conn:
        try:
            # Check if knowledgebases table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'knowledgebases'
                )
            """))
            exists = result.scalar()
            
            if not exists:
                print("✓ Table 'knowledgebases' does not exist (might already be renamed)")
                return
            
            # Rename the table
            conn.execute(text("ALTER TABLE knowledgebases RENAME TO knowledge_bases"))
            conn.commit()
            print("✓ Renamed table: knowledgebases → knowledge_bases")
            
            # Update alembic version
            conn.execute(text("DELETE FROM alembic_version"))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('20260120_rename_kb')"))
            conn.commit()
            print("✓ Updated alembic version to: 20260120_rename_kb")
            
        except Exception as e:
            conn.rollback()
            raise e

if __name__ == "__main__":
    try:
        rename_table()
        print("\n✅ Table rename complete!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
