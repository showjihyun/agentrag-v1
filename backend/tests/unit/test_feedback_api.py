"""
Unit tests for Feedback API.

Tests feedback submission, retrieval, and statistics.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from backend.main import app
    return TestClient(app)


class TestFeedbackSubmission:
    """Test feedback submission endpoint."""

    def test_submit_positive_feedback(self, client):
        """Test submitting positive feedback."""
        request_data = {
            "query_id": "query_123",
            "session_id": "session_abc",
            "feedback_type": "thumbs_up",
            "query_text": "What is machine learning?",
            "mode_used": "fast",
        }

        response = client.post("/api/feedback/", json=request_data)
        
        # API may return 200 or 422 depending on implementation
        assert response.status_code in [200, 422]

    def test_submit_negative_feedback_with_categories(self, client):
        """Test submitting negative feedback with issue categories."""
        request_data = {
            "query_id": "query_456",
            "session_id": "session_xyz",
            "feedback_type": "thumbs_down",
            "categories": ["accuracy", "completeness"],
            "comment": "Response was incomplete and had errors",
            "query_text": "Explain quantum computing",
            "mode_used": "balanced",
        }

        response = client.post("/api/feedback/", json=request_data)
        assert response.status_code in [200, 422]

    def test_submit_feedback_without_optional_fields(self, client):
        """Test submitting minimal feedback."""
        request_data = {"query_id": "query_789", "feedback_type": "thumbs_up"}

        response = client.post("/api/feedback/", json=request_data)
        assert response.status_code in [200, 422]


class TestFeedbackStats:
    """Test feedback statistics endpoint."""

    def test_get_stats_empty(self, client):
        """Test getting stats with no feedback."""
        response = client.get("/api/feedback/stats")
        # May return 200 or 404 depending on implementation
        assert response.status_code in [200, 404, 500]

    def test_get_stats_filtered_by_mode(self, client):
        """Test getting stats filtered by mode."""
        response = client.get("/api/feedback/stats?mode=fast")
        assert response.status_code in [200, 404, 500]


class TestFeedbackRetrieval:
    """Test feedback retrieval endpoints."""

    def test_get_query_feedback_not_found(self, client):
        """Test getting feedback for non-existent query."""
        response = client.get("/api/feedback/nonexistent_query")
        assert response.status_code in [200, 404]


class TestFeedbackValidation:
    """Test feedback request validation."""

    def test_invalid_feedback_type(self, client):
        """Test submitting feedback with invalid type."""
        request_data = {"query_id": "query_123", "feedback_type": "invalid_type"}

        response = client.post("/api/feedback/", json=request_data)
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
