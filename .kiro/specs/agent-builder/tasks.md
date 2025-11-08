# Implementation Plan

This document outlines the implementation tasks for the Agent Builder feature. Tasks are organized into phases and include specific coding objectives with references to requirements.

## Task Organization

- Tasks are numbered with decimal notation (e.g., 1.1, 1.2)
- Sub-tasks marked with `*` are optional (testing, documentation)
- Each task references specific requirements from requirements.md
- Tasks build incrementally on previous work

---

## Phase 1: Database Schema and Core Models

- [x] 1. Set up database schema and SQLAlchemy models







  - Create Alembic migration scripts for all Agent Builder tables
  - Implement SQLAlchemy ORM models with relationships in backend/db/models/
  - Add indexes for performance optimization
  - _Requirements: 1.4, 6.1, 8.3, 11.2_

- [x] 1.1 Create agent-related database models


  - Create backend/db/models/agent_builder.py with Agent, AgentVersion, AgentTool, Tool models
  - Add foreign key constraints to users table
  - Add indexes on user_id, agent_type, created_at, deleted_at
  - Update backend/db/models/__init__.py to export new models
  - _Requirements: 1.4, 6.1_

- [x] 1.2 Create block-related database models


  - Add Block, BlockVersion, BlockDependency, BlockTestCase models to agent_builder.py
  - Add unique constraints on block names per user
  - Add indexes on user_id, block_type, is_public
  - _Requirements: 24.4, 27.1_

- [x] 1.3 Create workflow-related database models


  - Add Workflow, WorkflowNode, WorkflowEdge models to agent_builder.py
  - Add JSON column for graph_definition
  - Add indexes on user_id, is_public
  - _Requirements: 4.5, 7.1_

- [x] 1.4 Create knowledgebase-related database models


  - Add Knowledgebase, KnowledgebaseDocument, KnowledgebaseVersion models to agent_builder.py
  - Add unique constraint on milvus_collection_name
  - Add indexes on user_id, created_at
  - _Requirements: 31.1, 35.1_

- [x] 1.5 Create variable and secret database models


  - Add Variable, Secret models to agent_builder.py
  - Add unique constraint on (name, scope, scope_id)
  - Add indexes on scope, scope_id, deleted_at
  - _Requirements: 32.2, 32.3_

- [x] 1.6 Create execution-related database models


  - Add AgentExecution, ExecutionStep, ExecutionMetrics, ExecutionSchedule models to agent_builder.py
  - Add indexes on execution_id, agent_id, user_id, status, started_at
  - Add foreign keys to agents and users tables
  - _Requirements: 8.3, 17.2, 21.1_

- [x] 1.7 Create permission and audit database models


  - Add Permission, ResourceShare, AuditLog models to agent_builder.py
  - Add unique constraint on (user_id, resource_type, resource_id, action)
  - Add indexes on user_id, resource_type, resource_id, timestamp
  - _Requirements: 11.1, 11.5, 34.1_

- [x] 1.8 Create Alembic migration for Agent Builder tables


  - Create migration file in backend/alembic/versions/
  - Include all table creations with proper constraints and indexes
  - Test migration up and down
  - _Requirements: 1.4_

- [x] 1.9 Write database model unit tests



  - Create backend/tests/unit/test_agent_builder_models.py
  - Test model creation, relationships, and constraints
  - Test soft delete functionality
  - _Requirements: 1.4_

---

## Phase 2: Backend Services - Core Infrastructure
- [x] 2. Implement core backend services and utilities



- [ ] 2. Implement core backend services and utilities

  - Create service layer classes in backend/services/agent_builder/
  - Implement error handling using existing backend/agents/error_recovery.py
  - Add input validation using Pydantic models
  - _Requirements: 1.4, 1.5, 10.3_

- [x] 2.1 Create Pydantic schemas for Agent Builder


  - Create backend/models/agent_builder.py with request/response schemas
  - Define AgentCreate, AgentUpdate, AgentResponse schemas
  - Define BlockCreate, BlockUpdate, WorkflowCreate schemas
  - Define ExecutionContext, AgentStep schemas (extend existing models/agent.py)
  - _Requirements: 1.1, 1.4, 5.3_

- [x] 2.2 Implement ToolRegistry service


  - Create backend/services/agent_builder/tool_registry.py
  - Register existing agents as tools (VectorSearchAgent, WebSearchAgent, LocalDataAgent)
  - Implement tool validation using LangChain tool schemas
  - Add DatabaseQueryTool, FileOperationTool, HTTPAPICallTool classes
  - Store tool definitions in database using Tool model
  - _Requirements: 3.1, 3.2, 3.3, 10.1_

