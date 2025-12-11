"""
Pytest configuration and shared fixtures.

This file imports fixtures from the fixtures package for better organization.
All fixtures are available globally in tests.
"""

import pytest

# Import all fixtures from fixtures package
from backend.tests.fixtures.database_fixtures import (
    test_engine,
    test_db,
    client,
)
from backend.tests.fixtures.user_fixtures import (
    sample_user_data,
    sample_admin_user_data,
    multiple_users_data,
    invalid_user_data,
)
from backend.tests.fixtures.document_fixtures import (
    sample_document_data,
    sample_pdf_file,
    sample_text_file,
    large_document_data,
    multiple_documents_data,
)
from backend.tests.fixtures.query_fixtures import (
    sample_query_data,
    simple_query_data,
    complex_query_data,
    korean_query_data,
    query_with_context,
    batch_queries,
    expected_search_results,
)

# Import test utilities for easy access
from backend.tests.utils.mock_helpers import (
    create_mock_llm_response,
    create_mock_embedding,
    create_mock_search_result,
    create_mock_embedding_service,
    create_mock_llm_manager,
    create_mock_milvus_service,
    create_mock_redis_client,
)
from backend.tests.utils.assertion_helpers import (
    assert_valid_response,
    assert_json_response,
    assert_error_response,
    assert_pagination_response,
    assert_contains_keys,
    assert_list_length,
    assert_response_time,
)
from backend.tests.utils.api_helpers import (
    AuthenticatedClient,
    create_test_user,
    get_auth_token,
    upload_test_document,
)


# Additional pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        "test_database_url": "sqlite:///:memory:",
        "test_redis_url": "redis://localhost:6379/15",
        "test_milvus_host": "localhost",
        "test_milvus_port": 19530,
        "timeout": 30,
    }


@pytest.fixture
def auth_client(client, sample_user_data):
    """Create authenticated test client."""
    # Register user
    client.post("/api/auth/register", json=sample_user_data)
    
    # Login and get token
    response = client.post(
        "/api/auth/login",
        json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        },
    )
    token = response.json().get("access_token")
    
    return AuthenticatedClient(client, token)


@pytest.fixture
async def async_client():
    """Create async test client for integration tests."""
    from httpx import AsyncClient
    from backend.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(async_client, sample_user_data):
    """Get authentication headers for async tests."""
    # Register user
    await async_client.post("/api/auth/register", json=sample_user_data)
    
    # Login and get token
    response = await async_client.post(
        "/api/auth/login",
        json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        },
    )
    token = response.json().get("access_token")
    
    return {"Authorization": f"Bearer {token}"}
