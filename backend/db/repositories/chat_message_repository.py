"""Repository for ChatMessage operations."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func

from backend.db.models.flows import ChatMessage, ChatSummary, ChatSession

class ChatMessageRepository:
    """Repository for ChatMessage operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding_id: Optional[str] = None
    ) -> ChatMessage:
        """Add a new message to session."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_metadata=metadata or {},
            embedding_id=embedding_id
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    async def get_session_messages(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
        offset: int = 0,
        include_system: bool = True
    ) -> List[ChatMessage]:
        """Get messages for a session."""
        query = self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        )
        
        if not include_system:
            query = query.filter(ChatMessage.role != 'system')
        
        query = query.order_by(asc(ChatMessage.created_at))
        
        if offset > 0:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    async def get_recent_messages(
        self,
        session_id: UUID,
        count: int = 20
    ) -> List[ChatMessage]:
        """Get recent messages (for buffer memory)."""
        messages = self.db.query(ChatMessage)\
                          .filter(ChatMessage.session_id == session_id)\
                          .order_by(desc(ChatMessage.created_at))\
                          .limit(count)\
                          .all()
        return messages[::-1]  # Reverse to chronological order
    
    async def get_important_messages(
        self,
        session_id: UUID,
        min_importance: float = 0.7,
        limit: int = 10
    ) -> List[ChatMessage]:
        """Get important messages based on importance score."""
        return self.db.query(ChatMessage)\
                      .filter(
                          ChatMessage.session_id == session_id,
                          ChatMessage.message_metadata['importance_score'].astext.cast(float) >= min_importance
                      )\
                      .order_by(desc(ChatMessage.message_metadata['importance_score'].astext.cast(float)))\
                      .limit(limit)\
                      .all()
    
    async def mark_messages_summarized(
        self,
        message_ids: List[UUID]
    ) -> None:
        """Mark messages as summarized."""
        self.db.query(ChatMessage)\
               .filter(ChatMessage.id.in_(message_ids))\
               .update({'is_summarized': True}, synchronize_session=False)
        self.db.commit()
    
    async def get_unsummarized_messages(
        self,
        session_id: UUID,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get messages that haven't been summarized yet."""
        query = self.db.query(ChatMessage)\
                       .filter(
                           ChatMessage.session_id == session_id,
                           ChatMessage.is_summarized == False,
                           ChatMessage.role.in_(['user', 'assistant'])
                       )\
                       .order_by(asc(ChatMessage.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    async def get_message_by_id(
        self,
        message_id: UUID,
        session_id: Optional[UUID] = None
    ) -> Optional[ChatMessage]:
        """Get a specific message by ID."""
        query = self.db.query(ChatMessage).filter(ChatMessage.id == message_id)
        
        if session_id:
            query = query.filter(ChatMessage.session_id == session_id)
        
        return query.first()
    
    async def update_message_metadata(
        self,
        message_id: UUID,
        metadata_updates: Dict[str, Any]
    ) -> bool:
        """Update message metadata."""
        message = await self.get_message_by_id(message_id)
        if not message:
            return False
        
        # Merge with existing metadata
        current_metadata = message.message_metadata or {}
        current_metadata.update(metadata_updates)
        message.message_metadata = current_metadata
        
        self.db.commit()
        return True
    
    async def delete_message(self, message_id: UUID) -> bool:
        """Delete a message."""
        message = await self.get_message_by_id(message_id)
        if not message:
            return False
        
        self.db.delete(message)
        self.db.commit()
        return True
    
    async def get_session_message_count(self, session_id: UUID) -> int:
        """Get total message count for a session."""
        return self.db.query(func.count(ChatMessage.id))\
                      .filter(ChatMessage.session_id == session_id)\
                      .scalar()
    
    async def get_message_by_embedding_id(
        self,
        embedding_id: str
    ) -> Optional[ChatMessage]:
        """Get message by embedding ID."""
        return self.db.query(ChatMessage)\
                      .filter(ChatMessage.embedding_id == embedding_id)\
                      .first()
    
    async def search_messages_by_content(
        self,
        session_id: UUID,
        search_term: str,
        limit: int = 10
    ) -> List[ChatMessage]:
        """Search messages by content."""
        return self.db.query(ChatMessage)\
                      .filter(
                          ChatMessage.session_id == session_id,
                          ChatMessage.content.ilike(f'%{search_term}%')
                      )\
                      .order_by(desc(ChatMessage.created_at))\
                      .limit(limit)\
                      .all()
    
    async def get_messages_by_intent(
        self,
        session_id: UUID,
        intent: str,
        limit: int = 10
    ) -> List[ChatMessage]:
        """Get messages by intent type."""
        return self.db.query(ChatMessage)\
                      .filter(
                          ChatMessage.session_id == session_id,
                          ChatMessage.message_metadata['intent'].astext == intent
                      )\
                      .order_by(desc(ChatMessage.created_at))\
                      .limit(limit)\
                      .all()
    
    async def get_referenced_messages(
        self,
        session_id: UUID,
        limit: int = 10
    ) -> List[ChatMessage]:
        """Get messages that have been referenced by other messages."""
        return self.db.query(ChatMessage)\
                      .filter(
                          ChatMessage.session_id == session_id,
                          ChatMessage.message_metadata.has_key('references'),
                          ChatMessage.message_metadata['references'] != '[]'
                      )\
                      .order_by(desc(ChatMessage.created_at))\
                      .limit(limit)\
                      .all()
    
    # Phase 3: Additional methods for cleanup and export
    async def count_all_messages(self) -> int:
        """Count total number of messages."""
        return self.db.query(ChatMessage).count()
    
    async def get_session_summaries(self, session_id: UUID) -> List[ChatSummary]:
        """Get summaries for a session."""
        return self.db.query(ChatSummary).filter(
            ChatSummary.session_id == session_id
        ).order_by(ChatSummary.created_at).all()
    
    async def add_summary(
        self,
        session_id: UUID,
        summary_text: str,
        message_range_start: int,
        message_range_end: int
    ) -> ChatSummary:
        """Add a summary for a session."""
        summary = ChatSummary(
            session_id=session_id,
            summary_text=summary_text,
            message_range_start=message_range_start,
            message_range_end=message_range_end
        )
        
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary
    
    async def delete_session_messages(
        self,
        session_id: UUID,
        keep_summaries: bool = True
    ) -> None:
        """Delete all messages for a session."""
        self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete()
        
        if not keep_summaries:
            self.db.query(ChatSummary).filter(
                ChatSummary.session_id == session_id
            ).delete()
        
        self.db.commit()
    
    async def create_message_from_archive(
        self,
        session_id: UUID,
        message_data: Dict[str, Any]
    ) -> ChatMessage:
        """Create message from archive data."""
        message = ChatMessage(
            session_id=session_id,
            role=message_data['role'],
            content=message_data['content'],
            message_metadata=message_data.get('metadata', {}),
            created_at=datetime.fromisoformat(message_data['created_at']) if 'created_at' in message_data else datetime.utcnow()
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    async def get_message_by_embedding_id(self, embedding_id: str) -> Optional[ChatMessage]:
        """Get message by embedding ID."""
        return self.db.query(ChatMessage).filter(
            ChatMessage.embedding_id == embedding_id
        ).first()
    
    async def delete_message(self, message_id: UUID) -> bool:
        """Delete a specific message."""
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()
        
        if message:
            self.db.delete(message)
            self.db.commit()
            return True
        
        return False