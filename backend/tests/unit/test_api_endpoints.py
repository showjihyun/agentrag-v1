"""Unit tests for API endpoints."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import json

from fastapi.testclient import TestClient
from fastapi import UploadFile
import io


@pytest.fixture
def mock_services():
    """Mock all service dependencies."""
    with (
        patch("main.embedding_service") as mock_embed,
        patch("main.milvus_manager") as mock_milvus,
        patch("main.llm_manager") as mock_llm,
        patch("main.document_processor") as mock_doc_proc,
        patch("main.memory_manager") as mock_memory,
        patch("main.aggregator_agent") as mock_agent,
        patch("main.redis_client") as mock_redis,
    ):
        # Configure mocks
        mock_embed.dimension = 384
        mock_milvus.dimension = 384

        yield {
            "embedding": mock_embed,
            "milvus": mock_milvus,
            "llm": mock_llm,
            "doc_processor": mock_doc_proc,
            "memory": mock_memory,
            "agent": mock_agent,
            "redis": mock_redis,
        }


@pytest.fixture
def client(mock_services):
    """Create test client with mocked services."""
    from main import app

    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_success(self, client, mock_services):
        """Test health check returns healthy status."""
        # Configure Redis mock
        mock_services["redis"].ping = AsyncMock()

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data


class TestDocumentEndpoints:
    """Tests for document management endpoints."""

    def test_upload_document_success(self, client, mock_services):
        """Test successful document upload."""
        # Mock ingestion service
        with patch("api.documents.DocumentIngestionService") as MockIngestion:
            mock_ingestion = MockIngestion.return_value
            mock_ingestion.ingest_document = AsyncMock(
                return_value={
                    "document_id": "doc123",
                    "filename": "test.pdf",
                    "status": "completed",
                    "chunk_count": 10,
                    "processing_time_ms": 1500.0,
                    "metadata": {},
                    "error": None,
                }
            )

            # Create test file
            file_content = b"Test PDF content"
            files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

            response = client.post("/api/documents/upload", files=files)

            assert response.status_code == 201
            data = response.json()
            assert data["document_id"] == "doc123"
            assert data["filename"] == "test.pdf"
            assert data["status"] == "completed"
            assert data["chunk_count"] == 10

    def test_upload_document_empty_file(self, client, mock_services):
        """Test upload with empty file."""
        files = {"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}

        response = client.post("/api/documents/upload", files=files)

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_document_too_large(self, client, mock_services):
        """Test upload with file exceeding size limit."""
        # Create file larger than 50MB
        large_content = b"x" * (51 * 1024 * 1024)
        files = {"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")}

        response = client.post("/api/documents/upload", files=files)

        assert response.status_code == 413
        assert "exceeds" in response.json()["detail"].lower()

    def test_upload_document_processing_failed(self, client, mock_services):
        """Test upload when document processing fails."""
        with patch("api.documents.DocumentIngestionService") as MockIngestion:
            mock_ingestion = MockIngestion.return_value
            mock_ingestion.ingest_document = AsyncMock(
                return_value={
                    "document_id": None,
                    "filename": "test.pdf",
                    "status": "failed",
                    "chunk_count": 0,
                    "processing_time_ms": 100.0,
                    "metadata": {},
                    "error": "Unsupported file format",
                }
            )

            file_content = b"Test content"
            files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}

            response = client.post("/api/documents/upload", files=files)

            assert response.status_code == 422
            assert "Unsupported file format" in response.json()["detail"]

    def test_list_documents_success(self, client, mock_services):
        """Test listing documents."""
        # Mock Milvus search
        mock_result = Mock()
        mock_result.metadata = {
            "document_id": "doc123",
            "document_name": "test.pdf",
            "file_type": "pdf",
            "upload_date": "2024-01-01T12:00:00",
        }

        mock_services["milvus"].search = AsyncMock(return_value=[mock_result])
        mock_services["milvus"].dimension = 384

        response = client.get("/api/documents")

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data

    def test_list_documents_with_pagination(self, client, mock_services):
        """Test listing documents with pagination."""
        mock_services["milvus"].search = AsyncMock(return_value=[])
        mock_services["milvus"].dimension = 384

        response = client.get("/api/documents?limit=10&offset=20")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["documents"], list)

    def test_get_document_details_success(self, client, mock_services):
        """Test getting document details."""
        with patch("api.documents.DocumentIngestionService") as MockIngestion:
            mock_ingestion = MockIngestion.return_value
            mock_ingestion.get_document_chunks = AsyncMock(
                return_value=[
                    {
                        "id": "chunk1",
                        "document_id": "doc123",
                        "document_name": "test.pdf",
                        "file_type": "pdf",
                        "upload_date": "2024-01-01T12:00:00",
                        "text": "Test content",
                        "chunk_index": 0,
                        "score": 0.95,
                    }
                ]
            )

            response = client.get("/api/documents/doc123")

            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == "doc123"
            assert data["chunk_count"] == 1

    def test_get_document_details_not_found(self, client, mock_services):
        """Test getting details for non-existent document."""
        with patch("api.documents.DocumentIngestionService") as MockIngestion:
            mock_ingestion = MockIngestion.return_value
            mock_ingestion.get_document_chunks = AsyncMock(return_value=[])

            response = client.get("/api/documents/nonexistent")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_get_document_details_with_chunks(self, client, mock_services):
        """Test getting document details with chunks included."""
        with patch("api.documents.DocumentIngestionService") as MockIngestion:
            mock_ingestion = MockIngestion.return_value
            mock_ingestion.get_document_chunks = AsyncMock(
                return_value=[
                    {
                        "id": "chunk1",
                        "document_id": "doc123",
                        "document_name": "test.pdf",
                        "file_type": "pdf",
                        "upload_date": "2024-01-01T12:00:00",
                        "text": "Test content",
                        "chunk_index": 0,
                        "score": 0.95,
                    }
                ]
            )

            response = client.get("/api/documents/doc123?include_chunks=true")

            assert response.status_code == 200
            data = response.json()
            assert len(data["chunks"]) > 0

    def test_delete_document_success(self, client, mock_services):
        """Test successful document deletion."""
        with patch("api.documents.DocumentIngestionService") as MockIngestion:
            mock_ingestion = MockIngestion.return_value
            mock_ingestion.delete_document = AsyncMock(
                return_value={
                    "document_id": "doc123",
                    "status": "deleted",
                    "chunks_deleted": 10,
                    "error": None,
                }
            )

            response = client.delete("/api/documents/doc123")

            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == "doc123"
            assert data["status"] == "deleted"
            assert data["chunks_deleted"] == 10

    def test_delete_document_not_found(self, client, mock_services):
        """Test deleting non-existent document."""
        with patch("api.documents.DocumentIngestionService") as MockIngestion:
            mock_ingestion = MockIngestion.return_value
            mock_ingestion.delete_document = AsyncMock(
                return_value={
                    "document_id": "nonexistent",
                    "status": "deleted",
                    "chunks_deleted": 0,
                    "error": None,
                }
            )

            response = client.delete("/api/documents/nonexistent")

            assert response.status_code == 404

    def test_delete_document_failed(self, client, mock_services):
        """Test document deletion failure."""
        with patch("api.documents.DocumentIngestionService") as MockIngestion:
            mock_ingestion = MockIngestion.return_value
            mock_ingestion.delete_document = AsyncMock(
                return_value={
                    "document_id": "doc123",
                    "status": "failed",
                    "chunks_deleted": 0,
                    "error": "Database error",
                }
            )

            response = client.delete("/api/documents/doc123")

            assert response.status_code == 500


class TestQueryEndpoints:
    """Tests for query processing endpoints."""

    def test_process_query_sync_success(self, client, mock_services):
        """Test synchronous query processing."""

        # Mock agent
        async def mock_process_query(*args, **kwargs):
            from models.agent import AgentStep

            yield AgentStep(
                step_id="step1",
                type="thought",
                content="Thinking about the query",
                metadata={},
            )
            yield AgentStep(
                step_id="step2",
                type="response",
                content="This is the answer",
                metadata={"sources": []},
            )

        mock_services["agent"].process_query = mock_process_query

        response = client.post(
            "/api/query/sync",
            json={"query": "What is machine learning?", "top_k": 10, "stream": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert "query_id" in data
        assert data["query"] == "What is machine learning?"
        assert "response" in data
        assert "reasoning_steps" in data

    def test_process_query_sync_empty_query(self, client, mock_services):
        """Test sync query with empty query string."""
        response = client.post("/api/query/sync", json={"query": "", "top_k": 10})

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_process_query_sync_with_session(self, client, mock_services):
        """Test sync query with session ID."""

        async def mock_process_query(*args, **kwargs):
            from models.agent import AgentStep

            yield AgentStep(
                step_id="step1", type="response", content="Answer", metadata={}
            )

        mock_services["agent"].process_query = mock_process_query

        response = client.post(
            "/api/query/sync",
            json={"query": "Test query", "session_id": "session123", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "session123"

    def test_get_query_status(self, client, mock_services):
        """Test getting query status."""
        response = client.get("/api/query/query123")

        assert response.status_code == 200
        data = response.json()
        assert "query_id" in data
        assert "status" in data


class TestErrorHandling:
    """Tests for error handling."""

    def test_validation_error_response(self, client, mock_services):
        """Test validation error response format."""
        # Send invalid request (missing required field)
        response = client.post("/api/query/sync", json={})

        assert response.status_code == 422
        data = response.json()
        assert "validation_errors" in data

    def test_404_error_response(self, client, mock_services):
        """Test 404 error response format."""
        response = client.get("/api/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "error_type" in data

    def test_request_id_in_response(self, client, mock_services):
        """Test that request ID is included in response headers."""
        response = client.get("/api/health")

        assert "X-Request-ID" in response.headers


class TestStreamingResponse:
    """Tests for streaming query endpoint."""

    def test_streaming_query_format(self, client, mock_services):
        """Test streaming response format."""

        async def mock_process_query(*args, **kwargs):
            from models.agent import AgentStep

            yield AgentStep(
                step_id="step1", type="thought", content="Processing", metadata={}
            )

        mock_services["agent"].process_query = mock_process_query

        response = client.post(
            "/api/query", json={"query": "Test query", "stream": True}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_streaming_query_empty_query(self, client, mock_services):
        """Test streaming with empty query."""
        response = client.post("/api/query", json={"query": "   ", "stream": True})

        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
