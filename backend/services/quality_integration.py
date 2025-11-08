"""
Integration helper for answer quality evaluation in query processing.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from backend.services.answer_quality_service import get_answer_quality_service
from backend.db.models.feedback import AnswerFeedback
from backend.core.context_managers import db_transaction_sync

logger = logging.getLogger(__name__)


async def evaluate_and_store_quality(
    query: str,
    answer: str,
    sources: List[Dict[str, Any]],
    user_id: Optional[UUID],
    session_id: Optional[UUID],
    message_id: Optional[UUID],
    mode: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Evaluate answer quality and store in database.

    Args:
        query: User query
        answer: Generated answer
        sources: Source documents
        user_id: Optional user ID
        session_id: Optional session ID
        message_id: Optional message ID
        mode: Query mode (fast, balanced, deep)
        db: Database session

    Returns:
        Quality metrics dictionary
    """
    try:
        # Get quality service
        quality_service = get_answer_quality_service()

        # Evaluate quality
        quality_metrics = await quality_service.evaluate_answer(
            query=query, answer=answer, sources=sources, metadata={"mode": mode}
        )

        # Store in database
        with db_transaction_sync(db):
            feedback_record = AnswerFeedback(
                user_id=user_id,
                session_id=session_id,
                message_id=message_id,
                query=query,
                answer=answer,
                overall_score=quality_metrics.get("overall_score", 0.5),
                source_relevance=quality_metrics.get("metrics", {}).get("source_relevance"),
                grounding_score=quality_metrics.get("metrics", {}).get("grounding"),
                hallucination_risk=quality_metrics.get("metrics", {}).get(
                    "hallucination_risk"
                ),
                completeness_score=quality_metrics.get("metrics", {}).get("completeness"),
                length_score=quality_metrics.get("metrics", {}).get("length_score"),
                citation_score=quality_metrics.get("metrics", {}).get("citation_score"),
                source_count=len(sources),
                mode=mode,
                quality_level=quality_metrics.get("quality_level"),
                suggestions=quality_metrics.get("suggestions", []),
                extra_metadata=quality_metrics.get("metadata", {}),
            )

            db.add(feedback_record)
            db.flush()
            db.refresh(feedback_record)

        logger.info(
            f"Quality evaluation stored: id={feedback_record.id}, "
            f"score={feedback_record.overall_score:.2f}, "
            f"level={feedback_record.quality_level}"
        )

        return quality_metrics

    except Exception as e:
        logger.error(f"Failed to evaluate and store quality: {e}", exc_info=True)
        # Don't fail the query, just log the error
        return {"overall_score": 0.5, "quality_level": "unknown", "error": str(e)}
