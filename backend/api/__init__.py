"""
API endpoints package

Organized by domain:
- auth/: Authentication and authorization (documentation only)
- documents/: Document management (documentation only)
- conversations/: Chat and conversation history (documentation only)
- query/: Query processing and RAG (documentation only)
- monitoring/: Health checks and metrics (documentation only)
- admin/: Administration and configuration (documentation only)
- agent_builder/: Agent Builder feature APIs
- v1/: Legacy API version 1
- v2/: API version 2

Root-level .py files contain the actual router implementations.
Domain folders contain documentation and organization info.
"""

# Note: Routers should be imported directly from their .py files
# e.g., from backend.api.auth import router as auth_router
# Do not import routers here to avoid circular imports with domain folders.

__all__ = []
