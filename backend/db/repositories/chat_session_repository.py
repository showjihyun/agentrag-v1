"""Repository for ChatSession operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func

from backend.db.models.flows import ChatSession, ChatMessage, ChatSummary
from backend.core.cache_decorators import cached_medium

class ChatSessionRepository:
    """Repository for ChatSession operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_session(
        self,
        chatflow_id: UUID,
        user_id: Optional[UUID] = None,
        memory_type: str = 'buffer',
        memory_config: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session."""
        session_token = f"{chatflow_id}:{user_id or 'anonymous'}:{datetime.utcnow().timestamp()}"
        
        session = ChatSession(
            chatflow_id=chatflow_id,
            user_id=user_id,
            session_token=session_token,
            title=title or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            memory_type=memory_type,
            memory_config=memory_config or {},
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    async def get_session(
        self,
        session_id: UUID,
        user_id: Optional[UUID] = None,
        include_messages: bool = False
    ) -> Optional[ChatSession]:
        """Get session by ID with optional user validation."""
        query = self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.status == 'active'
        )
        
        if user_id:
            query = query.filter(ChatSession.user_id == user_id)
        
        if include_messages:
            query = query.options(
                joinedload(ChatSession.messages)
            )
        
        return query.first()
    
    async def get_session_by_token(
        self,
        session_token: str,
        user_id: Optional[UUID] = None
    ) -> Optional[ChatSession]:
        """Get session by token."""
        query = self.db.query(ChatSession).filter(
            ChatSession.session_token == session_token,
            ChatSession.status == 'active'
        )
        
        if user_id:
            query = query.filter(ChatSession.user_id == user_id)
        
        return query.first()
    
    async def list_user_sessions(
        self,
        user_id: UUID,
        chatflow_id: Optional[UUID] = None,
        status: str = 'active',
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatSession]:
        """List user's chat sessions."""
        query = self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.status == status
        )
        
        if chatflow_id:
            query = query.filter(ChatSession.chatflow_id == chatflow_id)
        
        return query.order_by(desc(ChatSession.last_activity_at))\
                   .offset(offset)\
                   .limit(limit)\
                   .all()
    
    async def update_session_activity(
        self,
        session_id: UUID,
        message_count_delta: int = 1,
        tokens_used: int = 0,
        response_time: float = 0.0
    ) -> None:
        """Update session activity metrics."""
        session = await self.get_session(session_id)
        if not session:
            return
        
        session.message_count += message_count_delta
        session.total_tokens_used += tokens_used
        session.last_activity_at = datetime.utcnow()
        session.last_message_at = datetime.utcnow()
        
        # Update average response time
        if response_time > 0:
            current_avg = session.avg_response_time or 0.0
            total_responses = session.message_count // 2  # Assuming user-assistant pairs
            if total_responses > 0:
                session.avg_response_time = (
                    (current_avg * (total_responses - 1) + response_time) / total_responses
                )
        
        self.db.commit()
    
    async def archive_session(self, session_id: UUID) -> bool:
        """Archive a session."""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.status = 'archived'
        self.db.commit()
        return True
    
    async def delete_session(self, session_id: UUID, user_id: Optional[UUID] = None) -> bool:
        """Soft delete a session."""
        session = await self.get_session(session_id, user_id)
        if not session:
            return False
        
        session.status = 'deleted'
        self.db.commit()
        return True
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        expired_sessions = self.db.query(ChatSession).filter(
            ChatSession.expires_at < datetime.utcnow(),
            ChatSession.status == 'active'
        ).all()
        
        for session in expired_sessions:
            session.status = 'archived'
        
        self.db.commit()
        return len(expired_sessions)
    
    async def get_session_stats(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get session statistics."""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        return {
            'id': str(session.id),
            'title': session.title,
            'memory_type': session.memory_type,
            'message_count': session.message_count,
            'total_tokens_used': session.total_tokens_used,
            'avg_response_time': session.avg_response_time,
            'created_at': session.created_at.isoformat(),
            'last_activity_at': session.last_activity_at.isoformat() if session.last_activity_at else None,
            'status': session.status
        }
    
    # Phase 3: Additional methods for cleanup and statistics
    async def count_sessions(self) -> int:
        """Count total number of sessions."""
        return self.db.query(ChatSession).filter(
            ChatSession.status != 'deleted'
        ).count()
    
    async def count_active_sessions(self) -> int:
        """Count active sessions."""
        return self.db.query(ChatSession).filter(
            ChatSession.status == 'active'
        ).count()
    
    async def count_archived_sessions(self) -> int:
        """Count archived sessions."""
        return self.db.query(ChatSession).filter(
            ChatSession.status == 'archived'
        ).count()
    
    async def count_inactive_sessions(self, cutoff_date: datetime) -> int:
        """Count sessions inactive since cutoff date."""
        return self.db.query(ChatSession).filter(
            ChatSession.status == 'active',
            or_(
                ChatSession.last_activity_at < cutoff_date,
                and_(
                    ChatSession.last_activity_at.is_(None),
                    ChatSession.created_at < cutoff_date
                )
            )
        ).count()
    
    async def find_inactive_sessions(
        self,
        cutoff_date: datetime,
        limit: int = 1000
    ) -> List[ChatSession]:
        """Find sessions inactive since cutoff date."""
        return self.db.query(ChatSession).filter(
            ChatSession.status == 'active',
            or_(
                ChatSession.last_activity_at < cutoff_date,
                and_(
                    ChatSession.last_activity_at.is_(None),
                    ChatSession.created_at < cutoff_date
                )
            )
        ).limit(limit).all()
    
    async def update_session_status(
        self,
        session_id: UUID,
        status: str,
        archive_path: Optional[str] = None
    ) -> None:
        """Update session status."""
        session = await self.get_session(session_id)
        
        if session:
            session.status = status
            if archive_path is not None:
                session.archive_path = archive_path
            self.db.commit()
    
    async def update_session_metadata(
        self,
        session_id: UUID,
        metadata: Dict[str, Any]
    ) -> None:
        """Update session metadata."""
        session = await self.get_session(session_id)
        
        if session:
            if session.session_metadata is None:
                session.session_metadata = {}
            session.session_metadata.update(metadata)
            self.db.commit()