- [x] 2.3 Implement VariableResolver and SecretManager


  - Create backend/services/agent_builder/variable_resolver.py
  - Implement scope precedence logic (agent > user > workspace > global)
  - Add Redis caching using existing backend/core/cache_manager.py
  - Create backend/services/agent_builder/secret_manager.py with AES-256 encryption
  - Implement variable substitution with ${variable_name} format
  - _Requirements: 32.2, 32.3, 32.4, 36.1, 36.2_

- [x] 2.4 Implement AgentService


  - Create backend/services/agent_builder/agent_service.py
  - Implement CRUD operations using SQLAlchemy
  - Add agent creation with tool attachment via AgentTool model
  - Implement agent cloning (copy with new ID and user_id)
  - Add export/import as JSON with version history
  - Implement soft delete (set deleted_at timestamp)
  - _Requirements: 1.1, 1.2, 1.4, 6.1, 6.4, 6.5_

- [x] 2.5 Implement BlockService


  - Create backend/services/agent_builder/block_service.py
  - Implement CRUD operations for blocks
  - Add block type validation (llm, tool, logic, composite)
  - Implement block testing with isolated execution
  - Add composite block creation from workflow definitions
  - _Requirements: 24.1, 24.3, 24.4, 26.1, 28.2_

- [x] 2.6 Implement WorkflowService


  - Create backend/services/agent_builder/workflow_service.py
  - Implement CRUD operations for workflows
  - Add workflow validation (detect cycles using graph algorithms)
  - Implement workflow export/import as JSON
  - Add workflow node and edge management
  - _Requirements: 4.1, 4.2, 4.5, 13.5_

- [x] 2.7 Implement KnowledgebaseService


  - Create backend/services/agent_builder/knowledgebase_service.py
  - Implement Milvus collection creation using existing backend/services/milvus.py
  - Add document upload integration with existing backend/services/document_processor.py
  - Implement hybrid search using existing backend/services/hybrid_search.py
  - Add version management with KnowledgebaseVersion model
  - Implement rollback by restoring document snapshots
  - _Requirements: 31.1, 31.2, 31.4, 35.1, 35.4_

- [x] 2.8 Write service layer unit tests






  - Create backend/tests/unit/test_agent_builder_services.py
  - Test each service method with mocked database
  - Test error handling and validation
  - _Requirements: All Phase 2_

---

## Phase 3: Workflow Execution Engine
-

- [x] 3. Implement LangGraph-based workflow execution engine




  - Create WorkflowExecutor in backend/services/agent_builder/
  - Implement StateGraph compilation from workflow definitions
  - Add streaming execution with SSE using existing infrastructure
  - Integrate with existing backend/memory/manager.py and backend/services/llm_manager.py
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 10.2, 10.3_

- [x] 3.1 Install and configure LangGraph dependencies


  - Add langgraph to backend/requirements.txt
  - Test LangGraph StateGraph creation and compilation
  - Verify compatibility with existing LangChain setup
  - _Requirements: 7.1_

- [x] 3.2 Implement WorkflowExecutor core


  - Create backend/services/agent_builder/workflow_executor.py
  - Implement compile_workflow() to convert Workflow model to LangGraph StateGraph
  - Add LRU cache for compiled graphs (use functools.lru_cache)
  - Implement state initialization with variables from VariableResolver
  - Add knowledgebase loading from KnowledgebaseService
  - _Requirements: 7.1, 15.4_

- [x] 3.3 Implement node execution functions


  - Create _create_agent_node() that loads Agent model and executes
  - Create _create_block_node() that loads Block model and executes
  - Create _create_control_node() for conditional, loop, and parallel nodes
  - Add state management to pass data between nodes
  - Store execution results in LangGraph state dictionary
  - _Requirements: 7.1, 33.1, 33.2, 33.3_

- [x] 3.4 Implement BlockExecutor


  - Create backend/services/agent_builder/block_executor.py
  - Implement _execute_llm_block() using existing backend/services/llm_manager.py
  - Implement _execute_tool_block() using ToolRegistry
  - Implement _execute_logic_block() with restricted Python exec() environment
  - Implement _execute_composite_block() with nested WorkflowExecutor call
  - _Requirements: 24.3, 26.3, 28.2_

- [x] 3.5 Implement streaming execution


  - Add execute_workflow() async generator method
  - Yield AgentStep objects for each LangGraph node execution
  - Format steps for SSE using existing backend/api/query.py SSE patterns
  - Add execution logging to AgentExecution and ExecutionStep models
  - _Requirements: 5.2, 5.3, 10.5, 20.1, 20.2, 20.3_

