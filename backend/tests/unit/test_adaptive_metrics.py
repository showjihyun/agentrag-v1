"""
Unit tests for AdaptiveMetricsService
"""

import pytest
from datetime import datetime, timedelta
from backend.services.adaptive_metrics import (
    AdaptiveMetricsService,
    AlertLevel,
    MetricSnapshot,
    PerformanceAlert,
)
from backend.models.hybrid import QueryMode
from backend.services.adaptive_rag_service import QueryComplexity


@pytest.fixture
def metrics_service():
    """Create a fresh metrics service for each test."""
    return AdaptiveMetricsService(max_history_size=100)


@pytest.mark.asyncio
async def test_record_query_basic(metrics_service):
    """Test basic query recording."""
    await metrics_service.record_query(
        query_id="test-1",
        mode=QueryMode.FAST,
        complexity=QueryComplexity.SIMPLE,
        latency=0.5,
        cache_hit=True,
        routing_confidence=0.9,
        routing_time=0.01,
    )

    assert metrics_service.total_queries == 1
    assert metrics_service.mode_counts["fast"] == 1
    assert metrics_service.complexity_counts["simple"] == 1
    assert metrics_service.cache_hits_by_mode["fast"] == 1
    assert len(metrics_service.latency_by_mode["fast"]) == 1
    assert metrics_service.latency_by_mode["fast"][0] == 0.5


