"""
Conversation Service for Agent Builder

Handles conversation history and session management for chatflows.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversation history and sessions."""
    
    def __init__(self, db: Session):
        self.db = db
        # In-memory storage for now - should be replaced with proper database models
        self._conversations: Dict[str, List[Dict[str, Any]]] = {}
    
    async def get_conversation_history(
        self,
        session_id: str,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            limit: Maximum number of messages to return
            
        Returns:
            List of conversation messages
        """
        try:
            # Get from in-memory storage
            messages = self._conversations.get(session_id, [])
            
            # Filter by user_id and limit
            user_messages = [
                msg for msg in messages 
                if msg.get('user_id') == user_id
            ]
            
            return user_messages[-limit:] if limit > 0 else user_messages
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}", exc_info=True)
            return []
    
    async def add_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a message to conversation history.
        
        Args:
            session_id: Session ID
            user_id: User ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Created message
        """
        try:
            message = {
                'id': str(uuid.uuid4()),
                'session_id': session_id,
                'user_id': user_id,
                'role': role,
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow()
            }
            
            # Add to in-memory storage
            if session_id not in self._conversations:
                self._conversations[session_id] = []
            
            self._conversations[session_id].append(message)
            
            # Keep only last 100 messages per session
            if len(self._conversations[session_id]) > 100:
                self._conversations[session_id] = self._conversations[session_id][-100:]
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to add message: {e}", exc_info=True)
            raise
    
    async def clear_conversation_history(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            True if successful
        """
        try:
            if session_id in self._conversations:
                # Filter out messages for this user
                self._conversations[session_id] = [
                    msg for msg in self._conversations[session_id]
                    if msg.get('user_id') != user_id
                ]
                
                # Remove session if no messages left
                if not self._conversations[session_id]:
                    del self._conversations[session_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear conversation history: {e}", exc_info=True)
            return False
    
    async def get_session_info(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session ID
            user_id: User ID
            
        Returns:
            Session information or None
        """
        try:
            messages = await self.get_conversation_history(session_id, user_id)
            
            if not messages:
                return None
            
            return {
                'session_id': session_id,
                'user_id': user_id,
                'message_count': len(messages),
                'created_at': messages[0]['timestamp'] if messages else None,
                'last_activity': messages[-1]['timestamp'] if messages else None,
            }
            
        except Exception as e:
            logger.error(f"Failed to get session info: {e}", exc_info=True)
            return None
    
    def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of active sessions
        """
        try:
            sessions = []
            
            for session_id, messages in self._conversations.items():
                user_messages = [
                    msg for msg in messages 
                    if msg.get('user_id') == user_id
                ]
                
                if user_messages:
                    sessions.append({
                        'session_id': session_id,
                        'message_count': len(user_messages),
                        'created_at': user_messages[0]['timestamp'],
                        'last_activity': user_messages[-1]['timestamp'],
                    })
            
            # Sort by last activity
            sessions.sort(key=lambda x: x['last_activity'], reverse=True)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}", exc_info=True)
            return []