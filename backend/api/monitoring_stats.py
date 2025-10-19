"""
Monitoring Statistics API
Provides detailed statistics for file uploads, embeddings, hybrid search, and RAG processing
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.db.database import get_db
from backend.db.models.document import Document
from backend.models.query_log import QueryLog

router = APIRouter(prefix="/api/monitoring/stats", tags=["monitoring-stats"])


# Response Models
class FileUploadStats(BaseModel):
    total_files: int
    successful_uploads: int
    failed_uploads: int
    total_size_mb: float
    avg_processing_time_ms: float
    by_file_type: Dict[str, int]
    recent_uploads: List[Dict[str, Any]]


class EmbeddingStats(BaseModel):
    total_embeddings: int
    total_chunks: int
    avg_chunks_per_document: float
    embedding_model: str
    avg_embedding_time_ms: float
    by_chunking_strategy: Dict[str, int]


class HybridSearchStats(BaseModel):
    total_searches: int
    vector_only: int
    keyword_only: int
    hybrid: int
    avg_search_time_ms: float
    avg_results_count: float
    cache_hit_rate: float


class RAGProcessingStats(BaseModel):
    total_queries: int
    by_mode: Dict[str, int]
    by_complexity: Dict[str, int]
    avg_response_time_ms: float
    avg_confidence_score: float
    success_rate: float


class AccuracyTrend(BaseModel):
    date: str
    total_queries: int
    avg_confidence: float
    high_confidence_rate: float
    success_rate: float
    avg_response_time_ms: float


class MonitoringStatsResponse(BaseModel):
    file_uploads: FileUploadStats
    embeddings: EmbeddingStats
    hybrid_search: HybridSearchStats
    rag_processing: RAGProcessingStats
    accuracy_trends: List[AccuracyTrend]


@router.get("/overview", response_model=MonitoringStatsResponse)
async def get_monitoring_overview(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive monitoring statistics overview
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # File Upload Stats
    file_uploads = get_file_upload_stats(db, start_date)
    
    # Embedding Stats
    embeddings = get_embedding_stats(db, start_date)
    
    # Hybrid Search Stats
    hybrid_search = get_hybrid_search_stats(db, start_date)
    
    # RAG Processing Stats
    rag_processing = get_rag_processing_stats(db, start_date)
    
    # Accuracy Trends (daily)
    accuracy_trends = get_accuracy_trends(db, days)
    
    return MonitoringStatsResponse(
        file_uploads=file_uploads,
        embeddings=embeddings,
        hybrid_search=hybrid_search,
        rag_processing=rag_processing,
        accuracy_trends=accuracy_trends
    )


def get_file_upload_stats(db: Session, start_date: datetime) -> FileUploadStats:
    """Get file upload statistics"""
    
    # Total files and status
    total_files = db.query(func.count(Document.id)).filter(
        Document.uploaded_at >= start_date
    ).scalar() or 0
    
    successful = db.query(func.count(Document.id)).filter(
        and_(
            Document.uploaded_at >= start_date,
            Document.status == "completed"
        )
    ).scalar() or 0
    
    failed = db.query(func.count(Document.id)).filter(
        and_(
            Document.uploaded_at >= start_date,
            Document.status == "failed"
        )
    ).scalar() or 0
    
    # Total size
    total_size = db.query(func.sum(Document.file_size_bytes)).filter(
        Document.uploaded_at >= start_date
    ).scalar() or 0
    total_size_mb = total_size / (1024 * 1024)
    
    # Average processing time (from extra_metadata)
    try:
        avg_time = db.query(
            func.avg(
                func.cast(
                    Document.extra_metadata['processing_time_ms'].astext,
                    type_=float
                )
            )
        ).filter(
            and_(
                Document.uploaded_at >= start_date,
                Document.extra_metadata.isnot(None),
                Document.extra_metadata.has_key('processing_time_ms')
            )
        ).scalar() or 0
    except:
        avg_time = 0
    
    # By file type
    by_type = db.query(
        Document.mime_type,
        func.count(Document.id)
    ).filter(
        Document.uploaded_at >= start_date
    ).group_by(Document.mime_type).all()
    
    by_file_type = {mime_type or "unknown": count for mime_type, count in by_type}
    
    # Recent uploads
    recent = db.query(Document).filter(
        Document.uploaded_at >= start_date
    ).order_by(Document.uploaded_at.desc()).limit(10).all()
    
    recent_uploads = [
        {
            "id": str(doc.id),
            "filename": doc.filename,
            "file_type": doc.mime_type or "unknown",
            "status": doc.status,
            "created_at": doc.uploaded_at.isoformat(),
            "file_size_mb": doc.file_size_bytes / (1024 * 1024) if doc.file_size_bytes else 0
        }
        for doc in recent
    ]
    
    return FileUploadStats(
        total_files=total_files,
        successful_uploads=successful,
        failed_uploads=failed,
        total_size_mb=round(total_size_mb, 2),
        avg_processing_time_ms=round(avg_time, 2),
        by_file_type=by_file_type,
        recent_uploads=recent_uploads
    )


def get_embedding_stats(db: Session, start_date: datetime) -> EmbeddingStats:
    """Get embedding statistics"""
    
    # Total documents with embeddings
    total_embeddings = db.query(func.count(Document.id)).filter(
        and_(
            Document.uploaded_at >= start_date,
            Document.status == "completed"
        )
    ).scalar() or 0
    
    # Total chunks (from metadata)
    try:
        total_chunks = db.query(
            func.sum(
                func.cast(
                    Document.extra_metadata['chunk_count'].astext,
                    type_=int
                )
            )
        ).filter(
            and_(
                Document.uploaded_at >= start_date,
                Document.extra_metadata.isnot(None),
                Document.extra_metadata.has_key('chunk_count')
            )
        ).scalar() or 0
    except:
        total_chunks = 0
    
    avg_chunks = total_chunks / total_embeddings if total_embeddings > 0 else 0
    
    # Embedding model (from config)
    from backend.config import settings
    embedding_model = settings.EMBEDDING_MODEL
    
    # Average embedding time
    try:
        avg_embedding_time = db.query(
            func.avg(
                func.cast(
                    Document.extra_metadata['embedding_time_ms'].astext,
                    type_=float
                )
            )
        ).filter(
            and_(
                Document.uploaded_at >= start_date,
                Document.extra_metadata.isnot(None),
                Document.extra_metadata.has_key('embedding_time_ms')
            )
        ).scalar() or 0
    except:
        avg_embedding_time = 0
    
    # By chunking strategy
    try:
        by_strategy = db.query(
            Document.extra_metadata['chunking_strategy'].astext,
            func.count(Document.id)
        ).filter(
            and_(
                Document.uploaded_at >= start_date,
                Document.extra_metadata.isnot(None),
                Document.extra_metadata.has_key('chunking_strategy')
            )
        ).group_by(
            Document.extra_metadata['chunking_strategy'].astext
        ).all()
        
        by_chunking_strategy = {strategy or "unknown": count for strategy, count in by_strategy}
    except:
        by_chunking_strategy = {"unknown": total_embeddings}
    
    return EmbeddingStats(
        total_embeddings=total_embeddings,
        total_chunks=total_chunks,
        avg_chunks_per_document=round(avg_chunks, 2),
        embedding_model=embedding_model,
        avg_embedding_time_ms=round(avg_embedding_time, 2),
        by_chunking_strategy=by_chunking_strategy
    )


def get_hybrid_search_stats(db: Session, start_date: datetime) -> HybridSearchStats:
    """Get hybrid search statistics"""
    
    # Total searches
    total_searches = db.query(func.count(QueryLog.id)).filter(
        QueryLog.created_at >= start_date
    ).scalar() or 0
    
    # By search type (from query_metadata)
    try:
        vector_only = db.query(func.count(QueryLog.id)).filter(
            and_(
                QueryLog.created_at >= start_date,
                QueryLog.query_metadata.isnot(None),
                QueryLog.query_metadata.has_key('search_type'),
                QueryLog.query_metadata['search_type'].astext == 'vector'
            )
        ).scalar() or 0
        
        keyword_only = db.query(func.count(QueryLog.id)).filter(
            and_(
                QueryLog.created_at >= start_date,
                QueryLog.query_metadata.isnot(None),
                QueryLog.query_metadata.has_key('search_type'),
                QueryLog.query_metadata['search_type'].astext == 'keyword'
            )
        ).scalar() or 0
    except:
        vector_only = 0
        keyword_only = 0
    
    hybrid = total_searches - vector_only - keyword_only
    
    # Average search time
    try:
        avg_search_time = db.query(
            func.avg(
                func.cast(
                    QueryLog.query_metadata['search_time_ms'].astext,
                    type_=float
                )
            )
        ).filter(
            and_(
                QueryLog.created_at >= start_date,
                QueryLog.query_metadata.isnot(None),
                QueryLog.query_metadata.has_key('search_time_ms')
            )
        ).scalar() or 0
    except:
        avg_search_time = 0
    
    # Average results count
    try:
        avg_results = db.query(
            func.avg(
                func.cast(
                    QueryLog.query_metadata['results_count'].astext,
                    type_=float
                )
            )
        ).filter(
            and_(
                QueryLog.created_at >= start_date,
                QueryLog.query_metadata.isnot(None),
                QueryLog.query_metadata.has_key('results_count')
            )
        ).scalar() or 0
    except:
        avg_results = 0
    
    # Cache hit rate
    try:
        cache_hits = db.query(func.count(QueryLog.id)).filter(
            and_(
                QueryLog.created_at >= start_date,
                QueryLog.query_metadata.isnot(None),
                QueryLog.query_metadata.has_key('cache_hit'),
                QueryLog.query_metadata['cache_hit'].astext == 'true'
            )
        ).scalar() or 0
    except:
        cache_hits = 0
    
    cache_hit_rate = cache_hits / total_searches if total_searches > 0 else 0
    
    return HybridSearchStats(
        total_searches=total_searches,
        vector_only=vector_only,
        keyword_only=keyword_only,
        hybrid=hybrid,
        avg_search_time_ms=round(avg_search_time, 2),
        avg_results_count=round(avg_results, 2),
        cache_hit_rate=round(cache_hit_rate, 3)
    )


def get_rag_processing_stats(db: Session, start_date: datetime) -> RAGProcessingStats:
    """Get RAG processing statistics"""
    
    # Total queries
    total_queries = db.query(func.count(QueryLog.id)).filter(
        QueryLog.created_at >= start_date
    ).scalar() or 0
    
    # By mode
    by_mode_data = db.query(
        QueryLog.query_mode,
        func.count(QueryLog.id)
    ).filter(
        QueryLog.created_at >= start_date
    ).group_by(QueryLog.query_mode).all()
    
    by_mode = {mode or "unknown": count for mode, count in by_mode_data}
    
    # By complexity
    try:
        by_complexity_data = db.query(
            QueryLog.query_metadata['complexity_level'].astext,
            func.count(QueryLog.id)
        ).filter(
            and_(
                QueryLog.created_at >= start_date,
                QueryLog.query_metadata.isnot(None),
                QueryLog.query_metadata.has_key('complexity_level')
            )
        ).group_by(
            QueryLog.query_metadata['complexity_level'].astext
        ).all()
        
        by_complexity = {level or "unknown": count for level, count in by_complexity_data}
    except:
        by_complexity = {"unknown": total_queries}
    
    # Average response time
    avg_response_time = db.query(func.avg(QueryLog.response_time_ms)).filter(
        QueryLog.created_at >= start_date
    ).scalar() or 0
    
    # Average confidence score
    avg_confidence = db.query(func.avg(QueryLog.confidence_score)).filter(
        and_(
            QueryLog.created_at >= start_date,
            QueryLog.confidence_score.isnot(None)
        )
    ).scalar() or 0
    
    # Success rate (queries with confidence > 0.5)
    successful = db.query(func.count(QueryLog.id)).filter(
        and_(
            QueryLog.created_at >= start_date,
            QueryLog.confidence_score >= 0.5
        )
    ).scalar() or 0
    
    success_rate = successful / total_queries if total_queries > 0 else 0
    
    return RAGProcessingStats(
        total_queries=total_queries,
        by_mode=by_mode,
        by_complexity=by_complexity,
        avg_response_time_ms=round(avg_response_time, 2),
        avg_confidence_score=round(avg_confidence, 3),
        success_rate=round(success_rate, 3)
    )


def get_accuracy_trends(db: Session, days: int) -> List[AccuracyTrend]:
    """Get daily accuracy trends"""
    
    trends = []
    
    for i in range(days):
        date = datetime.utcnow().date() - timedelta(days=i)
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        
        # Total queries for the day
        total = db.query(func.count(QueryLog.id)).filter(
            and_(
                QueryLog.created_at >= start,
                QueryLog.created_at <= end
            )
        ).scalar() or 0
        
        if total == 0:
            continue
        
        # Average confidence
        avg_conf = db.query(func.avg(QueryLog.confidence_score)).filter(
            and_(
                QueryLog.created_at >= start,
                QueryLog.created_at <= end,
                QueryLog.confidence_score.isnot(None)
            )
        ).scalar() or 0
        
        # High confidence rate (>0.7)
        high_conf = db.query(func.count(QueryLog.id)).filter(
            and_(
                QueryLog.created_at >= start,
                QueryLog.created_at <= end,
                QueryLog.confidence_score >= 0.7
            )
        ).scalar() or 0
        
        high_conf_rate = high_conf / total if total > 0 else 0
        
        # Success rate (>0.5)
        successful = db.query(func.count(QueryLog.id)).filter(
            and_(
                QueryLog.created_at >= start,
                QueryLog.created_at <= end,
                QueryLog.confidence_score >= 0.5
            )
        ).scalar() or 0
        
        success_rate = successful / total if total > 0 else 0
        
        # Average response time
        avg_time = db.query(func.avg(QueryLog.response_time_ms)).filter(
            and_(
                QueryLog.created_at >= start,
                QueryLog.created_at <= end
            )
        ).scalar() or 0
        
        trends.append(AccuracyTrend(
            date=date.isoformat(),
            total_queries=total,
            avg_confidence=round(avg_conf, 3),
            high_confidence_rate=round(high_conf_rate, 3),
            success_rate=round(success_rate, 3),
            avg_response_time_ms=round(avg_time, 2)
        ))
    
    # Reverse to show oldest first
    return list(reversed(trends))
