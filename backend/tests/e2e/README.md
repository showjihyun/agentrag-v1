# End-to-End Tests

This directory contains comprehensive end-to-end tests for the Agentic RAG system.

## Test Files

### test_document_workflow.py
Tests the complete document upload and indexing workflow:
- Document processing and chunking
- Embedding generation
- Vector database storage
- Document retrieval and deletion
- Multiple document indexing
- Different file format support
- Large document handling

**Requirements Tested:** 1.5, 2.4

### test_query_workflow.py
Tests query processing with agents:
- Simple query workflow
- Multi-turn conversations
- Memory persistence across sessions
- Complex multi-step queries
- Streaming response generation

**Requirements Tested:** 4.1, 5.1, 7.2

### test_mcp_integration.py
Tests MCP server integration:
- Vector Search Agent with MCP
- Local Data Agent with MCP
- Web Search Agent with MCP
- Multi-agent coordination
- Error handling for unavailable servers

**Requirements Tested:** 3.1, 3.3, 3.4, 3.5, 3.6

### test_full_workflow.py
Tests complete end-to-end workflows:
- Complete RAG workflow (upload → query → response)
- Concurrent queries from multiple sessions
- Error recovery
- Data persistence

**Requirements Tested:** 1.5, 2.4, 4.1, 5.1, 7.2, 7.4, 7.5

### test_performance.py
Performance and load testing:
- Embedding generation performance
- Vector search performance
- Concurrent search performance
- Memory operations performance
- Document processing performance
- System under sustained load

**Requirements Tested:** 7.4

## Running Tests

### Prerequisites

1. Start test services:
```bash
docker-compose -f docker-compose.test.yml up -d
```

2. Set up test environment:
```bash
python backend/tests/setup_test_env.py
```

3. Ensure Ollama is running (for LLM tests):
```bash
ollama serve
ollama pull llama3.1
```

### Run All E2E Tests

```bash
# From backend directory
pytest tests/e2e/ -v
```

### Run Specific Test Files

```bash
# Document workflow tests
pytest tests/e2e/test_document_workflow.py -v

# Query workflow tests
pytest tests/e2e/test_query_workflow.py -v

# MCP integration tests
pytest tests/e2e/test_mcp_integration.py -v

# Full workflow tests
pytest tests/e2e/test_full_workflow.py -v

# Performance tests
pytest tests/e2e/test_performance.py -v
```

### Run Tests by Marker

```bash
# Run only e2e tests
pytest -m e2e

# Run slow tests
pytest -m slow

# Run tests that require Ollama
pytest -m requires_ollama

# Run tests that require MCP servers
pytest -m requires_mcp

# Exclude slow tests
pytest -m "e2e and not slow"
```

### Run with Coverage

```bash
pytest tests/e2e/ --cov=. --cov-report=html --cov-report=term
```

### Run with Verbose Output

```bash
pytest tests/e2e/ -v -s
```

## Test Markers

- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow running tests (>10 seconds)
- `@pytest.mark.requires_ollama` - Tests that require Ollama
- `@pytest.mark.requires_mcp` - Tests that require MCP servers
- `@pytest.mark.asyncio` - Async tests

## Expected Test Duration

- **Document Workflow Tests**: ~30 seconds
- **Query Workflow Tests**: ~60 seconds (with Ollama)
- **MCP Integration Tests**: ~20 seconds
- **Full Workflow Tests**: ~90 seconds (with Ollama)
- **Performance Tests**: ~120 seconds

**Total E2E Suite**: ~5-6 minutes

## Test Data

Test data is located in `backend/tests/data/`:
- `sample_doc.txt` - Sample document for testing

Additional test files are created dynamically in temporary directories.

## Troubleshooting

### Tests Fail with Connection Errors

Check if test services are running:
```bash
docker-compose -f docker-compose.test.yml ps
```

Restart services if needed:
```bash
docker-compose -f docker-compose.test.yml restart
```

### Ollama Tests Fail

Ensure Ollama is running and model is available:
```bash
curl http://localhost:11434/api/tags
ollama pull llama3.1
```

### Slow Test Performance

Performance tests are marked with `@pytest.mark.slow`. Skip them for faster runs:
```bash
pytest tests/e2e/ -m "not slow"
```

### Memory Issues

If tests fail with memory errors, reduce concurrency in performance tests or run tests sequentially:
```bash
pytest tests/e2e/ -n 1
```

## CI/CD Integration

For automated testing in CI/CD:

```bash
# Start services
docker-compose -f docker-compose.test.yml up -d

# Wait for services
sleep 30

# Set up environment
python backend/tests/setup_test_env.py

# Run tests with coverage
pytest tests/e2e/ --cov=. --cov-report=xml --cov-report=term -v

# Stop services
docker-compose -f docker-compose.test.yml down
```

## Performance Benchmarks

Expected performance metrics (on standard hardware):

- **Embedding Generation**: <50ms per text
- **Batch Embedding (100 texts)**: <500ms
- **Vector Search**: <100ms
- **Document Indexing**: <1s per 1000 characters
- **Concurrent Queries (10)**: <2s total
- **Memory Operations**: <10ms per operation

If your results significantly differ, consider:
- Hardware specifications
- Network latency
- Database configuration
- LLM provider response time

## Writing New E2E Tests

Template for new e2e tests:

```python
import pytest

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_my_workflow(
    milvus_manager,
    embedding_service,
    memory_manager
):
    """
    Test description.
    
    Requirements: X.X
    """
    # Setup
    # ... prepare test data
    
    # Execute
    # ... run the workflow
    
    # Verify
    # ... assert expected results
    
    # Cleanup
    # ... clean up test data
```

## Contact

For issues or questions about e2e tests, refer to:
- Main test documentation: `backend/tests/TEST_SETUP.md`
- Test utilities: `backend/tests/test_utils.py`
- Fixtures: `backend/tests/conftest.py`
