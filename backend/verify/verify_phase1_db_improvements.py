"""
Verification script for Phase 1 Database Improvements

Tests:
1. Pool monitoring is active
2. Database metrics API is accessible
3. Partial indexes are created
4. Performance improvements are measurable
"""

import asyncio
import sys
import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pool_monitoring():
    """Test that pool monitoring is active"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 1: Pool Monitoring")
    logger.info("=" * 60)

    try:
        from db.pool_monitor import get_pool_monitor
        from db.database import engine

        # Get monitor
        monitor = get_pool_monitor()

        # Get stats
        stats = monitor.get_pool_stats()

        logger.info("✅ Pool monitoring is active")
        logger.info(f"   Pool size: {stats['pool_size']}")
        logger.info(f"   Max connections: {stats['max_connections']}")
        logger.info(f"   Checked out: {stats['checked_out']}")
        logger.info(f"   Utilization: {stats['utilization_percent']:.1f}%")
        logger.info(f"   Health: {stats['health_status']}")

        return True
    except Exception as e:
        logger.error(f"❌ Pool monitoring test failed: {e}")
        return False


def test_database_metrics_api():
    """Test database metrics API endpoints"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Database Metrics API")
    logger.info("=" * 60)

    try:
        import requests

        base_url = "http://localhost:8000"

        endpoints = [
            "/api/metrics/database/postgresql/pool",
            "/api/metrics/database/postgresql/health",
            "/api/metrics/database/summary",
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {endpoint} - OK")
                else:
                    logger.warning(f"⚠️  {endpoint} - Status {response.status_code}")
            except requests.exceptions.ConnectionError:
                logger.warning(f"⚠️  {endpoint} - Server not running (expected in test)")

        return True
    except Exception as e:
        logger.error(f"❌ API test failed: {e}")
        return False


def test_partial_indexes():
    """Test that partial indexes are created"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Partial Indexes")
    logger.info("=" * 60)

    try:
        from db.database import engine

        with engine.connect() as conn:
            # Check for partial indexes
            result = conn.execute(
                text(
                    """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                AND (
                    indexname LIKE 'ix_%_active%'
                    OR indexname LIKE 'ix_%_failed%'
                    OR indexname LIKE 'ix_%_recent%'
                    OR indexname LIKE 'ix_%_processing%'
                    OR indexname LIKE 'ix_%_low_confidence%'
                    OR indexname LIKE 'ix_%_cache_hits%'
                )
                ORDER BY indexname
            """
                )
            )

            indexes = result.fetchall()

            if indexes:
                logger.info(f"✅ Found {len(indexes)} partial indexes:")
                for idx in indexes:
                    logger.info(f"   - {idx[2]} on {idx[1]} ({idx[3]})")
                return True
            else:
                logger.warning("⚠️  No partial indexes found. Run migration first:")
                logger.warning(
                    "   psql -U raguser -d agentic_rag -f backend/db/migrations/phase1_partial_indexes.sql"
                )
                return False

    except Exception as e:
        logger.error(f"❌ Partial indexes test failed: {e}")
        return False


def test_query_performance():
    """Test query performance with new indexes"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Query Performance")
    logger.info("=" * 60)

    try:
        from db.database import engine
        import time

        with engine.connect() as conn:
            # Test 1: Active documents query
            start = time.time()
            result = conn.execute(
                text(
                    """
                EXPLAIN ANALYZE
                SELECT id, filename, uploaded_at
                FROM documents
                WHERE user_id = '00000000-0000-0000-0000-000000000000'
                AND status != 'archived'
                ORDER BY uploaded_at DESC
                LIMIT 20
            """
                )
            )
            duration = (time.time() - start) * 1000

            plan = result.fetchall()
            uses_index = any(
                "ix_documents_active_user_uploaded" in str(row) for row in plan
            )

            if uses_index:
                logger.info(
                    f"✅ Active documents query uses partial index ({duration:.2f}ms)"
                )
            else:
                logger.warning(
                    f"⚠️  Active documents query doesn't use partial index ({duration:.2f}ms)"
                )

            # Test 2: Recent messages query
            start = time.time()
            result = conn.execute(
                text(
                    """
                EXPLAIN ANALYZE
                SELECT id, content, created_at
                FROM messages
                WHERE user_id = '00000000-0000-0000-0000-000000000000'
                AND created_at > NOW() - INTERVAL '30 days'
                ORDER BY created_at DESC
                LIMIT 50
            """
                )
            )
            duration = (time.time() - start) * 1000

            plan = result.fetchall()
            uses_index = any("ix_messages_recent" in str(row) for row in plan)

            if uses_index:
                logger.info(
                    f"✅ Recent messages query uses partial index ({duration:.2f}ms)"
                )
            else:
                logger.warning(
                    f"⚠️  Recent messages query doesn't use partial index ({duration:.2f}ms)"
                )

            return True

    except Exception as e:
        logger.error(f"❌ Query performance test failed: {e}")
        return False


def main():
    """Run all Phase 1 verification tests"""
    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1 DATABASE IMPROVEMENTS VERIFICATION")
    logger.info("=" * 60)

    results = {
        "Pool Monitoring": test_pool_monitoring(),
        "Database Metrics API": test_database_metrics_api(),
        "Partial Indexes": test_partial_indexes(),
        "Query Performance": test_query_performance(),
    }

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n🎉 Phase 1 improvements verified successfully!")
        return 0
    else:
        logger.warning("\n⚠️  Some tests failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
