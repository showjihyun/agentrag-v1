"""Check if knowledgebases table exists"""
from db.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    # Check for knowledge-related tables
    result = db.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE '%knowledge%'"
    ))
    tables = [r[0] for r in result]
    print("Knowledge-related tables:", tables)
    
    # Check all tables
    result = db.execute(text(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    ))
    all_tables = [r[0] for r in result]
    print(f"\nTotal tables: {len(all_tables)}")
    print("All tables:", all_tables[:20], "..." if len(all_tables) > 20 else "")
    
finally:
    db.close()
