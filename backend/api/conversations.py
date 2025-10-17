"""Conversation management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging

from backend.db.database import get_db
from backend.db.models.user import User
from backend.core.auth_dependencies import get_current_user
from backend.services.conversation_service import ConversationService
from backend.models.conversation import (
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    MessageResponse,
    MessageListResponse,
    MessageSourceResponse,
    SearchRequest,
    SearchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post(
    "/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED
)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new conversation session.

    Requires authentication. Creates a new session for the authenticated user.
    If no title is provided, it will be auto-generated from the first user message.

    Args:
        session_data: Session creation data (optional title)
        current_user: Authenticated user
        db: Database session

    Returns:
        Created session information

    Raises:
        401: If not authenticated
        500: If database operation fails
    """
    try:
        conv_service = ConversationService(db)
        session = conv_service.create_session(
            user_id=current_user.id, title=session_data.title
        )

        logger.info(f"User {current_user.email} created session {session.id}")
        return SessionResponse.model_validate(session)

    except Exception as e:
        logger.error(f"Failed to create session for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session",
        )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = Query(50, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List user's conversation sessions.

    Requires authentication. Returns paginated list of sessions ordered by creation date (newest first).

    Args:
        limit: Maximum number of sessions to return (1-100, default 50)
        offset: Number of sessions to skip for pagination (default 0)
        current_user: Authenticated user
        db: Database session

    Returns:
        List of session information

    Raises:
        401: If not authenticated
        422: If invalid pagination parameters
    """
    try:
        conv_service = ConversationService(db)
        sessions = conv_service.session_repo.get_user_sessions(
            user_id=current_user.id, limit=limit, offset=offset
        )

        logger.debug(
            f"User {current_user.email} retrieved {len(sessions)} sessions "
            f"(limit={limit}, offset={offset})"
        )

        return [SessionResponse.model_validate(session) for session in sessions]

    except Exception as e:
        logger.error(f"Failed to list sessions for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions",
        )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get session details by ID.

    Requires authentication. Verifies that the session belongs to the authenticated user.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Session information

    Raises:
        401: If not authenticated
        403: If session doesn't belong to user
        404: If session not found
    """
    try:
        conv_service = ConversationService(db)
        session = conv_service.session_repo.get_session_by_id(
            session_id=session_id, user_id=current_user.id
        )

        if not session:
            logger.warning(
                f"User {current_user.email} attempted to access non-existent "
                f"or unauthorized session {session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied",
            )

        logger.debug(f"User {current_user.email} retrieved session {session_id}")
        return SessionResponse.model_validate(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get session {session_id} for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session",
        )


@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: UUID,
    session_update: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update session title.

    Requires authentication. Verifies that the session belongs to the authenticated user.

    Args:
        session_id: Session UUID
        session_update: Update data (new title)
        current_user: Authenticated user
        db: Database session

    Returns:
        Updated session information

    Raises:
        401: If not authenticated
        403: If session doesn't belong to user
        404: If session not found
        422: If validation fails
    """
    try:
        conv_service = ConversationService(db)
        session = conv_service.update_session_title(
            session_id=session_id, user_id=current_user.id, title=session_update.title
        )

        if not session:
            logger.warning(
                f"User {current_user.email} attempted to update non-existent "
                f"or unauthorized session {session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied",
            )

        logger.info(
            f"User {current_user.email} updated session {session_id} "
            f"title to '{session_update.title}'"
        )
        return SessionResponse.model_validate(session)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to update session {session_id} for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update session",
        )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a session and all associated messages.

    Requires authentication. Verifies that the session belongs to the authenticated user.
    Cascade deletes all messages and sources associated with the session.

    Args:
        session_id: Session UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        No content (204)

    Raises:
        401: If not authenticated
        403: If session doesn't belong to user
        404: If session not found
    """
    try:
        conv_service = ConversationService(db)
        deleted = conv_service.delete_session(
            session_id=session_id, user_id=current_user.id
        )

        if not deleted:
            logger.warning(
                f"User {current_user.email} attempted to delete non-existent "
                f"or unauthorized session {session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied",
            )

        logger.info(
            f"User {current_user.email} deleted session {session_id} "
            "and all associated messages"
        )
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to delete session {session_id} for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session",
        )


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(
    session_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get messages for a session.

    Requires authentication. Verifies that the session belongs to the authenticated user.
    Returns paginated list of messages ordered chronologically (oldest first).

    Args:
        session_id: Session UUID
        limit: Maximum number of messages to return (1-200, default 50)
        offset: Number of messages to skip for pagination (default 0)
        current_user: Authenticated user
        db: Database session

    Returns:
        Paginated list of messages with sources

    Raises:
        401: If not authenticated
        403: If session doesn't belong to user
        404: If session not found
        422: If invalid pagination parameters
    """
    try:
        conv_service = ConversationService(db)

        # Verify session ownership
        session = conv_service.session_repo.get_session_by_id(
            session_id=session_id, user_id=current_user.id
        )

        if not session:
            logger.warning(
                f"User {current_user.email} attempted to access messages from "
                f"non-existent or unauthorized session {session_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied",
            )

        # Get messages with sources
        messages = conv_service.message_repo.get_session_messages(
            session_id=session_id, limit=limit, offset=offset, load_sources=True
        )

        # Convert to response models
        message_responses = []
        for message in messages:
            # Convert sources
            source_responses = [
                MessageSourceResponse.model_validate(source)
                for source in message.sources
            ]

            # Create message response
            message_dict = {
                "id": message.id,
                "session_id": message.session_id,
                "role": message.role,
                "content": message.content,
                "query_mode": message.query_mode,
                "confidence_score": message.confidence_score,
                "cache_hit": message.cache_hit,
                "created_at": message.created_at,
                "sources": source_responses,
            }
            message_responses.append(MessageResponse(**message_dict))

        logger.debug(
            f"User {current_user.email} retrieved {len(messages)} messages "
            f"from session {session_id} (limit={limit}, offset={offset})"
        )

        return MessageListResponse(
            messages=message_responses,
            total=session.message_count,
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get messages for session {session_id} "
            f"for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages",
        )


@router.post("/search", response_model=SearchResponse)
async def search_messages(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search messages by content.

    Requires authentication. Searches only within the authenticated user's messages.
    Supports full-text search with optional filters for session, date range, etc.

    Args:
        search_request: Search parameters (query, filters)
        current_user: Authenticated user
        db: Database session

    Returns:
        List of matching messages with sources

    Raises:
        401: If not authenticated
        422: If validation fails
    """
    try:
        conv_service = ConversationService(db)

        # Build filters
        filters = {}
        if search_request.session_id:
            filters["session_id"] = search_request.session_id
        if search_request.start_date:
            filters["start_date"] = search_request.start_date
        if search_request.end_date:
            filters["end_date"] = search_request.end_date

        # Search messages
        messages = conv_service.search_conversations(
            user_id=current_user.id, query=search_request.query, filters=filters
        )

        # Convert to response models
        message_responses = []
        for message in messages:
            # Convert sources
            source_responses = [
                MessageSourceResponse.model_validate(source)
                for source in message.sources
            ]

            # Create message response
            message_dict = {
                "id": message.id,
                "session_id": message.session_id,
                "role": message.role,
                "content": message.content,
                "query_mode": message.query_mode,
                "confidence_score": message.confidence_score,
                "cache_hit": message.cache_hit,
                "created_at": message.created_at,
                "sources": source_responses,
            }
            message_responses.append(MessageResponse(**message_dict))

        logger.info(
            f"User {current_user.email} searched messages with query "
            f"'{search_request.query}' and found {len(messages)} results"
        )

        return SearchResponse(messages=message_responses, total=len(messages))

    except Exception as e:
        logger.error(f"Failed to search messages for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages",
        )
