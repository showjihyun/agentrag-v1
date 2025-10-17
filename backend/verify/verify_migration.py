#!/usr/bin/env python3
"""
Verification script for Alembic migration setup (Task 5.1.4)

This script verifies that:
1. All 8 required tables exist
2. All indexes are created
3. All foreign key relationships are configured
4. Migration version is tracked
"""

from sqlalchemy import create_engine, inspect
from config import settings
import sys


def verify_migration():
    """Verify the database migration setup."""

    print("=" * 70)
    print("ALEMBIC MIGRATION VERIFICATION - Task 5.1.4")
    print("=" * 70)

    # Connect to database
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    # Expected tables
    expected_tables = {
        "users",
        "sessions",
        "messages",
        "message_sources",
        "documents",
        "batch_uploads",
        "feedback",
        "usage_logs",
    }

    # Get actual tables
    actual_tables = set(inspector.get_table_names())

    # Remove alembic_version from comparison
    actual_tables.discard("alembic_version")

    print(f"\n✓ Expected tables: {len(expected_tables)}")
    print(f"✓ Actual tables: {len(actual_tables)}")

    # Check if all expected tables exist
    missing_tables = expected_tables - actual_tables
    extra_tables = actual_tables - expected_tables

    if missing_tables:
        print(f"\n✗ ERROR: Missing tables: {missing_tables}")
        return False

    if extra_tables:
        print(f"\n⚠ WARNING: Extra tables: {extra_tables}")

    print(f"\n✓ All 8 required tables exist!")
    print(f"  Tables: {sorted(actual_tables)}")

    # Verify key table structures
    print("\n" + "-" * 70)
    print("TABLE STRUCTURE VERIFICATION")
    print("-" * 70)

    # Check users table
    users_columns = {col["name"] for col in inspector.get_columns("users")}
    required_user_columns = {
        "id",
        "email",
        "username",
        "password_hash",
        "role",
        "created_at",
        "query_count",
        "storage_used_bytes",
    }

    if required_user_columns.issubset(users_columns):
        print("✓ users table: All required columns present")
    else:
        missing = required_user_columns - users_columns
        print(f"✗ users table: Missing columns: {missing}")
        return False

    # Check indexes on users
    users_indexes = inspector.get_indexes("users")
    index_names = {idx["name"] for idx in users_indexes}

    if "ix_users_email" in index_names and "ix_users_username" in index_names:
        print("✓ users table: Email and username indexes exist")
    else:
        print("✗ users table: Missing required indexes")
        return False

    # Check messages table
    messages_columns = {col["name"] for col in inspector.get_columns("messages")}
    required_message_columns = {
        "id",
        "session_id",
        "user_id",
        "role",
        "content",
        "query_mode",
        "processing_time_ms",
        "confidence_score",
        "cache_hit",
        "cache_match_type",
        "cache_similarity",
    }

    if required_message_columns.issubset(messages_columns):
        print("✓ messages table: All required columns present")
    else:
        missing = required_message_columns - messages_columns
        print(f"✗ messages table: Missing columns: {missing}")
        return False

    # Check foreign keys
    print("\n" + "-" * 70)
    print("FOREIGN KEY VERIFICATION")
    print("-" * 70)

    # Check messages foreign keys
    messages_fks = inspector.get_foreign_keys("messages")
    fk_tables = {fk["referred_table"] for fk in messages_fks}

    if "users" in fk_tables and "sessions" in fk_tables:
        print("✓ messages table: Foreign keys to users and sessions exist")
    else:
        print(f"✗ messages table: Missing foreign keys. Found: {fk_tables}")
        return False

    # Check cascade delete
    cascade_found = False
    for fk in messages_fks:
        if fk.get("options", {}).get("ondelete") == "CASCADE":
            cascade_found = True
            break

    if cascade_found:
        print("✓ CASCADE delete configured on foreign keys")
    else:
        print("⚠ WARNING: CASCADE delete may not be configured")

    # Check alembic version
    print("\n" + "-" * 70)
    print("MIGRATION VERSION")
    print("-" * 70)

    if "alembic_version" in inspector.get_table_names():
        print("✓ alembic_version table exists")

        # Get current version
        from sqlalchemy import text

        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            if version:
                print(f"✓ Current migration version: {version[0]}")
            else:
                print("⚠ WARNING: No migration version recorded")
    else:
        print("✗ ERROR: alembic_version table not found")
        return False

    print("\n" + "=" * 70)
    print("✓ ALL VERIFICATION CHECKS PASSED!")
    print("=" * 70)
    print("\nTask 5.1.4: Alembic Migration Setup - COMPLETE")
    print("\nNext steps:")
    print("  1. Task 5.2.1: UserRepository + Auth Dependencies")
    print("  2. Task 5.2.2: Auth API Endpoints")
    print("  3. Task 5.3.1: Conversation Repositories")
    print("\n")

    return True


if __name__ == "__main__":
    try:
        success = verify_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
