"""
Script to verify database optimizations and caching improvements.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_indexes(db):
    """Verify that performance indexes are created."""
    logger.info("Checking database indexes...")
    
    expected_indexes = [
        # Agent Executions
        'idx_agent_executions_user_started_desc',
        'idx_agent_executions_agent_started_desc',
        'idx_agent_executions_status_started',
        'idx_agent_executions_agent_status',
        
        # Tool Executions
        'idx_tool_executions_user_started_desc',
        'idx_tool_executions_tool_status',
        'idx_tool_executions_user_tool',
        'idx_tool_executions_status_started',
        
        # Agents
        'idx_agents_user_updated_desc',
        'idx_agents_user_created_desc',
        
        # Workflows
        'idx_workflows_user_updated_desc',
        'idx_workflow_executions_workflow_status',
        'idx_workflow_executions_user_workflow',
        'idx_workflow_executions_status_started',
        
        # Blocks
        'idx_blocks_user_type_public',
        'idx_blocks_type_public',
        
        # Comprehensive indexes
        'idx_agent_tools_tool_agent',
        'idx_agent_knowledgebases_agent_kb',
        'idx_workflow_schedules_active_next',
    ]
    
    query = text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_%'
        ORDER BY indexname
    """)
    
    result = db.execute(query)
    existing_indexes = {row[0] for row in result}
    
    missing_indexes = []
    found_indexes = []
    
    for idx in expected_indexes:
        if idx in existing_indexes:
            found_indexes.append(idx)
        else:
            missing_indexes.append(idx)
    
    logger.info(f"✅ Found {len(found_indexes)} indexes")
    
    if missing_indexes:
        logger.warning(f"⚠️  Missing {len(missing_indexes)} indexes:")
        for idx in missing_indexes:
            logger.warning(f"   - {idx}")
        return False
    
    logger.info("✅ All expected indexes are present")
    return True


