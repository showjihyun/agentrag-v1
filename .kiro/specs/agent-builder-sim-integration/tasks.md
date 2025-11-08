# Implementation Plan

> **📖 IMPORTANT**: Before starting, read `.kiro/specs/agent-builder-sim-integration/INTEGRATION_GUIDE.md`
> This guide shows which existing agent-builder components to reuse vs create new.

## Phase 1: Database Schema & Backend Models

- [x] 1. Set up database schema and core models





  - **EXTEND** existing backend/db/models/agent_builder.py (don't create new file)
  - **REUSE** existing Agent, AgentVersion, AgentExecution models
  - **ADD** new models: AgentBlock, AgentEdge, WorkflowSchedule, WorkflowWebhook, WorkflowSubflow
  - **EXTEND** existing Workflow model with new relationships
  - Create Alembic migration for new tables only
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  - _Reference: INTEGRATION_GUIDE.md - Database Infrastructure_

- [x] 1.1 Extend existing database models file


  - **OPEN** backend/db/models/agent_builder.py (existing file)
  - **ADD** AgentBlock model to existing file
  - **ADD** AgentEdge model to existing file
  - **ADD** WorkflowSchedule model to existing file
  - **ADD** WorkflowWebhook model to existing file
  - **ADD** WorkflowSubflow model to existing file
  - **UPDATE** existing Workflow model: add blocks, edges, schedules, webhooks relationships
  - **VERIFY** existing models (Agent, AgentExecution, Variable) are not modified
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  - _Reference: INTEGRATION_GUIDE.md - Phase 1_

- [x] 1.2 Create database migration script


  - Create Alembic migration in backend/alembic/versions/
  - **ONLY** add new tables: agent_blocks, agent_edges, workflow_schedules, workflow_webhooks, workflow_subflows
  - **DO NOT** modify existing tables (agents, workflows, agent_executions)
  - Add foreign keys to existing workflows table
  - Add indexes for performance optimization
  - Test migration up and down
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  - _Reference: IMPLEMENTATION_PHASE1.md_

- [x] 1.3 Extend Pydantic schemas


  - **OPEN** backend/models/agent_builder.py (existing file)
  - **VERIFY** existing schemas: AgentCreate, AgentUpdate, AgentResponse, WorkflowCreate, WorkflowUpdate
  - **ADD** SubBlockConfig schema to existing file
  - **ADD** BlockConfig schema to existing file
  - **ADD** AgentBlockCreate/Update/Response schemas to existing file
  - **ADD** AgentEdgeCreate/Response schemas to existing file
  - **ADD** WorkflowExecutionLogResponse schema to existing file
  - **REUSE** existing ExecutionContext schema
  - Add validation rules for all new schemas
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  - _Reference: INTEGRATION_GUIDE.md - Phase 1_

- [x] 1.4 Write database tests



  - Test AgentBlock CRUD operations
  - Test AgentEdge creation and relationships
  - Test cascade delete behavior
  - Test execution log creation
  - Test schedule and webhook creation
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

## Phase 2: Block System Implementation

- [x] 2. Implement block registry and base blocks



  - **EXTEND** existing backend/services/agent_builder/tool_registry.py
  - **CREATE** new backend/core/blocks/ directory for block system
  - **REUSE** existing tool validation logic
  - Create 5-10 essential tool blocks
  - Add SubBlock rendering support
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  - _Reference: INTEGRATION_GUIDE.md - Backend Services_

- [x] 2.1 Create Block Registry


  - **CREATE** backend/core/blocks/registry.py (new file)
  - **REFERENCE** existing backend/services/agent_builder/tool_registry.py for patterns
  - Implement BlockRegistry class with decorator pattern
  - Add block registration mechanism
  - Implement block lookup by type
  - Add block listing by category
  - **INTEGRATE** with existing ToolRegistry for tool blocks
  - _Requirements: 1.1, 1.2, 1.3_
  - _Reference: INTEGRATION_GUIDE.md - Backend Services_

- [x] 2.2 Implement Base Block class


  - **CREATE** backend/core/blocks/base.py (new file)
  - Create BaseBlock abstract class
  - Define execute() method interface
  - Implement get_config() class method
  - Add input validation logic
  - **REUSE** existing error handling from backend/agents/error_recovery.py
  - _Requirements: 1.1, 1.2, 1.3, 1.4_
  - _Reference: INTEGRATION_GUIDE.md - Backend Services_

- [x] 2.3 Create OpenAI block


  - Implement OpenAIBlock with chat completion
  - Add SubBlocks for model, prompt, temperature
  - Configure tool access for openai_chat
  - Define input/output schemas
  - Add API key authentication
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2.4 Create HTTP block


  - Implement HTTPBlock for API requests
  - Add SubBlocks for URL, method, headers, body
  - Support GET, POST, PUT, DELETE methods
  - Define input/output schemas
  - Add response transformation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2.5 Create Condition block


  - Implement ConditionBlock for branching logic
  - Add SubBlocks for condition expression
  - Support multiple condition paths
  - Define input/output schemas
  - Add condition evaluation engine
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.2_

- [x] 2.6 Create Loop block


  - Implement LoopBlock for iteration
  - Add SubBlocks for loop type (for/forEach)
  - Support iteration count and collection iteration
  - Define input/output schemas
  - Add loop state management
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.3, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 2.7 Create Parallel block


  - Implement ParallelBlock for concurrent execution
  - Add SubBlocks for parallel count/collection
  - Support result aggregation
  - Define input/output schemas
  - Add parallel execution management
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.4, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 2.8 Write block tests



  - Test block registration and lookup
  - Test OpenAI block execution
  - Test HTTP block execution
  - Test Condition block evaluation
  - Test Loop block iteration
  - Test Parallel block concurrency
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 15.1, 15.2, 15.3, 15.4, 15.5_

## Phase 3: Execution Engine Implementation

- [x] 3. Build workflow execution engine




  - Implement Workflow Executor
  - Add execution context management
  - Implement control flow (conditions, loops, parallel)
  - Add execution logging
  - Implement error handling
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 3.1 Implement Workflow Executor core


  - Create WorkflowExecutor class
  - Implement workflow loading from database
  - Add topological sort for block execution order
  - Implement block execution loop
  - Add execution result aggregation
  - _Requirements: 3.1, 3.6_

- [x] 3.2 Implement Execution Context


  - Create ExecutionContext dataclass
  - Add block state management
  - Implement execution log collection
  - Add variable resolution
  - Create context serialization
  - _Requirements: 3.1, 3.6, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 3.3 Implement condition branching


  - Add condition evaluation logic
  - Implement path selection based on condition result
  - Store routing decisions in context
  - Add condition result logging
  - Handle condition evaluation errors
  - _Requirements: 3.2_

- [x] 3.4 Implement loop execution


  - Add for-loop execution logic
  - Add forEach-loop execution logic
  - Implement iteration state tracking
  - Add loop result aggregation
  - Handle loop execution errors
  - _Requirements: 3.3, 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 3.5 Implement parallel execution


  - Add parallel execution manager
  - Implement concurrent block execution
  - Add result aggregation from parallel branches
  - Implement parallel execution limits
  - Handle parallel execution errors
  - _Requirements: 3.4, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 3.6 Implement execution logging


  - Create execution log entry on workflow start
  - Log each block execution with timing
  - Log errors with stack traces
  - Calculate and log token usage/cost
  - Store file metadata in logs
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 3.7 Implement error handling


  - Add try-catch blocks for block execution
  - Implement error logging
  - Add error recovery strategies
  - Create error response formatting
  - Handle execution timeouts
  - _Requirements: 3.5_

- [x] 3.8 Write execution engine tests



  - Test simple workflow execution
  - Test condition branching
  - Test loop execution
  - Test parallel execution
  - Test error handling
  - Test execution logging
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

## Phase 4: Frontend Workflow Editor

- [-] 4. Build visual workflow editor



  - Implement ReactFlow-based editor
  - Create Block Palette component
  - Build block configuration panel
  - Add SubBlock rendering components
  - Implement workflow save/load
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 4.1 Create Workflow Editor component


  - Set up ReactFlow canvas
  - Implement node rendering
  - Add edge rendering
  - Implement drag-and-drop from palette
  - Add zoom and pan controls
  - _Requirements: 5.1, 5.2, 5.3_

- [x] 4.2 Create Block Palette component


  - Implement block list display
  - Add category filtering (blocks/tools/triggers)
  - Implement search functionality
  - Add drag-and-drop support
  - Display block icons and descriptions
  - _Requirements: 5.2_

- [x] 4.3 Create block configuration panel


  - Implement side panel for block settings
  - Add SubBlock rendering
  - Implement form validation
  - Add save/cancel actions
  - Display validation errors
  - _Requirements: 5.4, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 4.4 Implement SubBlock components


  - Create ShortInput component
  - Create LongInput component
  - Create Dropdown component
  - Create CodeEditor component
  - Create OAuthInput component
  - Create conditional rendering logic
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 4.5 Implement workflow save/load


  - Add save workflow API call
  - Implement workflow loading on mount
  - Add auto-save functionality
  - Implement version history
  - Add save confirmation UI
  - _Requirements: 5.5_

- [x] 4.6 Add workflow validation UI


  - Implement validation on save
  - Display validation errors on blocks
  - Add validation error panel
  - Highlight invalid connections
  - Show validation warnings
  - _Requirements: 5.6, 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 4.7 Write frontend tests





  - Test workflow editor rendering
  - Test block addition and removal
  - Test edge creation
  - Test block configuration
  - Test workflow save/load
  - Test validation UI
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

## Phase 5: Tool Integration System
-

- [x] 5. Integrate 70+ tools






  - Create Tool Registry
  - Implement tool execution framework
  - Add OAuth authentication support
  - Integrate AI/LLM tools (10+ tools)
  - Integrate communication tools (10+ tools)
  - Integrate productivity tools (10+ tools)
  - Integrate data tools (10+ tools)
  - Integrate search tools (5+ tools)
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 5.1 Create Tool Registry


  - Implement ToolRegistry class
  - Add tool registration mechanism
  - Implement tool lookup by ID
  - Add tool execution wrapper
  - Create tool response transformation
  - _Requirements: 4.1, 4.2_

- [x] 5.2 Implement OAuth authentication


  - Create OAuth flow for tool authentication
  - Add credential storage
  - Implement token refresh
  - Add OAuth UI components
  - Handle OAuth errors
  - _Requirements: 4.3_

- [x] 5.3 Integrate AI/LLM tools


  - Add Anthropic (Claude) integration
  - Add Google (Gemini) integration
  - Add Mistral integration
  - Add Groq integration
  - Add Cerebras integration
  - Add Perplexity integration
  - Add DeepSeek integration
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5.4 Integrate communication tools

  - Add Slack integration
  - Add Discord integration
  - Add Telegram integration
  - Add WhatsApp integration
  - Add Twilio SMS integration
  - Add Microsoft Teams integration
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5.5 Integrate productivity tools

  - Add Gmail integration
  - Add Google Calendar integration
  - Add Google Docs integration
  - Add Google Sheets integration
  - Add Notion integration
  - Add Microsoft Excel integration
  - Add Outlook integration
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5.6 Integrate data tools

  - Add MongoDB integration
  - Add PostgreSQL integration
  - Add MySQL integration
  - Add Supabase integration
  - Add Pinecone integration
  - Add Qdrant integration
  - Add S3 integration
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5.7 Integrate search tools

  - Add Tavily integration
  - Add Serper integration
  - Add Exa integration
  - Add Wikipedia integration
  - Add Arxiv integration
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5.8 Write tool integration tests



  - Test tool registration and lookup
  - Test OAuth authentication flow
  - Test AI/LLM tool execution
  - Test communication tool execution
  - Test productivity tool execution
  - Test data tool execution
  - Test search tool execution
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

## Phase 6: Trigger System
-



- [x] 6. Implement trigger system






  - Create Trigger Manager
  - Implement webhook triggers
  - Implement schedule triggers
  - Implement API triggers
  - Implement chat triggers
  - Add trigger configuration UI
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 6.1 Create Trigger Manager


  - Implement TriggerManager class
  - Add trigger registration
  - Implement trigger execution
  - Add trigger status monitoring
  - Create trigger logging
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 6.2 Implement webhook triggers


  - Create webhook endpoint handler
  - Generate unique webhook URLs
  - Add webhook signature verification
  - Implement webhook payload parsing
  - Add webhook execution logging
  - _Requirements: 6.1, 6.2_

- [x] 6.3 Implement schedule triggers


  - Integrate Celery for scheduling
  - Add cron expression parsing
  - Implement schedule registration
  - Add schedule execution
  - Implement schedule monitoring
  - _Requirements: 6.3, 6.4_

- [x] 6.4 Implement API triggers


  - Create REST API endpoints for workflows
  - Add API key authentication
  - Implement rate limiting
  - Add API request validation
  - Create API response formatting
  - _Requirements: 6.5_

- [x] 6.5 Implement chat triggers


  - Create chat interface
  - Add chat message handling
  - Implement conversation context
  - Add chat response streaming
  - Create chat UI components
  - _Requirements: 6.6_

- [x] 6.6 Add trigger configuration UI


  - Create trigger configuration panel
  - Add webhook URL display
  - Implement cron expression builder
  - Add API key management UI
  - Create chat interface settings
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 6.7 Write trigger system tests



  - Test webhook trigger execution
  - Test schedule trigger execution
  - Test API trigger execution
  - Test chat trigger execution
  - Test trigger configuration


  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

## -hase 7: Knowledge Base Integration


- [-] 7. Integrate Knowledge Base system with existing Milvus







  - Connect to existing Milvus collections
  - Implement document upload workflow
  - Add vector search integration
  - Create Knowledge Base block
  - Add Knowledge Base UI
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7.1 Connect to existing Milvus


  - Use existing Milvus connection from backend/models/milvus_schema.py
  - Verify document collection schema compatibility
  - Test Milvus connection and search
  - Configure collection parameters
  - Add error handling for Milvus operations
  - _Requirements: 7.1_

- [x] 7.2 Implement document processing workflow


  - Reuse existing document upload API
  - Integrate with existing file parsing (PDF, DOCX, TXT)
  - Use existing text chunking logic
  - Leverage existing chunk metadata extraction
  - Connect to existing document storage
  - _Requirements: 7.2_

- [x] 7.3 Implement embedding generation


  - Use existing embedding service (sentence-transformers)
  - Reuse batch embedding generation
  - Leverage existing embedding caching
  - Connect to existing Milvus storage
  - Use existing embedding update logic
  - _Requirements: 7.2_

- [x] 7.4 Implement vector search integration


  - Use existing Milvus similarity search
  - Implement metadata filtering (author, date, language, keywords)
  - Add result ranking with existing logic
  - Implement search result formatting
  - Create workflow-compatible search API



  
  - _Requirements: 7.3, 7.4, 7.5_

- [x] 7.5 Create Knowledge Base block


  - Implement KnowledgeBaseBlock
  - Add SubBlocks for query and metadata filters
  - Configure Milvus search execution
  - Define input/output schemas
  - Add search result transformation
  - _Requirements: 7.3, 7.4, 7.5_

- [x] 7.6 Add Knowledge Base UI for workflows





  - Create knowledge base selector component
  - Add document collection browser
  - Implement metadata filter UI
  - Add search preview interface
  - Create result visualization
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7.7 Write Knowledge Base integration tests






  - Test Milvus connection from workflow
  - Test document search from block
  - Test metadata filtering
  - Test result formatting
  - Test Knowledge Base block execution
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

## Phase 8: Advanced Features
-



-

- [x] 8. Implement advanced features




  - Add workflow variables system
  - Implement execution console
  - Add workflow validation
  - Create workflow templates
  - Implement workflow versioning
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 8.1 Implement workflow variables


  - Add variable definition UI
  - Implement variable resolution
  - Add environment variable support
  - Create secret variable encryption
  - Implement variable validation
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 8.2 Create execution console


  - Build execution log viewer
  - Add real-time execution updates
  - Implement log filtering
  - Add execution timeline view
  - Create execution export
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 8.3 Implement workflow validation


  - Add graph cycle detection
  - Implement disconnected node detection
  - Add required input validation
  - Create validation error reporting
  - Implement validation warnings
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 8.4 Create workflow templates


  - Add template creation from workflow
  - Implement template library
  - Add template instantiation
  - Create template sharing
  - Implement template versioning
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 8.5 Implement workflow versioning


  - Add version creation on save
  - Implement version history view
  - Add version comparison
  - Create version rollback
  - Implement version tagging
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 8.6 Write advanced features tests



  - Test variable resolution
  - Test execution console updates
  - Test workflow validation
  - Test template creation and use
  - Test workflow versioning
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 13.1, 13.2, 13.3, 13.4, 13.5_
