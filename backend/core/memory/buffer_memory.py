"""Buffer memory strategy - keeps recent N messages."""

from typing import List, Dict, Any
from uuid import UUID

from backend.core.memory.base import BaseMemoryStrategy
from backend.db.models.flows import ChatMessage
from backend.db.repositories.chat_message_repository import ChatMessageRepository

class BufferMemoryStrategy(BaseMemoryStrategy):
    """Buffer memory strategy - keeps recent N messages."""
    
    def __init__(self, session_id: UUID, config: Dict[str, Any], db_session):
        super().__init__(session_id, config)
        self.buffer_size = config.get('buffer_size', 20)
        self.message_repo = ChatMessageRepository(db_session)
    
    async def get_context_messages(
        self,
        current_message: str,
        message_history: List[ChatMessage]
    ) -> List[Dict[str, str]]:
        """Get recent messages as context."""
        # Get recent messages from database
        recent_messages = await self.message_repo.get_recent_messages(
            self.session_id,
            count=self.buffer_size
        )
        
        # Convert to LLM format
        context_messages = []
        for message in recent_messages:
            if message.role in ['user', 'assistant', 'system']:
                context_messages.append(self._message_to_dict(message))
        
        return context_messages
    
    async def add_message(self, message: ChatMessage) -> None:
        """Process new message - calculate importance score."""
        # Calculate and update importance score
        importance_score = self._calculate_importance_score(message)
        
        metadata_updates = {
            'importance_score': importance_score,
            'processed_at': message.created_at.isoformat()
        }
        
        await self.message_repo.update_message_metadata(
            message.id,
            metadata_updates
        )
    
    async def cleanup(self) -> None:
        """No cleanup needed for buffer memory."""
        pass