- [x] 3.6 Implement parallel execution


  - Add parallel node support using LangGraph Send API
  - Implement concurrent execution with asyncio.gather()
  - Add semaphore to limit concurrent LLM calls (max 5)
  - Implement result aggregation from parallel branches
  - _Requirements: 7.2, 15.3, 33.2_

- [x] 3.7 Implement error handling and retry logic


  - Integrate existing backend/services/retry_handler.py
  - Add block-level error configuration (retry_count, fallback_value)
  - Implement fallback behavior when retries exhausted
  - Add asyncio.timeout for execution timeouts (60 seconds default)
  - Log errors to AgentExecution model with error_message field
  - _Requirements: 7.3, 7.5, 30.1, 30.2, 30.3_

- [x] 3.8 Write workflow execution integration tests



  - Create backend/tests/integration/test_workflow_execution.py
  - Test simple sequential workflow execution
  - Test parallel execution with multiple branches
  - Test conditional branching with Python expressions
  - Test error handling and retry mechanisms
  - _Requirements: All Phase 3_

---

## Phase 4: Backend API Endpoints

- [x] 4. Implement FastAPI endpoints for Agent Builder







  - Create API routers in backend/api/agent_builder/
  - Add JWT authentication using existing backend/core/auth_dependencies.py
  - Implement request/response models using Pydantic schemas from Phase 2
  - Add OpenAPI documentation with tags and descriptions
  - _Requirements: 1.1, 11.1, 34.2_

- [x] 4.1 Implement Agent API endpoints


  - Create backend/api/agent_builder/agents.py router
  - POST /api/agent-builder/agents - Create agent (requires auth)
  - GET /api/agent-builder/agents/{agent_id} - Get agent (check permissions)
  - PUT /api/agent-builder/agents/{agent_id} - Update agent (check ownership)
  - DELETE /api/agent-builder/agents/{agent_id} - Soft delete agent
  - GET /api/agent-builder/agents - List user's agents with pagination
  - POST /api/agent-builder/agents/{agent_id}/clone - Clone agent
  - GET /api/agent-builder/agents/{agent_id}/export - Export as JSON
  - POST /api/agent-builder/agents/import - Import from JSON
  - Register router in backend/main.py
  - _Requirements: 1.1, 1.4, 6.4, 6.5, 9.3_

- [x] 4.2 Implement Block API endpoints


  - Create backend/api/agent_builder/blocks.py router
  - POST /api/agent-builder/blocks - Create block
  - GET /api/agent-builder/blocks/{block_id} - Get block
  - PUT /api/agent-builder/blocks/{block_id} - Update block
  - DELETE /api/agent-builder/blocks/{block_id} - Delete block
  - GET /api/agent-builder/blocks - List blocks with type filter
  - POST /api/agent-builder/blocks/{block_id}/test - Test block execution
  - GET /api/agent-builder/blocks/{block_id}/versions - Get version history
  - Register router in backend/main.py
  - _Requirements: 24.1, 24.4, 27.1, 28.1, 28.2_

- [x] 4.3 Implement Workflow API endpoints


  - Create backend/api/agent_builder/workflows.py router
  - POST /api/agent-builder/workflows - Create workflow
  - GET /api/agent-builder/workflows/{workflow_id} - Get workflow
  - PUT /api/agent-builder/workflows/{workflow_id} - Update workflow
  - DELETE /api/agent-builder/workflows/{workflow_id} - Delete workflow
  - GET /api/agent-builder/workflows - List workflows
  - POST /api/agent-builder/workflows/{workflow_id}/validate - Validate graph
  - POST /api/agent-builder/workflows/{workflow_id}/compile - Compile to LangGraph
  - Register router in backend/main.py
  - _Requirements: 4.1, 4.5, 13.5_

- [x] 4.4 Implement Knowledgebase API endpoints


  - Create backend/api/agent_builder/knowledgebases.py router
  - POST /api/agent-builder/knowledgebases - Create knowledgebase
  - GET /api/agent-builder/knowledgebases/{kb_id} - Get knowledgebase
  - PUT /api/agent-builder/knowledgebases/{kb_id} - Update knowledgebase
  - DELETE /api/agent-builder/knowledgebases/{kb_id} - Delete knowledgebase
  - POST /api/agent-builder/knowledgebases/{kb_id}/documents - Upload documents
  - GET /api/agent-builder/knowledgebases/{kb_id}/search - Search with query
  - GET /api/agent-builder/knowledgebases/{kb_id}/versions - Get versions
  - POST /api/agent-builder/knowledgebases/{kb_id}/rollback - Rollback version
  - Register router in backend/main.py
  - _Requirements: 31.1, 31.2, 31.4, 35.1, 35.3, 35.4_

