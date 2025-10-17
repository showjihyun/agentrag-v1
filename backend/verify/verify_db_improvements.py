"""Verify database improvements implementation."""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verify_transaction_management():
    """Verify transaction management fix."""
    print("\n=== Verifying Transaction Management ===")

    from db.database import get_db
    import inspect

    # Check that get_db no longer auto-commits
    source = inspect.getsource(get_db)

    if "db.commit()" in source:
        print("❌ FAIL: get_db() still contains auto-commit")
        return False

    if "db.rollback()" in source and "except" in source:
        print("❌ FAIL: get_db() still contains auto-rollback in except block")
        return False

    print("✅ PASS: Transaction management fixed - no auto-commit/rollback in get_db()")
    return True


def verify_composite_indexes():
    """Verify composite indexes are defined."""
    print("\n=== Verifying Composite Indexes ===")

    from db.models.conversation import Session, Message
    from db.models.document import Document
    from db.models.usage import UsageLog

    checks = []

    # Check Session model
    if hasattr(Session, "__table_args__"):
        session_indexes = [
            idx for idx in Session.__table_args__ if hasattr(idx, "name")
        ]
        if any("user_updated" in idx.name for idx in session_indexes):
            print("✅ Session: ix_sessions_user_updated found")
            checks.append(True)
        else:
            print("❌ Session: ix_sessions_user_updated NOT found")
            checks.append(False)
    else:
        print("❌ Session: No __table_args__ defined")
        checks.append(False)

    # Check Message model
    if hasattr(Message, "__table_args__"):
        message_indexes = [
            idx for idx in Message.__table_args__ if hasattr(idx, "name")
        ]
        expected = ["user_session", "session_created", "user_created"]
        found = [
            name
            for name in expected
            if any(name in idx.name for idx in message_indexes)
        ]
        if len(found) == 3:
            print(f"✅ Message: All 3 composite indexes found ({', '.join(found)})")
            checks.append(True)
        else:
            print(f"❌ Message: Only {len(found)}/3 indexes found")
            checks.append(False)
    else:
        print("❌ Message: No __table_args__ defined")
        checks.append(False)

    # Check Document model
    if hasattr(Document, "__table_args__"):
        doc_indexes = [idx for idx in Document.__table_args__ if hasattr(idx, "name")]
        expected = ["user_status", "user_uploaded"]
        found = [
            name for name in expected if any(name in idx.name for idx in doc_indexes)
        ]
        if len(found) == 2:
            print(f"✅ Document: All 2 composite indexes found ({', '.join(found)})")
            checks.append(True)
        else:
            print(f"❌ Document: Only {len(found)}/2 indexes found")
            checks.append(False)
    else:
        print("❌ Document: No __table_args__ defined")
        checks.append(False)

    # Check UsageLog model
    if hasattr(UsageLog, "__table_args__"):
        usage_indexes = [idx for idx in UsageLog.__table_args__ if hasattr(idx, "name")]
        if any("user_action_created" in idx.name for idx in usage_indexes):
            print("✅ UsageLog: ix_usage_logs_user_action_created found")
            checks.append(True)
        else:
            print("❌ UsageLog: ix_usage_logs_user_action_created NOT found")
            checks.append(False)
    else:
        print("❌ UsageLog: No __table_args__ defined")
        checks.append(False)

    return all(checks)


def verify_check_constraints():
    """Verify CHECK constraints are defined."""
    print("\n=== Verifying CHECK Constraints ===")

    from db.models.user import User
    from db.models.document import Document, BatchUpload
    from db.models.conversation import Session, Message
    from sqlalchemy import CheckConstraint

    checks = []

    # Check User model
    if hasattr(User, "__table_args__"):
        user_constraints = [
            c for c in User.__table_args__ if isinstance(c, CheckConstraint)
        ]
        if len(user_constraints) >= 3:
            print(f"✅ User: {len(user_constraints)} CHECK constraints found")
            checks.append(True)
        else:
            print(
                f"❌ User: Only {len(user_constraints)} CHECK constraints (expected >= 3)"
            )
            checks.append(False)
    else:
        print("❌ User: No __table_args__ defined")
        checks.append(False)

    # Check Document model
    if hasattr(Document, "__table_args__"):
        doc_constraints = [
            c for c in Document.__table_args__ if isinstance(c, CheckConstraint)
        ]
        if len(doc_constraints) >= 3:
            print(f"✅ Document: {len(doc_constraints)} CHECK constraints found")
            checks.append(True)
        else:
            print(
                f"❌ Document: Only {len(doc_constraints)} CHECK constraints (expected >= 3)"
            )
            checks.append(False)
    else:
        print("❌ Document: No __table_args__ defined")
        checks.append(False)

    # Check BatchUpload model
    if hasattr(BatchUpload, "__table_args__"):
        batch_constraints = [
            c for c in BatchUpload.__table_args__ if isinstance(c, CheckConstraint)
        ]
        if len(batch_constraints) >= 4:
            print(f"✅ BatchUpload: {len(batch_constraints)} CHECK constraints found")
            checks.append(True)
        else:
            print(
                f"❌ BatchUpload: Only {len(batch_constraints)} CHECK constraints (expected >= 4)"
            )
            checks.append(False)
    else:
        print("❌ BatchUpload: No __table_args__ defined")
        checks.append(False)

    # Check Session model
    if hasattr(Session, "__table_args__"):
        session_constraints = [
            c for c in Session.__table_args__ if isinstance(c, CheckConstraint)
        ]
        if len(session_constraints) >= 2:
            print(f"✅ Session: {len(session_constraints)} CHECK constraints found")
            checks.append(True)
        else:
            print(
                f"❌ Session: Only {len(session_constraints)} CHECK constraints (expected >= 2)"
            )
            checks.append(False)
    else:
        print("❌ Session: No __table_args__ defined")
        checks.append(False)

    # Check Message model
    if hasattr(Message, "__table_args__"):
        message_constraints = [
            c for c in Message.__table_args__ if isinstance(c, CheckConstraint)
        ]
        if len(message_constraints) >= 3:
            print(f"✅ Message: {len(message_constraints)} CHECK constraints found")
            checks.append(True)
        else:
            print(
                f"❌ Message: Only {len(message_constraints)} CHECK constraints (expected >= 3)"
            )
            checks.append(False)
    else:
        print("❌ Message: No __table_args__ defined")
        checks.append(False)

    return all(checks)


