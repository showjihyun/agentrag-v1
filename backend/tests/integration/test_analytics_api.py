"""
Integration tests for Analytics API endpoints.

Tests analytics endpoint responses and performance reporting.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.main import app
from backend.services.performance_monitor import get_performance_monitor
from backend.models.hybrid import QueryMode, PathSource


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
async def mock_performance_monitor():
    """Create a mock PerformanceMonitor."""
    monitor = AsyncMock(spec=PerformanceMonitor)

    # Mock timing stats
    monitor.get_timing_stats.return_value = {
        "total_queries": 100,
        "time_window_hours": 24,
        "avg_speculative_time": 1.5,
        "avg_agentic_time": 8.0,
        "avg_total_time": 7.5,
        "speculative_first_percentage": 95.0,
        "agentic_first_percentage": 5.0,
        "fast_mode_count": 20,
        "balanced_mode_count": 60,
        "deep_mode_count": 20,
    }

    # Mock confidence stats
    monitor.get_confidence_stats.return_value = {
        "time_window_hours": 24,
        "avg_speculative_confidence": 0.75,
        "avg_agentic_confidence": 0.92,
        "avg_confidence_improvement": 0.17,
    }

    # Mock error stats
    monitor.get_error_stats.return_value = {
        "total_errors": 5,
        "total_queries": 100,
        "error_rate": 0.05,
        "time_window_hours": 24,
        "speculative_errors": 3,
        "speculative_error_rate": 0.03,
        "agentic_errors": 2,
        "agentic_error_rate": 0.02,
        "hybrid_errors": 0,
        "hybrid_error_rate": 0.0,
        "error_types": {"timeout": 3, "llm_error": 2},
    }

    # Mock mode usage stats
    monitor.get_mode_usage_stats.return_value = {"fast": 20, "balanced": 60, "deep": 20}

    # Mock alerts
    monitor.get_recent_alerts.return_value = [
        {
            "category": "timing",
            "alert_type": "slow_response",
            "timestamp": "2024-01-01T12:00:00",
            "query_id": "slow_query",
            "total_time": 12.5,
            "threshold": 5.0,
        },
        {
            "category": "error",
            "alert_type": "high_error_rate",
            "timestamp": "2024-01-01T12:05:00",
            "path": "speculative",
            "error_rate": 0.15,
            "threshold": 0.1,
        },
    ]

    return monitor


class TestTimingAnalyticsEndpoint:
    """Test /analytics/timing endpoint."""

    @patch("api.analytics.get_performance_monitor")
    def test_get_timing_analytics_success(
        self, mock_get_monitor, client, mock_performance_monitor
    ):
        """Test successful timing analytics retrieval."""
        mock_get_monitor.return_value = mock_performance_monitor

        response = client.get("/analytics/timing?time_window_hours=24")

        assert response.status_code == 200
        data = response.json()

        assert data["total_queries"] == 100
        assert data["time_window_hours"] == 24
        assert data["avg_speculative_time"] == 1.5
        assert data["avg_agentic_time"] == 8.0
        assert data["speculative_first_percentage"] == 95.0
        assert data["fast_mode_count"] == 20
        assert data["balanced_mode_count"] == 60
        assert data["deep_mode_count"] == 20

    @patch("api.analytics.get_performance_monitor")
    def test_get_timing_analytics_custom_window(
        self, mock_get_monitor, client, mock_performance_monitor
    ):
        """Test timing analytics with custom time window."""
        mock_get_monitor.return_value = mock_performance_monitor

        response = client.get("/analytics/timing?time_window_hours=168")

        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data

    @patch("api.analytics.get_performance_monitor")
    def test_get_timing_analytics_empty_data(self, mock_get_monitor, client):
        """Test timing analytics with no data."""
        monitor = AsyncMock(spec=PerformanceMonitor)
        monitor.get_timing_stats.return_value = {}
        mock_get_monitor.return_value = monitor

        response = client.get("/analytics/timing")

        assert response.status_code == 200
        data = response.json()
        assert data["total_queries"] == 0


class TestConfidenceAnalyticsEndpoint:
    """Test /analytics/confidence endpoint."""

    @patch("api.analytics.get_performance_monitor")
    def test_get_confidence_analytics_success(
        self, mock_get_monitor, client, mock_performance_monitor
    ):
        """Test successful confidence analytics retrieval."""
        mock_get_monitor.return_value = mock_performance_monitor

        response = client.get("/analytics/confidence?time_window_hours=24")

        assert response.status_code == 200
        data = response.json()

        assert data["time_window_hours"] == 24
        assert data["avg_speculative_confidence"] == 0.75
        assert data["avg_agentic_confidence"] == 0.92
        assert data["avg_confidence_improvement"] == 0.17

    @patch("api.analytics.get_performance_monitor")
    def test_get_confidence_analytics_empty_data(self, mock_get_monitor, client):
        """Test confidence analytics with no data."""
        monitor = AsyncMock(spec=PerformanceMonitor)
        monitor.get_confidence_stats.return_value = {}
        mock_get_monitor.return_value = monitor

        response = client.get("/analytics/confidence")

        assert response.status_code == 200
        data = response.json()
        assert data["time_window_hours"] == 24


class TestErrorAnalyticsEndpoint:
    """Test /analytics/errors endpoint."""

    @patch("api.analytics.get_performance_monitor")
    def test_get_error_analytics_success(
        self, mock_get_monitor, client, mock_performance_monitor
    ):
        """Test successful error analytics retrieval."""
        mock_get_monitor.return_value = mock_performance_monitor

        response = client.get("/analytics/errors?time_window_hours=24")

        assert response.status_code == 200
        data = response.json()

        assert data["total_errors"] == 5
        assert data["total_queries"] == 100
        assert data["error_rate"] == 0.05
        assert data["speculative_errors"] == 3
        assert data["agentic_errors"] == 2
        assert "error_types" in data
        assert data["error_types"]["timeout"] == 3

    @patch("api.analytics.get_performance_monitor")
    def test_get_error_analytics_zero_errors(self, mock_get_monitor, client):
        """Test error analytics with zero errors."""
        monitor = AsyncMock(spec=PerformanceMonitor)
        monitor.get_error_stats.return_value = {
            "total_errors": 0,
            "total_queries": 100,
            "error_rate": 0.0,
            "time_window_hours": 24,
        }
        mock_get_monitor.return_value = monitor

        response = client.get("/analytics/errors")

        assert response.status_code == 200
        data = response.json()
        assert data["total_errors"] == 0
        assert data["error_rate"] == 0.0


class TestModeUsageAnalyticsEndpoint:
    """Test /analytics/mode-usage endpoint."""

    @patch("api.analytics.get_performance_monitor")
    def test_get_mode_usage_analytics_success(
        self, mock_get_monitor, client, mock_performance_monitor
    ):
        """Test successful mode usage analytics retrieval."""
        mock_get_monitor.return_value = mock_performance_monitor

        response = client.get("/analytics/mode-usage")

        assert response.status_code == 200
        data = response.json()

        assert data["fast"] == 20
        assert data["balanced"] == 60
        assert data["deep"] == 20
        assert data["total"] == 100

    @patch("api.analytics.get_performance_monitor")
    def test_get_mode_usage_analytics_empty(self, mock_get_monitor, client):
        """Test mode usage analytics with no data."""
        monitor = AsyncMock(spec=PerformanceMonitor)
        monitor.get_mode_usage_stats.return_value = {}
        mock_get_monitor.return_value = monitor

        response = client.get("/analytics/mode-usage")

        assert response.status_code == 200
        data = response.json()
        assert data["fast"] == 0
        assert data["balanced"] == 0
        assert data["deep"] == 0
        assert data["total"] == 0


class TestPathEffectivenessEndpoint:
    """Test /analytics/path-effectiveness endpoint."""

    @patch("api.analytics.get_performance_monitor")
    def test_get_path_effectiveness_report_success(
        self, mock_get_monitor, client, mock_performance_monitor
    ):
        """Test successful path effectiveness report retrieval."""
        mock_get_monitor.return_value = mock_performance_monitor

        response = client.get("/analytics/path-effectiveness?time_window_hours=24")

        assert response.status_code == 200
        data = response.json()

        # Check all sections are present
        assert "timing" in data
        assert "confidence" in data
        assert "errors" in data
        assert "mode_usage" in data
        assert "insights" in data

        # Check timing section
        assert data["timing"]["total_queries"] == 100
        assert data["timing"]["avg_speculative_time"] == 1.5

        # Check confidence section
        assert data["confidence"]["avg_speculative_confidence"] == 0.75

        # Check errors section
        assert data["errors"]["total_errors"] == 5

        # Check mode usage section
        assert data["mode_usage"]["total"] == 100

        # Check insights
        assert isinstance(data["insights"], list)
        assert len(data["insights"]) > 0

    @patch("api.analytics.get_performance_monitor")
    def test_path_effectiveness_insights_generation(
        self, mock_get_monitor, client, mock_performance_monitor
    ):
        """Test that insights are generated correctly."""
        mock_get_monitor.return_value = mock_performance_monitor

        response = client.get("/analytics/path-effectiveness")

        assert response.status_code == 200
        data = response.json()

        insights = data["insights"]

        # Should have insights about speedup
        speedup_insights = [i for i in insights if "faster" in i.lower()]
        assert len(speedup_insights) > 0

        # Should have insights about confidence improvement
        confidence_insights = [i for i in insights if "confidence" in i.lower()]
        assert len(confidence_insights) > 0


class TestAlertsEndpoint:
    """Test /analytics/alerts endpoint."""

    @patch("api.analytics.get_performance_monitor")
    def test_get_recent_alerts_success(
        self, mock_get_monitor, client, mock_performance_monitor
    ):
        """Test successful alerts retrieval."""
        mock_get_monitor.return_value = mock_performance_monitor

        response = client.get("/analytics/alerts?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2

        # Check first alert (timing)
        assert data[0]["category"] == "timing"
        assert data[0]["alert_type"] == "slow_response"
        assert "details" in data[0]

        # Check second alert (error)
        assert data[1]["category"] == "error"
        assert data[1]["alert_type"] == "high_error_rate"

    @patch("api.analytics.get_performance_monitor")
    def test_get_recent_alerts_custom_limit(
        self, mock_get_monitor, client, mock_performance_monitor
    ):
        """Test alerts retrieval with custom limit."""
        mock_get_monitor.return_value = mock_performance_monitor

        response = client.get("/analytics/alerts?limit=5")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch("api.analytics.get_performance_monitor")
    def test_get_recent_alerts_empty(self, mock_get_monitor, client):
        """Test alerts retrieval with no alerts."""
        monitor = AsyncMock(spec=PerformanceMonitor)
        monitor.get_recent_alerts.return_value = []
        mock_get_monitor.return_value = monitor

        response = client.get("/analytics/alerts")

        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestErrorHandling:
    """Test error handling in analytics endpoints."""

    @patch("api.analytics.get_performance_monitor")
    def test_timing_analytics_error_handling(self, mock_get_monitor, client):
        """Test error handling in timing analytics endpoint."""
        monitor = AsyncMock(spec=PerformanceMonitor)
        monitor.get_timing_stats.side_effect = Exception("Database error")
        mock_get_monitor.return_value = monitor

        response = client.get("/analytics/timing")

        assert response.status_code == 500
        assert "Failed to retrieve timing analytics" in response.json()["detail"]

    @patch("api.analytics.get_performance_monitor")
    def test_confidence_analytics_error_handling(self, mock_get_monitor, client):
        """Test error handling in confidence analytics endpoint."""
        monitor = AsyncMock(spec=PerformanceMonitor)
        monitor.get_confidence_stats.side_effect = Exception("Database error")
        mock_get_monitor.return_value = monitor

        response = client.get("/analytics/confidence")

        assert response.status_code == 500
        assert "Failed to retrieve confidence analytics" in response.json()["detail"]


class TestQueryParameterValidation:
    """Test query parameter validation."""

    def test_timing_analytics_invalid_time_window(self, client):
        """Test timing analytics with invalid time window."""
        # Too small
        response = client.get("/analytics/timing?time_window_hours=0")
        assert response.status_code == 422

        # Too large
        response = client.get("/analytics/timing?time_window_hours=200")
        assert response.status_code == 422

    def test_alerts_invalid_limit(self, client):
        """Test alerts endpoint with invalid limit."""
        # Too small
        response = client.get("/analytics/alerts?limit=0")
        assert response.status_code == 422

        # Too large
        response = client.get("/analytics/alerts?limit=200")
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