@pytest.mark.asyncio
async def test_record_multiple_queries(metrics_service):
    """Test recording multiple queries."""
    # Record FAST queries
    for i in range(5):
        await metrics_service.record_query(
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
        await metrics_service.record_query(
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
        await metrics_service.record_query(
            query_id=f"deep-{i}",
            mode=QueryMode.DEEP,
            complexity=QueryComplexity.COMPLEX,
            latency=10.0 + i * 2.0,
            cache_hit=False,
            routing_confidence=0.95,
            routing_time=0.03,
        )

    assert metrics_service.total_queries == 10
    assert metrics_service.mode_counts["fast"] == 5
    assert metrics_service.mode_counts["balanced"] == 3
    assert metrics_service.mode_counts["deep"] == 2

    # Check cache hits
    assert metrics_service.cache_hits_by_mode["fast"] == 3  # 0, 2, 4
    assert metrics_service.cache_misses_by_mode["fast"] == 2  # 1, 3
    assert metrics_service.cache_misses_by_mode["balanced"] == 3
    assert metrics_service.cache_misses_by_mode["deep"] == 2


@pytest.mark.asyncio
async def test_record_escalation(metrics_service):
    """Test recording mode escalations."""
    await metrics_service.record_query(
        query_id="escalated-1",
        mode=QueryMode.BALANCED,
        complexity=QueryComplexity.MEDIUM,
        latency=3.0,
        cache_hit=False,
        routing_confidence=0.7,
        routing_time=0.02,
        escalated=True,
        escalated_from=QueryMode.FAST,
    )

    assert metrics_service.escalations["fast_to_balanced"] == 1


@pytest.mark.asyncio
async def test_record_user_satisfaction(metrics_service):
    """Test recording user satisfaction."""
    await metrics_service.record_query(
        query_id="satisfied-1",
        mode=QueryMode.FAST,
        complexity=QueryComplexity.SIMPLE,
        latency=0.5,
        cache_hit=True,
        routing_confidence=0.9,
        routing_time=0.01,
        user_satisfaction=5.0,
    )

    await metrics_service.record_query(
        query_id="satisfied-2",
        mode=QueryMode.FAST,
        complexity=QueryComplexity.SIMPLE,
        latency=0.6,
        cache_hit=True,
        routing_confidence=0.9,
        routing_time=0.01,
        user_satisfaction=4.0,
    )

    assert len(metrics_service.satisfaction_by_mode["fast"]) == 2
    assert metrics_service.satisfaction_by_mode["fast"][0] == 5.0
    assert metrics_service.satisfaction_by_mode["fast"][1] == 4.0


@pytest.mark.asyncio
async def test_record_threshold_change(metrics_service):
    """Test recording threshold changes."""
    await metrics_service.record_threshold_change(
        simple_threshold=0.35, complex_threshold=0.70, reason="Initial configuration"
    )

    await metrics_service.record_threshold_change(
        simple_threshold=0.40, complex_threshold=0.75, reason="Auto-tuning adjustment"
    )

    assert len(metrics_service.threshold_history) == 2
    assert metrics_service.threshold_history[0]["simple_threshold"] == 0.35
    assert metrics_service.threshold_history[1]["simple_threshold"] == 0.40


@pytest.mark.asyncio
async def test_get_current_metrics(metrics_service):
    """Test getting current metrics snapshot."""
    # Record some queries
    await metrics_service.record_query(
        query_id="test-1",
        mode=QueryMode.FAST,
        complexity=QueryComplexity.SIMPLE,
        latency=0.5,
        cache_hit=True,
        routing_confidence=0.9,
        routing_time=0.01,
    )

    await metrics_service.record_query(
        query_id="test-2",
        mode=QueryMode.BALANCED,
        complexity=QueryComplexity.MEDIUM,
        latency=2.0,
        cache_hit=False,
        routing_confidence=0.8,
        routing_time=0.02,
    )

    metrics = await metrics_service.get_current_metrics()

    assert metrics.total_queries == 2
    assert metrics.mode_distribution["fast"] == 1
    assert metrics.mode_distribution["balanced"] == 1
    assert metrics.complexity_distribution["simple"] == 1
    assert metrics.complexity_distribution["medium"] == 1
    assert len(metrics.latency_by_mode["fast"]) == 1
    assert len(metrics.latency_by_mode["balanced"]) == 1


@pytest.mark.asyncio
async def test_get_dashboard_data(metrics_service):
    """Test getting dashboard-formatted data."""
    # Record queries with different modes
    for i in range(10):
        mode = (
            QueryMode.FAST
            if i < 5
            else (QueryMode.BALANCED if i < 8 else QueryMode.DEEP)
        )
        complexity = (
            QueryComplexity.SIMPLE
            if i < 5
            else (QueryComplexity.MEDIUM if i < 8 else QueryComplexity.COMPLEX)
        )

        await metrics_service.record_query(
            query_id=f"test-{i}",
            mode=mode,
            complexity=complexity,
            latency=(
                0.5
                if mode == QueryMode.FAST
                else (2.0 if mode == QueryMode.BALANCED else 10.0)
            ),
            cache_hit=i % 2 == 0,
            routing_confidence=0.9,
            routing_time=0.01,
            user_satisfaction=4.5,
        )

    dashboard = await metrics_service.get_dashboard_data()

    assert dashboard["overview"]["total_queries"] == 10
    assert "mode_distribution" in dashboard
    assert "latency" in dashboard
    assert "cache_performance" in dashboard
    assert "user_satisfaction" in dashboard

    # Check mode distribution percentages
    assert dashboard["mode_distribution"]["percentages"]["fast"] == 50.0
    assert dashboard["mode_distribution"]["percentages"]["balanced"] == 30.0
    assert dashboard["mode_distribution"]["percentages"]["deep"] == 20.0


@pytest.mark.asyncio
async def test_performance_alerts_latency(metrics_service):
    """Test performance alerts for high latency."""
    # Record queries with high latency
    for i in range(20):
        await metrics_service.record_query(
            query_id=f"slow-{i}",
            mode=QueryMode.FAST,
            complexity=QueryComplexity.SIMPLE,
            latency=1.5,  # Above 1.0s threshold
            cache_hit=False,
            routing_confidence=0.9,
            routing_time=0.01,
        )

    # Check for alerts
    dashboard = await metrics_service.get_dashboard_data()
    alerts = dashboard["alerts"]

    # Should have at least one latency alert
    latency_alerts = [a for a in alerts if "latency" in a["metric"]]
    assert len(latency_alerts) > 0

    # Check alert structure
    alert = latency_alerts[0]
    assert "level" in alert
    assert "message" in alert
    assert "current_value" in alert
    assert "threshold_value" in alert
    assert "recommendations" in alert


@pytest.mark.asyncio
async def test_performance_alerts_cache_hit_rate(metrics_service):
    """Test performance alerts for low cache hit rate."""
    # Record queries with low cache hit rate
    for i in range(20):
        await metrics_service.record_query(
            query_id=f"uncached-{i}",
            mode=QueryMode.FAST,
            complexity=QueryComplexity.SIMPLE,
            latency=0.5,
            cache_hit=i < 2,  # Only 10% hit rate
            routing_confidence=0.9,
            routing_time=0.01,
        )

    # Check for alerts
    dashboard = await metrics_service.get_dashboard_data()
    alerts = dashboard["alerts"]

    # Should have cache hit rate alert
    cache_alerts = [a for a in alerts if "cache" in a["metric"]]
    assert len(cache_alerts) > 0


@pytest.mark.asyncio
async def test_performance_alerts_escalation_rate(metrics_service):
    """Test performance alerts for high escalation rate."""
    # Record queries with high escalation rate
    for i in range(20):
        await metrics_service.record_query(
            query_id=f"escalated-{i}",
            mode=QueryMode.BALANCED,
            complexity=QueryComplexity.MEDIUM,
            latency=2.0,
            cache_hit=False,
            routing_confidence=0.7,
            routing_time=0.02,
            escalated=i < 5,  # 25% escalation rate
            escalated_from=QueryMode.FAST if i < 5 else None,
        )

    # Check for alerts
    dashboard = await metrics_service.get_dashboard_data()
    alerts = dashboard["alerts"]

    # Should have escalation rate alert
    escalation_alerts = [a for a in alerts if "escalation" in a["metric"]]
    assert len(escalation_alerts) > 0


@pytest.mark.asyncio
async def test_create_snapshot(metrics_service):
    """Test creating metric snapshots."""
    # Record some queries
    for i in range(5):
        await metrics_service.record_query(
            query_id=f"test-{i}",
            mode=QueryMode.FAST,
            complexity=QueryComplexity.SIMPLE,
            latency=0.5,
            cache_hit=True,
            routing_confidence=0.9,
            routing_time=0.01,
        )

    # Create snapshot
    await metrics_service.create_snapshot()

    assert len(metrics_service.snapshots) == 1

    snapshot = metrics_service.snapshots[0]
    assert isinstance(snapshot, MetricSnapshot)
    assert snapshot.total_queries == 5
    assert "fast" in snapshot.mode_distribution


@pytest.mark.asyncio
async def test_get_time_series_data(metrics_service):
    """Test getting time-series data."""
    # Create multiple snapshots
    for i in range(3):
        await metrics_service.record_query(
            query_id=f"test-{i}",
            mode=QueryMode.FAST,
            complexity=QueryComplexity.SIMPLE,
            latency=0.5 + i * 0.1,
            cache_hit=True,
            routing_confidence=0.9,
            routing_time=0.01,
        )
        await metrics_service.create_snapshot()

    # Get time-series data
    latency_data = await metrics_service.get_time_series_data("latency")

    assert len(latency_data) == 3
    assert all("timestamp" in d for d in latency_data)
    assert all("values" in d for d in latency_data)


@pytest.mark.asyncio
async def test_reset_metrics(metrics_service):
    """Test resetting metrics."""
    # Record some queries
    await metrics_service.record_query(
        query_id="test-1",
        mode=QueryMode.FAST,
        complexity=QueryComplexity.SIMPLE,
        latency=0.5,
        cache_hit=True,
        routing_confidence=0.9,
        routing_time=0.01,
    )

    assert metrics_service.total_queries == 1

    # Reset
    await metrics_service.reset_metrics()

    assert metrics_service.total_queries == 0
    assert len(metrics_service.mode_counts) == 0
    assert len(metrics_service.complexity_counts) == 0


@pytest.mark.asyncio
async def test_max_history_size(metrics_service):
    """Test that history size is limited."""
    # Record more queries than max_history_size
    for i in range(150):
        await metrics_service.record_query(
            query_id=f"test-{i}",
            mode=QueryMode.FAST,
            complexity=QueryComplexity.SIMPLE,
            latency=0.5,
            cache_hit=True,
            routing_confidence=0.9,
            routing_time=0.01,
        )

    # Check that latency history is limited
    assert len(metrics_service.latency_by_mode["fast"]) == 100  # max_history_size
    assert len(metrics_service.routing_confidence) == 100


@pytest.mark.asyncio
async def test_calculate_percentile(metrics_service):
    """Test percentile calculation."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

    p50 = metrics_service._calculate_percentile(values, 50)
    p95 = metrics_service._calculate_percentile(values, 95)
    p99 = metrics_service._calculate_percentile(values, 99)

    assert p50 == 5.0
    assert p95 == 9.0
    assert p99 == 10.0


@pytest.mark.asyncio
async def test_empty_metrics(metrics_service):
    """Test getting metrics when no data recorded."""
    dashboard = await metrics_service.get_dashboard_data()

    assert dashboard["overview"]["total_queries"] == 0
    assert len(dashboard["mode_distribution"]["counts"]) == 0
    assert len(dashboard["alerts"]) == 0
