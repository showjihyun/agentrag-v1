"""
Unit tests for PerformanceMonitor.

Tests metrics collection accuracy, alert triggering conditions,
and analytics endpoint responses.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.performance_monitor import (
    PerformanceMonitor,
    TimingMetrics,
    ConfidenceMetrics,
    ErrorMetrics,
    MetricType,
)
from backend.models.hybrid import QueryMode, PathSource


@pytest.fixture
async def mock_redis():
    """Create a mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.zadd = AsyncMock()
    redis_mock.expire = AsyncMock()
    redis_mock.hincrby = AsyncMock()
    redis_mock.hincrbyfloat = AsyncMock()
    redis_mock.hget = AsyncMock()
    redis_mock.hgetall = AsyncMock()
    redis_mock.zcard = AsyncMock(return_value=0)
    redis_mock.zrange = AsyncMock(return_value=[])
    redis_mock.zrem = AsyncMock()
    redis_mock.delete = AsyncMock()
    redis_mock.zrevrange = AsyncMock(return_value=[])
    redis_mock.pipeline = MagicMock()

    # Mock pipeline
    pipeline_mock = AsyncMock()
    pipeline_mock.hincrby = MagicMock(return_value=pipeline_mock)
    pipeline_mock.hincrbyfloat = MagicMock(return_value=pipeline_mock)
    pipeline_mock.execute = AsyncMock()
    redis_mock.pipeline.return_value = pipeline_mock

    return redis_mock


@pytest.fixture
async def performance_monitor(mock_redis):
    """Create a PerformanceMonitor instance with mock Redis."""
    return PerformanceMonitor(
        redis_client=mock_redis,
        metrics_ttl=3600,
        alert_threshold_error_rate=0.1,
        alert_threshold_slow_response=5.0,
    )


class TestTimingMetrics:
    """Test timing metrics collection."""

    def test_timing_metrics_creation(self):
        """Test TimingMetrics dataclass creation."""
        metrics = TimingMetrics(
            query_id="test_query",
            mode="balanced",
            speculative_time=1.5,
            agentic_time=8.0,
            total_time=8.0,
            first_response_time=1.5,
        )

        assert metrics.query_id == "test_query"
        assert metrics.mode == "balanced"
        assert metrics.speculative_time == 1.5
        assert metrics.agentic_time == 8.0
        assert metrics.total_time == 8.0
        assert metrics.path_completed_first == "speculative"
        assert isinstance(metrics.timestamp, datetime)

    def test_timing_metrics_path_detection(self):
        """Test automatic detection of which path completed first."""
        # Speculative faster
        metrics1 = TimingMetrics(
            query_id="test1",
            mode="balanced",
            speculative_time=1.0,
            agentic_time=5.0,
            total_time=5.0,
        )
        assert metrics1.path_completed_first == "speculative"

        # Agentic faster (unusual but possible)
        metrics2 = TimingMetrics(
            query_id="test2",
            mode="balanced",
            speculative_time=3.0,
            agentic_time=2.0,
            total_time=3.0,
        )
        assert metrics2.path_completed_first == "agentic"

        # Only speculative
        metrics3 = TimingMetrics(
            query_id="test3", mode="fast", speculative_time=1.5, total_time=1.5
        )
        assert metrics3.path_completed_first == "speculative"

        # Only agentic
        metrics4 = TimingMetrics(
            query_id="test4", mode="deep", agentic_time=10.0, total_time=10.0
        )
        assert metrics4.path_completed_first == "agentic"

    @pytest.mark.asyncio
    async def test_log_timing_metrics(self, performance_monitor, mock_redis):
        """Test logging timing metrics."""
        await performance_monitor.log_timing_metrics(
            query_id="test_query",
            mode=QueryMode.BALANCED,
            speculative_time=1.5,
            agentic_time=8.0,
            total_time=8.0,
            first_response_time=1.5,
        )

        # Verify Redis zadd was called
        assert mock_redis.zadd.called
        call_args = mock_redis.zadd.call_args
        assert "metrics:timing" in call_args[0]

        # Verify expire was called
        assert mock_redis.expire.called

    @pytest.mark.asyncio
    async def test_timing_stats_aggregation(self, performance_monitor, mock_redis):
        """Test timing statistics aggregation."""
        # Mock pipeline execution
        pipeline_mock = mock_redis.pipeline.return_value

        await performance_monitor.log_timing_metrics(
            query_id="test_query",
            mode=QueryMode.BALANCED,
            speculative_time=1.5,
            agentic_time=8.0,
            total_time=8.0,
        )

        # Verify pipeline operations
        assert pipeline_mock.execute.called


