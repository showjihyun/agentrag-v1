"""
RAG (Retrieval-Augmented Generation) Services Module.

This module contains all RAG-related services including:
- Hybrid search (vector + BM25)
- Query expansion
- Reranking
- Speculative processing
- Adaptive RAG routing
"""

from backend.services.hybrid_search import HybridSearchService, get_hybrid_search_service
from backend.services.query_expansion import QueryExpansionService
from backend.services.reranker import RerankerService
from backend.services.speculative_processor import SpeculativeProcessor
from backend.services.adaptive_rag_service import AdaptiveRAGService
from backend.services.intelligent_mode_router import IntelligentModeRouter

__all__ = [
    "HybridSearchService",
    "get_hybrid_search_service",
    "QueryExpansionService",
    "RerankerService",
    "SpeculativeProcessor",
    "AdaptiveRAGService",
    "IntelligentModeRouter",
]
