"""Session repository for database operations."""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime
import logging
from uuid import UUID

from backend.db.models.conversation import Session as SessionModel

logger = logging.getLogger(__name__)


class SessionRepository:
    """Database operations for conversation sessions."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_session(
        self, user_id: UUID, title: Optional[str] = None
    ) -> SessionModel:
        """
        Create a new conversation session.

        Args:
            user_id: User UUID
            title: Optional session title

        Returns:
            Created Session object

        Raises:
            IntegrityError: If database constraint is violated
        """
        try:
            session = SessionModel(
                user_id=user_id, title=title, message_count=0, total_tokens=0
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            logger.info(f"Created session: {session.id} for user {user_id}")
            return session

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise

    def get_user_sessions(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        load_messages: bool = False,
    ) -> List[SessionModel]:
        """
        Get user's conversation sessions.

        Args:
            user_id: User UUID
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            load_messages: If True, eagerly load messages using joinedload

        Returns:
            List of Session objects ordered by created_at DESC
        """
        query = self.db.query(SessionModel).filter(SessionModel.user_id == user_id)

        # Eagerly load messages if requested to avoid N+1 queries
        if load_messages:
            query = query.options(joinedload(SessionModel.messages))

        sessions = (
            query.order_by(SessionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        logger.debug(
            f"Retrieved {len(sessions)} sessions for user {user_id} "
            f"(limit={limit}, offset={offset}, load_messages={load_messages})"
        )

        return sessions

    def get_session_by_id(
        self, session_id: UUID, user_id: UUID, load_messages: bool = False
    ) -> Optional[SessionModel]:
        """
        Get session by ID with user ownership verification.

        Args:
            session_id: Session UUID
            user_id: User UUID (for ownership verification)
            load_messages: If True, eagerly load messages using joinedload

        Returns:
            Session object if found and owned by user, None otherwise
        """
        query = self.db.query(SessionModel).filter(
            SessionModel.id == session_id, SessionModel.user_id == user_id
        )

        # Eagerly load messages if requested to avoid N+1 queries
        if load_messages:
            query = query.options(joinedload(SessionModel.messages))

        session = query.first()

        if session:
            logger.debug(f"Found session {session_id} for user {user_id}")
        else:
            logger.debug(
                f"Session {session_id} not found or not owned by user {user_id}"
            )

        return session

    def update_session(
        self, session_id: UUID, user_id: UUID, updates: dict
    ) -> Optional[SessionModel]:
        """
        Update session information.

        Args:
            session_id: Session UUID
            user_id: User UUID (for ownership verification)
            updates: Dictionary of fields to update (e.g., {"title": "New Title"})

        Returns:
            Updated Session object if found and owned by user, None otherwise
        """
        session = self.get_session_by_id(session_id, user_id)

        if not session:
            logger.warning(
                f"Cannot update session {session_id}: not found or not owned by user {user_id}"
            )
            return None

        # Update allowed fields
        allowed_fields = {"title"}

        for key, value in updates.items():
            if key in allowed_fields and hasattr(session, key):
                setattr(session, key, value)
                logger.debug(f"Updated session {session_id} field {key}")

        # Update timestamp
        session.updated_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(session)
            logger.info(f"Updated session: {session_id}")
            return session
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to update session {session_id}: {e}")
            raise

    def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        """
        Delete a session and all associated messages (cascade).

        Args:
            session_id: Session UUID
            user_id: User UUID (for ownership verification)

        Returns:
            True if session was deleted, False if not found or not owned by user
        """
        session = self.get_session_by_id(session_id, user_id)

        if not session:
            logger.warning(
                f"Cannot delete session {session_id}: not found or not owned by user {user_id}"
            )
            return False

        try:
            self.db.delete(session)
            self.db.commit()

            logger.info(
                f"Deleted session {session_id} and associated messages for user {user_id}"
            )
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise

    def update_session_stats(
        self,
        session_id: UUID,
        message_count: Optional[int] = None,
        total_tokens: Optional[int] = None,
    ) -> Optional[SessionModel]:
        """
        Update session statistics.

        Args:
            session_id: Session UUID
            message_count: New message count (if provided)
            total_tokens: New total tokens (if provided)

        Returns:
            Updated Session object if found, None otherwise
        """
        session = (
            self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        )

        if not session:
            logger.warning(f"Cannot update stats for session {session_id}: not found")
            return None

        # Update provided stats
        if message_count is not None:
            session.message_count = message_count

        if total_tokens is not None:
            session.total_tokens = total_tokens

        # Update timestamps
        session.updated_at = datetime.utcnow()
        session.last_message_at = datetime.utcnow()

        try:
            self.db.commit()
            self.db.refresh(session)

            logger.debug(
                f"Updated stats for session {session_id}: "
                f"messages={session.message_count}, tokens={session.total_tokens}"
            )

            return session
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update stats for session {session_id}: {e}")
            raise