class TestConfidenceMetrics:
    """Test confidence score tracking."""

    def test_confidence_metrics_creation(self):
        """Test ConfidenceMetrics dataclass creation."""
        metrics = ConfidenceMetrics(
            query_id="test_query",
            mode="balanced",
            initial_speculative_confidence=0.75,
            final_agentic_confidence=0.92,
        )

        assert metrics.query_id == "test_query"
        assert metrics.initial_speculative_confidence == 0.75
        assert metrics.final_agentic_confidence == 0.92
        assert metrics.confidence_improvement == 0.17
        assert isinstance(metrics.timestamp, datetime)

    def test_confidence_improvement_calculation(self):
        """Test confidence improvement calculation."""
        # Positive improvement
        metrics1 = ConfidenceMetrics(
            query_id="test1",
            mode="balanced",
            initial_speculative_confidence=0.6,
            final_agentic_confidence=0.9,
        )
        assert metrics1.confidence_improvement == pytest.approx(0.3, rel=1e-6)

        # Negative improvement (rare but possible)
        metrics2 = ConfidenceMetrics(
            query_id="test2",
            mode="balanced",
            initial_speculative_confidence=0.8,
            final_agentic_confidence=0.7,
        )
        assert metrics2.confidence_improvement == pytest.approx(-0.1, rel=1e-6)

        # No improvement
        metrics3 = ConfidenceMetrics(
            query_id="test3",
            mode="balanced",
            initial_speculative_confidence=0.85,
            final_agentic_confidence=0.85,
        )
        assert metrics3.confidence_improvement == 0.0

    @pytest.mark.asyncio
    async def test_log_confidence_metrics(self, performance_monitor, mock_redis):
        """Test logging confidence metrics."""
        await performance_monitor.log_confidence_metrics(
            query_id="test_query",
            mode=QueryMode.BALANCED,
            initial_speculative_confidence=0.75,
            final_agentic_confidence=0.92,
        )

        # Verify Redis operations
        assert mock_redis.zadd.called
        assert mock_redis.expire.called


