"""
Monitoring Statistics Service

Handles saving and retrieving monitoring statistics from PostgreSQL.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, Float
from sqlalchemy.orm import Session

from backend.db.models.monitoring import (
    FileUploadStat,
    EmbeddingStat,
    HybridSearchStat,
    RAGProcessingStat,
    DailyAccuracyTrend
)

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for monitoring statistics"""
    
    def __init__(self, db: Session):
        self.db = db
    
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
        """Save file upload statistics"""
        try:
            stat = FileUploadStat(
                file_id=file_id,
                filename=filename,
                file_type=file_type,
                file_size_mb=file_size_mb,
                status=status,
                processing_time_ms=processing_time_ms,
                error_message=error_message
            )
            self.db.add(stat)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save file upload stat: {e}")
            self.db.rollback()
    
    def get_file_upload_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get file upload statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total stats
            total_files = self.db.query(func.count(FileUploadStat.id)).filter(
                FileUploadStat.created_at >= cutoff_date
            ).scalar() or 0
            
            successful = self.db.query(func.count(FileUploadStat.id)).filter(
                and_(
                    FileUploadStat.created_at >= cutoff_date,
                    FileUploadStat.status == 'completed'
                )
            ).scalar() or 0
            
            failed = self.db.query(func.count(FileUploadStat.id)).filter(
                and_(
                    FileUploadStat.created_at >= cutoff_date,
                    FileUploadStat.status == 'failed'
                )
            ).scalar() or 0
            
            total_size = self.db.query(func.sum(FileUploadStat.file_size_mb)).filter(
                FileUploadStat.created_at >= cutoff_date
            ).scalar() or 0.0
            
            avg_time = self.db.query(func.avg(FileUploadStat.processing_time_ms)).filter(
                and_(
                    FileUploadStat.created_at >= cutoff_date,
                    FileUploadStat.processing_time_ms.isnot(None)
                )
            ).scalar() or 0.0
            
            # By file type
            by_type = self.db.query(
                FileUploadStat.file_type,
                func.count(FileUploadStat.id)
            ).filter(
                FileUploadStat.created_at >= cutoff_date
            ).group_by(FileUploadStat.file_type).all()
            
            # Recent uploads
            recent = self.db.query(FileUploadStat).filter(
                FileUploadStat.created_at >= cutoff_date
            ).order_by(FileUploadStat.created_at.desc()).limit(10).all()
            
            return {
                "total_files": total_files,
                "successful_uploads": successful,
                "failed_uploads": failed,
                "total_size_mb": float(total_size),
                "avg_processing_time_ms": float(avg_time),
                "by_file_type": {ft: count for ft, count in by_type},
                "recent_uploads": [
                    {
                        "id": r.file_id,
                        "filename": r.filename,
                        "file_type": r.file_type,
                        "status": r.status,
                        "created_at": r.created_at.isoformat(),
                        "file_size_mb": r.file_size_mb
                    }
                    for r in recent
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get file upload stats: {e}")
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
        """Save embedding statistics"""
        try:
            stat = EmbeddingStat(
                document_id=document_id,
                embedding_model=embedding_model,
                total_chunks=total_chunks,
                chunking_strategy=chunking_strategy,
                embedding_time_ms=embedding_time_ms
            )
            self.db.add(stat)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save embedding stat: {e}")
            self.db.rollback()
    
    def get_embedding_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get embedding statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            total_embeddings = self.db.query(func.count(EmbeddingStat.id)).filter(
                EmbeddingStat.created_at >= cutoff_date
            ).scalar() or 0
            
            total_chunks = self.db.query(func.sum(EmbeddingStat.total_chunks)).filter(
                EmbeddingStat.created_at >= cutoff_date
            ).scalar() or 0
            
            avg_chunks = self.db.query(func.avg(EmbeddingStat.total_chunks)).filter(
                EmbeddingStat.created_at >= cutoff_date
            ).scalar() or 0.0
            
            avg_time = self.db.query(func.avg(EmbeddingStat.embedding_time_ms)).filter(
                EmbeddingStat.created_at >= cutoff_date
            ).scalar() or 0.0
            
            # Get most recent model
            latest = self.db.query(EmbeddingStat).filter(
                EmbeddingStat.created_at >= cutoff_date
            ).order_by(EmbeddingStat.created_at.desc()).first()
            
            model = latest.embedding_model if latest else "unknown"
            
            # By strategy
            by_strategy = self.db.query(
                EmbeddingStat.chunking_strategy,
                func.count(EmbeddingStat.id)
            ).filter(
                EmbeddingStat.created_at >= cutoff_date
            ).group_by(EmbeddingStat.chunking_strategy).all()
            
            return {
                "total_embeddings": total_embeddings,
                "total_chunks": total_chunks,
                "avg_chunks_per_document": float(avg_chunks),
                "embedding_model": model,
                "avg_embedding_time_ms": float(avg_time),
                "by_chunking_strategy": {strategy: count for strategy, count in by_strategy}
            }
        except Exception as e:
            logger.error(f"Failed to get embedding stats: {e}")
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
        """Save hybrid search statistics"""
        try:
            stat = HybridSearchStat(
                session_id=session_id,
                search_type=search_type,
                query_text=query_text[:1000] if query_text else None,
                results_count=results_count,
                search_time_ms=search_time_ms,
                cache_hit=1 if cache_hit else 0
            )
            self.db.add(stat)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save hybrid search stat: {e}")
            self.db.rollback()
    
    def get_hybrid_search_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get hybrid search statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            total_searches = self.db.query(func.count(HybridSearchStat.id)).filter(
                HybridSearchStat.created_at >= cutoff_date
            ).scalar() or 0
            
            vector_only = self.db.query(func.count(HybridSearchStat.id)).filter(
                and_(
                    HybridSearchStat.created_at >= cutoff_date,
                    HybridSearchStat.search_type == 'vector_only'
                )
            ).scalar() or 0
            
            keyword_only = self.db.query(func.count(HybridSearchStat.id)).filter(
                and_(
                    HybridSearchStat.created_at >= cutoff_date,
                    HybridSearchStat.search_type == 'keyword_only'
                )
            ).scalar() or 0
            
            hybrid = self.db.query(func.count(HybridSearchStat.id)).filter(
                and_(
                    HybridSearchStat.created_at >= cutoff_date,
                    HybridSearchStat.search_type == 'hybrid'
                )
            ).scalar() or 0
            
            avg_time = self.db.query(func.avg(HybridSearchStat.search_time_ms)).filter(
                HybridSearchStat.created_at >= cutoff_date
            ).scalar() or 0.0
            
            avg_results = self.db.query(func.avg(HybridSearchStat.results_count)).filter(
                HybridSearchStat.created_at >= cutoff_date
            ).scalar() or 0.0
            
            cache_hits = self.db.query(func.count(HybridSearchStat.id)).filter(
                and_(
                    HybridSearchStat.created_at >= cutoff_date,
                    HybridSearchStat.cache_hit == 1
                )
            ).scalar() or 0
            
            cache_hit_rate = cache_hits / total_searches if total_searches > 0 else 0.0
            
            return {
                "total_searches": total_searches,
                "vector_only": vector_only,
                "keyword_only": keyword_only,
                "hybrid": hybrid,
                "avg_search_time_ms": float(avg_time),
                "avg_results_count": float(avg_results),
                "cache_hit_rate": cache_hit_rate
            }
        except Exception as e:
            logger.error(f"Failed to get hybrid search stats: {e}")
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
        """Save RAG processing statistics"""
        try:
            stat = RAGProcessingStat(
                session_id=session_id,
                query_text=query_text[:1000] if query_text else None,
                mode=mode,
                complexity=complexity,
                response_time_ms=response_time_ms,
                confidence_score=confidence_score,
                success=1 if success else 0,
                error_message=error_message,
                token_usage=token_usage,
                quality_scores=quality_scores
            )
            self.db.add(stat)
            self.db.commit()
            
            # Update daily trend
            self._update_daily_trend()
            
        except Exception as e:
            logger.error(f"Failed to save RAG processing stat: {e}")
            self.db.rollback()
    
    def get_rag_processing_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get RAG processing statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            total_queries = self.db.query(func.count(RAGProcessingStat.id)).filter(
                RAGProcessingStat.created_at >= cutoff_date
            ).scalar() or 0
            
            # By mode
            by_mode = self.db.query(
                RAGProcessingStat.mode,
                func.count(RAGProcessingStat.id)
            ).filter(
                RAGProcessingStat.created_at >= cutoff_date
            ).group_by(RAGProcessingStat.mode).all()
            
            # By complexity
            by_complexity = self.db.query(
                RAGProcessingStat.complexity,
                func.count(RAGProcessingStat.id)
            ).filter(
                and_(
                    RAGProcessingStat.created_at >= cutoff_date,
                    RAGProcessingStat.complexity.isnot(None)
                )
            ).group_by(RAGProcessingStat.complexity).all()
            
            avg_time = self.db.query(func.avg(RAGProcessingStat.response_time_ms)).filter(
                RAGProcessingStat.created_at >= cutoff_date
            ).scalar() or 0.0
            
            avg_confidence = self.db.query(func.avg(RAGProcessingStat.confidence_score)).filter(
                and_(
                    RAGProcessingStat.created_at >= cutoff_date,
                    RAGProcessingStat.confidence_score.isnot(None)
                )
            ).scalar() or 0.0
            
            successful = self.db.query(func.count(RAGProcessingStat.id)).filter(
                and_(
                    RAGProcessingStat.created_at >= cutoff_date,
                    RAGProcessingStat.success == 1
                )
            ).scalar() or 0
            
            success_rate = successful / total_queries if total_queries > 0 else 0.0
            
            return {
                "total_queries": total_queries,
                "by_mode": {mode: count for mode, count in by_mode},
                "by_complexity": {comp: count for comp, count in by_complexity if comp},
                "avg_response_time_ms": float(avg_time),
                "avg_confidence_score": float(avg_confidence),
                "success_rate": success_rate
            }
        except Exception as e:
            logger.error(f"Failed to get RAG processing stats: {e}")
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
        """Update daily accuracy trend (called after each RAG query)"""
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get or create today's trend
            trend = self.db.query(DailyAccuracyTrend).filter(
                DailyAccuracyTrend.date == today
            ).first()
            
            if not trend:
                trend = DailyAccuracyTrend(date=today)
                self.db.add(trend)
            
            # Calculate stats for today
            stats = self.db.query(
                func.count(RAGProcessingStat.id).label('total'),
                func.avg(RAGProcessingStat.confidence_score).label('avg_conf'),
                func.avg(RAGProcessingStat.response_time_ms).label('avg_time'),
                func.count(func.nullif(RAGProcessingStat.success, 0)).label('successful')
            ).filter(
                RAGProcessingStat.created_at >= today
            ).first()
            
            if stats and stats.total:
                trend.total_queries = stats.total
                trend.avg_confidence = float(stats.avg_conf) if stats.avg_conf else None
                trend.avg_response_time_ms = float(stats.avg_time) if stats.avg_time else None
                trend.success_rate = stats.successful / stats.total if stats.total > 0 else 0.0
                
                # High confidence rate (> 0.8)
                high_conf = self.db.query(func.count(RAGProcessingStat.id)).filter(
                    and_(
                        RAGProcessingStat.created_at >= today,
                        RAGProcessingStat.confidence_score > 0.8
                    )
                ).scalar() or 0
                
                trend.high_confidence_rate = high_conf / stats.total if stats.total > 0 else 0.0
                
                # Average token usage (PostgreSQL JSON syntax)
                try:
                    from sqlalchemy import text
                    avg_tokens_result = self.db.execute(
                        text("""
                            SELECT AVG((token_usage->>'total')::float)
                            FROM rag_processing_stats
                            WHERE created_at >= :today
                            AND token_usage IS NOT NULL
                        """),
                        {"today": today}
                    ).scalar()
                    trend.avg_token_usage = float(avg_tokens_result) if avg_tokens_result else None
                except Exception as e:
                    logger.warning(f"Could not calculate avg token usage: {e}")
                    trend.avg_token_usage = None
                
                # Average quality score (PostgreSQL JSON syntax)
                try:
                    avg_quality_result = self.db.execute(
                        text("""
                            SELECT AVG((quality_scores->>'overall_score')::float)
                            FROM rag_processing_stats
                            WHERE created_at >= :today
                            AND quality_scores IS NOT NULL
                        """),
                        {"today": today}
                    ).scalar()
                    trend.avg_quality_score = float(avg_quality_result) if avg_quality_result else None
                except Exception as e:
                    logger.warning(f"Could not calculate avg quality score: {e}")
                    trend.avg_quality_score = None
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update daily trend: {e}")
            self.db.rollback()
    
    def get_daily_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get daily accuracy trends"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            trends = self.db.query(DailyAccuracyTrend).filter(
                DailyAccuracyTrend.date >= cutoff_date
            ).order_by(DailyAccuracyTrend.date).all()
            
            return [
                {
                    "date": t.date.isoformat(),
                    "total_queries": t.total_queries,
                    "avg_confidence": t.avg_confidence or 0.0,
                    "high_confidence_rate": t.high_confidence_rate or 0.0,
                    "success_rate": t.success_rate or 0.0,
                    "avg_response_time_ms": t.avg_response_time_ms or 0.0
                }
                for t in trends
            ]
        except Exception as e:
            logger.error(f"Failed to get daily trends: {e}")
            return []
    
    # ==================== Overview ====================
    
    def get_overview(self, days: int = 7) -> Dict[str, Any]:
        """Get complete monitoring overview"""
        return {
            "file_uploads": self.get_file_upload_stats(days),
            "embeddings": self.get_embedding_stats(days),
            "hybrid_search": self.get_hybrid_search_stats(days),
            "rag_processing": self.get_rag_processing_stats(days),
            "accuracy_trends": self.get_daily_trends(days)
        }