def verify_connection_pool_config():
    """Verify connection pool configuration."""
    print("\n=== Verifying Connection Pool Configuration ===")

    from config import settings
    from db.database import engine

    checks = []

    # Check config settings
    required_settings = [
        "DB_POOL_SIZE",
        "DB_MAX_OVERFLOW",
        "DB_POOL_PRE_PING",
        "DB_POOL_RECYCLE",
        "DB_POOL_TIMEOUT",
        "DB_STATEMENT_TIMEOUT",
    ]

    for setting in required_settings:
        if hasattr(settings, setting):
            value = getattr(settings, setting)
            print(f"✅ {setting}: {value}")
            checks.append(True)
        else:
            print(f"❌ {setting}: NOT FOUND")
            checks.append(False)

    # Check engine configuration
    pool = engine.pool
    print(f"\n✅ Engine pool configured:")
    print(f"   - Pool size: {pool.size()}")
    print(f"   - Max overflow: {pool._max_overflow}")

    return all(checks)


def verify_monitoring():
    """Verify monitoring utilities."""
    print("\n=== Verifying Monitoring Utilities ===")

    checks = []

    # Check monitoring module exists
    try:
        from db import monitoring

        print("✅ db.monitoring module exists")
        checks.append(True)
    except ImportError as e:
        print(f"❌ db.monitoring module NOT found: {e}")
        checks.append(False)
        return False

    # Check monitoring functions
    required_functions = [
        "setup_query_monitoring",
        "get_pool_status",
        "QueryPerformanceTracker",
    ]

    for func_name in required_functions:
        if hasattr(monitoring, func_name):
            print(f"✅ {func_name} found")
            checks.append(True)
        else:
            print(f"❌ {func_name} NOT found")
            checks.append(False)

    # Check get_pool_status in database module
    try:
        from db.database import get_pool_status

        print("✅ get_pool_status in db.database")
        checks.append(True)
    except ImportError:
        print("❌ get_pool_status NOT in db.database")
        checks.append(False)

    return all(checks)


def verify_health_endpoint():
    """Verify health check endpoint."""
    print("\n=== Verifying Health Check Endpoint ===")

    checks = []

    # Check health API module exists
    try:
        from api import health

        print("✅ api.health module exists")
        checks.append(True)
    except ImportError as e:
        print(f"❌ api.health module NOT found: {e}")
        checks.append(False)
        return False

    # Check router exists
    if hasattr(health, "router"):
        print("✅ health.router exists")
        checks.append(True)
    else:
        print("❌ health.router NOT found")
        checks.append(False)

    # Check health endpoint is registered in main.py
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            main_content = f.read()
            if "health.router" in main_content:
                print("✅ health.router registered in main.py")
                checks.append(True)
            else:
                print("❌ health.router NOT registered in main.py")
                checks.append(False)
    except Exception as e:
        print(f"❌ Could not verify main.py: {e}")
        checks.append(False)

    return all(checks)


def verify_migration():
    """Verify migration file exists."""
    print("\n=== Verifying Migration File ===")

    import glob

    # Find migration files
    migration_files = glob.glob(
        "alembic/versions/*_add_composite_indexes_and_constraints.py"
    )

    if migration_files:
        print(f"✅ Migration file found: {os.path.basename(migration_files[0])}")
        return True
    else:
        print("❌ Migration file NOT found")
        return False


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("DATABASE IMPROVEMENTS VERIFICATION")
    print("=" * 70)

    results = {
        "Transaction Management": verify_transaction_management(),
        "Composite Indexes": verify_composite_indexes(),
        "CHECK Constraints": verify_check_constraints(),
        "Connection Pool Config": verify_connection_pool_config(),
        "Monitoring Utilities": verify_monitoring(),
        "Health Check Endpoint": verify_health_endpoint(),
        "Migration File": verify_migration(),
    }

    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print("=" * 70)
        return 0
    else:
        failed_count = sum(1 for passed in results.values() if not passed)
        print(f"❌ {failed_count} CHECK(S) FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
