"""
Monitoring Statistics Models

Stores monitoring statistics for:
- File uploads
- Embeddings
- Hybrid search
- RAG processing
- Daily accuracy trends
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class FileUploadStat(Base):
    """File upload statistics"""
    __tablename__ = "file_upload_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(255), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_mb = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)  # completed, failed
    processing_time_ms = Column(Float)
    error_message = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_file_upload_created_status', 'created_at', 'status'),
        Index('idx_file_upload_type', 'file_type'),
    )


class EmbeddingStat(Base):
    """Embedding generation statistics"""
    __tablename__ = "embedding_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(255), nullable=False, index=True)
    embedding_model = Column(String(100), nullable=False)
    total_chunks = Column(Integer, nullable=False)
    chunking_strategy = Column(String(50), nullable=False)
    embedding_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_embedding_created', 'created_at'),
        Index('idx_embedding_model', 'embedding_model'),
    )


class HybridSearchStat(Base):
    """Hybrid search statistics"""
    __tablename__ = "hybrid_search_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), index=True)
    search_type = Column(String(50), nullable=False)  # vector_only, keyword_only, hybrid
    query_text = Column(String(1000))
    results_count = Column(Integer, nullable=False)
    search_time_ms = Column(Float, nullable=False)
    cache_hit = Column(Integer, default=0)  # 0 or 1
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_search_created_type', 'created_at', 'search_type'),
        Index('idx_search_cache', 'cache_hit'),
    )


class RAGProcessingStat(Base):
    """RAG processing statistics"""
    __tablename__ = "rag_processing_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), index=True)
    query_text = Column(String(1000))
    mode = Column(String(50), nullable=False)  # auto, fast, balanced, deep
    complexity = Column(String(50))  # simple, medium, complex
    response_time_ms = Column(Float, nullable=False)
    confidence_score = Column(Float)
    success = Column(Integer, default=1)  # 0 or 1
    error_message = Column(String(1000))
    token_usage = Column(JSON)  # {input: X, output: Y, total: Z}
    quality_scores = Column(JSON)  # {relevance: X, accuracy: Y, ...}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    __table_args__ = (
        Index('idx_rag_created_mode', 'created_at', 'mode'),
        Index('idx_rag_success', 'success'),
        Index('idx_rag_complexity', 'complexity'),
    )


class DailyAccuracyTrend(Base):
    """Daily aggregated accuracy trends"""
    __tablename__ = "daily_accuracy_trends"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    total_queries = Column(Integer, nullable=False, default=0)
    avg_confidence = Column(Float)
    high_confidence_rate = Column(Float)  # % of queries with confidence > 0.8
    success_rate = Column(Float)
    avg_response_time_ms = Column(Float)
    avg_token_usage = Column(Float)
    avg_quality_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_daily_trend_date', 'date'),
    )