- [x] 4.5 Implement Variable API endpoints


  - Create backend/api/agent_builder/variables.py router
  - POST /api/agent-builder/variables - Create variable
  - GET /api/agent-builder/variables/{var_id} - Get variable
  - PUT /api/agent-builder/variables/{var_id} - Update variable
  - DELETE /api/agent-builder/variables/{var_id} - Soft delete variable
  - GET /api/agent-builder/variables - List variables with scope filter
  - POST /api/agent-builder/variables/resolve - Resolve template variables
  - Register router in backend/main.py
  - _Requirements: 32.1, 32.2, 32.4, 36.1, 36.3_

- [x] 4.6 Implement Execution API endpoints


  - Create backend/api/agent_builder/executions.py router
  - POST /api/agent-builder/executions/agents/{agent_id} - Execute agent with SSE
  - POST /api/agent-builder/executions/workflows/{workflow_id} - Execute workflow with SSE
  - GET /api/agent-builder/executions/{execution_id} - Get execution details
  - GET /api/agent-builder/executions - List executions with filters
  - POST /api/agent-builder/executions/{execution_id}/cancel - Cancel running execution
  - POST /api/agent-builder/executions/{execution_id}/replay - Replay with same inputs
  - POST /api/agent-builder/executions/schedules - Create cron schedule
  - Register router in backend/main.py
  - _Requirements: 5.1, 5.2, 17.1, 17.2, 22.1, 22.2_

- [x] 4.7 Implement Permission API endpoints


  - Create backend/api/agent_builder/permissions.py router
  - POST /api/agent-builder/permissions - Grant permission
  - DELETE /api/agent-builder/permissions/{permission_id} - Revoke permission
  - GET /api/agent-builder/permissions - List user permissions
  - POST /api/agent-builder/shares - Create shareable link with token
  - GET /api/agent-builder/shares/{token} - Access shared resource
  - Register router in backend/main.py
  - _Requirements: 9.1, 9.2, 11.1, 34.1, 34.3, 34.4_

- [x] 4.8 Write API integration tests



  - Create backend/tests/integration/test_agent_builder_api.py
  - Test all endpoints with JWT authentication
  - Test permission checks and ownership validation
  - Test error responses (400, 401, 403, 404)
  - Test pagination and filtering
  - _Requirements: All Phase 4_

---

## Phase 5: Frontend - Agent Builder UI with shadcn/ui
-
-

- [x] 5. Implement Agent Builder user interface with shadcn/ui






  - Install required shadcn/ui components in frontend/
  - Create React components in frontend/components/agent-builder/
  - Add form validation with react-hook-form and zod
  - Implement API client in frontend/lib/api/agent-builder.ts
  - Follow ui-design.md specifications for all components
  - _Requirements: 1.1, 1.2, 1.3, 12.1_
  - _Reference: .kiro/specs/agent-builder/ui-design.md_

- [x] 5.1 Install shadcn/ui components and dependencies


  - Run npx shadcn-ui@latest add button card input label select textarea dialog dropdown-menu tabs badge separator scroll-area toast alert skeleton table form popover command sheet accordion switch slider progress avatar tooltip
  - Install @monaco-editor/react for prompt editor
  - Install react-hook-form and zod for form validation
  - Install @tanstack/react-query for API state management
  - Verify Tailwind CSS configuration supports all components
  - _Requirements: 1.1_
  - _Reference: ui-design.md - Design System section_

- [x] 5.2 Create AgentBuilder main layout and routing


  - Create frontend/app/agent-builder/layout.tsx with sidebar navigation
  - Add navigation links: Agents, Blocks, Workflows, Knowledgebases, Variables, Executions
  - Use shadcn/ui Button (variant: ghost) and ScrollArea for sidebar
  - Add Lucide icons for each navigation item
  - Implement responsive layout with mobile menu
  - _Requirements: 1.1_
  - _Reference: ui-design.md - Agent Builder Main Layout_

- [x] 5.3 Create AgentList page with shadcn/ui


  - Create frontend/app/agent-builder/agents/page.tsx
  - Fetch agents from GET /api/agent-builder/agents
  - Display agent grid using shadcn/ui Card components
  - Add search input with debounced filtering
  - Add type filter dropdown (All, Custom, Template)
  - Implement agent actions: Edit, Clone, Export, Delete with DropdownMenu
  - Add empty state with "Create Agent" button
  - Add loading skeleton using shadcn/ui Skeleton
  - _Requirements: 1.1, 6.2, 9.3_
  - _Reference: ui-design.md - Agent List Page_

