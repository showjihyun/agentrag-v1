"""
Agents package for specialized agent implementations.

This package contains specialized agents that interface with MCP servers
to perform specific tasks like vector search, local data access, and web search.
"""

from backend.agents.vector_search import VectorSearchAgent
from backend.agents.local_data import LocalDataAgent
from backend.agents.web_search import WebSearchAgent, WebSearchResult

__all__ = [
    "VectorSearchAgent",
    "LocalDataAgent",
    "WebSearchAgent",
    "WebSearchResult",
]