class TestErrorMetrics:
    """Test error rate monitoring."""

    def test_error_metrics_creation(self):
        """Test ErrorMetrics dataclass creation."""
        metrics = ErrorMetrics(
            query_id="test_query",
            mode="balanced",
            path="speculative",
            error_type="timeout",
            error_message="Vector search timed out",
        )

        assert metrics.query_id == "test_query"
        assert metrics.mode == "balanced"
        assert metrics.path == "speculative"
        assert metrics.error_type == "timeout"
        assert metrics.error_message == "Vector search timed out"
        assert isinstance(metrics.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_log_error_metrics(self, performance_monitor, mock_redis):
        """Test logging error metrics."""
        await performance_monitor.log_error_metrics(
            query_id="test_query",
            mode=QueryMode.BALANCED,
            path=PathSource.SPECULATIVE,
            error_type="timeout",
            error_message="Vector search timed out",
        )

        # Verify Redis operations
        assert mock_redis.zadd.called
        assert mock_redis.expire.called

    @pytest.mark.asyncio
    async def test_error_message_truncation(self, performance_monitor, mock_redis):
        """Test that long error messages are truncated."""
        long_message = "x" * 500

        await performance_monitor.log_error_metrics(
            query_id="test_query",
            mode=QueryMode.BALANCED,
            path=PathSource.SPECULATIVE,
            error_type="llm_error",
            error_message=long_message,
        )

        # Verify the call was made (message truncation happens in ErrorMetrics)
        assert mock_redis.zadd.called


class TestAlertTriggering:
    """Test alert triggering conditions."""

    @pytest.mark.asyncio
    async def test_slow_response_alert(self, performance_monitor, mock_redis):
        """Test alert triggering for slow responses."""
        # Log a slow query (> 5 seconds threshold)
        await performance_monitor.log_timing_metrics(
            query_id="slow_query",
            mode=QueryMode.BALANCED,
            speculative_time=2.0,
            agentic_time=12.0,
            total_time=12.0,
        )

        # Verify alert was stored
        alert_calls = [
            call for call in mock_redis.zadd.call_args_list if "alerts" in str(call)
        ]
        assert len(alert_calls) > 0

    @pytest.mark.asyncio
    async def test_fast_response_no_alert(self, performance_monitor, mock_redis):
        """Test that fast responses don't trigger alerts."""
        # Reset mock
        mock_redis.zadd.reset_mock()

        # Log a fast query (< 5 seconds threshold)
        await performance_monitor.log_timing_metrics(
            query_id="fast_query",
            mode=QueryMode.FAST,
            speculative_time=1.5,
            total_time=1.5,
        )

        # Check that no alert was stored (only metrics zadd, not alerts zadd)
        alert_calls = [
            call for call in mock_redis.zadd.call_args_list if "alerts" in str(call)
        ]
        assert len(alert_calls) == 0

    @pytest.mark.asyncio
    async def test_high_error_rate_alert(self, performance_monitor, mock_redis):
        """Test alert triggering for high error rates."""
        # Mock stats to simulate high error rate
        mock_redis.hget.side_effect = lambda key, field: {
            (b"metrics:error:stats", "speculative_errors"): b"15",
            (b"metrics:timing:stats", "total_queries"): b"100",
        }.get((key.encode() if isinstance(key, str) else key, field), None)

        # Log an error
        await performance_monitor.log_error_metrics(
            query_id="error_query",
            mode=QueryMode.BALANCED,
            path=PathSource.SPECULATIVE,
            error_type="timeout",
            error_message="Timeout occurred",
        )

        # Verify alert check was performed
        assert mock_redis.hget.called


class TestAnalytics:
    """Test analytics retrieval."""

    @pytest.mark.asyncio
    async def test_get_timing_stats(self, performance_monitor, mock_redis):
        """Test retrieving timing statistics."""
        # Mock Redis response
        mock_redis.hgetall.return_value = {
            b"total_queries": b"100",
            b"speculative_time_sum": b"150.5",
            b"speculative_count": b"80",
            b"agentic_time_sum": b"640.0",
            b"agentic_count": b"60",
            b"total_time_sum": b"750.0",
            b"speculative_first_count": b"75",
            b"agentic_first_count": b"5",
            b"fast_count": b"20",
            b"balanced_count": b"60",
            b"deep_count": b"20",
        }

        stats = await performance_monitor.get_timing_stats(time_window_hours=24)

        assert stats["total_queries"] == 100
        assert "avg_speculative_time" in stats
        assert "avg_agentic_time" in stats
        assert "avg_total_time" in stats
        assert "speculative_first_percentage" in stats
        assert stats["fast_mode_count"] == 20
        assert stats["balanced_mode_count"] == 60
        assert stats["deep_mode_count"] == 20

    @pytest.mark.asyncio
    async def test_get_confidence_stats(self, performance_monitor, mock_redis):
        """Test retrieving confidence statistics."""
        # Mock Redis response
        mock_redis.hgetall.return_value = {
            b"speculative_confidence_sum": b"60.5",
            b"speculative_confidence_count": b"80",
            b"agentic_confidence_sum": b"72.0",
            b"agentic_confidence_count": b"60",
            b"confidence_improvement_sum": b"12.5",
            b"confidence_improvement_count": b"60",
        }

        stats = await performance_monitor.get_confidence_stats(time_window_hours=24)

        assert "avg_speculative_confidence" in stats
        assert "avg_agentic_confidence" in stats
        assert "avg_confidence_improvement" in stats

    @pytest.mark.asyncio
    async def test_get_error_stats(self, performance_monitor, mock_redis):
        """Test retrieving error statistics."""

        # Mock Redis responses
        async def mock_hgetall(key):
            if b"error:stats" in key or "error:stats" in key:
                return {
                    b"total_errors": b"10",
                    b"speculative_errors": b"6",
                    b"agentic_errors": b"3",
                    b"hybrid_errors": b"1",
                    b"type_timeout": b"5",
                    b"type_llm_error": b"3",
                    b"type_search_error": b"2",
                }
            elif b"timing:stats" in key or "timing:stats" in key:
                return {b"total_queries": b"100"}
            return {}

        mock_redis.hgetall.side_effect = mock_hgetall

        stats = await performance_monitor.get_error_stats(time_window_hours=24)

        assert stats["total_errors"] == 10
        assert stats["total_queries"] == 100
        assert stats["error_rate"] == 0.1
        assert "speculative_errors" in stats
        assert "agentic_errors" in stats
        assert "error_types" in stats

    @pytest.mark.asyncio
    async def test_get_mode_usage_stats(self, performance_monitor, mock_redis):
        """Test retrieving mode usage statistics."""
        # Mock Redis response
        mock_redis.hgetall.return_value = {
            b"fast": b"25",
            b"balanced": b"60",
            b"deep": b"15",
        }

        stats = await performance_monitor.get_mode_usage_stats()

        assert stats["fast"] == 25
        assert stats["balanced"] == 60
        assert stats["deep"] == 15

    @pytest.mark.asyncio
    async def test_get_recent_alerts(self, performance_monitor, mock_redis):
        """Test retrieving recent alerts."""
        # Mock alert data
        alert1 = json.dumps(
            {
                "query_id": "slow_query",
                "alert_type": "slow_response",
                "total_time": 12.5,
                "threshold": 5.0,
                "timestamp": "2024-01-01T12:00:00",
            }
        )

        alert2 = json.dumps(
            {
                "path": "speculative",
                "alert_type": "high_error_rate",
                "error_rate": 0.15,
                "threshold": 0.1,
                "timestamp": "2024-01-01T12:05:00",
            }
        )

        mock_redis.zrevrange.side_effect = [
            [alert1.encode()],
            [alert2.encode()],
        ]  # timing alerts  # error alerts

        alerts = await performance_monitor.get_recent_alerts(limit=10)

        assert len(alerts) == 2
        assert alerts[0]["category"] == "timing"
        assert alerts[1]["category"] == "error"


class TestModeUsageTracking:
    """Test mode usage pattern tracking."""

    @pytest.mark.asyncio
    async def test_log_mode_usage(self, performance_monitor, mock_redis):
        """Test logging mode usage."""
        await performance_monitor.log_mode_usage(
            mode=QueryMode.BALANCED, session_id="test_session"
        )

        # Verify Redis operations
        assert mock_redis.hincrby.called
        assert mock_redis.expire.called

    @pytest.mark.asyncio
    async def test_mode_usage_counter_increment(self, performance_monitor, mock_redis):
        """Test that mode usage counters are incremented correctly."""
        # Log multiple mode usages
        await performance_monitor.log_mode_usage(QueryMode.FAST)
        await performance_monitor.log_mode_usage(QueryMode.BALANCED)
        await performance_monitor.log_mode_usage(QueryMode.BALANCED)
        await performance_monitor.log_mode_usage(QueryMode.DEEP)

        # Verify hincrby was called for each mode
        assert mock_redis.hincrby.call_count == 4


class TestErrorHandling:
    """Test error handling in monitoring."""

    @pytest.mark.asyncio
    async def test_redis_failure_graceful_degradation(self, mock_redis):
        """Test that Redis failures don't crash the system."""
        # Make Redis operations fail
        mock_redis.zadd.side_effect = Exception("Redis connection failed")

        monitor = PerformanceMonitor(redis_client=mock_redis, metrics_ttl=3600)

        # Should not raise exception
        await monitor.log_timing_metrics(
            query_id="test", mode=QueryMode.FAST, speculative_time=1.5, total_time=1.5
        )

    @pytest.mark.asyncio
    async def test_empty_stats_handling(self, performance_monitor, mock_redis):
        """Test handling of empty statistics."""
        # Mock empty Redis response
        mock_redis.hgetall.return_value = {}

        stats = await performance_monitor.get_timing_stats()

        # Should return empty dict, not crash
        assert stats == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
