# Agent Builder API

This directory contains the FastAPI endpoints for the Agent Builder feature, which enables users to create, configure, and manage custom AI agents with specialized capabilities.

## Overview

The Agent Builder API provides a comprehensive set of endpoints for:
- **Agent Management**: Create, update, delete, and manage custom agents
- **Block Management**: Create reusable logic components
- **Workflow Management**: Design and execute agent workflows using LangGraph
- **Knowledgebase Management**: Attach domain-specific knowledge to agents
- **Variable Management**: Define global variables and secrets
- **Execution Management**: Execute agents and workflows with streaming support
- **Permission Management**: Fine-grained access control and resource sharing

## API Modules

### 1. Agents API (`agents.py`)
**Endpoints:**
- `POST /api/agent-builder/agents` - Create a new agent
- `GET /api/agent-builder/agents/{agent_id}` - Get agent details
- `PUT /api/agent-builder/agents/{agent_id}` - Update agent
- `DELETE /api/agent-builder/agents/{agent_id}` - Soft delete agent
- `GET /api/agent-builder/agents` - List user's agents with pagination
- `POST /api/agent-builder/agents/{agent_id}/clone` - Clone agent
- `GET /api/agent-builder/agents/{agent_id}/export` - Export agent as JSON
- `POST /api/agent-builder/agents/import` - Import agent from JSON

**Requirements:** 1.1, 1.4, 6.4, 6.5, 9.3

### 2. Blocks API (`blocks.py`)
**Endpoints:**
- `POST /api/agent-builder/blocks` - Create a new block
- `GET /api/agent-builder/blocks/{block_id}` - Get block details
- `PUT /api/agent-builder/blocks/{block_id}` - Update block
- `DELETE /api/agent-builder/blocks/{block_id}` - Delete block
- `GET /api/agent-builder/blocks` - List blocks with type filter
- `POST /api/agent-builder/blocks/{block_id}/test` - Test block execution
- `GET /api/agent-builder/blocks/{block_id}/versions` - Get version history

**Requirements:** 24.1, 24.4, 27.1, 28.1, 28.2

### 3. Workflows API (`workflows.py`)
**Endpoints:**
- `POST /api/agent-builder/workflows` - Create a new workflow
- `GET /api/agent-builder/workflows/{workflow_id}` - Get workflow details
- `PUT /api/agent-builder/workflows/{workflow_id}` - Update workflow
- `DELETE /api/agent-builder/workflows/{workflow_id}` - Delete workflow
- `GET /api/agent-builder/workflows` - List workflows
- `POST /api/agent-builder/workflows/{workflow_id}/validate` - Validate workflow graph
- `POST /api/agent-builder/workflows/{workflow_id}/compile` - Compile to LangGraph

**Requirements:** 4.1, 4.5, 13.5

### 4. Knowledgebases API (`knowledgebases.py`)
**Endpoints:**
- `POST /api/agent-builder/knowledgebases` - Create a new knowledgebase
- `GET /api/agent-builder/knowledgebases/{kb_id}` - Get knowledgebase details
- `PUT /api/agent-builder/knowledgebases/{kb_id}` - Update knowledgebase
- `DELETE /api/agent-builder/knowledgebases/{kb_id}` - Delete knowledgebase
- `POST /api/agent-builder/knowledgebases/{kb_id}/documents` - Upload documents
- `GET /api/agent-builder/knowledgebases/{kb_id}/search` - Search with query
- `GET /api/agent-builder/knowledgebases/{kb_id}/versions` - Get version history
- `POST /api/agent-builder/knowledgebases/{kb_id}/rollback` - Rollback to version

**Requirements:** 31.1, 31.2, 31.4, 35.1, 35.3, 35.4

### 5. Variables API (`variables.py`)
**Endpoints:**
- `POST /api/agent-builder/variables` - Create a new variable
- `GET /api/agent-builder/variables/{var_id}` - Get variable details
- `PUT /api/agent-builder/variables/{var_id}` - Update variable
- `DELETE /api/agent-builder/variables/{var_id}` - Soft delete variable
- `GET /api/agent-builder/variables` - List variables with scope filter
- `POST /api/agent-builder/variables/resolve` - Resolve template variables

**Requirements:** 32.1, 32.2, 32.4, 36.1, 36.3

### 6. Executions API (`executions.py`)
**Endpoints:**
- `POST /api/agent-builder/executions/agents/{agent_id}` - Execute agent with SSE
- `POST /api/agent-builder/executions/workflows/{workflow_id}` - Execute workflow with SSE
- `GET /api/agent-builder/executions/{execution_id}` - Get execution details
- `GET /api/agent-builder/executions` - List executions with filters
- `POST /api/agent-builder/executions/{execution_id}/cancel` - Cancel running execution
- `POST /api/agent-builder/executions/{execution_id}/replay` - Replay execution
- `POST /api/agent-builder/executions/schedules` - Create cron schedule

**Requirements:** 5.1, 5.2, 17.1, 17.2, 22.1, 22.2

### 7. Permissions API (`permissions.py`)
**Endpoints:**
- `POST /api/agent-builder/permissions` - Grant permission to user
- `DELETE /api/agent-builder/permissions/{permission_id}` - Revoke permission
- `GET /api/agent-builder/permissions` - List user permissions
- `POST /api/agent-builder/shares` - Create shareable link with token
- `GET /api/agent-builder/shares/{token}` - Access shared resource

**Requirements:** 9.1, 9.2, 11.1, 34.1, 34.3, 34.4

## Authentication

All endpoints require JWT authentication using the `Authorization: Bearer <token>` header. The authentication is handled by the `get_current_user` dependency from `backend/core/auth_dependencies.py`.

## Authorization

The API implements fine-grained permission controls:
- **Ownership**: Users have full access to resources they create
- **Explicit Permissions**: Owners can grant specific permissions (read, write, execute, delete, share, admin) to other users
- **Shareable Links**: Resources can be shared via time-limited tokens with configurable permissions

## Error Handling

All endpoints follow consistent error handling patterns:
- `400 Bad Request` - Invalid request data or validation errors
- `401 Unauthorized` - Missing or invalid authentication token
- `403 Forbidden` - User lacks permission for the requested action
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate permission)
- `500 Internal Server Error` - Unexpected server error

## Testing

Comprehensive integration tests are available in `backend/tests/integration/test_agent_builder_api.py`. The tests cover:
- CRUD operations for all resource types
- Authentication and authorization
- Permission management
- Resource sharing
- Error handling
- Pagination and filtering

Run tests with:
```bash
pytest backend/tests/integration/test_agent_builder_api.py -v
```

## OpenAPI Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

All endpoints are tagged with `agent-builder-*` for easy navigation.

## Dependencies

The API relies on:
- **Service Layer**: `backend/services/agent_builder/` - Business logic and data access
- **Models**: `backend/models/agent_builder.py` - Pydantic schemas for request/response
- **Database Models**: `backend/db/models/agent_builder.py` - SQLAlchemy ORM models
- **Authentication**: `backend/core/auth_dependencies.py` - JWT authentication

## Future Enhancements

Planned improvements include:
- Rate limiting per user/agent
- Execution quotas and resource limits
- Advanced analytics and monitoring
- Agent marketplace integration
- Webhook support for execution events
