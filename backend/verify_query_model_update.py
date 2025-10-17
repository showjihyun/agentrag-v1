"""Verify that QueryRequest accepts optional UUID session_id."""

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from uuid import uuid4
from backend.models.query import QueryRequest, QueryResponse


def test_query_request_with_uuid_session_id():
    """Test QueryRequest with UUID session_id."""
    session_id = uuid4()

    # Test with UUID session_id
    request = QueryRequest(query="What is machine learning?", session_id=session_id)

    assert request.query == "What is machine learning?"
    assert request.session_id == session_id
    assert isinstance(request.session_id, type(session_id))
    print(f"✅ QueryRequest accepts UUID session_id: {request.session_id}")


def test_query_request_without_session_id():
    """Test QueryRequest without session_id (should be None)."""
    request = QueryRequest(query="What is deep learning?")

    assert request.query == "What is deep learning?"
    assert request.session_id is None
    print("✅ QueryRequest works without session_id (defaults to None)")


def test_query_response_with_uuid_session_id():
    """Test QueryResponse with UUID session_id."""
    session_id = uuid4()

    response = QueryResponse(
        query_id="query_123",
        query="What is AI?",
        response="AI is artificial intelligence...",
        session_id=session_id,
    )

    assert response.session_id == session_id
    assert isinstance(response.session_id, type(session_id))
    print(f"✅ QueryResponse accepts UUID session_id: {response.session_id}")


def test_json_serialization():
    """Test that models can be serialized to JSON."""
    session_id = uuid4()

    request = QueryRequest(query="Test query", session_id=session_id)

    # Test JSON serialization
    json_data = request.model_dump_json()
    print(f"✅ QueryRequest serializes to JSON: {json_data[:100]}...")

    # Test JSON deserialization
    request_from_json = QueryRequest.model_validate_json(json_data)
    assert request_from_json.session_id == session_id
    print("✅ QueryRequest deserializes from JSON correctly")


if __name__ == "__main__":
    print("Testing QueryRequest and QueryResponse with UUID session_id...\n")

    test_query_request_with_uuid_session_id()
    test_query_request_without_session_id()
    test_query_response_with_uuid_session_id()
    test_json_serialization()

    print(
        "\n✅ All tests passed! QueryRequest now accepts Optional[UUID] for session_id"
    )
