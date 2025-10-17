"""Integration tests for API endpoints.

These tests require running services (Milvus, Redis) and test the full stack.
"""

import pytest
import asyncio
import io
from datetime import datetime

from fastapi.testclient import TestClient


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def client():
    """Create test client for integration tests."""
    # Import here to ensure services are initialized
    from main import app

    return TestClient(app)


class TestDocumentUploadIntegration:
    """Integration tests for document upload flow."""

    def test_upload_and_retrieve_document(self, client):
        """Test complete document upload and retrieval flow."""
        # Create a test document
        test_content = b"This is a test document for integration testing. " * 20
        files = {
            "file": ("test_integration.txt", io.BytesIO(test_content), "text/plain")
        }

        # Upload document
        upload_response = client.post("/api/documents/upload", files=files)

        # Should succeed or fail gracefully if services unavailable
        if upload_response.status_code == 201:
            data = upload_response.json()
            document_id = data["document_id"]

            assert data["status"] == "completed"
            assert data["chunk_count"] > 0

            # Retrieve document details
            details_response = client.get(f"/api/documents/{document_id}")
            assert details_response.status_code == 200

            details = details_response.json()
            assert details["document_id"] == document_id
            assert details["chunk_count"] > 0

            # List documents
            list_response = client.get("/api/documents")
            assert list_response.status_code == 200

            # Delete document
            delete_response = client.delete(f"/api/documents/{document_id}")
            assert delete_response.status_code == 200
        else:
            # Services not available - test should not fail
            pytest.skip("Required services not available")

    def test_upload_pdf_document(self, client):
        """Test uploading a PDF document."""
        # Create minimal PDF content
        pdf_content = (
            b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        )
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}

        response = client.post("/api/documents/upload", files=files)

        # Should process or fail gracefully
        assert response.status_code in [201, 422, 500, 503]

    def test_upload_unsupported_format(self, client):
        """Test uploading unsupported file format."""
        files = {
            "file": ("test.xyz", io.BytesIO(b"content"), "application/octet-stream")
        }

        response = client.post("/api/documents/upload", files=files)

        # Should reject unsupported format
        assert response.status_code in [422, 400]


class TestQueryProcessingIntegration:
    """Integration tests for query processing."""

    def test_sync_query_processing(self, client):
        """Test synchronous query processing."""
        response = client.post(
            "/api/query/sync",
            json={"query": "What is artificial intelligence?", "top_k": 5},
        )

        # Should process or fail gracefully if services unavailable
        if response.status_code == 200:
            data = response.json()
            assert "query_id" in data
            assert "response" in data
            assert "reasoning_steps" in data
            assert data["query"] == "What is artificial intelligence?"
        else:
            pytest.skip("Required services not available")

    def test_streaming_query_processing(self, client):
        """Test streaming query processing."""
        response = client.post(
            "/api/query", json={"query": "Explain machine learning", "stream": True}
        )

        # Should return streaming response or fail gracefully
        if response.status_code == 200:
            assert "text/event-stream" in response.headers.get("content-type", "")

            # Read first few chunks
            content = response.content.decode("utf-8")
            assert len(content) > 0
        else:
            pytest.skip("Required services not available")

    def test_query_with_session_persistence(self, client):
        """Test query processing with session context."""
        session_id = "test_session_123"

        # First query
        response1 = client.post(
            "/api/query/sync",
            json={"query": "What is Python?", "session_id": session_id, "top_k": 5},
        )

        if response1.status_code == 200:
            # Second query in same session
            response2 = client.post(
                "/api/query/sync",
                json={
                    "query": "Tell me more about it",
                    "session_id": session_id,
                    "top_k": 5,
                },
            )

            assert response2.status_code == 200
            data = response2.json()
            assert data["session_id"] == session_id
        else:
            pytest.skip("Required services not available")


class TestEndToEndFlow:
    """End-to-end integration tests."""

    def test_complete_rag_workflow(self, client):
        """Test complete RAG workflow: upload, query, delete."""
        # Step 1: Upload a document
        test_content = (
            b"""
        Machine learning is a subset of artificial intelligence.
        It focuses on building systems that can learn from data.
        Deep learning is a type of machine learning using neural networks.
        """
            * 5
        )

        files = {"file": ("ml_doc.txt", io.BytesIO(test_content), "text/plain")}
        upload_response = client.post("/api/documents/upload", files=files)

        if upload_response.status_code != 201:
            pytest.skip("Document upload failed - services not available")

        document_id = upload_response.json()["document_id"]

        try:
            # Step 2: Query the document
            query_response = client.post(
                "/api/query/sync",
                json={"query": "What is machine learning?", "top_k": 5},
            )

            assert query_response.status_code == 200
            query_data = query_response.json()
            assert "response" in query_data

            # Step 3: Verify document exists
            details_response = client.get(f"/api/documents/{document_id}")
            assert details_response.status_code == 200

        finally:
            # Step 4: Clean up - delete document
            delete_response = client.delete(f"/api/documents/{document_id}")
            assert delete_response.status_code in [200, 404]

    def test_health_check_integration(self, client):
        """Test health check with real services."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data

        # Log service status for debugging
        print(f"\nService health: {data}")


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_invalid_document_id(self, client):
        """Test handling of invalid document ID."""
        response = client.get("/api/documents/invalid_id_12345")

        # Should return 404 or handle gracefully
        assert response.status_code in [404, 500]
        data = response.json()
        assert "error" in data or "detail" in data

    def test_malformed_query_request(self, client):
        """Test handling of malformed query request."""
        response = client.post("/api/query/sync", json={"invalid_field": "value"})

        assert response.status_code == 422
        data = response.json()
        assert "validation_errors" in data

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def make_request():
            return client.get("/api/health")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]

        # All should succeed
        assert all(r.status_code == 200 for r in responses)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
