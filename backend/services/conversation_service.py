"""Conversation service for managing sessions and messages."""

from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
import logging

from backend.db.repositories.session_repository import SessionRepository
from backend.db.repositories.message_repository import MessageRepository
from backend.db.repositories.message_source_repository import MessageSourceRepository
from backend.db.models.conversation import Session as SessionModel, Message

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations and messages."""

    def __init__(self, db: Session):
        """
        Initialize conversation service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.session_repo = SessionRepository(db)
        self.message_repo = MessageRepository(db)
        self.source_repo = MessageSourceRepository(db)

    def create_session(
        self, user_id: UUID, title: Optional[str] = None
    ) -> SessionModel:
        """
        Create a new conversation session.

        Args:
            user_id: User UUID
            title: Optional session title (auto-generated from first message if None)

        Returns:
            Created Session object

        Raises:
            Exception: If database operation fails
        """
        try:
            # Create session in transaction
            session = self.session_repo.create_session(user_id=user_id, title=title)

            # Commit transaction
            self.db.commit()
            self.db.refresh(session)

            logger.info(f"Created session {session.id} for user {user_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            self.db.rollback()
            raise

    def save_message_with_sources(
        self,
        session_id: UUID,
        user_id: UUID,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None,
        metadata: Optional[dict] = None,
    ) -> Message:
        """
        Save message and sources in a transaction.

        Args:
            session_id: Session UUID
            user_id: User UUID
            role: Message role (user, assistant, system)
            content: Message content
            sources: Optional list of source dictionaries containing:
                - document_id: str
                - document_name: str
                - chunk_id: str (optional)
                - score: float (optional)
                - text: str (optional)
                - extra_metadata: dict (optional)
            metadata: Optional metadata dictionary containing:
                - query_mode: str
                - processing_time_ms: int
                - confidence_score: float
                - cache_hit: bool
                - cache_match_type: str
                - cache_similarity: float
                - extra_metadata: dict

        Returns:
            Created Message object with sources

        Raises:
            Exception: If database operation fails (transaction will be rolled back)
        """
        try:
            # Begin transaction (all operations below are atomic)
            # Create message
            message = self.message_repo.create_message(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                metadata=metadata or {},
            )

            # Create sources if provided
            if sources:
                self.source_repo.create_sources(message_id=message.id, sources=sources)
                logger.debug(f"Created {len(sources)} sources for message {message.id}")

            # Update session stats
            session = self.session_repo.get_session_by_id(session_id, user_id)
            if session:
                new_message_count = session.message_count + 1
                new_total_tokens = session.total_tokens + (metadata or {}).get(
                    "tokens_used", 0
                )

                self.session_repo.update_session_stats(
                    session_id=session_id,
                    message_count=new_message_count,
                    total_tokens=new_total_tokens,
                )

            # Auto-generate title from first user message if session has no title
            if role == "user" and session and not session.title:
                auto_title = self._generate_title_from_content(content)
                self.session_repo.update_session(
                    session_id=session_id,
                    user_id=user_id,
                    updates={"title": auto_title},
                )
                logger.debug(
                    f"Auto-generated title for session {session_id}: {auto_title}"
                )

            # Commit transaction - all operations succeed or fail together
            self.db.commit()

            # Refresh to get updated relationships
            self.db.refresh(message)

            logger.info(
                f"Saved message {message.id} with {len(sources) if sources else 0} sources "
                f"in session {session_id}"
            )

            return message

        except Exception as e:
            logger.error(f"Failed to save message in session {session_id}: {e}")
            self.db.rollback()
            raise

    def get_or_create_session(
        self, user_id: UUID, session_id: Optional[UUID] = None
    ) -> SessionModel:
        """
        Get existing session or create new one (helper for query endpoint).

        Args:
            user_id: User UUID
            session_id: Optional session UUID (creates new if None)

        Returns:
            Session object (existing or newly created)

        Raises:
            Exception: If database operation fails
        """
        try:
            # If session_id provided, try to get it
            if session_id:
                session = self.session_repo.get_session_by_id(session_id, user_id)

                if session:
                    logger.debug(f"Found existing session {session_id}")
                    return session
                else:
                    logger.warning(
                        f"Session {session_id} not found or not owned by user {user_id}, "
                        "creating new session"
                    )

            # Create new session
            session = self.create_session(user_id=user_id)
            logger.info(f"Created new session {session.id} for user {user_id}")

            return session

        except Exception as e:
            logger.error(f"Failed to get or create session for user {user_id}: {e}")
            self.db.rollback()
            raise

    def search_conversations(
        self, user_id: UUID, query: str, filters: Optional[dict] = None
    ) -> List[Message]:
        """
        Search messages by content with optional filters.

        Args:
            user_id: User UUID
            query: Search query string
            filters: Optional filters dictionary containing:
                - session_id: UUID
                - role: str
                - start_date: datetime
                - end_date: datetime
                - query_mode: str

        Returns:
            List of Message objects matching search criteria

        Raises:
            Exception: If database operation fails
        """
        try:
            messages = self.message_repo.search_messages(
                user_id=user_id,
                query=query,
                filters=filters or {},
                load_sources=True,  # Load sources for search results
            )

            logger.info(
                f"Search found {len(messages)} messages for user {user_id} "
                f"with query '{query}'"
            )

            return messages

        except Exception as e:
            logger.error(f"Failed to search conversations for user {user_id}: {e}")
            self.db.rollback()
            raise

    def update_session_title(
        self, session_id: UUID, user_id: UUID, title: str
    ) -> Optional[SessionModel]:
        """
        Update session title.

        Args:
            session_id: Session UUID
            user_id: User UUID
            title: New session title

        Returns:
            Updated Session object if found and owned by user, None otherwise

        Raises:
            Exception: If database operation fails
        """
        try:
            # Update session in transaction
            session = self.session_repo.update_session(
                session_id=session_id, user_id=user_id, updates={"title": title}
            )

            if session:
                # Commit transaction
                self.db.commit()
                self.db.refresh(session)
                logger.info(f"Updated title for session {session_id}")
            else:
                logger.warning(
                    f"Cannot update session {session_id}: not found or not owned by user {user_id}"
                )

            return session

        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            self.db.rollback()
            raise

    def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        """
        Delete a session and all associated messages.

        Args:
            session_id: Session UUID
            user_id: User UUID

        Returns:
            True if session was deleted, False if not found or not owned by user

        Raises:
            Exception: If database operation fails
        """
        try:
            # Delete session in transaction (cascade deletes messages and sources)
            deleted = self.session_repo.delete_session(
                session_id=session_id, user_id=user_id
            )

            if deleted:
                # Commit transaction
                self.db.commit()
                logger.info(f"Deleted session {session_id} for user {user_id}")
            else:
                logger.warning(
                    f"Cannot delete session {session_id}: not found or not owned by user {user_id}"
                )

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            self.db.rollback()
            raise

    @staticmethod
    def _generate_title_from_content(content: str, max_length: int = 50) -> str:
        """
        Generate a session title from message content.

        Args:
            content: Message content
            max_length: Maximum title length

        Returns:
            Generated title (first N characters of content)
        """
        # Remove extra whitespace and newlines
        cleaned = " ".join(content.split())

        # Truncate to max_length
        if len(cleaned) <= max_length:
            return cleaned

        # Truncate and add ellipsis
        return cleaned[:max_length].rsplit(" ", 1)[0] + "..."
