#!/usr/bin/env python3
"""Final comprehensive table verification"""

from sqlalchemy import create_engine, inspect, text
from config import settings


def main():
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    print("\n" + "=" * 70)
    print("FINAL TABLE VERIFICATION - Task Complete")
    print("=" * 70 + "\n")

    # Get all tables
    tables = inspector.get_table_names()
    required_tables = [
        "users",
        "sessions",
        "messages",
        "message_sources",
        "documents",
        "batch_uploads",
        "feedback",
        "usage_logs",
    ]

    print(f"Total tables in database: {len(tables)}")
    print(f"Required tables: {len(required_tables)}\n")

    # Check each required table
    all_present = True
    for table in required_tables:
        if table in tables:
            columns = inspector.get_columns(table)
            indexes = inspector.get_indexes(table)
            fks = inspector.get_foreign_keys(table)

            print(
                f"✅ {table:20} | Columns: {len(columns):2} | Indexes: {len(indexes):2} | FKs: {len(fks):2}"
            )
        else:
            print(f"❌ {table:20} | MISSING")
            all_present = False

    # Check alembic version
    print(f"\n{'='*70}")
    if "alembic_version" in tables:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            if version:
                print(f"Migration Version: {version[0]}")

    print(f"{'='*70}\n")

    if all_present:
        print("✅ SUCCESS: All 8 required tables are present and verified!")
        print("\n🎉 Database is ready for Phase 5 development!")
        print("\nNext: Task 5.2.1 - UserRepository + Auth Dependencies")
    else:
        print("❌ ERROR: Some tables are missing!")
        return False

    print(f"\n{'='*70}\n")
    return True


if __name__ == "__main__":
    main()