- [x] 5.4 Create AgentForm component with shadcn/ui


  - Create frontend/components/agent-builder/AgentForm.tsx
  - Use shadcn/ui Form with react-hook-form and zod validation
  - Add fields: name (required), description, agent_type, llm_provider, llm_model
  - Add tool selection section with Switch toggles
  - Add prompt template textarea with monospace font
  - Implement form submission to POST /api/agent-builder/agents
  - Add error handling and toast notifications
  - _Requirements: 1.1, 1.2, 3.1_
  - _Reference: ui-design.md - Agent Creation/Edit Form_

- [x] 5.5 Create ToolSelector component with shadcn/ui

  - Create frontend/components/agent-builder/ToolSelector.tsx
  - Fetch tools from GET /api/agent-builder/tools
  - Display tools in Card grid with Switch for selection
  - Add search input for tool filtering
  - Add category filter dropdown
  - Show tool description and Badge for category
  - Implement tool configuration Dialog for selected tools
  - _Requirements: 3.1, 3.2_
  - _Reference: ui-design.md - Agent Creation/Edit Form (Tools section)_

- [x] 5.6 Create PromptTemplateEditor component with shadcn/ui

  - Create frontend/components/agent-builder/PromptTemplateEditor.tsx
  - Integrate @monaco-editor/react with LangChain syntax highlighting
  - Add variable autocomplete for ${variable_name} format
  - Show prompt preview Card with sample variable substitution
  - Display token count Badge using tiktoken-js
  - Add "Advanced Editor" button opening full-screen Dialog
  - _Requirements: 12.1, 12.2, 12.3_
  - _Reference: ui-design.md - Agent Creation/Edit Form (Prompt Template section)_

- [x] 5.7 Create AgentTestPanel component with shadcn/ui

  - Create frontend/components/agent-builder/AgentTestPanel.tsx
  - Implement test Dialog with query Textarea
  - Add context variables Accordion with key-value inputs
  - Connect to POST /api/agent-builder/executions/agents/{id} SSE endpoint
  - Stream AgentStep objects in real-time using EventSource
  - Display steps in ScrollArea with Card for each step
  - Show step type icons (Brain, Zap, Eye, MessageSquare)
  - Display execution metrics Card (duration, tokens, tool calls)
  - Add error Alert with stack trace display
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - _Reference: ui-design.md - Agent Test Panel_

- [x] 5.8 Write frontend component tests


  - Create frontend/__tests__/agent-builder/ directory
  - Test AgentForm validation with invalid inputs
  - Test ToolSelector selection and filtering
  - Test PromptTemplateEditor variable suggestions
  - Test AgentTestPanel SSE streaming with mock EventSource
  - Test responsive layouts at different breakpoints
  - _Requirements: All Phase 5_

---

## Phase 6: Frontend - Workflow Designer with shadcn/ui
-

- [x] 6. Implement visual workflow designer with React Flow




  - Install reactflow library in frontend/
  - Create workflow designer page in frontend/app/agent-builder/workflows/[id]/designer/
  - Implement drag-and-drop node palette
  - Add connection validation and properties panel
  - _Requirements: 4.1, 4.2, 4.3, 13.1, 13.2, 13.3_
  - _Reference: ui-design.md - Workflow Designer Canvas_

- [x] 6.1 Install React Flow and create WorkflowDesigner page


  - Install reactflow package
  - Create frontend/app/agent-builder/workflows/[id]/designer/page.tsx
  - Add toolbar with Save, Validate, Run buttons
  - Create sidebar palette with draggable agent/block/control nodes
  - Use shadcn/ui Button, ScrollArea, Card for layout
  - _Requirements: 13.1_
  - _Reference: ui-design.md - Workflow Designer Canvas_

- [x] 6.2 Create custom React Flow node components


  - Create frontend/components/agent-builder/workflow-nodes/AgentNode.tsx
  - Create frontend/components/agent-builder/workflow-nodes/BlockNode.tsx
  - Create frontend/components/agent-builder/workflow-nodes/ControlNode.tsx
  - Add input/output handles for connections
  - Style nodes with shadcn/ui Card styling
  - _Requirements: 13.1, 13.2_

- [x] 6.3 Implement node drag-and-drop and connection logic


  - Implement onDragStart handler for palette items
  - Implement onDrop handler on canvas to create nodes
  - Add onConnect handler with schema validation
  - Prevent invalid connections (type mismatch)
  - Show validation errors with toast notifications
  - _Requirements: 4.2, 13.2, 13.3_

- [x] 6.4 Create workflow properties panel with shadcn/ui Sheet


  - Create frontend/components/agent-builder/WorkflowPropertiesPanel.tsx
  - Use shadcn/ui Sheet for slide-out panel
  - Add node configuration forms (agent settings, block params, conditions)
  - Implement variable mapping UI for data flow
  - Add conditional expression editor for branch nodes
  - _Requirements: 4.3, 4.4, 13.4_
  - _Reference: ui-design.md - Workflow Designer Canvas (Properties Panel)_

