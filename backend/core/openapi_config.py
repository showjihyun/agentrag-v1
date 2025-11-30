"""
OpenAPI Documentation Configuration

Provides enhanced OpenAPI documentation with:
- Detailed API descriptions
- Example requests/responses
- Tag grouping
- Security schemes
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


# ============================================================================
# API Tags Configuration
# ============================================================================

API_TAGS: List[Dict[str, Any]] = [
    {
        "name": "Health Check v1",
        "description": "System health monitoring endpoints including Kubernetes probes",
    },
    {
        "name": "Authentication",
        "description": "User authentication and authorization endpoints",
    },
    {
        "name": "Documents",
        "description": "Document upload, management, and processing",
    },
    {
        "name": "Query",
        "description": "RAG query processing and search endpoints",
    },
    {
        "name": "Conversations",
        "description": "Conversation history and management",
    },
    {
        "name": "Agent Builder",
        "description": "Agent and workflow builder APIs",
    },
    {
        "name": "Workflows",
        "description": "Workflow execution and management",
    },
    {
        "name": "Knowledge Bases",
        "description": "Knowledge base management for agents",
    },
    {
        "name": "Monitoring",
        "description": "System monitoring and metrics",
    },
    {
        "name": "Admin",
        "description": "Administrative operations",
    },
]


# ============================================================================
# Security Schemes
# ============================================================================

SECURITY_SCHEMES: Dict[str, Any] = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT Bearer token authentication",
    },
    "APIKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API Key authentication for external integrations",
    },
}


# ============================================================================
# Common Response Examples
# ============================================================================

COMMON_RESPONSES: Dict[str, Dict[str, Any]] = {
    "400": {
        "description": "Bad Request - Invalid input",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "VAL_2001",
                        "message": "Validation failed",
                        "field": "email",
                        "details": {
                            "validation_errors": [
                                {
                                    "field": "email",
                                    "message": "Invalid email format",
                                    "type": "value_error",
                                }
                            ]
                        },
                    },
                    "meta": {
                        "request_id": "req_abc123",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "version": "1.0",
                    },
                }
            }
        },
    },
    "401": {
        "description": "Unauthorized - Authentication required",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "AUTH_1001",
                        "message": "Invalid credentials",
                        "field": None,
                        "details": None,
                    },
                    "meta": {
                        "request_id": "req_abc123",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "version": "1.0",
                    },
                }
            }
        },
    },
    "403": {
        "description": "Forbidden - Insufficient permissions",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "AUTH_1004",
                        "message": "Insufficient permissions",
                        "field": None,
                        "details": {
                            "resource_type": "workflow",
                            "resource_id": "wf_123",
                            "required_permission": "edit",
                        },
                    },
                    "meta": {
                        "request_id": "req_abc123",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "version": "1.0",
                    },
                }
            }
        },
    },
    "404": {
        "description": "Not Found - Resource does not exist",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "RES_3001",
                        "message": "Resource not found",
                        "field": None,
                        "details": {
                            "resource_type": "document",
                            "resource_id": "doc_123",
                        },
                    },
                    "meta": {
                        "request_id": "req_abc123",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "version": "1.0",
                    },
                }
            }
        },
    },
    "429": {
        "description": "Too Many Requests - Rate limit exceeded",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "BIZ_4004",
                        "message": "Rate limit exceeded: 60 requests per minute",
                        "field": None,
                        "details": {
                            "limit": 60,
                            "window": "minute",
                            "retry_after": 30,
                        },
                    },
                    "meta": {
                        "request_id": "req_abc123",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "version": "1.0",
                    },
                }
            }
        },
    },
    "500": {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "INT_9001",
                        "message": "An unexpected error occurred",
                        "field": None,
                        "details": None,
                    },
                    "meta": {
                        "request_id": "req_abc123",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "version": "1.0",
                    },
                }
            }
        },
    },
}


# ============================================================================
# Custom OpenAPI Schema
# ============================================================================

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Generate custom OpenAPI schema with enhanced documentation.
    
    Usage:
        from backend.core.openapi_config import custom_openapi
        
        app = FastAPI()
        app.openapi = lambda: custom_openapi(app)
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Agentic RAG System API",
        version="1.0.0",
        description="""
# Agentic RAG System API

An intelligent document search and question-answering system that combines 
multi-agent architecture with multimodal RAG capabilities.

## Features

- **Multi-Agent Architecture**: Orchestrates specialized agents for different tasks
- **Adaptive Query Routing**: Automatically routes queries to optimal processing mode
- **Multimodal Document Processing**: Supports PDF, DOCX, images, and more
- **Hybrid Search**: Combines vector and keyword search for optimal retrieval
- **Real-time Streaming**: SSE-based streaming for live responses

## Authentication

Most endpoints require JWT Bearer token authentication. 
Obtain a token via the `/api/auth/login` endpoint.

```
Authorization: Bearer <your_jwt_token>
```

## Rate Limiting

API requests are rate-limited:
- 60 requests per minute
- 1000 requests per hour
- 10000 requests per day

Rate limit headers are included in all responses:
- `X-RateLimit-Remaining-Minute`
- `X-RateLimit-Remaining-Hour`
- `X-RateLimit-Remaining-Day`

## Response Format

All API responses follow a standardized format:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0"
  }
}
```

## Error Codes

Error codes follow a structured format:
- `AUTH_1xxx`: Authentication errors
- `VAL_2xxx`: Validation errors
- `RES_3xxx`: Resource errors
- `BIZ_4xxx`: Business logic errors
- `EXT_5xxx`: External service errors
- `INT_9xxx`: Internal errors
        """,
        routes=app.routes,
        tags=API_TAGS,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES
    
    # Add common responses to components
    openapi_schema["components"]["responses"] = COMMON_RESPONSES
    
    # Add servers
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Development server",
        },
        {
            "url": "https://api.example.com",
            "description": "Production server",
        },
    ]
    
    # Add contact info
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "email": "support@example.com",
    }
    
    # Add license
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def configure_openapi(app: FastAPI) -> None:
    """
    Configure OpenAPI documentation for the application.
    
    Usage:
        from backend.core.openapi_config import configure_openapi
        
        app = FastAPI()
        configure_openapi(app)
    """
    app.openapi = lambda: custom_openapi(app)
