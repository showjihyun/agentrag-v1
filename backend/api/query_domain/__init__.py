"""
Query domain API routers

Groups all query-related endpoints:
- query.py: Main query processing
- advanced_rag.py: Advanced RAG features
- web_search.py: Web search integration
- confidence.py: Confidence scoring
"""

# Re-export routers for easy access
# Usage: from backend.api.query import query_router

__all__ = [
    "query",
    "advanced_rag",
    "web_search",
    "confidence",
]
