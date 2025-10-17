# Integration Tests

This directory contains integration tests that require external services to be running.

## Milvus Integration Tests

The Milvus integration tests (`test_milvus_integration.py`) test the complete functionality of the MilvusManager service including:

- **Connection Management**: Connection, disconnection, retry logic, health checks
- **Collection Operations**: Creation, schema validation, collection management
- **Insert Operations**: Single and batch embedding insertion, data persistence
- **Search Operations**: Similarity search, filtering, result ordering
- **Delete Operations**: Document deletion, cleanup verification
- **End-to-End Workflows**: Complete document lifecycle testing
- **Error Handling**: Graceful failure handling

### Prerequisites

Before running the integration tests, ensure Milvus is running:

```bash
# Start Milvus using Docker Compose
docker-compose up -d milvus

# Verify Milvus is running
docker-compose ps milvus
```

### Running the Tests

```bash
# Run all integration tests
pytest backend/tests/integration/ -v

# Run only Milvus integration tests
pytest backend/tests/integration/test_milvus_integration.py -v

# Run specific test class
pytest backend/tests/integration/test_milvus_integration.py::TestSearchOperations -v

# Run specific test
pytest backend/tests/integration/test_milvus_integration.py::TestSearchOperations::test_search_success -v

# Run with detailed output
pytest backend/tests/integration/test_milvus_integration.py -vv -s

# Run with coverage
pytest backend/tests/integration/test_milvus_integration.py --cov=backend.services.milvus
```

### Test Configuration

The tests use configuration from `backend/config.py`:
- `MILVUS_HOST`: Milvus server host (default: localhost)
- `MILVUS_PORT`: Milvus server port (default: 19530)

Tests create a temporary collection (`test_integration_collection`) that is automatically cleaned up after each test.

### Test Fixtures

- `milvus_manager`: Provides a connected MilvusManager instance with automatic cleanup
- `sample_embeddings`: Generates 5 sample embedding vectors (384 dimensions)
- `sample_metadata`: Generates corresponding metadata for sample embeddings

### Skipping Tests

If Milvus is not available, tests will be automatically skipped with an appropriate message:

```
SKIPPED [1] test_milvus_integration.py:XX: Milvus not available: Failed to connect...
```

### Troubleshooting

**Connection Errors:**
- Ensure Milvus is running: `docker-compose ps milvus`
- Check Milvus logs: `docker-compose logs milvus`
- Verify port 19530 is accessible: `telnet localhost 19530`

**Slow Tests:**
- Integration tests may take longer due to actual database operations
- Use `-v` flag to see progress
- Consider running specific test classes instead of all tests

**Cleanup Issues:**
- Tests automatically clean up test collections
- If cleanup fails, manually drop the collection:
  ```python
  from pymilvus import connections, utility
  connections.connect(host="localhost", port=19530)
  utility.drop_collection("test_integration_collection")
  ```

## Requirements Coverage

These integration tests satisfy the following requirements:

- **Requirement 1.1**: Vector database connection and initialization
- **Requirement 1.3**: Similarity search with top-k results and filtering

## Future Integration Tests

Additional integration tests to be added:
- Redis integration tests for memory management
- End-to-end API tests with all services
- Performance and load testing
