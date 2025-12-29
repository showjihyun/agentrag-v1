"""
Chat History Service

Provides persistent storage for chat conversations:
- Save/load chat messages
- Session management
- History search
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ChatMessage:
    """Chat message model."""
    
    def __init__(
        self,
        id: str,
        session_id: str,
        role: str,  # 'user', 'assistant', 'system'
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.session_id = session_id
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() + "Z",
        }


class ChatHistoryService:
    """
    Service for managing chat history persistence.
    """
    
    def __init__(self, db: Optional[Session] = None, redis_client=None):
        self.db = db
        self.redis = redis_client
        # In-memory fallback
        self._sessions: Dict[str, List[ChatMessage]] = {}
        self._session_metadata: Dict[str, dict] = {}
    
    def create_session(
        self,
        user_id: str,
        agent_id: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Create a new chat session."""
        session_id = str(uuid4())
        session_title = title or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        self._session_metadata[session_id] = {
            "id": session_id,
            "user_id": user_id,
            "agent_id": agent_id,
            "title": session_title,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "message_count": 0,
        }
        
        self._sessions[session_id] = []
        
        # Store in Redis for caching
        if self.redis:
            import json
            self.redis.hset(
                f"chat:sessions:{user_id}",
                session_id,
                json.dumps(self._session_metadata[session_id])
            )
        
        # Store in PostgreSQL for persistence using existing conversation models
        if self.db:
            try:
                from backend.db.models.conversation import Session as DBSession
                
                db_session = DBSession(
                    id=session_id,
                    user_id=user_id,
                    title=session_title,
                    # Note: conversation.Session doesn't have agent_id or metadata fields
                    # This is a simplified mapping to existing schema
                )
                self.db.add(db_session)
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to save session to DB: {e}")
                self.db.rollback()
        
        logger.info(f"Created chat session {session_id} for user {user_id}")
        return session_id
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> ChatMessage:
        """Add a message to a session."""
        message_id = str(uuid4())
        message = ChatMessage(
            id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata,
        )
        
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        
        self._sessions[session_id].append(message)
        
        # Update session metadata
        if session_id in self._session_metadata:
            self._session_metadata[session_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
            self._session_metadata[session_id]["message_count"] = len(self._sessions[session_id])
        
        # Store in Redis cache
        if self.redis:
            import json
            self.redis.rpush(
                f"chat:messages:{session_id}",
                json.dumps(message.to_dict())
            )
            self.redis.expire(f"chat:messages:{session_id}", 86400 * 30)  # 30 days
        
        # Store in PostgreSQL for persistence using existing conversation models
        if self.db:
            try:
                from backend.db.models.conversation import Message as DBMessage, Session as DBSession
                
                db_message = DBMessage(
                    id=message_id,
                    session_id=session_id,
                    role=role,
                    content=content,
                    # Note: conversation.Message has different schema than chat_history
                    # This is a simplified mapping
                )
                self.db.add(db_message)
                
                # Update session message count (if session exists)
                db_session = self.db.query(DBSession).filter(DBSession.id == session_id).first()
                if db_session:
                    # Note: conversation.Session doesn't have message_count field
                    # Just update the updated_at timestamp
                    db_session.updated_at = datetime.utcnow()
                
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to save message to DB: {e}")
                self.db.rollback()
        
        return message
    
    def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        before_id: Optional[str] = None,
    ) -> List[ChatMessage]:
        """Get messages from a session."""
        # Try Redis first
        if self.redis:
            try:
                import json
                messages_data = self.redis.lrange(f"chat:messages:{session_id}", 0, -1)
                messages = []
                for data in messages_data:
                    msg_dict = json.loads(data)
                    messages.append(ChatMessage(
                        id=msg_dict["id"],
                        session_id=msg_dict["session_id"],
                        role=msg_dict["role"],
                        content=msg_dict["content"],
                        metadata=msg_dict.get("metadata", {}),
                        created_at=datetime.fromisoformat(msg_dict["created_at"].replace("Z", "")),
                    ))
                
                if limit:
                    messages = messages[-limit:]
                
                return messages
            except Exception as e:
                logger.warning(f"Redis read failed, using memory: {e}")
        
        # Fallback to memory
        messages = self._sessions.get(session_id, [])
        
        if before_id:
            idx = next((i for i, m in enumerate(messages) if m.id == before_id), len(messages))
            messages = messages[:idx]
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session metadata."""
        return self._session_metadata.get(session_id)
    
    def list_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        """List user's chat sessions."""
        sessions = [
            meta for meta in self._session_metadata.values()
            if meta.get("user_id") == user_id
        ]
        
        # Sort by updated_at descending
        sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return sessions[offset:offset + limit]
    
    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session."""
        if session_id in self._session_metadata:
            if self._session_metadata[session_id].get("user_id") != user_id:
                return False
            
            del self._session_metadata[session_id]
            
            if session_id in self._sessions:
                del self._sessions[session_id]
            
            # Delete from Redis
            if self.redis:
                self.redis.delete(f"chat:messages:{session_id}")
                self.redis.hdel(f"chat:sessions:{user_id}", session_id)
            
            logger.info(f"Deleted chat session {session_id}")
            return True
        
        return False
    
    def clear_session(self, session_id: str) -> bool:
        """Clear all messages in a session."""
        if session_id in self._sessions:
            self._sessions[session_id] = []
            
            if session_id in self._session_metadata:
                self._session_metadata[session_id]["message_count"] = 0
                self._session_metadata[session_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Clear from Redis
            if self.redis:
                self.redis.delete(f"chat:messages:{session_id}")
            
            logger.info(f"Cleared chat session {session_id}")
            return True
        
        return False
    
    def search_messages(
        self,
        user_id: str,
        query: str,
        limit: int = 20,
    ) -> List[dict]:
        """Search messages across user's sessions."""
        results = []
        query_lower = query.lower()
        
        for session_id, messages in self._sessions.items():
            # Check if session belongs to user
            session_meta = self._session_metadata.get(session_id, {})
            if session_meta.get("user_id") != user_id:
                continue
            
            for message in messages:
                if query_lower in message.content.lower():
                    results.append({
                        "message": message.to_dict(),
                        "session": session_meta,
                    })
        
        # Sort by relevance (simple: exact match first)
        results.sort(key=lambda x: query_lower in x["message"]["content"].lower(), reverse=True)
        
        return results[:limit]
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Update session title."""
        if session_id in self._session_metadata:
            self._session_metadata[session_id]["title"] = title
            self._session_metadata[session_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
            return True
        return False


# Global instance
_chat_history_service: Optional[ChatHistoryService] = None


def get_chat_history_service() -> ChatHistoryService:
    """Get or create chat history service instance."""
    global _chat_history_service
    if _chat_history_service is None:
        try:
            from backend.core.dependencies import get_redis_client
            redis = get_redis_client()
            _chat_history_service = ChatHistoryService(redis_client=redis)
        except Exception:
            _chat_history_service = ChatHistoryService()
    return _chat_history_service
