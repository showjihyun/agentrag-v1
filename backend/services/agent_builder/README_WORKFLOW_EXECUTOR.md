# Workflow Executor Implementation

## Overview

This document describes the implementation of the LangGraph-based workflow execution engine for the Agent Builder feature.

## Components Implemented

### 1. WorkflowExecutor (`workflow_executor.py`)

The core execution engine that compiles and executes agent workflows using LangGraph.

**Key Features:**
- **Workflow Compilation**: Converts workflow definitions to LangGraph StateGraph
- **Node Execution**: Supports agent, block, and control flow nodes
- **Streaming Execution**: Yields AgentStep objects in real-time via async generators
- **State Management**: Manages data flow between nodes through LangGraph state dictionary
- **Execution Logging**: Logs execution steps to database (when models are available)
- **Parallel Execution**: Executes multiple branches concurrently with semaphore limiting
- **Error Handling**: Comprehensive retry logic with fallback support
- **Timeout Management**: Configurable timeouts for node execution

**Main Methods:**
- `compile_workflow()`: Compiles workflow definition to StateGraph
- `execute_workflow()`: Executes workflow with streaming support
- `execute_parallel_branches()`: Handles parallel branch execution
- `_create_agent_node()`: Creates agent execution nodes
- `_create_block_node()`: Creates block execution nodes
- `_create_control_node()`: Creates control flow nodes

### 2. BlockExecutor (`block_executor.py`)

Executes individual blocks based on their type.

**Supported Block Types:**
- **LLM Blocks**: Execute LLM calls with prompt templates
- **Tool Blocks**: Execute tool invocations via ToolRegistry
- **Logic Blocks**: Execute custom Python code in restricted environment
- **Composite Blocks**: Execute nested workflows (placeholder for now)

**Key Features:**
- Variable substitution in templates
- Safe Python execution environment for logic blocks
- Input/output mapping
- Integration with LLMManager and ToolRegistry

### 3. ExecutionContext

Data class for managing execution context including:
- Execution ID, user ID, agent ID, workflow ID
- Session ID, workspace ID
- Input data, variables, knowledgebases

### 4. Integration Tests (`test_workflow_execution.py`)

Comprehensive integration tests covering:
- Sequential workflow execution
- Parallel execution with multiple branches
- Conditional branching
- Error handling and retry mechanisms
- Timeout handling
- Fallback behavior

## Architecture

```
WorkflowExecutor
├── LangGraph StateGraph (workflow compilation)
├── BlockExecutor (block execution)
│   ├── LLMManager (LLM blocks)
│   └── ToolRegistry (tool blocks)
├── RetryHandler (error recovery)
├── MemoryManager (STM/LTM integration)
├── VariableResolver (variable resolution)
└── KnowledgebaseService (document retrieval)
```

## Workflow Execution Flow

1. **Compilation Phase**
   - Load workflow definition
   - Create StateGraph with nodes and edges
   - Add conditional edges for branching
   - Compile graph

2. **Initialization Phase**
   - Resolve variables from context
   - Load knowledgebases
   - Initialize state dictionary
   - Create execution record

3. **Execution Phase**
   - Stream through graph nodes
   - Execute each node (agent/block/control)
   - Yield AgentStep objects
   - Log steps to database
   - Handle errors with retry/fallback

4. **Completion Phase**
   - Yield final output
   - Update execution record
   - Calculate metrics

## Error Handling

The implementation includes comprehensive error handling:

### Retry Logic
- Configurable retry count (default: 3)
- Exponential backoff with jitter
- Retryable exceptions: TimeoutError, ConnectionError

### Timeout Management
- Default timeout: 60 seconds
- Configurable per agent/block
- Graceful timeout handling with fallback

### Fallback Behavior
- Configurable fallback values
- Used when retries exhausted or timeout occurs
- Prevents workflow failure for non-critical nodes

## Parallel Execution

Parallel execution is implemented with:
- `asyncio.gather()` for concurrent execution
- Semaphore limiting (max 5 concurrent LLM calls)
- Result aggregation from all branches
- Error isolation (one branch failure doesn't stop others)

## State Management

State flows through the workflow via LangGraph state dictionary:
- `input`: Initial input data
- `context`: Execution context
- `variables`: Resolved variables
- `knowledgebases`: Loaded knowledgebases
- `steps`: Execution steps
- `output`: Final output
- `node_{id}_output`: Output from each node
- `agent_{id}_output`: Output from each agent
- `block_{id}_output`: Output from each block

## Integration Points

### Existing Infrastructure
- **LLMManager**: For LLM calls in LLM blocks
- **MemoryManager**: For STM/LTM access (ready for integration)
- **RetryHandler**: For retry logic
- **ToolRegistry**: For tool execution in tool blocks

### Future Integration
- **Agent Models**: Will load from database when Phase 1 is complete
- **Block Models**: Will load from database when Phase 1 is complete
- **Execution Models**: Will log to database when Phase 1 is complete

## Configuration

### Agent/Block Error Configuration
```python
{
    "error_handling": {
        "retry_enabled": True,
        "retry_count": 3,
        "timeout": 60.0,
        "fallback_value": "default response"
    }
}
```

### Workflow Definition Format
```python
{
    "nodes": [
        {
            "id": "node_1",
            "type": "agent|block|control",
            "agent_id": "...",  # for agent nodes
            "block_id": "...",  # for block nodes
            "control_type": "conditional|loop|parallel",  # for control nodes
            "name": "Node Name",
            "input_mapping": {...}
        }
    ],
    "edges": [
        {
            "type": "normal|conditional",
            "source": "node_1",
            "target": "node_2",
            "condition": "...",  # for conditional edges
            "branches": {...}  # for conditional edges
        }
    ],
    "entry_point": "node_1",
    "finish_points": ["node_n"]
}
```

## Testing

Run integration tests:
```bash
cd backend
python -m pytest tests/integration/test_workflow_execution.py -v
```

## Dependencies

- `langgraph==0.2.55`: LangGraph for workflow execution
- `langchain`: For LangChain integration
- Existing backend services (LLMManager, MemoryManager, etc.)

## Future Enhancements

1. **Composite Block Execution**: Full nested workflow support
2. **Advanced Control Flows**: More sophisticated loop and parallel patterns
3. **Execution Metrics**: Detailed performance tracking
4. **Workflow Optimization**: Graph optimization and caching
5. **Visual Debugging**: Step-by-step execution visualization

## Notes

- The implementation is designed to work with Phase 1 models once they're available
- Database logging is gracefully skipped if models aren't imported
- All core functionality is implemented and tested
- Ready for integration with frontend and API layers
