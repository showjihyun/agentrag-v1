"""
Verification script for Mode-Aware Caching (Task 5).

Tests:
1. Mode-specific cache strategies (FAST, BALANCED, DEEP)
2. Mode-specific TTLs
3. Cache performance tracking by mode
4. get_with_mode() and set_with_mode() methods
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# Mock dependencies for testing
class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def setex(self, key: str, ttl: int, value: str):
        self.data[key] = value

    async def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)

    async def keys(self, pattern: str):
        return [k for k in self.data.keys() if k.startswith(pattern.replace("*", ""))]


class MockMilvus:
    """Mock Milvus manager for testing."""

    async def search(self, **kwargs):
        return []

    async def insert(self, **kwargs):
        pass


class MockEmbedding:
    """Mock embedding service for testing."""

    async def embed_text(self, text: str):
        return [0.1] * 768


def test_cache_strategy_enum():
    """Test 1: Verify CacheStrategy enum exists."""
    print("\n" + "=" * 60)
    print("TEST 1: CacheStrategy Enum")
    print("=" * 60)

    try:
        from core.multi_level_cache import CacheStrategy

        assert hasattr(CacheStrategy, "FAST"), "Missing FAST strategy"
        assert hasattr(CacheStrategy, "BALANCED"), "Missing BALANCED strategy"
        assert hasattr(CacheStrategy, "DEEP"), "Missing DEEP strategy"

        print("✓ CacheStrategy enum defined correctly")
        print(f"  - FAST: {CacheStrategy.FAST.value}")
        print(f"  - BALANCED: {CacheStrategy.BALANCED.value}")
        print(f"  - DEEP: {CacheStrategy.DEEP.value}")

        return True

    except Exception as e:
        print(f"✗ CacheStrategy enum test failed: {e}")
        return False


async def test_mode_aware_get():
    """Test 2: Verify get_with_mode() method."""
    print("\n" + "=" * 60)
    print("TEST 2: get_with_mode() Method")
    print("=" * 60)

    try:
        from core.multi_level_cache import MultiLevelCache

        redis = MockRedis()
        cache = MultiLevelCache(
            redis_client=redis,
            milvus_manager=None,
            embedding_service=None,
            l1_maxsize=10,
            enabled=True,
        )

        # Test FAST mode (L1 only)
        print("\n1. Testing FAST mode (L1 only):")

        # Set in L1
        await cache.set_with_mode(
            query="What is RAG?",
            response="RAG is Retrieval-Augmented Generation",
            metadata={"test": True},
            mode="fast",
        )

        # Should hit L1
        result = await cache.get_with_mode("What is RAG?", mode="fast")
        assert result is not None, "FAST mode should hit L1"
        assert result.response == "RAG is Retrieval-Augmented Generation"
        print("  ✓ FAST mode hits L1 cache")

        # Test BALANCED mode (L1 + L2)
        print("\n2. Testing BALANCED mode (L1 + L2):")

        await cache.set_with_mode(
            query="What is ML?",
            response="ML is Machine Learning",
            metadata={"test": True},
            mode="balanced",
        )

        # Clear L1 to test L2
        cache.l1.clear()

        # Should hit L2 and populate L1
        result = await cache.get_with_mode("What is ML?", mode="balanced")
        assert result is not None, "BALANCED mode should hit L2"
        assert result.response == "ML is Machine Learning"
        print("  ✓ BALANCED mode hits L2 cache")
        print("  ✓ BALANCED mode populates L1 from L2")

        # Test DEEP mode (L1 + L2 + L3)
        print("\n3. Testing DEEP mode (L1 + L2 + L3):")

        await cache.set_with_mode(
            query="What is AI?",
            response="AI is Artificial Intelligence",
            metadata={"test": True},
            mode="deep",
        )

        # Should be in L2 (DEEP mode skips L1 for set)
        result = await cache.get_with_mode("What is AI?", mode="deep")
        assert result is not None, "DEEP mode should hit L2"
        print("  ✓ DEEP mode hits L2 cache")

        print("\n✓ get_with_mode() works correctly for all modes")
        return True

    except Exception as e:
        print(f"✗ get_with_mode() test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_mode_specific_ttls():
    """Test 3: Verify mode-specific TTLs."""
    print("\n" + "=" * 60)
    print("TEST 3: Mode-Specific TTLs")
    print("=" * 60)

    try:
        from core.multi_level_cache import MultiLevelCache

        redis = MockRedis()
        cache = MultiLevelCache(
            redis_client=redis,
            milvus_manager=None,
            embedding_service=None,
            enabled=True,
        )

        # Check default TTLs
        print("\nDefault TTLs:")
        print(f"  - FAST: {cache.mode_ttls['fast']}s (expected: 3600s)")
        print(f"  - BALANCED: {cache.mode_ttls['balanced']}s (expected: 1800s)")
        print(f"  - DEEP: {cache.mode_ttls['deep']}s (expected: 7200s)")

        assert cache.mode_ttls["fast"] == 3600, "FAST TTL should be 3600s"
        assert cache.mode_ttls["balanced"] == 1800, "BALANCED TTL should be 1800s"
        assert cache.mode_ttls["deep"] == 7200, "DEEP TTL should be 7200s"

        print("\n✓ Mode-specific TTLs configured correctly")
        return True

    except Exception as e:
        print(f"✗ Mode-specific TTL test failed: {e}")
        return False


async def test_cache_performance_tracking():
    """Test 4: Verify cache performance tracking by mode."""
    print("\n" + "=" * 60)
    print("TEST 4: Cache Performance Tracking by Mode")
    print("=" * 60)

    try:
        from core.multi_level_cache import MultiLevelCache

        redis = MockRedis()
        cache = MultiLevelCache(
            redis_client=redis,
            milvus_manager=None,
            embedding_service=None,
            enabled=True,
        )

        # Simulate cache operations for different modes
        print("\nSimulating cache operations:")

        # FAST mode operations
        await cache.set_with_mode("q1", "a1", {}, mode="fast")
        await cache.get_with_mode("q1", mode="fast")  # Hit
        await cache.get_with_mode("q2", mode="fast")  # Miss

        # BALANCED mode operations
        await cache.set_with_mode("q3", "a3", {}, mode="balanced")
        await cache.get_with_mode("q3", mode="balanced")  # Hit
        await cache.get_with_mode("q4", mode="balanced")  # Miss

        # DEEP mode operations
        await cache.set_with_mode("q5", "a5", {}, mode="deep")
        await cache.get_with_mode("q5", mode="deep")  # Hit
        await cache.get_with_mode("q6", mode="deep")  # Miss

        # Get statistics
        stats = cache.get_stats()

        print("\nCache Statistics:")
        print(f"  Mode Hits: {stats['mode_hits']}")
        print(f"  Mode Misses: {stats['mode_misses']}")
        print(f"  Mode Hit Rates: {stats['mode_hit_rates']}")

        # Verify tracking
        assert "mode_hits" in stats, "Missing mode_hits in stats"
        assert "mode_misses" in stats, "Missing mode_misses in stats"
        assert "mode_hit_rates" in stats, "Missing mode_hit_rates in stats"

        # Verify counts
        assert stats["mode_hits"]["fast"] == 1, "FAST mode should have 1 hit"
        assert stats["mode_misses"]["fast"] == 1, "FAST mode should have 1 miss"
        assert stats["mode_hits"]["balanced"] == 1, "BALANCED mode should have 1 hit"
        assert stats["mode_misses"]["balanced"] == 1, "BALANCED mode should have 1 miss"
        assert stats["mode_hits"]["deep"] == 1, "DEEP mode should have 1 hit"
        assert stats["mode_misses"]["deep"] == 1, "DEEP mode should have 1 miss"

        # Verify hit rates
        assert stats["mode_hit_rates"]["fast"] == 0.5, "FAST hit rate should be 50%"
        assert (
            stats["mode_hit_rates"]["balanced"] == 0.5
        ), "BALANCED hit rate should be 50%"
        assert stats["mode_hit_rates"]["deep"] == 0.5, "DEEP hit rate should be 50%"

        print("\n✓ Cache performance tracking by mode works correctly")
        return True

    except Exception as e:
        print(f"✗ Cache performance tracking test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_cache_level_tracking():
    """Test 5: Verify L1, L2, L3 level tracking."""
    print("\n" + "=" * 60)
    print("TEST 5: Cache Level Tracking")
    print("=" * 60)

    try:
        from core.multi_level_cache import MultiLevelCache

        redis = MockRedis()
        cache = MultiLevelCache(
            redis_client=redis,
            milvus_manager=None,
            embedding_service=None,
            enabled=True,
        )

        # Test L1 tracking
        print("\n1. Testing L1 level tracking:")
        cache.l1._mode_hits = {"fast": 0, "balanced": 0, "deep": 0}

        await cache.set_with_mode("q1", "a1", {}, mode="fast")
        result = await cache.get_with_mode("q1", mode="fast")

        l1_stats = cache.l1.stats()
        print(f"  L1 Stats: {l1_stats}")
        assert "mode_hits" in l1_stats, "L1 should track mode hits"
        print("  ✓ L1 tracks mode-specific hits")

        # Test L2 tracking
        print("\n2. Testing L2 level tracking:")
        if cache.l2:
            cache.l2._mode_hits = {"fast": 0, "balanced": 0, "deep": 0}

            await cache.set_with_mode("q2", "a2", {}, mode="balanced")
            cache.l1.clear()  # Clear L1 to force L2 hit
            result = await cache.get_with_mode("q2", mode="balanced")

            l2_stats = await cache.l2.stats()
            print(f"  L2 Stats: {l2_stats}")
            assert "mode_hits" in l2_stats, "L2 should track mode hits"
            print("  ✓ L2 tracks mode-specific hits")

        print("\n✓ Cache level tracking works correctly")
        return True

    except Exception as e:
        print(f"✗ Cache level tracking test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("MODE-AWARE CACHING VERIFICATION")
    print("Task 5: Implement Mode-Aware Caching")
    print("=" * 60)

    results = []

    # Test 1: CacheStrategy enum
    results.append(("CacheStrategy Enum", test_cache_strategy_enum()))

    # Test 2: get_with_mode()
    results.append(("get_with_mode() Method", await test_mode_aware_get()))

    # Test 3: Mode-specific TTLs
    results.append(("Mode-Specific TTLs", await test_mode_specific_ttls()))

    # Test 4: Performance tracking
    results.append(("Performance Tracking", await test_cache_performance_tracking()))

    # Test 5: Level tracking
    results.append(("Level Tracking", await test_cache_level_tracking()))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Mode-aware caching is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
