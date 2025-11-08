# Workflow Execution Engine

This module provides a comprehensive workflow execution engine for the Agent Builder system. It orchestrates the execution of visual workflows by processing blocks in topological order and handling advanced control flow.

## Components

### 1. Execution Context (`context.py`)
Maintains state during workflow execution including:
- Block execution states and outputs
- Workflow and environment variables
- Execution logs and timing
- Token usage and cost tracking
- Control flow state (loops, parallel, conditions)

**Key Features:**
- Variable resolution with template support (`{{variable_name}}`)
- Block output tracking and retrieval
- Execution log collection
- Token usage and cost calculation
- Serialization/deserialization for persistence

### 2. Workflow Executor (`executor.py`)
Main orchestrator for workflow execution:
- Loads workflow definition from database
- Performs topological sort for execution order
- Executes blocks sequentially
- Handles control flow (conditions, loops, parallel)
- Saves execution logs to database

**Key Features:**
- Topological sorting with cycle detection
- Block input preparation with variable resolution
- Execution result aggregation
- Comprehensive error handling
- Database persistence

### 3. Condition Evaluator (`condition_evaluator.py`)
Handles conditional branching:
- Evaluates condition block outputs
- Selects next block based on path
- Stores routing decisions in context
- Supports multiple condition paths

**Key Features:**
- Path selection based on condition results
- Edge matching by source handle
- Routing decision logging

### 4. Loop Executor (`loop_executor.py`)
Manages loop execution:
- Supports 'for' loops (fixed count)
- Supports 'forEach' loops (collection iteration)
- Tracks iteration state
- Aggregates loop results

**Key Features:**
- Iteration variable management
- Loop body block execution
- Result aggregation
- Error handling per iteration

### 5. Parallel Executor (`parallel_executor.py`)
Handles concurrent execution:
- Supports fixed-count parallel execution
- Supports collection-based parallel processing
- Manages concurrency limits
- Aggregates results from parallel branches

**Key Features:**
- Async/await based concurrency
- Semaphore-based concurrency limiting
- Multiple aggregation strategies (array, merge, first)
- Branch-level error handling

### 6. Error Handler (`error_handler.py`)
Comprehensive error handling:
- Timeout handling for blocks and workflows
- Retry strategies for recoverable errors
- Error response formatting
- Error logging with stack traces

**Key Features:**
- Timeout detection and handling
- Recoverable error detection
- Retry strategy determination
- Error summary creation

### 7. Execution Logger (`logger.py`)
Enhanced logging capabilities:
- Workflow start/complete logging
- Block execution logging
- Token usage tracking
- File metadata logging
- Execution summary creation

**Key Features:**
- Structured logging with context
- Performance metrics
- Cost tracking
- Detailed error logging

### 8. Error Classes (`errors.py`)
Custom exception hierarchy:
- `ExecutionError` - Base exception
- `WorkflowNotFoundError` - Workflow not found
- `BlockExecutionError` - Block execution failure
- `CyclicDependencyError` - Workflow has cycles
- `ExecutionTimeoutError` - Execution timeout
- `ConditionEvaluationError` - Condition evaluation failure
- `LoopExecutionError` - Loop execution failure
- `ParallelExecutionError` - Parallel execution failure

## Usage

### Basic Workflow Execution

```python
from sqlalchemy.orm import Session
from backend.core.execution import WorkflowExecutor

# Create executor
executor = WorkflowExecutor(db_session)

# Execute workflow
context = await executor.execute(
    workflow_id="workflow_123",
    user_id="user_456",
    trigger="manual",
    input_data={"query": "Hello"}
)

# Check results
if context.status == "completed":
    print(f"Workflow completed successfully")
    print(f"Duration: {context.duration_ms}ms")
    print(f"Tokens used: {context.total_tokens}")
    print(f"Cost: ${context.estimated_cost}")
else:
    print(f"Workflow failed: {context.error_message}")
```

### Accessing Block Outputs

```python
# Get output from a specific block
block_output = context.get_block_output("block_123")

# Get specific output key
result = context.get_block_output("block_123", "response")
```

### Variable Resolution

```python
# Set variables
context.workflow_variables = {"name": "John", "age": 30}

# Resolve variable
name = context.resolve_variable("name")

# Resolve template
template = "Hello {{name}}, you are {{age}} years old"
resolved = context.resolve_template(template)
```

### Error Handling

```python
from backend.core.execution import ErrorHandler

try:
    context = await executor.execute(workflow_id, user_id)
except ExecutionError as e:
    # Format error response
    error_response = ErrorHandler.format_error_response(e, context)
    
    # Log error
    ErrorHandler.log_error(e, context)
    
    # Check if recoverable
    if ErrorHandler.is_recoverable_error(e):
        # Get retry strategy
        strategy = ErrorHandler.get_retry_strategy(e)
        # Retry if appropriate
```

## Architecture

### Execution Flow

1. **Load Workflow**: Load workflow definition and blocks from database
2. **Create Context**: Initialize execution context with variables
3. **Topological Sort**: Determine block execution order
4. **Execute Blocks**: Execute blocks sequentially in order
5. **Handle Control Flow**: Process conditions, loops, and parallel blocks
6. **Save Results**: Persist execution log to database

### Control Flow Handling

#### Conditions
- Condition block evaluates and returns selected path
- Executor follows edge matching the selected path
- Routing decision stored in context

#### Loops
- Loop block prepares iteration contexts
- Executor executes loop body for each iteration
- Iteration variables injected into context
- Results aggregated after all iterations

#### Parallel
- Parallel block prepares branch contexts
- Executor executes branches concurrently
- Concurrency limited by semaphore
- Results aggregated based on strategy

## Testing

Comprehensive test suite in `backend/tests/unit/test_execution_engine.py`:
- ExecutionContext tests
- WorkflowExecutor tests
- ConditionEvaluator tests
- ErrorHandler tests
- ExecutionLogger tests

Run tests:
```bash
pytest backend/tests/unit/test_execution_engine.py -v
```

## Future Enhancements

1. **Streaming Support**: Real-time execution updates via WebSocket
2. **Breakpoints**: Pause execution at specific blocks for debugging
3. **Rollback**: Undo execution to previous state
4. **Subworkflows**: Execute workflows within workflows
5. **Caching**: Cache block outputs for repeated executions
6. **Metrics**: Detailed performance metrics and profiling
7. **Visualization**: Real-time execution visualization in UI

## Dependencies

- SQLAlchemy: Database ORM
- asyncio: Async execution
- Python 3.8+: Type hints and async/await

## Related Modules

- `backend.core.blocks`: Block implementations
- `backend.db.models.agent_builder`: Database models
- `backend.models.agent_builder`: Pydantic schemas
- `backend.api.agent_builder`: API endpoints
