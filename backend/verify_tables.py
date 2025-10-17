#!/usr/bin/env python3
"""Quick verification of all 8 tables in PostgreSQL"""

from sqlalchemy import create_engine, text
from config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Get all tables
    result = conn.execute(
        text(
            """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """
        )
    )

    tables = [row[0] for row in result]

    print("=" * 70)
    print("POSTGRESQL TABLES VERIFICATION")
    print("=" * 70)
    print(f"\nTotal tables found: {len(tables)}\n")

    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")

    # Expected tables
    expected = {
        "users",
        "sessions",
        "messages",
        "message_sources",
        "documents",
        "batch_uploads",
        "feedback",
        "usage_logs",
    }

    actual = set(tables) - {"alembic_version"}

    print(f"\n{'=' * 70}")
    if expected == actual:
        print("✓ SUCCESS: All 8 required tables are present!")
    else:
        print("✗ ERROR: Table mismatch")
        print(f"Missing: {expected - actual}")
        print(f"Extra: {actual - expected}")
    print("=" * 70)
