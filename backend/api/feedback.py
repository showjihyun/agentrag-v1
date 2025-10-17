"""
Feedback API endpoints for user feedback collection.

Allows users to rate responses and provide comments for improvement.
"""

import logging
from typing import Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


# Request/Response Models
class FeedbackSubmitRequest(BaseModel):
    """Feedback submission request"""
    message_id: str = Field(..., description="Message ID being rated")
    rating: int = Field(..., ge=-1, le=1, description="Rating: 1 (positive), -1 (negative)")
    comment: Optional[str] = Field(None, description="Optional comment for negative feedback")


class FeedbackSubmitResponse(BaseModel):
    """Feedback submission response"""
    feedback_id: str
    message: str
    timestamp: datetime


class FeedbackStatsResponse(BaseModel):
    """Feedback statistics response"""
    total_feedback: int
    positive_count: int
    negative_count: int
    positive_rate: float
    recent_feedback: list


# In-memory storage (replace with database in production)
feedback_storage = []


@router.post("/submit", response_model=FeedbackSubmitResponse)
async def submit_feedback(request: FeedbackSubmitRequest):
    """
    Submit user feedback for a message.
    
    Args:
        request: Feedback submission request
    
    Returns:
        FeedbackSubmitResponse with feedback ID
    
    Raises:
        400: Invalid rating value
        500: Internal server error
    """
    try:
        logger.info(
            f"Received feedback: message_id={request.message_id}, "
            f"rating={request.rating}, has_comment={bool(request.comment)}"
        )
        
        # Validate rating
        if request.rating not in [-1, 1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be 1 (positive) or -1 (negative)"
            )
        
        # Create feedback record
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        feedback_record = {
            "feedback_id": feedback_id,
            "message_id": request.message_id,
            "rating": request.rating,
            "comment": request.comment,
            "timestamp": timestamp,
            "rating_type": "positive" if request.rating > 0 else "negative"
        }
        
        # Store feedback (in-memory for now)
        feedback_storage.append(feedback_record)
        
        logger.info(
            f"Feedback stored: feedback_id={feedback_id}, "
            f"rating_type={feedback_record['rating_type']}"
        )
        
        # Log negative feedback with comments for monitoring
        if request.rating < 0 and request.comment:
            logger.warning(
                f"Negative feedback with comment: "
                f"message_id={request.message_id}, "
                f"comment='{request.comment}'"
            )
        
        return FeedbackSubmitResponse(
            feedback_id=feedback_id,
            message="Feedback submitted successfully",
            timestamp=timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats():
    """
    Get feedback statistics.
    
    Returns:
        FeedbackStatsResponse with aggregated statistics
    """
    try:
        total_feedback = len(feedback_storage)
        
        if total_feedback == 0:
            return FeedbackStatsResponse(
                total_feedback=0,
                positive_count=0,
                negative_count=0,
                positive_rate=0.0,
                recent_feedback=[]
            )
        
        # Calculate statistics
        positive_count = sum(1 for f in feedback_storage if f["rating"] > 0)
        negative_count = sum(1 for f in feedback_storage if f["rating"] < 0)
        positive_rate = (positive_count / total_feedback) * 100 if total_feedback > 0 else 0.0
        
        # Get recent feedback (last 10)
        recent_feedback = sorted(
            feedback_storage,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:10]
        
        # Format recent feedback
        recent_formatted = [
            {
                "feedback_id": f["feedback_id"],
                "message_id": f["message_id"],
                "rating_type": f["rating_type"],
                "comment": f["comment"],
                "timestamp": f["timestamp"].isoformat()
            }
            for f in recent_feedback
        ]
        
        logger.info(
            f"Feedback stats: total={total_feedback}, "
            f"positive={positive_count}, negative={negative_count}, "
            f"positive_rate={positive_rate:.1f}%"
        )
        
        return FeedbackStatsResponse(
            total_feedback=total_feedback,
            positive_count=positive_count,
            negative_count=negative_count,
            positive_rate=positive_rate,
            recent_feedback=recent_formatted
        )
        
    except Exception as e:
        logger.error(f"Failed to get feedback stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback stats: {str(e)}"
        )


@router.get("/message/{message_id}")
async def get_message_feedback(message_id: str):
    """
    Get feedback for a specific message.
    
    Args:
        message_id: Message ID
    
    Returns:
        List of feedback for the message
    """
    try:
        message_feedback = [
            {
                "feedback_id": f["feedback_id"],
                "rating": f["rating"],
                "rating_type": f["rating_type"],
                "comment": f["comment"],
                "timestamp": f["timestamp"].isoformat()
            }
            for f in feedback_storage
            if f["message_id"] == message_id
        ]
        
        logger.info(
            f"Retrieved {len(message_feedback)} feedback(s) for message {message_id}"
        )
        
        return {
            "message_id": message_id,
            "feedback_count": len(message_feedback),
            "feedback": message_feedback
        }
        
    except Exception as e:
        logger.error(f"Failed to get message feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message feedback: {str(e)}"
        )


@router.delete("/clear")
async def clear_feedback():
    """
    Clear all feedback (admin only - for testing).
    
    Returns:
        Confirmation message
    """
    try:
        count = len(feedback_storage)
        feedback_storage.clear()
        
        logger.info(f"Cleared {count} feedback records")
        
        return {
            "message": f"Cleared {count} feedback records",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear feedback: {str(e)}"
        )
