"""Message repository for database operations."""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, and_
from typing import Optional, List
from datetime import datetime
import logging
from uuid import UUID

from backend.db.models.conversation import Message

logger = logging.getLogger(__name__)


class MessageRepository:
    """Database operations for conversation messages."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_message(
        self,
        session_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> Message:
        """
        Create a new message.

        Args:
            session_id: Session UUID
            user_id: User UUID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata dictionary containing:
                - query_mode: str
                - processing_time_ms: int
                - confidence_score: float
                - cache_hit: bool
                - cache_match_type: str
                - cache_similarity: float
                - extra_metadata: dict

        Returns:
            Created Message object

        Raises:
            IntegrityError: If database constraint is violated
        """
        try:
            metadata = metadata or {}

            message = Message(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                query_mode=metadata.get("query_mode"),
                processing_time_ms=metadata.get("processing_time_ms"),
                confidence_score=metadata.get("confidence_score"),
                cache_hit=metadata.get("cache_hit", False),
                cache_match_type=metadata.get("cache_match_type"),
                cache_similarity=metadata.get("cache_similarity"),
                extra_metadata=metadata.get("extra_metadata", {}),
            )

            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)

            logger.info(
                f"Created message: {message.id} in session {session_id} "
                f"(role={role})"
            )
            return message

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create message in session {session_id}: {e}")
            raise

    def get_session_messages(
        self,
        session_id: UUID,
        limit: int = 50,
        offset: int = 0,
        load_sources: bool = False,
    ) -> List[Message]:
        """
        Get messages for a session with pagination.

        Args:
            session_id: Session UUID
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            load_sources: If True, eagerly load sources using joinedload

        Returns:
            List of Message objects ordered by created_at ASC (chronological)
        """
        query = self.db.query(Message).filter(Message.session_id == session_id)

        # Eagerly load sources if requested to avoid N+1 queries
        if load_sources:
            query = query.options(joinedload(Message.sources))

        messages = (
            query.order_by(Message.created_at.asc()).limit(limit).offset(offset).all()
        )

        logger.debug(
            f"Retrieved {len(messages)} messages for session {session_id} "
            f"(limit={limit}, offset={offset}, load_sources={load_sources})"
        )

        return messages

    def search_messages(
        self,
        user_id: UUID,
        query: str,
        filters: Optional[dict] = None,
        load_sources: bool = False,
    ) -> List[Message]:
        """
        Search messages by content with optional filters.

        Args:
            user_id: User UUID (for user isolation)
            query: Search query string
            filters: Optional filters dictionary containing:
                - session_id: UUID
                - role: str
                - start_date: datetime
                - end_date: datetime
                - query_mode: str
            load_sources: If True, eagerly load sources using joinedload

        Returns:
            List of Message objects ordered by created_at DESC
        """
        filters = filters or {}

        # Base query with user isolation
        query_obj = self.db.query(Message).filter(Message.user_id == user_id)

        # Eagerly load sources if requested to avoid N+1 queries
        if load_sources:
            query_obj = query_obj.options(joinedload(Message.sources))

        # Full-text search on content (case-insensitive)
        if query:
            query_obj = query_obj.filter(Message.content.ilike(f"%{query}%"))

        # Apply filters
        if filters.get("session_id"):
            query_obj = query_obj.filter(Message.session_id == filters["session_id"])

        if filters.get("role"):
            query_obj = query_obj.filter(Message.role == filters["role"])

        if filters.get("start_date"):
            query_obj = query_obj.filter(Message.created_at >= filters["start_date"])

        if filters.get("end_date"):
            query_obj = query_obj.filter(Message.created_at <= filters["end_date"])

        if filters.get("query_mode"):
            query_obj = query_obj.filter(Message.query_mode == filters["query_mode"])

        # Order by most recent first (created_at DESC)
        messages = query_obj.order_by(Message.created_at.desc()).all()

        logger.debug(
            f"Search found {len(messages)} messages for user {user_id} "
            f"with query '{query}' (load_sources={load_sources})"
        )

        return messages

    def get_message_with_sources(self, message_id: UUID) -> Optional[Message]:
        """
        Get message with sources eagerly loaded.

        Args:
            message_id: Message UUID

        Returns:
            Message object with sources loaded, None if not found
        """
        message = (
            self.db.query(Message)
            .options(joinedload(Message.sources))
            .filter(Message.id == message_id)
            .first()
        )

        if message:
            logger.debug(
                f"Found message {message_id} with {len(message.sources)} sources"
            )
        else:
            logger.debug(f"Message {message_id} not found")

        return message

    def get_message_by_id(
        self, message_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[Message]:
        """
        Get message by ID with optional user ownership verification.

        Args:
            message_id: Message UUID
            user_id: Optional User UUID (for ownership verification)

        Returns:
            Message object if found (and owned by user if user_id provided), None otherwise
        """
        query_obj = self.db.query(Message).filter(Message.id == message_id)

        if user_id:
            query_obj = query_obj.filter(Message.user_id == user_id)

        message = query_obj.first()

        if message:
            logger.debug(f"Found message {message_id}")
        else:
            logger.debug(f"Message {message_id} not found")

        return message

    def delete_message(self, message_id: UUID, user_id: UUID) -> bool:
        """
        Delete a message and all associated sources (cascade).

        Args:
            message_id: Message UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if message was deleted, False if not found or not owned by user
        """
        message = self.get_message_by_id(message_id, user_id)

        if not message:
            logger.warning(
                f"Cannot delete message {message_id}: not found or not owned by user {user_id}"
            )
            return False

        try:
            self.db.delete(message)
            self.db.commit()

            logger.info(
                f"Deleted message {message_id} and associated sources for user {user_id}"
            )
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete message {message_id}: {e}")
            raise
