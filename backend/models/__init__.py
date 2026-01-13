"""Data models for the Agentic RAG system."""

from .document import Document, TextChunk
from .query import QueryRequest, QueryResponse, SearchResult
from .agent import AgentStep, AgentState
from .error import ErrorResponse, ValidationErrorResponse
from .hybrid import (
    QueryMode,
    ResponseType,
    PathSource,
    ResponseChunk,
    HybridQueryRequest,
    HybridQueryResponse,
    SpeculativeResponse,
)
from .auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    TokenRefresh,
    UserUpdate,
)
from .plugin import (
    PluginManifest,
    PluginInfo,
    PluginConfiguration,
    PluginStatus,
    PluginCategory,
    AgentRole,
    OrchestrationPattern,
    ValidationResult,
    SecurityValidationResult,
    ExecutionResult,
    ErrorResponse,
    IPlugin,
    IOrchestrationPlugin,
)

__all__ = [
    "Document",
    "TextChunk",
    "QueryRequest",
    "QueryResponse",
    "SearchResult",
    "AgentStep",
    "AgentState",
    "ErrorResponse",
    "ValidationErrorResponse",
    "QueryMode",
    "ResponseType",
    "PathSource",
    "ResponseChunk",
    "HybridQueryRequest",
    "HybridQueryResponse",
    "SpeculativeResponse",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
    "TokenRefresh",
    "UserUpdate",
    # Plugin models
    "PluginManifest",
    "PluginInfo",
    "PluginConfiguration",
    "PluginStatus",
    "PluginCategory",
    "AgentRole",
    "OrchestrationPattern",
    "ValidationResult",
    "SecurityValidationResult",
    "ExecutionResult",
    "IPlugin",
    "IOrchestrationPlugin",
]