async def verify_cache_connection():
    """Verify Redis cache connection."""
    logger.info("Checking Redis cache connection...")
    
    try:
        from backend.core.dependencies import get_redis_client
        
        redis_client = await get_redis_client()
        
        # Test connection
        await redis_client.ping()
        
        # Get cache stats
        info = await redis_client.info('stats')
        
        logger.info("✅ Redis connection successful")
        logger.info(f"   Total keys: {await redis_client.dbsize()}")
        logger.info(f"   Hits: {info.get('keyspace_hits', 0)}")
        logger.info(f"   Misses: {info.get('keyspace_misses', 0)}")
        
        total_ops = info.get('keyspace_hits', 0) + info.get('keyspace_misses', 1)
        hit_rate = (info.get('keyspace_hits', 0) / total_ops) * 100
        logger.info(f"   Hit rate: {hit_rate:.2f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        return False


async def test_query_optimization(db):
    """Test query optimization improvements."""
    logger.info("Testing query optimizations...")
    
    try:
        from backend.db.models.agent_builder import Agent
        from backend.core.query_optimizer import QueryOptimizer
        
        # Test 1: Eager loading
        logger.info("Test 1: Eager loading")
        query = db.query(Agent).filter(Agent.deleted_at.is_(None)).limit(5)
        
        query_optimized = QueryOptimizer.apply_eager_loading(
            query,
            Agent,
            ['tools', 'knowledgebases'],
            strategy='joined'
        )
        
        start = datetime.utcnow()
        agents = query_optimized.all()
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        
        logger.info(f"   Loaded {len(agents)} agents in {duration:.2f}ms")
        
        # Test 2: Count optimization
        logger.info("Test 2: Count optimization")
        query = db.query(Agent).filter(Agent.deleted_at.is_(None))
        
        start = datetime.utcnow()
        count = QueryOptimizer.optimize_count_query(query)
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        
        logger.info(f"   Counted {count} agents in {duration:.2f}ms")
        
        # Test 3: Exists check
        logger.info("Test 3: Exists check optimization")
        
        if agents:
            start = datetime.utcnow()
            exists = QueryOptimizer.optimize_exists_check(
                db,
                Agent,
                {'id': agents[0].id}
            )
            duration = (datetime.utcnow() - start).total_seconds() * 1000
            
            logger.info(f"   Exists check in {duration:.2f}ms (result: {exists})")
        
        logger.info("✅ Query optimization tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Query optimization test failed: {e}")
        return False


async def test_caching_strategy():
    """Test caching strategy."""
    logger.info("Testing caching strategy...")
    
    try:
        from backend.core.cache_strategy import CacheStrategy
        from backend.core.dependencies import get_redis_client
        
        redis_client = await get_redis_client()
        
        # Test 1: Cache key generation
        logger.info("Test 1: Cache key generation")
        key = CacheStrategy.generate_cache_key("test", "arg1", "arg2", param="value")
        logger.info(f"   Generated key: {key}")
        
        # Test 2: Get or compute
        logger.info("Test 2: Get or compute")
        
        async def expensive_computation():
            await asyncio.sleep(0.1)
            return {"result": "computed"}
        
        # First call (cache miss)
        start = datetime.utcnow()
        result1 = await CacheStrategy.get_or_compute(
            redis_client,
            "cache:test:123",
            expensive_computation,
            ttl=60
        )
        duration1 = (datetime.utcnow() - start).total_seconds() * 1000
        logger.info(f"   First call (miss): {duration1:.2f}ms")
        
        # Second call (cache hit)
        start = datetime.utcnow()
        result2 = await CacheStrategy.get_or_compute(
            redis_client,
            "cache:test:123",
            expensive_computation,
            ttl=60
        )
        duration2 = (datetime.utcnow() - start).total_seconds() * 1000
        logger.info(f"   Second call (hit): {duration2:.2f}ms")
        
        speedup = duration1 / duration2 if duration2 > 0 else 0
        logger.info(f"   Speedup: {speedup:.1f}x")
        
        # Test 3: Cache invalidation
        logger.info("Test 3: Cache invalidation")
        deleted = await CacheStrategy.invalidate_pattern(
            redis_client,
            "cache:test:*"
        )
        logger.info(f"   Deleted {deleted} cache entries")
        
        # Test 4: Cache stats
        logger.info("Test 4: Cache statistics")
        stats = await CacheStrategy.get_cache_stats(redis_client)
        logger.info(f"   Total keys: {stats.get('total_keys', 0)}")
        logger.info(f"   Hit rate: {stats.get('hit_rate', 0):.2f}%")
        logger.info(f"   Memory used: {stats.get('memory_used', 'N/A')}")
        
        logger.info("✅ Caching strategy tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Caching strategy test failed: {e}")
        return False


async def analyze_query_performance(db):
    """Analyze query performance with EXPLAIN."""
    logger.info("Analyzing query performance...")
    
    try:
        # Test Agent query with index
        query = text("""
            EXPLAIN ANALYZE
            SELECT * FROM agents 
            WHERE user_id = :user_id 
            AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        # Get a sample user_id
        user_result = db.execute(text("SELECT id FROM users LIMIT 1"))
        user_row = user_result.fetchone()
        
        if user_row:
            user_id = user_row[0]
            result = db.execute(query, {"user_id": str(user_id)})
            
            logger.info("Query plan:")
            for row in result:
                logger.info(f"   {row[0]}")
            
            logger.info("✅ Query performance analysis complete")
            return True
        else:
            logger.warning("⚠️  No users found for query analysis")
            return True
            
    except Exception as e:
        logger.error(f"❌ Query performance analysis failed: {e}")
        return False


async def main():
    """Run all verification tests."""
    logger.info("=" * 60)
    logger.info("Backend Optimization Verification")
    logger.info("=" * 60)
    
    try:
        from backend.db.database import SessionLocal
        
        db = SessionLocal()
        
        results = {
            "indexes": await verify_indexes(db),
            "cache_connection": await verify_cache_connection(),
            "query_optimization": await test_query_optimization(db),
            "caching_strategy": await test_caching_strategy(),
            "query_performance": await analyze_query_performance(db),
        }
        
        db.close()
        
        logger.info("=" * 60)
        logger.info("Verification Results:")
        logger.info("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{test_name:.<40} {status}")
        
        all_passed = all(results.values())
        
        if all_passed:
            logger.info("=" * 60)
            logger.info("✅ All optimizations verified successfully!")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("=" * 60)
            logger.error("❌ Some optimizations failed verification")
            logger.error("=" * 60)
            return 1
            
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
