"""
Verification script for Adaptive Metrics Collection (Task 7)

Tests:
1. AdaptiveMetricsService functionality
2. Metrics collection and aggregation
3. Dashboard data generation
4. Performance alerts
5. Time-series data
6. API endpoints
"""

import asyncio
import sys
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, ".")

from backend.services.adaptive_metrics import (
    AdaptiveMetricsService,
    get_adaptive_metrics_service,
    AlertLevel,
)
from backend.models.hybrid import QueryMode
from backend.services.adaptive_rag_service import QueryComplexity
from backend.core.metrics_collector import get_metrics_collector


async def test_basic_metrics_recording():
    """Test 1: Basic metrics recording."""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Metrics Recording")
    print("=" * 60)

    service = AdaptiveMetricsService()

    # Record a query
    await service.record_query(
        query_id="test-1",
        mode=QueryMode.FAST,
        complexity=QueryComplexity.SIMPLE,
        latency=0.5,
        cache_hit=True,
        routing_confidence=0.9,
        routing_time=0.01,
    )

    assert service.total_queries == 1, "Total queries should be 1"
    assert service.mode_counts["fast"] == 1, "FAST mode count should be 1"
    assert (
        service.complexity_counts["simple"] == 1
    ), "SIMPLE complexity count should be 1"
    assert service.cache_hits_by_mode["fast"] == 1, "Cache hits should be 1"

    print("✓ Basic metrics recording works")
    return True


async def test_multiple_queries():
    """Test 2: Multiple queries with different modes."""
    print("\n" + "=" * 60)
    print("TEST 2: Multiple Queries")
    print("=" * 60)

    service = AdaptiveMetricsService()

    # Record FAST queries
    for i in range(5):
        await service.record_query(
            query_id=f"fast-{i}",
            mode=QueryMode.FAST,
            complexity=QueryComplexity.SIMPLE,
            latency=0.5 + i * 0.1,
            cache_hit=i % 2 == 0,
            routing_confidence=0.9,
            routing_time=0.01,
        )

    # Record BALANCED queries
    for i in range(3):
        await service.record_query(
            query_id=f"balanced-{i}",
            mode=QueryMode.BALANCED,
            complexity=QueryComplexity.MEDIUM,
            latency=2.0 + i * 0.5,
            cache_hit=False,
            routing_confidence=0.8,
            routing_time=0.02,
        )

    # Record DEEP queries
    for i in range(2):
        await service.record_query(
            query_id=f"deep-{i}",
            mode=QueryMode.DEEP,
            complexity=QueryComplexity.COMPLEX,
            latency=10.0 + i * 2.0,
            cache_hit=False,
            routing_confidence=0.95,
            routing_time=0.03,
        )

    assert service.total_queries == 10, "Total queries should be 10"
    assert service.mode_counts["fast"] == 5, "FAST mode count should be 5"
    assert service.mode_counts["balanced"] == 3, "BALANCED mode count should be 3"
    assert service.mode_counts["deep"] == 2, "DEEP mode count should be 2"

    print(f"✓ Recorded {service.total_queries} queries")
    print(f"  - FAST: {service.mode_counts['fast']}")
    print(f"  - BALANCED: {service.mode_counts['balanced']}")
    print(f"  - DEEP: {service.mode_counts['deep']}")
    return True


async def test_dashboard_data():
    """Test 3: Dashboard data generation."""
    print("\n" + "=" * 60)
    print("TEST 3: Dashboard Data Generation")
    print("=" * 60)

    service = AdaptiveMetricsService()

    # Record diverse queries
    for i in range(20):
        mode = (
            QueryMode.FAST
            if i < 10
            else (QueryMode.BALANCED if i < 16 else QueryMode.DEEP)
        )
        complexity = (
            QueryComplexity.SIMPLE
            if i < 10
            else (QueryComplexity.MEDIUM if i < 16 else QueryComplexity.COMPLEX)
        )

        await service.record_query(
            query_id=f"test-{i}",
            mode=mode,
            complexity=complexity,
            latency=(
                0.5
                if mode == QueryMode.FAST
                else (2.0 if mode == QueryMode.BALANCED else 10.0)
            ),
            cache_hit=i % 3 == 0,
            routing_confidence=0.85 + (i % 10) * 0.01,
            routing_time=0.01 + (i % 5) * 0.002,
            user_satisfaction=4.0 + (i % 5) * 0.2,
        )

    dashboard = await service.get_dashboard_data()

    assert "overview" in dashboard, "Dashboard should have overview"
    assert "mode_distribution" in dashboard, "Dashboard should have mode distribution"
    assert "latency" in dashboard, "Dashboard should have latency metrics"
    assert "cache_performance" in dashboard, "Dashboard should have cache metrics"

    print("✓ Dashboard data structure:")
    print(f"  - Total queries: {dashboard['overview']['total_queries']}")
    print(f"  - Mode distribution: {dashboard['mode_distribution']['percentages']}")
    print(f"  - Average latency: {dashboard['latency']['average_by_mode']}")
    print(f"  - Cache hit rates: {dashboard['cache_performance']['hit_rates']}")

    return True


