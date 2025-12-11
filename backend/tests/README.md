# Test Suite Structure

## Overview

The test suite is organized by test type with shared fixtures and utilities.

## Directory Structure

```
tests/
├── conftest.py           # Global pytest configuration and fixture imports
├── README.md             # This file
│
├── fixtures/             # Reusable test fixtures
│   ├── __init__.py
│   ├── database_fixtures.py   # Database session fixtures
│   ├── user_fixtures.py       # User-related fixtures
│   ├── document_fixtures.py   # Document-related fixtures
│   └── query_fixtures.py      # Query-related fixtures
│
├── utils/                # Test utilities
│   ├── __init__.py
│   ├── mock_helpers.py        # Mock object creation
│   ├── assertion_helpers.py   # Custom assertions
│   └── api_helpers.py         # API testing utilities
│
├── unit/                 # Unit tests
│   ├── __init__.py
│   ├── services/              # Service layer tests
│   └── test_*.py              # Unit test files
│
├── integration/          # Integration tests
│   ├── __init__.py
│   ├── api/                   # API integration tests
│   └── test_*.py              # Integration test files
│
├── e2e/                  # End-to-end tests
│   ├── __init__.py
│   └── test_*.py              # E2E test files
│
├── performance/          # Performance tests
│   └── test_*.py              # Performance test files
│
└── data/                 # Test data files
    └── sample_doc.txt
```

## Running Tests

### All tests
```bash
cd backend
pytest
```

### By type
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/

# Performance tests
pytest tests/performance/
```

### By marker
```bash
# Skip slow tests
pytest -m "not slow"

# Only integration tests
pytest -m integration

# Only unit tests
pytest -m unit
```

### With coverage
```bash
pytest --cov=backend --cov-report=html
```

## Using Fixtures

Fixtures are automatically available in all tests via conftest.py:

```python
def test_user_creation(client, sample_user_data):
    response = client.post("/api/auth/register", json=sample_user_data)
    assert response.status_code == 200

def test_document_upload(auth_client, sample_pdf_file):
    response = auth_client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", sample_pdf_file, "application/pdf")}
    )
    assert response.status_code == 200
```

## Using Utilities

### Mock helpers
```python
from backend.tests.utils.mock_helpers import create_mock_llm_response

def test_llm_processing(mocker):
    mock_response = create_mock_llm_response(content="Test response")
    mocker.patch("backend.services.llm_manager.generate", return_value=mock_response)
    # ... test code
```

### Assertion helpers
```python
from backend.tests.utils.assertion_helpers import assert_valid_response, assert_contains_keys

def test_api_response(client):
    response = client.get("/api/health")
    assert_valid_response(response, 200)
    data = response.json()
    assert_contains_keys(data, ["status", "version"])
```

### API helpers
```python
from backend.tests.utils.api_helpers import AuthenticatedClient

def test_protected_endpoint(client, sample_user_data):
    auth_client = AuthenticatedClient(client)
    auth_client.login(sample_user_data["email"], sample_user_data["password"])
    response = auth_client.get("/api/protected")
    assert response.status_code == 200
```

## Writing Tests

### Unit tests
- Test single functions/methods in isolation
- Mock external dependencies
- Fast execution (< 100ms per test)

### Integration tests
- Test component interactions
- Use test database
- May involve multiple services

### E2E tests
- Test complete user workflows
- Full stack testing
- Slower execution acceptable

## Test Markers

Add markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_fast_function():
    pass

@pytest.mark.integration
def test_api_endpoint():
    pass

@pytest.mark.slow
def test_heavy_processing():
    pass

@pytest.mark.e2e
def test_full_workflow():
    pass
```

## Coverage Targets

- Unit tests: 85%+
- Integration tests: 70%+
- Overall: 80%+
