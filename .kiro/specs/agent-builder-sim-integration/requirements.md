# Requirements Document

## Introduction

This specification defines the integration of Sim Workflows LLM's core features into the AgenticRAG agent-builder system. The goal is to transform the current basic agent-builder into a powerful visual workflow builder with 70+ integrated tools, advanced execution engine, and comprehensive trigger system.

## Glossary

- **Block**: A reusable workflow component that performs a specific function (e.g., OpenAI API call, HTTP request, condition check)
- **SubBlock**: UI configuration component within a block (e.g., input field, dropdown, code editor)
- **Workflow**: A directed graph of connected blocks that defines an agent's behavior
- **Execution Engine**: The system that executes workflows by processing blocks in order
- **Trigger**: An event that initiates workflow execution (webhook, schedule, API call, chat, manual)
- **Knowledge Base**: Vector database integration for semantic search using Milvus
- **Execution Context**: Runtime state containing block outputs, variables, and execution metadata
- **Block Registry**: Central registry of all available block types
- **ReactFlow**: Visual graph editor library for building workflows

## Requirements

### Requirement 1: Block System Architecture

**User Story:** As a developer, I want a flexible block system that supports 70+ integrated tools, so that users can build complex workflows with diverse functionality.

#### Acceptance Criteria

1. WHEN the system initializes, THE Block Registry SHALL load all available block definitions from the registry
2. WHEN a block is requested by type, THE Block Registry SHALL return the corresponding BlockConfig with all metadata
3. WHEN a block is created, THE System SHALL validate that the block type exists in the registry
4. WHEN a block configuration is provided, THE System SHALL validate inputs against the block's input schema
5. WHERE a block has SubBlocks, THE System SHALL render appropriate UI components based on SubBlock type

### Requirement 2: Database Schema for Blocks and Workflows

**User Story:** As a system administrator, I want a robust database schema that stores workflow definitions and execution history, so that workflows persist reliably and execution can be tracked.

#### Acceptance Criteria

1. WHEN a workflow is created, THE System SHALL store workflow metadata in the workflow table
2. WHEN blocks are added to a workflow, THE System SHALL store block definitions in the agent_blocks table with position and configuration
3. WHEN blocks are connected, THE System SHALL store edge relationships in the agent_edges table
4. WHEN a workflow executes, THE System SHALL create an execution log entry in workflow_execution_logs table
5. WHEN a workflow has loops or parallel structures, THE System SHALL store subflow configuration in workflow_subflows table
6. WHERE a workflow has schedules, THE System SHALL store cron expressions in workflow_schedules table
7. WHERE a workflow has webhooks, THE System SHALL store webhook paths in workflow_webhooks table

### Requirement 3: Execution Engine with Advanced Control Flow

**User Story:** As a workflow designer, I want to create workflows with conditional branching, loops, and parallel execution, so that I can build sophisticated agent behaviors.

#### Acceptance Criteria

1. WHEN a workflow is executed, THE Execution Engine SHALL process blocks in topological order based on edges
2. WHEN a condition block is encountered, THE Execution Engine SHALL evaluate the condition and follow the appropriate path
3. WHEN a loop block is encountered, THE Execution Engine SHALL execute the loop body for the specified iterations
4. WHEN a parallel block is encountered, THE Execution Engine SHALL execute multiple branches concurrently
5. WHEN a block execution fails, THE Execution Engine SHALL log the error and halt execution
6. WHEN a workflow completes, THE Execution Engine SHALL return the final output and execution metadata
7. WHERE streaming is enabled, THE Execution Engine SHALL stream block outputs in real-time

### Requirement 4: Tool Integration System

**User Story:** As a workflow designer, I want access to 70+ pre-built tool integrations, so that I can quickly build workflows without writing custom code.

#### Acceptance Criteria

1. WHEN the system starts, THE Tool Registry SHALL load all available tool definitions
2. WHEN a tool block is added to a workflow, THE System SHALL provide the tool's configuration UI based on SubBlocks
3. WHEN a tool requires OAuth, THE System SHALL prompt for authentication and store credentials securely
4. WHEN a tool is executed, THE System SHALL call the appropriate API with configured parameters
5. WHEN a tool execution completes, THE System SHALL transform the response according to the tool's output schema
6. WHERE a tool execution fails, THE System SHALL extract error information using configured error extractors

### Requirement 5: Visual Workflow Editor

**User Story:** As a workflow designer, I want a visual drag-and-drop editor, so that I can build workflows intuitively without writing code.

#### Acceptance Criteria

1. WHEN the editor loads, THE System SHALL display the workflow canvas with ReactFlow
2. WHEN a user drags a block from the palette, THE System SHALL add the block to the canvas at the drop position
3. WHEN a user connects two blocks, THE System SHALL create an edge in the workflow definition
4. WHEN a user clicks a block, THE System SHALL display the block's configuration panel with SubBlock components
5. WHEN a user saves the workflow, THE System SHALL persist the workflow definition to the database
6. WHERE validation errors exist, THE System SHALL highlight invalid blocks and display error messages

### Requirement 6: Trigger System

**User Story:** As a workflow designer, I want multiple ways to trigger workflow execution, so that workflows can respond to various events automatically.

#### Acceptance Criteria

1. WHEN a webhook trigger is configured, THE System SHALL create a unique webhook URL for the workflow
2. WHEN a webhook receives a request, THE System SHALL execute the associated workflow with the request payload
3. WHEN a schedule trigger is configured, THE System SHALL register a cron job for the workflow
4. WHEN a scheduled time arrives, THE System SHALL execute the workflow automatically
5. WHEN an API trigger is configured, THE System SHALL expose a REST API endpoint for the workflow
6. WHERE a chat trigger is configured, THE System SHALL create a chat interface for the workflow