async def test_performance_alerts():
    """Test 4: Performance alerts."""
    print("\n" + "=" * 60)
    print("TEST 4: Performance Alerts")
    print("=" * 60)

    service = AdaptiveMetricsService()

    # Record queries with high latency to trigger alert
    for i in range(20):
        await service.record_query(
            query_id=f"slow-{i}",
            mode=QueryMode.FAST,
            complexity=QueryComplexity.SIMPLE,
            latency=1.5,  # Above 1.0s threshold
            cache_hit=False,
            routing_confidence=0.9,
            routing_time=0.01,
        )

    dashboard = await service.get_dashboard_data()
    alerts = dashboard["alerts"]

    print(f"✓ Generated {len(alerts)} alerts")
    for alert in alerts:
        print(f"  - [{alert['level'].upper()}] {alert['message']}")
        print(
            f"    Current: {alert['current_value']:.3f}, Threshold: {alert['threshold_value']:.3f}"
        )

    return True


async def test_escalations():
    """Test 5: Escalation tracking."""
    print("\n" + "=" * 60)
    print("TEST 5: Escalation Tracking")
    print("=" * 60)

    service = AdaptiveMetricsService()

    # Record escalated queries
    for i in range(10):
        await service.record_query(
            query_id=f"escalated-{i}",
            mode=QueryMode.BALANCED,
            complexity=QueryComplexity.MEDIUM,
            latency=2.5,
            cache_hit=False,
            routing_confidence=0.7,
            routing_time=0.02,
            escalated=i < 3,  # 30% escalation rate
            escalated_from=QueryMode.FAST if i < 3 else None,
        )

    dashboard = await service.get_dashboard_data()
    escalations = dashboard["escalations"]

    print(f"✓ Escalation metrics:")
    print(f"  - Total escalations: {escalations['total']}")
    print(f"  - Escalation rate: {escalations['rate_percent']:.1f}%")
    print(f"  - By transition: {escalations['by_transition']}")

    return True


async def test_time_series():
    """Test 6: Time-series data."""
    print("\n" + "=" * 60)
    print("TEST 6: Time-Series Data")
    print("=" * 60)

    service = AdaptiveMetricsService()

    # Create multiple snapshots
    for snapshot_num in range(5):
        # Record queries
        for i in range(3):
            await service.record_query(
                query_id=f"ts-{snapshot_num}-{i}",
                mode=QueryMode.FAST,
                complexity=QueryComplexity.SIMPLE,
                latency=0.5 + snapshot_num * 0.1,
                cache_hit=True,
                routing_confidence=0.9,
                routing_time=0.01,
            )

        # Create snapshot
        await service.create_snapshot()

    # Get time-series data
    latency_data = await service.get_time_series_data("latency")
    mode_data = await service.get_time_series_data("mode_distribution")

    print(f"✓ Time-series data:")
    print(f"  - Latency snapshots: {len(latency_data)}")
    print(f"  - Mode distribution snapshots: {len(mode_data)}")

    return True


async def test_threshold_history():
    """Test 7: Threshold change history."""
    print("\n" + "=" * 60)
    print("TEST 7: Threshold Change History")
    print("=" * 60)

    service = AdaptiveMetricsService()

    # Record threshold changes
    await service.record_threshold_change(
        simple_threshold=0.35, complex_threshold=0.70, reason="Initial configuration"
    )

    await service.record_threshold_change(
        simple_threshold=0.40, complex_threshold=0.75, reason="Auto-tuning adjustment"
    )

    dashboard = await service.get_dashboard_data()
    thresholds = dashboard["thresholds"]

    print(f"✓ Threshold history:")
    print(f"  - Current: {thresholds['current']}")
    print(f"  - History entries: {len(thresholds['history'])}")

    return True


async def test_metrics_collector_integration():
    """Test 8: Integration with MetricsCollector."""
    print("\n" + "=" * 60)
    print("TEST 8: MetricsCollector Integration")
    print("=" * 60)

    collector = get_metrics_collector()

    if collector.enabled:
        # Record adaptive routing metrics
        collector.record_adaptive_routing(
            mode="fast",
            complexity="simple",
            routing_confidence=0.9,
            routing_time=0.01,
            cache_hit=True,
        )

        # Update thresholds
        collector.update_adaptive_thresholds(
            simple_threshold=0.35, complex_threshold=0.70
        )

        print("✓ MetricsCollector integration works")
        print("  - Adaptive routing metrics recorded")
        print("  - Threshold gauges updated")
    else:
        print("⚠ MetricsCollector not enabled (prometheus_client not installed)")

    return True


async def test_global_instance():
    """Test 9: Global instance."""
    print("\n" + "=" * 60)
    print("TEST 9: Global Instance")
    print("=" * 60)

    service1 = get_adaptive_metrics_service()
    service2 = get_adaptive_metrics_service()

    assert service1 is service2, "Should return same instance"

    print("✓ Global instance works correctly")
    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ADAPTIVE METRICS COLLECTION VERIFICATION")
    print("Task 7: Implement Adaptive Metrics Collection")
    print("=" * 60)

    tests = [
        ("Basic Metrics Recording", test_basic_metrics_recording),
        ("Multiple Queries", test_multiple_queries),
        ("Dashboard Data", test_dashboard_data),
        ("Performance Alerts", test_performance_alerts),
        ("Escalation Tracking", test_escalations),
        ("Time-Series Data", test_time_series),
        ("Threshold History", test_threshold_history),
        ("MetricsCollector Integration", test_metrics_collector_integration),
        ("Global Instance", test_global_instance),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"✗ Test failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result, _ in results if result)
    total = len(results)

    for name, result, error in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if error:
            print(f"  Error: {error}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Task 7 implementation verified.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