- [x] 6.5 Implement workflow save, validate, and execute


  - Add save handler to POST /api/agent-builder/workflows
  - Add validate handler to POST /api/agent-builder/workflows/{id}/validate
  - Add execute handler to POST /api/agent-builder/executions/workflows/{id}
  - Show execution progress by highlighting active nodes
  - Display results in Dialog with execution metrics
  - _Requirements: 5.2, 13.5_

- [x] 6.6 Write workflow designer tests



  - Test node creation from palette
  - Test connection validation logic
  - Test workflow save and load
  - Test execution visualization
  - _Requirements: All Phase 6_

---

## Phase 7: Frontend - Block Library and Knowledgebase Manager
-

- [x] 7. Implement Block Library and Knowledgebase Manager UI




  - Create block browser and editor pages
  - Implement knowledgebase management UI
  - Add document upload with progress tracking
  - _Requirements: 24.1, 25.1, 31.1, 31.2_
  - _Reference: ui-design.md - Block Library Page_

- [x] 7.1 Create BlockLibrary page with shadcn/ui


  - Create frontend/app/agent-builder/blocks/page.tsx
  - Fetch blocks from GET /api/agent-builder/blocks
  - Display blocks in Card grid with category Tabs (LLM, Tool, Logic, Composite)
  - Add search Input with filtering
  - Show block actions in DropdownMenu (Edit, Test, Delete)
  - Add "Create Block" button
  - _Requirements: 25.1, 25.2_
  - _Reference: ui-design.md - Block Library Page_

- [x] 7.2 Create BlockEditor component


  - Create frontend/components/agent-builder/BlockEditor.tsx
  - Add block type Select (LLM, Tool, Logic, Composite)
  - Implement input/output schema editor with JSON editor
  - Add Monaco Editor for Logic block code
  - Add workflow designer integration for Composite blocks
  - Submit to POST /api/agent-builder/blocks
  - _Requirements: 24.1, 24.2, 26.1_

- [x] 7.3 Create BlockTestPanel component


  - Create frontend/components/agent-builder/BlockTestPanel.tsx
  - Generate test input form from block's input schema
  - Execute block via POST /api/agent-builder/blocks/{id}/test
  - Display output and execution metrics
  - Add test case save functionality
  - _Requirements: 28.1, 28.2, 28.3, 28.4_

- [x] 7.4 Create KnowledgebaseManager page


  - Create frontend/app/agent-builder/knowledgebases/page.tsx
  - Fetch knowledgebases from GET /api/agent-builder/knowledgebases
  - Display knowledgebases in Table with document count and size
  - Add create/edit/delete actions
  - Show version history
  - _Requirements: 31.1_

- [x] 7.5 Create DocumentUpload component


  - Create frontend/components/agent-builder/DocumentUpload.tsx
  - Implement drag-and-drop file upload
  - Show upload Progress bar
  - Display processing status for each document
  - Support batch upload to POST /api/agent-builder/knowledgebases/{id}/documents
  - _Requirements: 31.2_

- [x] 7.6 Create KnowledgebaseSearch component


  - Create frontend/components/agent-builder/KnowledgebaseSearch.tsx
  - Add search Input with query
  - Fetch results from GET /api/agent-builder/knowledgebases/{id}/search
  - Display results with relevance scores and snippets
  - Add document type filter
  - _Requirements: 31.4_

- [x] 7.7 Write block and knowledgebase UI tests



  - Test block creation with different types
  - Test block testing functionality
  - Test document upload and progress
  - Test knowledgebase search
  - _Requirements: All Phase 7_

---

## Phase 8: Frontend - Execution Monitor and Variables Manager
-

- [x] 8. Implement Execution Monitor and Variables Manager UI




  - Create execution dashboard with real-time updates
  - Implement execution trace viewer
  - Add variables management UI
  - _Requirements: 8.1, 8.4, 18.1, 32.1, 37.1_
  - _Reference: ui-design.md - Execution Monitor Dashboard and Variables Manager_

- [x] 8.1 Create ExecutionMonitor page with shadcn/ui


  - Create frontend/app/agent-builder/executions/page.tsx
  - Display stats Cards (total, running, success rate, avg duration)
  - Fetch executions from GET /api/agent-builder/executions
  - Display executions Table with status Badge, agent name, duration
  - Add filters (status, agent, date range) with Select components
  - Implement real-time updates with polling or WebSocket
  - Add execution actions (View, Replay, Cancel) in DropdownMenu
  - _Requirements: 37.1, 37.2_
  - _Reference: ui-design.md - Execution Monitor Dashboard_

