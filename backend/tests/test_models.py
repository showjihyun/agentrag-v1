"""Tests for data models."""

import pytest
from datetime import datetime
from backend.models import (
    Document,
    TextChunk,
    QueryRequest,
    QueryResponse,
    SearchResult,
    AgentStep,
    AgentState,
)


def test_document_model():
    """Test Document model creation and validation."""
    doc = Document(
        document_id="doc123",
        filename="test.pdf",
        file_type="pdf",
        file_size=1024,
        processing_status="completed",
        chunk_count=10,
    )

    assert doc.document_id == "doc123"
    assert doc.filename == "test.pdf"
    assert doc.processing_status == "completed"
    assert doc.chunk_count == 10
    assert isinstance(doc.upload_timestamp, datetime)


def test_text_chunk_model():
    """Test TextChunk model creation and validation."""
    chunk = TextChunk(
        chunk_id="chunk_001",
        document_id="doc123",
        text="Sample text content",
        chunk_index=0,
        start_char=0,
        end_char=19,
        metadata={"page": 1},
    )

    assert chunk.chunk_id == "chunk_001"
    assert chunk.document_id == "doc123"
    assert chunk.text == "Sample text content"
    assert chunk.metadata["page"] == 1


def test_search_result_model():
    """Test SearchResult model creation and validation."""
    result = SearchResult(
        chunk_id="chunk_001",
        document_id="doc123",
        document_name="test.pdf",
        text="Relevant text",
        score=0.95,
        metadata={"page": 1},
    )

    assert result.chunk_id == "chunk_001"
    assert result.score == 0.95
    assert result.document_name == "test.pdf"


def test_query_request_model():
    """Test QueryRequest model creation and validation."""
    request = QueryRequest(
        query="What is machine learning?",
        session_id="session_123",
        top_k=10,
        stream=True,
    )

    assert request.query == "What is machine learning?"
    assert request.session_id == "session_123"
    assert request.top_k == 10
    assert request.stream is True


def test_query_request_validation():
    """Test QueryRequest validation."""
    # Empty query should fail
    with pytest.raises(ValueError):
        QueryRequest(query="")

    # top_k out of range should fail
    with pytest.raises(ValueError):
        QueryRequest(query="test", top_k=100)


def test_query_response_model():
    """Test QueryResponse model creation and validation."""
    response = QueryResponse(
        query_id="query_001",
        query="What is ML?",
        response="Machine learning is...",
        sources=[],
        reasoning_steps=[],
        processing_time=2.5,
    )

    assert response.query_id == "query_001"
    assert response.query == "What is ML?"
    assert response.processing_time == 2.5


def test_agent_step_model():
    """Test AgentStep model creation and validation."""
    step = AgentStep(
        step_id="step_001",
        type="thought",
        content="I need to search for documents",
        metadata={"action": "vector_search"},
    )

    assert step.step_id == "step_001"
    assert step.type == "thought"
    assert step.content == "I need to search for documents"
    assert isinstance(step.timestamp, datetime)


def test_agent_state_model():
    """Test AgentState model creation and validation."""
    state = AgentState(
        query="What are the benefits?",
        session_id="session_123",
        planning_steps=["Step 1", "Step 2"],
        action_history=[],
        retrieved_docs=[],
        reasoning_steps=[],
    )

    assert state.query == "What are the benefits?"
    assert state.session_id == "session_123"
    assert len(state.planning_steps) == 2
    assert state.final_response is None


def test_model_serialization():
    """Test that models can be serialized to JSON."""
    doc = Document(
        document_id="doc123",
        filename="test.pdf",
        file_type="pdf",
        file_size=1024,
    )

    # Should be able to convert to dict
    doc_dict = doc.model_dump()
    assert doc_dict["document_id"] == "doc123"

    # Should be able to convert to JSON
    doc_json = doc.model_dump_json()
    assert "doc123" in doc_json


def test_model_from_dict():
    """Test creating models from dictionaries."""
    data = {
        "document_id": "doc123",
        "filename": "test.pdf",
        "file_type": "pdf",
        "file_size": 1024,
        "processing_status": "completed",
    }

    doc = Document(**data)
    assert doc.document_id == "doc123"
    assert doc.filename == "test.pdf"
