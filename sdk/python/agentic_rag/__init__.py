"""
Agentic RAG Python SDK

Official Python client for the Agentic RAG platform.
"""

from .client import AgenticRAGClient
from .exceptions import (
    AgenticRAGError,
    AuthenticationError,
    RateLimitError,
    ResourceNotFoundError,
    ValidationError,
)

__version__ = "0.1.0"
__all__ = [
    "AgenticRAGClient",
    "AgenticRAGError",
    "AuthenticationError",
    "RateLimitError",
    "ResourceNotFoundError",
    "ValidationError",
]