- [x] 8.2 Create ExecutionDetails component


  - Create frontend/components/agent-builder/ExecutionDetails.tsx
  - Fetch execution from GET /api/agent-builder/executions/{id}
  - Display execution metadata (agent, user, duration, status)
  - Show execution steps in timeline with Card for each step
  - Display LangGraph state at each step with JSON viewer
  - Show tool calls with parameters and responses
  - _Requirements: 14.2, 14.3, 22.3_

- [x] 8.3 Create ExecutionMetrics component


  - Create frontend/components/agent-builder/ExecutionMetrics.tsx
  - Display metrics Cards (duration, tokens, tool calls, cache hits)
  - Add time-series charts using recharts library
  - Show performance percentiles (p50, p95, p99)
  - Display error rates and common error types
  - _Requirements: 8.1, 8.2, 23.1, 23.3_

- [x] 8.4 Create ExecutionComparison component


  - Create frontend/components/agent-builder/ExecutionComparison.tsx
  - Allow selecting two executions for comparison
  - Display side-by-side execution steps
  - Highlight differences in outputs with diff highlighting
  - Show metric comparisons in table
  - _Requirements: 22.4_

- [x] 8.5 Create VariablesManager page with shadcn/ui


  - Create frontend/app/agent-builder/variables/page.tsx
  - Fetch variables from GET /api/agent-builder/variables
  - Display variables with Tabs for scope filtering (Global, Workspace, User, Agent)
  - Show variables Table with name, type, scope, value (masked for secrets)
  - Add "Create Variable" button
  - Implement variable actions (Edit, Delete) in DropdownMenu
  - Show Lock icon for secret variables
  - _Requirements: 32.1, 36.4_
  - _Reference: ui-design.md - Variables Manager Page_

- [x] 8.6 Create VariableEditor component with shadcn/ui


  - Create frontend/components/agent-builder/VariableEditor.tsx
  - Implement Dialog for variable creation/editing
  - Add Form with fields: name, scope, type, value
  - Add scope Select (global, workspace, user, agent)
  - Add type Select (string, number, boolean, json)
  - Add secret Switch to toggle encryption
  - Add value Textarea with monospace font
  - Submit to POST /api/agent-builder/variables
  - _Requirements: 32.1, 32.2, 32.3_
  - _Reference: ui-design.md - Variables Manager Page (Variable Creation Dialog)_

- [x] 8.7 Write execution monitor and variables UI tests



  - Test execution filtering and pagination
  - Test execution trace viewer display
  - Test variable creation with different types
  - Test secret variable masking
  - _Requirements: All Phase 8_

---

## Phase 9: Advanced Features (Optional - Future Enhancements)

- [x] 9. Implement advanced features






  - Add execution scheduling with cron
  - Implement hooks and callbacks
  - Add agent marketplace
  - Implement performance optimizations
  - Add quota and rate limiting
  - _Requirements: 15.1, 15.2, 16.1, 17.2, 19.1_

- [x] 9.1 Implement execution scheduling



  - Create backend/services/agent_builder/scheduler.py with APScheduler
  - Add schedule CRUD endpoints in executions API
  - Implement cron expression parsing and validation
  - Add background task execution using FastAPI BackgroundTasks
  - Store schedules in ExecutionSchedule model
  - _Requirements: 17.1, 17.2, 17.3, 17.4_

- [x] 9.2 Implement execution hooks



  - Add hook configuration fields to Agent and Workflow models
  - Implement pre-execution, post-execution, error hooks
  - Add webhook invocation using httpx
  - Implement custom Python function hooks with safe execution
  - Add hook retry logic with exponential backoff
  - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

- [x] 9.3 Implement agent marketplace



  - Create frontend/app/agent-builder/marketplace/page.tsx
  - Add agent publishing workflow (mark as public)
  - Implement agent ratings and reviews models
  - Add agent installation (clone from marketplace)
  - Implement search and filtering by category, rating
  - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [x] 9.4 Implement performance optimizations



  - Add LLM response caching in Redis using existing backend/core/llm_cache.py
  - Implement compiled graph caching with functools.lru_cache
  - Add database query optimization with proper indexes
  - Tune connection pooling in backend/db/database.py
  - Add asyncio semaphore for concurrent LLM call limits
  - _Requirements: 15.1, 15.2, 15.3, 15.4_


- [x] 9.5 Implement quota and rate limiting



  - Add user quota fields to User model (execution_quota, token_quota)
  - Implement rate limiting using existing backend/core/rate_limiter.py
  - Add quota enforcement in execution endpoints
  - Implement resource limit checks (memory, duration)
  - Create admin quota dashboard page
  - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

