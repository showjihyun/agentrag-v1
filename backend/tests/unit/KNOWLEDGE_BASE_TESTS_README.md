# Knowledge Base Integration Tests

## Overview

Comprehensive test suite for Knowledge Base integration with Milvus, covering:
- Milvus connector functionality
- Search service operations
- Knowledge Base block execution
- Workflow integration scenarios

## Test File

`test_knowledge_base_integration.py`

## Test Coverage

### 1. Milvus Connector Tests (`TestMilvusConnector`)

#### Connection Management
- ✅ `test_connect_success` - Successful Milvus connection
- ✅ `test_connect_collection_not_found` - Handle missing collection
- ✅ `test_disconnect` - Clean disconnection

#### Filter Expression Building
- ✅ `test_build_filter_expression_string` - String value filters
- ✅ `test_build_filter_expression_numeric` - Numeric value filters
- ✅ `test_build_filter_expression_list` - List/IN operator filters
- ✅ `test_build_filter_expression_range` - Range query filters ($gte, $lte, $gt, $lt)
- ✅ `test_build_filter_expression_empty` - Empty/null filters

#### Search Operations
- ✅ `test_search_basic` - Basic vector similarity search
- ✅ `test_search_with_filters` - Search with metadata filters

### 2. Search Service Tests (`TestSearchService`)

#### Semantic Search
- ✅ `test_search_basic` - Basic semantic search with embeddings
- ✅ `test_search_with_filters` - Search with metadata filtering
- ✅ `test_search_with_ranking` - Custom ranking methods (score, recency, hybrid)

#### Result Processing
- ✅ `test_format_search_results` - Result formatting with/without metadata
- ✅ `test_hybrid_ranking` - Hybrid ranking algorithm (score + recency)

### 3. Knowledge Base Block Tests (`TestKnowledgeBaseBlock`)

#### Block Registration
- ✅ `test_block_registration` - Block is properly registered in BlockRegistry

#### Execution Scenarios
- ✅ `test_execute_basic_search` - Basic search execution
- ✅ `test_execute_with_filters` - Search with metadata filters
- ✅ `test_execute_with_ranking` - Search with custom ranking
- ✅ `test_execute_missing_query` - Error handling for missing query
- ✅ `test_execute_json_filters` - JSON string filter parsing
- ✅ `test_execute_input_override` - Input parameter override

### 4. Knowledge Base Upload Block Tests (`TestKnowledgeBaseUploadBlock`)

#### Block Registration
- ✅ `test_upload_block_registration` - Upload block is registered

#### Validation
- ✅ `test_execute_missing_file` - Error handling for missing file

### 5. Integration Tests (`TestKnowledgeBaseIntegration`)

#### Workflow Integration
- ✅ `test_workflow_search_execution` - KB block in workflow context
- ✅ `test_multiple_searches_in_workflow` - Multiple KB searches in same workflow

## Test Requirements

### Dependencies
- pytest
- pytest-asyncio
- unittest.mock (standard library)

### Mocked Components
All tests use mocks to avoid requiring actual Milvus/database connections:
- `pymilvus.connections`
- `pymilvus.Collection`
- `pymilvus.utility`
- `MilvusConnector`
- `SearchService`
- `EmbeddingWorkflow`

## Running Tests

### Run all Knowledge Base tests
```bash
cd backend
python -m pytest tests/unit/test_knowledge_base_integration.py -v
```

### Run specific test class
```bash
python -m pytest tests/unit/test_knowledge_base_integration.py::TestMilvusConnector -v
```

### Run specific test
```bash
python -m pytest tests/unit/test_knowledge_base_integration.py::TestKnowledgeBaseBlock::test_execute_basic_search -v
```

### Run with coverage
```bash
python -m pytest tests/unit/test_knowledge_base_integration.py --cov=backend.core.knowledge_base --cov=backend.core.blocks.knowledge_base_block
```

## Test Patterns

### Async Test Pattern
```python
@pytest.mark.asyncio
async def test_async_operation():
    # Setup mocks
    mock_service = Mock()
    mock_service.search = AsyncMock(return_value=[])
    
    # Execute
    result = await service.search(query="test")
    
    # Verify
    assert result is not None
```

### Mock Pattern
```python
@patch("module.path.get_service")
def test_with_mock(mock_service):
    # Setup
    mock_instance = Mock()
    mock_service.return_value = mock_instance
    
    # Test
    # ...
```

## Key Test Scenarios

### 1. Milvus Connection from Workflow
Tests that workflow blocks can successfully connect to Milvus and perform searches.

### 2. Document Search from Block
Tests that Knowledge Base blocks execute searches correctly with proper parameter handling.

### 3. Metadata Filtering
Tests various metadata filter types:
- String equality: `{"author": "John Doe"}`
- Numeric comparison: `{"chunk_index": 5}`
- List/IN operator: `{"language": ["en", "ko"]}`
- Range queries: `{"upload_date": {"$gte": 1000000, "$lte": 2000000}}`

### 4. Result Formatting
Tests that search results are properly formatted for workflow consumption with:
- Text content
- Similarity scores
- Document metadata
- Chunk information

### 5. Knowledge Base Block Execution
Tests complete block execution including:
- Input validation
- Query processing
- Filter application
- Result aggregation
- Error handling

## Coverage Summary

| Component | Test Coverage |
|-----------|--------------|
| MilvusConnector | Connection, search, filter building |
| SearchService | Search, ranking, formatting |
| KnowledgeBaseBlock | Execution, validation, error handling |
| KnowledgeBaseUploadBlock | Registration, validation |
| Workflow Integration | Multi-block execution, context handling |

## Requirements Mapping

Tests cover requirements:
- **7.1**: Milvus connection and collection verification
- **7.2**: Document processing workflow integration
- **7.3**: Vector search with metadata filtering
- **7.4**: Result formatting and ranking
- **7.5**: Knowledge Base block execution

## Notes

- All tests use mocks to avoid external dependencies
- Tests are designed to run quickly without actual database connections
- Async tests use `pytest-asyncio` for proper async/await handling
- Tests follow the same patterns as other block tests in the codebase
