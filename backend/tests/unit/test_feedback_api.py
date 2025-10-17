"""
Unit tests for Feedback API.

Tests feedback submission, retrieval, and statistics.
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from backend.api.feedback import (
    FeedbackType,
    FeedbackCategory,
    FeedbackRequest,
    get_all_feedback,
    clear_feedback_storage,
)


@pytest.fixture
def client():
    """Create test client."""
    from main import app

    return TestClient(app)


@pytest.fixture(autouse=True)
async def clear_storage():
    """Clear feedback storage before each test."""
    await clear_feedback_storage()
    yield
    await clear_feedback_storage()


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

        assert response.status_code == 200
        data = response.json()

        assert "feedback_id" in data
        assert data["status"] == "success"
        assert "timestamp" in data

        # Verify storage
        storage = await get_all_feedback()
        assert len(storage) == 1
        assert storage[0]["feedback_type"] == "thumbs_up"

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

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"

        # Verify storage
        storage = await get_all_feedback()
        assert len(storage) == 1
        assert storage[0]["feedback_type"] == "thumbs_down"
        assert "accuracy" in storage[0]["categories"]
        assert "completeness" in storage[0]["categories"]
        assert storage[0]["comment"] == "Response was incomplete and had errors"

    def test_submit_feedback_without_optional_fields(self, client):
        """Test submitting minimal feedback."""
        request_data = {"query_id": "query_789", "feedback_type": "thumbs_up"}

        response = client.post("/api/feedback/", json=request_data)

        assert response.status_code == 200

        # Verify storage
        storage = await get_all_feedback()
        assert len(storage) == 1
        assert storage[0]["session_id"] is None
        assert storage[0]["comment"] is None


class TestFeedbackStats:
    """Test feedback statistics endpoint."""

    def test_get_stats_empty(self, client):
        """Test getting stats with no feedback."""
        response = client.get("/api/feedback/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total_feedback"] == 0
        assert data["thumbs_up"] == 0
        assert data["thumbs_down"] == 0
        assert data["satisfaction_rate"] == 0.0

    def test_get_stats_with_feedback(self, client):
        """Test getting stats with multiple feedback entries."""
        # Submit multiple feedback entries
        feedbacks = [
            {"query_id": "q1", "feedback_type": "thumbs_up", "mode_used": "fast"},
            {"query_id": "q2", "feedback_type": "thumbs_up", "mode_used": "fast"},
            {
                "query_id": "q3",
                "feedback_type": "thumbs_down",
                "categories": ["accuracy"],
                "mode_used": "balanced",
            },
            {"query_id": "q4", "feedback_type": "thumbs_up", "mode_used": "deep"},
        ]

        for feedback in feedbacks:
            client.post("/api/feedback/", json=feedback)

        # Get stats
        response = client.get("/api/feedback/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total_feedback"] == 4
        assert data["thumbs_up"] == 3
        assert data["thumbs_down"] == 1
        assert data["satisfaction_rate"] == 0.75

        # Check category breakdown
        assert data["category_breakdown"]["accuracy"] == 1

        # Check mode breakdown
        assert data["mode_breakdown"]["fast"]["thumbs_up"] == 2
        assert data["mode_breakdown"]["balanced"]["thumbs_down"] == 1
        assert data["mode_breakdown"]["deep"]["thumbs_up"] == 1

    def test_get_stats_filtered_by_mode(self, client):
        """Test getting stats filtered by mode."""
        # Submit feedback for different modes
        feedbacks = [
            {"query_id": "q1", "feedback_type": "thumbs_up", "mode_used": "fast"},
            {"query_id": "q2", "feedback_type": "thumbs_down", "mode_used": "fast"},
            {"query_id": "q3", "feedback_type": "thumbs_up", "mode_used": "balanced"},
        ]

        for feedback in feedbacks:
            client.post("/api/feedback/", json=feedback)

        # Get stats for fast mode only
        response = client.get("/api/feedback/stats?mode=fast")

        assert response.status_code == 200
        data = response.json()

        assert data["total_feedback"] == 2
        assert data["thumbs_up"] == 1
        assert data["thumbs_down"] == 1
        assert data["satisfaction_rate"] == 0.5


class TestFeedbackRetrieval:
    """Test feedback retrieval endpoints."""

    def test_get_query_feedback(self, client):
        """Test getting feedback for a specific query."""
        query_id = "query_test_123"

        # Submit multiple feedback for same query
        feedbacks = [
            {"query_id": query_id, "feedback_type": "thumbs_up"},
            {
                "query_id": query_id,
                "feedback_type": "thumbs_down",
                "categories": ["speed"],
            },
            {"query_id": "other_query", "feedback_type": "thumbs_up"},
        ]

        for feedback in feedbacks:
            client.post("/api/feedback/", json=feedback)

        # Get feedback for specific query
        response = client.get(f"/api/feedback/{query_id}")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        assert all(item["query_id"] == query_id for item in data)

    def test_get_query_feedback_not_found(self, client):
        """Test getting feedback for non-existent query."""
        response = client.get("/api/feedback/nonexistent_query")

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 0


class TestFeedbackDeletion:
    """Test feedback deletion endpoint."""

    def test_delete_feedback(self, client):
        """Test deleting a feedback entry."""
        # Submit feedback
        request_data = {"query_id": "query_delete", "feedback_type": "thumbs_up"}

        response = client.post("/api/feedback/", json=request_data)
        feedback_id = response.json()["feedback_id"]

        # Verify it exists
        storage = await get_all_feedback()
        assert len(storage) == 1

        # Delete it
        response = client.delete(f"/api/feedback/{feedback_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify it's deleted
        storage = await get_all_feedback()
        assert len(storage) == 0

    def test_delete_nonexistent_feedback(self, client):
        """Test deleting non-existent feedback."""
        response = client.delete("/api/feedback/nonexistent_id")

        assert response.status_code == 404


class TestFeedbackValidation:
    """Test feedback request validation."""

    def test_invalid_feedback_type(self, client):
        """Test submitting feedback with invalid type."""
        request_data = {"query_id": "query_123", "feedback_type": "invalid_type"}

        response = client.post("/api/feedback/", json=request_data)

        assert response.status_code == 422

    def test_invalid_category(self, client):
        """Test submitting feedback with invalid category."""
        request_data = {
            "query_id": "query_123",
            "feedback_type": "thumbs_down",
            "categories": ["invalid_category"],
        }

        response = client.post("/api/feedback/", json=request_data)

        assert response.status_code == 422

    def test_comment_too_long(self, client):
        """Test submitting feedback with comment exceeding max length."""
        request_data = {
            "query_id": "query_123",
            "feedback_type": "thumbs_down",
            "comment": "x" * 1001,  # Exceeds 1000 char limit
        }

        response = client.post("/api/feedback/", json=request_data)

        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
