"""
Monitoring Statistics API

Provides endpoints for monitoring statistics stored in PostgreSQL.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from backend.db.database import get_db
from backend.services.monitoring_service import MonitoringService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


@router.get("/stats/overview")
async def get_monitoring_overview(
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get complete monitoring statistics overview.
    
    Args:
        days: Number of days to include (1-90)
        
    Returns:
        Complete monitoring statistics including:
        - File uploads
        - Embeddings
        - Hybrid search
        - RAG processing
        - Daily accuracy trends
    """
    try:
        service = MonitoringService(db)
        overview = service.get_overview(days=days)
        return overview
    except Exception as e:
        logger.error(f"Failed to get monitoring overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve monitoring statistics: {str(e)}"
        )


@router.get("/stats/file-uploads")
async def get_file_upload_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get file upload statistics"""
    try:
        service = MonitoringService(db)
        return service.get_file_upload_stats(days=days)
    except Exception as e:
        logger.error(f"Failed to get file upload stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/embeddings")
async def get_embedding_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get embedding statistics"""
    try:
        service = MonitoringService(db)
        return service.get_embedding_stats(days=days)
    except Exception as e:
        logger.error(f"Failed to get embedding stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/hybrid-search")
async def get_hybrid_search_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get hybrid search statistics"""
    try:
        service = MonitoringService(db)
        return service.get_hybrid_search_stats(days=days)
    except Exception as e:
        logger.error(f"Failed to get hybrid search stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/rag-processing")
async def get_rag_processing_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get RAG processing statistics"""
    try:
        service = MonitoringService(db)
        return service.get_rag_processing_stats(days=days)
    except Exception as e:
        logger.error(f"Failed to get RAG processing stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/daily-trends")
async def get_daily_trends(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get daily accuracy trends"""
    try:
        service = MonitoringService(db)
        trends = service.get_daily_trends(days=days)
        return {"trends": trends}
    except Exception as e:
        logger.error(f"Failed to get daily trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))
