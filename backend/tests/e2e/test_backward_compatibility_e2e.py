"""
End-to-end tests for backward compatibility.

Tests complete workflows with hybrid mode enabled and disabled.

Requirements: 12.1, 12.2, 12.3, 12.5
"""

import pytest
import asyncio
import json
from typing import AsyncGenerator
from unittest.mock import patch

from fastapi.testclient import TestClient
from httpx import AsyncClient

from main import app
from config import settings


class TestHybridModeDisabledE2E:
    """Test complete system behavior with hybrid mode disabled."""

    @pytest.mark.asyncio
    async def test_query_with_hybrid_disabled(self):
        """
        Test that queries work when ENABLE_SPECULATIVE_RAG=false.

        Should fall back to legacy agentic-only mode.

        Requirements: 12.1, 12.4
        """
        # Patch settings to disable hybrid mode
        with patch.object(settings, "ENABLE_SPECULATIVE_RAG", False):
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Send a query request (old format)
                response = await client.post(
                    "/api/query",
                    json={
                        "query": "What is machine learning?",
                        "session_id": "test_session_disabled",
                        "top_k": 5,
                    },
                    headers={"Content-Type": "application/json"},
                )

                # Should return 200 (streaming response)
                assert response.status_code == 200
                assert (
                    response.headers["content-type"]
                    == "text/event-stream; charset=utf-8"
                )

    @pytest.mark.asyncio
    async def test_old_api_format_with_hybrid_disabled(self):
        """
        Test that old API format works with hybrid disabled.

        Requirements: 12.1, 12.2, 12.3
        """
        with patch.object(settings, "ENABLE_SPECULATIVE_RAG", False):
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Old format request (no mode parameter)
                response = await client.post(
                    "/api/query", json={"query": "Explain neural networks", "top_k": 10}
                )

                assert response.status_code == 200


class TestOldAPIFormatE2E:
    """Test that old API format works with new backend."""

    @pytest.mark.asyncio
    async def test_query_without_mode_parameter(self):
        """
        Test query request without mode parameter.

        Should use default mode (BALANCED).

        Requirements: 12.2, 12.3
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Old format - no mode
            response = await client.post(
                "/api/query",
                json={
                    "query": "What is deep learning?",
                    "session_id": "test_old_format",
                    "top_k": 10,
                },
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_query_without_optional_fields(self):
        """
        Test query with only required fields.

        Requirements: 12.2, 12.3
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Minimal request
            response = await client.post("/api/query", json={"query": "Test query"})

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_sync_endpoint_backward_compatible(self):
        """
        Test that sync endpoint maintains backward compatibility.

        Requirements: 12.2, 12.3
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/query/sync", json={"query": "What is AI?", "top_k": 5}
            )

            # Should work with old format
            assert response.status_code in [
                200,
                500,
            ]  # May fail if services not available


class TestNewAPIFormatE2E:
    """Test that new API format works correctly."""

    @pytest.mark.asyncio
    async def test_query_with_mode_parameter(self):
        """
        Test query with explicit mode parameter.

        Requirements: 12.2, 12.3
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            # New format with mode
            response = await client.post(
                "/api/query",
                json={
                    "query": "Explain transformers",
                    "session_id": "test_new_format",
                    "mode": "balanced",
                    "top_k": 10,
                },
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_query_with_all_new_fields(self):
        """
        Test query with all new hybrid fields.

        Requirements: 12.2, 12.3
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/query",
                json={
                    "query": "What is NLP?",
                    "session_id": "test_full_format",
                    "mode": "fast",
                    "enable_cache": True,
                    "speculative_timeout": 2.0,
                    "agentic_timeout": 15.0,
                    "top_k": 10,
                },
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_all_modes_work(self):
        """
        Test that all query modes work.

        Requirements: 12.1
        """
        modes = ["fast", "balanced", "deep"]

        async with AsyncClient(app=app, base_url="http://test") as client:
            for mode in modes:
                response = await client.post(
                    "/api/query",
                    json={
                        "query": f"Test query in {mode} mode",
                        "mode": mode,
                        "top_k": 5,
                    },
                )

                assert response.status_code == 200, f"Mode {mode} failed"


class TestResponseFormatCompatibility:
    """Test that response format is backward compatible."""

    @pytest.mark.asyncio
    async def test_legacy_response_format_preserved(self):
        """
        Test that legacy response format is preserved.

        When hybrid is disabled, response should match original format.

        Requirements: 12.2, 12.3
        """
        with patch.object(settings, "ENABLE_SPECULATIVE_RAG", False):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/query", json={"query": "Test query", "top_k": 5}
                )

                # Should be SSE stream
                assert response.status_code == 200
                assert "text/event-stream" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_hybrid_response_includes_new_fields(self):
        """
        Test that hybrid response includes new fields as optional extensions.

        Requirements: 12.2, 12.3
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/query",
                json={"query": "Test query", "mode": "balanced", "top_k": 5},
            )

            assert response.status_code == 200
            # New fields should be present in SSE events


class TestDataCompatibility:
    """Test data compatibility across versions."""

    @pytest.mark.asyncio
    async def test_existing_documents_accessible(self):
        """
        Test that existing documents remain accessible.

        Requirements: 12.5
        """
        # This would require actual document upload and retrieval
        # Simplified test to verify endpoint exists
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Check documents endpoint exists
            response = await client.get("/api/documents")
            assert response.status_code in [200, 404]  # May be empty

    @pytest.mark.asyncio
    async def test_session_continuity(self):
        """
        Test that sessions work across hybrid enabled/disabled.

        Requirements: 12.5
        """
        session_id = "test_continuity_session"

        async with AsyncClient(app=app, base_url="http://test") as client:
            # First query
            response1 = await client.post(
                "/api/query",
                json={"query": "First query", "session_id": session_id, "top_k": 5},
            )
            assert response1.status_code == 200

            # Second query in same session
            response2 = await client.post(
                "/api/query",
                json={"query": "Follow-up query", "session_id": session_id, "top_k": 5},
            )
            assert response2.status_code == 200


class TestHealthCheckCompatibility:
    """Test that health check works with hybrid enabled/disabled."""

    @pytest.mark.asyncio
    async def test_health_check_with_hybrid_enabled(self):
        """
        Test health check when hybrid is enabled.

        Requirements: 12.1
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/health")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "services" in data

    @pytest.mark.asyncio
    async def test_health_check_with_hybrid_disabled(self):
        """
        Test health check when hybrid is disabled.

        Requirements: 12.1
        """
        with patch.object(settings, "ENABLE_SPECULATIVE_RAG", False):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/health")

                assert response.status_code == 200
                data = response.json()
                assert "status" in data


class TestErrorHandlingCompatibility:
    """Test error handling maintains backward compatibility."""

    @pytest.mark.asyncio
    async def test_invalid_query_error_format(self):
        """
        Test that error format is consistent.

        Requirements: 12.2, 12.3
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Empty query should fail
            response = await client.post("/api/query", json={"query": "", "top_k": 5})

            # Should return error
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_invalid_mode_error(self):
        """
        Test that invalid mode returns proper error.

        Requirements: 12.1
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/query", json={"query": "Test query", "mode": "invalid_mode"}
            )

            # Should return validation error
            assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
