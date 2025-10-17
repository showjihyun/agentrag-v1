"""Message source repository for database operations."""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import logging
from uuid import UUID

from backend.db.models.conversation import MessageSource

logger = logging.getLogger(__name__)


class MessageSourceRepository:
    """Database operations for message source references."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_sources(
        self, message_id: UUID, sources: List[dict]
    ) -> List[MessageSource]:
        """
        Create multiple source references for a message (bulk insert).

        Args:
            message_id: Message UUID
            sources: List of source dictionaries containing:
                - document_id: str
                - document_name: str
                - chunk_id: str (optional)
                - score: float (optional)
                - text: str (optional)
                - extra_metadata: dict (optional)

        Returns:
            List of created MessageSource objects

        Raises:
            IntegrityError: If database constraint is violated
        """
        if not sources:
            logger.debug(f"No sources to create for message {message_id}")
            return []

        try:
            source_objects = []

            for source_data in sources:
                source = MessageSource(
                    message_id=message_id,
                    document_id=source_data.get("document_id", ""),
                    document_name=source_data.get("document_name", ""),
                    chunk_id=source_data.get("chunk_id"),
                    score=source_data.get("score"),
                    text=source_data.get("text"),
                    extra_metadata=source_data.get("extra_metadata", {}),
                )
                source_objects.append(source)

            # Add all objects to session
            for source in source_objects:
                self.db.add(source)

            # Commit to database
            self.db.commit()

            # Refresh to get IDs
            for source in source_objects:
                self.db.refresh(source)

            logger.info(
                f"Created {len(source_objects)} sources for message {message_id}"
            )
            return source_objects

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create sources for message {message_id}: {e}")
            raise

    def get_message_sources(self, message_id: UUID) -> List[MessageSource]:
        """
        Get all source references for a message.

        Args:
            message_id: Message UUID

        Returns:
            List of MessageSource objects ordered by score DESC
        """
        sources = (
            self.db.query(MessageSource)
            .filter(MessageSource.message_id == message_id)
            .order_by(MessageSource.score.desc().nullslast())
            .all()
        )

        logger.debug(f"Retrieved {len(sources)} sources for message {message_id}")

        return sources

    def delete_message_sources(self, message_id: UUID) -> int:
        """
        Delete all sources for a message.

        Args:
            message_id: Message UUID

        Returns:
            Number of sources deleted
        """
        try:
            count = (
                self.db.query(MessageSource)
                .filter(MessageSource.message_id == message_id)
                .delete()
            )

            self.db.commit()

            logger.info(f"Deleted {count} sources for message {message_id}")
            return count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete sources for message {message_id}: {e}")
            raise