### Requirement 7: Knowledge Base Integration

**User Story:** As a workflow designer, I want to integrate vector search capabilities, so that workflows can retrieve relevant information from document collections.

#### Acceptance Criteria

1. WHEN a knowledge base is created, THE System SHALL initialize a Milvus collection
2. WHEN documents are uploaded, THE System SHALL parse, chunk, and embed the content
3. WHEN a knowledge base block is executed, THE System SHALL perform vector similarity search using Milvus
4. WHEN search results are returned, THE System SHALL include document metadata and relevance scores
5. WHERE metadata filters are specified, THE System SHALL filter results by document metadata fields

### Requirement 8: Execution Logging and Monitoring

**User Story:** As a workflow operator, I want detailed execution logs, so that I can debug issues and monitor workflow performance.

#### Acceptance Criteria

1. WHEN a workflow executes, THE System SHALL log the start time, end time, and duration
2. WHEN each block executes, THE System SHALL log the block ID, inputs, outputs, and execution time
3. WHEN an error occurs, THE System SHALL log the error message and stack trace
4. WHEN execution completes, THE System SHALL calculate and log token usage and cost
5. WHERE files are generated, THE System SHALL store file metadata in the execution log

### Requirement 9: SubBlock Rendering System

**User Story:** As a developer, I want a flexible SubBlock rendering system, so that blocks can have rich configuration UIs without custom code.

#### Acceptance Criteria

1. WHEN a SubBlock type is 'short-input', THE System SHALL render a single-line text input
2. WHEN a SubBlock type is 'long-input', THE System SHALL render a multi-line textarea
3. WHEN a SubBlock type is 'dropdown', THE System SHALL render a select menu with provided options
4. WHEN a SubBlock type is 'code', THE System SHALL render a code editor with syntax highlighting
5. WHEN a SubBlock type is 'oauth-input', THE System SHALL render an OAuth authentication flow
6. WHERE a SubBlock has conditions, THE System SHALL show/hide the SubBlock based on other field values

### Requirement 10: Workflow Variables and Environment

**User Story:** As a workflow designer, I want to use variables and environment settings, so that workflows can be configured without hardcoding values.

#### Acceptance Criteria

1. WHEN a workflow is created, THE System SHALL allow defining workflow-level variables
2. WHEN a block references a variable, THE System SHALL resolve the variable value at execution time
3. WHEN environment variables are configured, THE System SHALL make them available to all workflows
4. WHERE a variable is marked as secret, THE System SHALL encrypt the value in storage
5. WHERE a variable is used in multiple places, THE System SHALL maintain consistency across references

### Requirement 11: Parallel Execution Support

**User Story:** As a workflow designer, I want to execute multiple blocks in parallel, so that workflows can process data concurrently for better performance.

#### Acceptance Criteria

1. WHEN a parallel block is configured with a count, THE System SHALL execute the specified number of parallel instances
2. WHEN a parallel block is configured with a collection, THE System SHALL execute one instance per collection item
3. WHEN parallel executions complete, THE System SHALL aggregate results from all instances
4. WHERE parallel executions fail, THE System SHALL handle errors independently for each instance
5. WHERE parallel execution limits are reached, THE System SHALL queue additional executions

### Requirement 12: Loop Execution Support

**User Story:** As a workflow designer, I want to execute blocks in loops, so that workflows can process collections and repeat operations.

#### Acceptance Criteria

1. WHEN a for-loop block is configured, THE System SHALL execute the loop body for the specified number of iterations
2. WHEN a forEach-loop block is configured, THE System SHALL execute the loop body once per collection item
3. WHEN loop iteration completes, THE System SHALL make the iteration index and item available to child blocks
4. WHERE a loop has a maximum iteration limit, THE System SHALL enforce the limit
5. WHERE a loop execution fails, THE System SHALL log the failed iteration and halt the loop

### Requirement 13: Workflow Validation

**User Story:** As a workflow designer, I want automatic workflow validation, so that I can identify issues before execution.

#### Acceptance Criteria

1. WHEN a workflow is saved, THE System SHALL validate that all blocks have required inputs configured
2. WHEN a workflow is saved, THE System SHALL detect cycles in the workflow graph
3. WHEN a workflow is saved, THE System SHALL identify disconnected blocks
4. WHERE validation errors exist, THE System SHALL prevent workflow execution
5. WHERE validation warnings exist, THE System SHALL display warnings but allow execution

### Requirement 14: Real-time Collaboration (Future)

**User Story:** As a team member, I want to collaborate on workflows in real-time, so that multiple people can work together efficiently.

#### Acceptance Criteria

1. WHEN multiple users open the same workflow, THE System SHALL synchronize changes in real-time
2. WHEN a user makes a change, THE System SHALL broadcast the change to other connected users
3. WHEN users are editing, THE System SHALL display cursor positions and selections
4. WHERE conflicts occur, THE System SHALL resolve conflicts using last-write-wins strategy
5. WHERE a user disconnects, THE System SHALL clean up their session state

### Requirement 15: Block Testing and Debugging

**User Story:** As a workflow designer, I want to test individual blocks, so that I can verify block behavior before adding them to workflows.

#### Acceptance Criteria

1. WHEN a block is selected for testing, THE System SHALL display a test input form
2. WHEN test inputs are provided, THE System SHALL execute the block with the test inputs
3. WHEN block execution completes, THE System SHALL display the output and execution time
4. WHERE block execution fails, THE System SHALL display the error message
5. WHERE a block has side effects, THE System SHALL warn the user before execution
