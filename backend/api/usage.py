"""
Usage Statistics API

Provides endpoints for usage statistics and analytics.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional
from datetime import datetime, timedelta

from backend.db.database import get_db
from sqlalchemy.orm import Session
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.usage_service import get_usage_service
from backend.core.enhanced_error_handler import handle_error, DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/usage", tags=["Usage"])


@router.get("/stats")
async def get_usage_stats(
    timeRange: str = Query("week", description="Time range: day, week, month, year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get usage statistics for specified time range."""
    try:
        usage_service = get_usage_service(db)
        
        stats = await usage_service.get_usage_stats(
            user_id=current_user.id,
            time_range=timeRange,
            limit=30
        )
        
        return stats

    except DatabaseError as e:
        app_error = handle_error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=app_error.message
        )
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to get usage stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage stats"
        )


@router.get("/summary")
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall usage summary."""
    try:
        usage_service = get_usage_service(db)
        
        summary = await usage_service.get_usage_summary(user_id=current_user.id)
        
        return summary

    except DatabaseError as e:
        app_error = handle_error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=app_error.message
        )
    except Exception as e:
        app_error = handle_error(e)
        logger.error(f"Failed to get usage summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage summary"
        )

    except Exception as e:
        logger.error(f"Failed to get usage summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get usage summary: {str(e)}"
        )


@router.get("/cost-breakdown")
async def get_cost_breakdown(
    timeRange: str = Query("month"), db: Session = Depends(get_db)
):
    """Get detailed cost breakdown."""
    try:
        # TODO: Implement actual database operations

        return {
            "breakdown": {
                "llmCosts": 25.50,
                "embeddingCosts": 8.75,
                "storageCosts": 5.25,
                "otherCosts": 2.15,
            },
            "total": 41.65,
            "currency": "USD",
        }

    except Exception as e:
        logger.error(f"Failed to get cost breakdown: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get cost breakdown: {str(e)}"
        )
