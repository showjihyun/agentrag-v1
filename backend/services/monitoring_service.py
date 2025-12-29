"""
Monitoring Statistics Service

DEPRECATED: Monitoring models have been removed from the database schema.
This service now returns empty/default data to maintain API compatibility.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring statistics (DEPRECATED - returns empty data)"""
    
    def __init__(self, db: Session):
        self.db = db
        logger.warning("MonitoringService is deprecated - monitoring models have been removed")
    
    # ==================== File Upload Stats ====================
    
    def save_file_upload_stat(
        self,
        file_id: str,
        filename: str,
        file_type: str,
        file_size_mb: float,
        status: str,
        processing_time_ms: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Save file upload statistics (DEPRECATED - no-op)"""
        logger.debug("save_file_upload_stat called but monitoring models are removed")
    
    def get_file_upload_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get file upload statistics (DEPRECATED - returns empty data)"""
        return self._empty_file_upload_stats()
    
    def _empty_file_upload_stats(self) -> Dict[str, Any]:
        return {
            "total_files": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "total_size_mb": 0.0,
            "avg_processing_time_ms": 0.0,
            "by_file_type": {},
            "recent_uploads": []
        }
    
    # ==================== Embedding Stats ====================
    
    def save_embedding_stat(
        self,
        document_id: str,
        embedding_model: str,
        total_chunks: int,
        chunking_strategy: str,
        embedding_time_ms: float
    ) -> None:
        """Save embedding statistics (DEPRECATED - no-op)"""
        logger.debug("save_embedding_stat called but monitoring models are removed")
    
    def get_embedding_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get embedding statistics (DEPRECATED - returns empty data)"""
        return self._empty_embedding_stats()
    
    def _empty_embedding_stats(self) -> Dict[str, Any]:
        return {
            "total_embeddings": 0,
            "total_chunks": 0,
            "avg_chunks_per_document": 0.0,
            "embedding_model": "unknown",
            "avg_embedding_time_ms": 0.0,
            "by_chunking_strategy": {}
        }
    
    # ==================== Hybrid Search Stats ====================
    
    def save_hybrid_search_stat(
        self,
        session_id: Optional[str],
        search_type: str,
        query_text: Optional[str],
        results_count: int,
        search_time_ms: float,
        cache_hit: bool = False
    ) -> None:
        """Save hybrid search statistics (DEPRECATED - no-op)"""
        logger.debug("save_hybrid_search_stat called but monitoring models are removed")
    
    def get_hybrid_search_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get hybrid search statistics (DEPRECATED - returns empty data)"""
        return self._empty_hybrid_search_stats()
    
    def _empty_hybrid_search_stats(self) -> Dict[str, Any]:
        return {
            "total_searches": 0,
            "vector_only": 0,
            "keyword_only": 0,
            "hybrid": 0,
            "avg_search_time_ms": 0.0,
            "avg_results_count": 0.0,
            "cache_hit_rate": 0.0
        }
    
    # ==================== RAG Processing Stats ====================
    
    def save_rag_processing_stat(
        self,
        session_id: Optional[str],
        query_text: Optional[str],
        mode: str,
        complexity: Optional[str],
        response_time_ms: float,
        confidence_score: Optional[float] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        token_usage: Optional[Dict[str, int]] = None,
        quality_scores: Optional[Dict[str, float]] = None
    ) -> None:
        """Save RAG processing statistics (DEPRECATED - no-op)"""
        logger.debug("save_rag_processing_stat called but monitoring models are removed")
    
    def get_rag_processing_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get RAG processing statistics (DEPRECATED - returns empty data)"""
        return self._empty_rag_processing_stats()
    
    def _empty_rag_processing_stats(self) -> Dict[str, Any]:
        return {
            "total_queries": 0,
            "by_mode": {},
            "by_complexity": {},
            "avg_response_time_ms": 0.0,
            "avg_confidence_score": 0.0,
            "success_rate": 0.0
        }
    
    # ==================== Daily Trends ====================
    
    def _update_daily_trend(self) -> None:
        """Update daily accuracy trend (DEPRECATED - no-op)"""
        logger.debug("_update_daily_trend called but monitoring models are removed")
    
    def get_daily_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily accuracy trends (DEPRECATED - returns empty data)"""
        return []
    
    # ==================== Overview ====================
    
    def get_overview(self, days: int = 7) -> Dict[str, Any]:
        """Get complete monitoring overview (DEPRECATED - returns empty data)"""
        return {
            "file_uploads": self.get_file_upload_stats(days),
            "embeddings": self.get_embedding_stats(days),
            "hybrid_search": self.get_hybrid_search_stats(days),
            "rag_processing": self.get_rag_processing_stats(days),
            "accuracy_trends": self.get_daily_trends(days)
        }
