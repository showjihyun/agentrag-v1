"""Feedback repository for database operations."""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict
from datetime import datetime
import logging
from uuid import UUID

from backend.db.models.feedback import AnswerFeedback

logger = logging.getLogger(__name__)


class FeedbackRepository:
    """Database operations for answer feedback."""

    def __init__(self, db: Session):
        """Initialize repository with database session."""
        self.db = db

    def create_feedback(
        self,
        message_id: UUID,
        user_id: UUID,
        rating: int,
        feedback_text: Optional[str] = None,
        feedback_type: Optional[str] = None,
    ) -> AnswerFeedback:
        """Create new feedback record."""
        try:
            feedback = AnswerFeedback(
                message_id=message_id,
                user_id=user_id,
                rating=rating,
                feedback_text=feedback_text,
                feedback_type=feedback_type,
            )

            self.db.add(feedback)
            self.db.commit()
            self.db.refresh(feedback)

            logger.info(f"Created feedback for message {message_id}")
            return feedback

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create feedback: {e}")
            raise

    def get_feedback_by_message(self, message_id: UUID) -> Optional[AnswerFeedback]:
        """Get feedback for a specific message."""
        return (
            self.db.query(AnswerFeedback)
            .filter(AnswerFeedback.message_id == message_id)
            .first()
        )

    def get_user_feedback(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[AnswerFeedback]:
        """Get all feedback from a user."""
        return (
            self.db.query(AnswerFeedback)
            .filter(AnswerFeedback.user_id == user_id)
            .order_by(AnswerFeedback.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_feedback_stats(self) -> Dict:
        """Get overall feedback statistics."""
        total = self.db.query(func.count(AnswerFeedback.id)).scalar() or 0
        avg_rating = self.db.query(func.avg(AnswerFeedback.rating)).scalar() or 0

        rating_distribution = {}
        for rating in range(1, 6):
            count = (
                self.db.query(func.count(AnswerFeedback.id))
                .filter(AnswerFeedback.rating == rating)
                .scalar()
                or 0
            )
            rating_distribution[rating] = count

        return {
            "total_feedback": total,
            "average_rating": float(avg_rating),
            "rating_distribution": rating_distribution,
        }

    def update_feedback(
        self,
        feedback_id: UUID,
        rating: Optional[int] = None,
        feedback_text: Optional[str] = None,
    ) -> Optional[AnswerFeedback]:
        """Update existing feedback."""
        feedback = (
            self.db.query(AnswerFeedback)
            .filter(AnswerFeedback.id == feedback_id)
            .first()
        )

        if not feedback:
            return None

        if rating is not None:
            feedback.rating = rating
        if feedback_text is not None:
            feedback.feedback_text = feedback_text

        feedback.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(feedback)
            return feedback
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update feedback: {e}")
            raise
