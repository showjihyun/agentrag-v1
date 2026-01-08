"""Base class for memory strategies."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.db.models.flows import ChatMessage

class BaseMemoryStrategy(ABC):
    """Base class for memory strategies."""
    
    def __init__(self, session_id: UUID, config: Dict[str, Any]):
        self.session_id = session_id
        self.config = config
    
    @abstractmethod
    async def get_context_messages(
        self,
        current_message: str,
        message_history: List[ChatMessage]
    ) -> List[Dict[str, str]]:
        """Get context messages for LLM input."""
        pass
    
    @abstractmethod
    async def add_message(
        self,
        message: ChatMessage
    ) -> None:
        """Process and store a new message."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Perform cleanup operations."""
        pass
    
    def _message_to_dict(self, message: ChatMessage) -> Dict[str, str]:
        """Convert ChatMessage to LLM format."""
        return {
            "role": message.role,
            "content": message.content
        }
    
    def _calculate_importance_score(self, message: ChatMessage) -> float:
        """Calculate importance score for a message."""
        content = message.content.lower()
        
        # Base score
        score = 0.5
        
        # Increase score for questions
        if '?' in content:
            score += 0.1
        
        # Increase score for decisions/conclusions
        decision_words = ['결정', '선택', '결론', '정리', '요약', 'decide', 'conclusion', 'summary']
        if any(word in content for word in decision_words):
            score += 0.2
        
        # Increase score for important topics
        important_words = ['중요', '핵심', '문제', '해결', 'important', 'key', 'problem', 'solution']
        if any(word in content for word in important_words):
            score += 0.15
        
        # Increase score for longer messages (more detailed)
        if len(content) > 200:
            score += 0.1
        
        # Cap at 1.0
        return min(score, 1.0)