---

## Phase 10: Integration and Polish

- [x] 10. Integrate with existing RAG system and polish

  - Ensure seamless integration with existing components
  - Add comprehensive error handling
  - Implement audit logging
  - Add end-to-end testing
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 11.5_

- [x] 10.1 Integrate with existing agents and services

  - Verify VectorSearchAgent, WebSearchAgent, LocalDataAgent work as tools in ToolRegistry
  - Test agent execution with existing backend/memory/manager.py
  - Verify LLM Manager integration with existing backend/services/llm_manager.py
  - Test Milvus integration with existing backend/services/milvus.py
  - Test PostgreSQL integration with existing backend/db/database.py
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 10.2 Implement comprehensive audit logging

  - Add audit logging to all Agent Builder API endpoints
  - Log user actions to AuditLog model (create, update, delete, execute)
  - Add IP address and user agent tracking from request headers
  - Create admin audit log viewer page in frontend
  - Add audit log export functionality (CSV/JSON)
  - _Requirements: 11.5, 34.5_

- [x] 10.3 Implement error handling improvements

  - Add user-friendly error messages for common errors
  - Implement error recovery suggestions in UI
  - Add error reporting to administrators via email/notification
  - Implement circuit breaker for external services using existing backend/core/resilience.py
  - _Requirements: 1.5, 7.3, 30.4_

- [x] 10.4 Add documentation and help

  - Create user guide in docs/agent-builder/user-guide.md
  - Add inline help tooltips in UI components
  - Create API documentation with OpenAPI examples
  - Add README.md in .kiro/specs/agent-builder/ with getting started guide
  - _Requirements: All requirements_

- [x] 10.5 Write end-to-end integration tests

  - Create backend/tests/e2e/test_agent_builder_flow.py
  - Test complete agent creation and execution flow
  - Test workflow designer and execution
  - Test knowledgebase creation and search
  - Test permission and sharing
  - Test execution monitoring and debugging
  - _Requirements: All requirements_

---

## Phase 11: Final Polish and Missing Items

- [x] 11. Complete remaining integration tasks and missing tests



  - Register audit logs router in main.py
  - Add missing frontend component tests
  - Verify all API endpoints are properly documented
  - _Requirements: All requirements_

- [x] 11.1 Register audit logs router in backend



  - Import audit_logs router in backend/main.py
  - Add app.include_router(agent_builder_audit_logs.router) after other agent builder routers
  - Verify audit logs endpoints are accessible at /api/agent-builder/audit-logs
  - Test audit log endpoints with authentication
  - _Requirements: 11.5, 34.5_

- [x] 11.2 Add missing frontend component tests



  - Create frontend/__tests__/agent-builder/agent-form.test.tsx
  - Test AgentForm validation with invalid inputs
  - Test ToolSelector selection and filtering
  - Test PromptTemplateEditor variable suggestions
  - Test form submission and error handling
  - _Requirements: 1.1, 1.2, 3.1, 12.1_

---

## Summary

**Total Tasks**: 11 phases, ~72 tasks (core implementation + advanced features + final polish)

**Implementation Status**:
- ✅ Phase 1: Database Schema and Core Models (Complete)
- ✅ Phase 2: Backend Services - Core Infrastructure (Complete)
- ✅ Phase 3: Workflow Execution Engine (Complete)
- ✅ Phase 4: Backend API Endpoints (Complete)
- ✅ Phase 5: Frontend - Agent Builder UI (Complete)
- ✅ Phase 6: Frontend - Workflow Designer (Complete)
- ✅ Phase 7: Frontend - Block Library and Knowledgebase Manager (Complete)
- ✅ Phase 8: Frontend - Execution Monitor and Variables Manager (Complete)
- ✅ Phase 9: Advanced Features (Complete)
- ✅ Phase 10: Integration and Polish (Complete)
- 🔄 Phase 11: Final Polish and Missing Items (2 tasks remaining)

**Remaining Tasks**: 2 tasks in Phase 11
1. Register audit logs router in backend/main.py
2. Add missing frontend component tests (AgentForm, ToolSelector, PromptTemplateEditor)

**Technology Stack**:
- Backend: FastAPI, SQLAlchemy, LangChain, LangGraph, LiteLLM, Alembic, APScheduler
- Frontend: Next.js 15, React 19, shadcn/ui, React Flow, Monaco Editor, react-hook-form, zod
- Database: PostgreSQL, Milvus, Redis
- Tools: Pydantic, httpx, aiofiles, python-jose, croniter

**Current Status**: 98% Complete - Only minor integration and testing tasks remaining
