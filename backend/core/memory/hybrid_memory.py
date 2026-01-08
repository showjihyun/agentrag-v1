"""Hybrid memory strategy - combines multiple memory strategies."""

from typing import List, Dict, Any, Set
from uuid import UUID
import logging

from backend.core.memory.base import BaseMemoryStrategy
from backend.core.memory.buffer_memory import BufferMemoryStrategy
from backend.core.memory.summary_memory import SummaryMemoryStrategy
from backend.core.memory.vector_memory import VectorMemoryStrategy
from backend.db.models.flows import ChatMessage

logger = logging.getLogger(__name__)

class HybridMemoryStrategy(BaseMemoryStrategy):
    """Hybrid memory strategy - intelligently combines buffer, summary, and vector strategies."""
    
    def __init__(self, session_id: UUID, config: Dict[str, Any], db_session):
        super().__init__(session_id, config)
        self.db_session = db_session
        
        # Get strategy weights
        weights = config.get('hybrid_weights', {
            'buffer': 0.4,
            'summary': 0.3,
            'vector': 0.3
        })
        
        self.buffer_weight = weights.get('buffer', 0.4)
        self.summary_weight = weights.get('summary', 0.3)
        self.vector_weight = weights.get('vector', 0.3)
        
        # Initialize sub-strategies
        self.buffer_strategy = BufferMemoryStrategy(
            session_id, 
            {
                'buffer_size': config.get('buffer_size', 10)
            }, 
            db_session
        )
        
        self.summary_strategy = SummaryMemoryStrategy(
            session_id,
            {
                'summary_threshold': config.get('summary_threshold', 30),
                'summary_interval': config.get('summary_interval', 15),
                'buffer_size': config.get('summary_buffer_size', 5)
            },
            db_session
        )
        
        self.vector_strategy = VectorMemoryStrategy(
            session_id,
            {
                'vector_top_k': config.get('vector_top_k', 3),
                'buffer_size': config.get('vector_buffer_size', 3)
            },
            db_session
        )
        
        # Configuration
        self.max_context_messages = config.get('max_context_messages', 20)
        self.enable_smart_selection = config.get('enable_smart_selection', True)
    
    async def get_context_messages(
        self,
        current_message: str,
        message_history: List[ChatMessage]
    ) -> List[Dict[str, str]]:
        """Get context using hybrid approach."""
        try:
            # Get messages from each strategy
            buffer_messages = []
            summary_messages = []
            vector_messages = []
            
            # 1. Buffer strategy (recent messages)
            if self.buffer_weight > 0:
                buffer_messages = await self.buffer_strategy.get_context_messages(
                    current_message, message_history
                )
            
            # 2. Summary strategy (summarized context)
            if self.summary_weight > 0:
                summary_messages = await self.summary_strategy.get_context_messages(
                    current_message, message_history
                )
            
            # 3. Vector strategy (semantically similar)
            if self.vector_weight > 0:
                vector_messages = await self.vector_strategy.get_context_messages(
                    current_message, message_history
                )
            
            # 4. Intelligent combination
            if self.enable_smart_selection:
                combined_messages = await self._smart_combine_messages(
                    current_message,
                    buffer_messages,
                    summary_messages,
                    vector_messages
                )
            else:
                combined_messages = await self._weighted_combine_messages(
                    buffer_messages,
                    summary_messages,
                    vector_messages
                )
            
            return combined_messages
            
        except Exception as e:
            logger.error(f"Hybrid memory retrieval failed: {e}")
            # Fallback to buffer strategy
            return await self.buffer_strategy.get_context_messages(
                current_message, message_history
            )
    
    async def _smart_combine_messages(
        self,
        current_message: str,
        buffer_messages: List[Dict[str, str]],
        summary_messages: List[Dict[str, str]],
        vector_messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Intelligently combine messages based on context and relevance."""
        combined = []
        seen_content = set()
        
        # Analyze current message to determine strategy priority
        message_lower = current_message.lower()
        
        # Determine if this is a follow-up question
        is_followup = any(word in message_lower for word in [
            '그것', '그거', '이것', '이거', '위에', '앞에', '전에', '방금', '아까',
            'that', 'this', 'above', 'previous', 'earlier', 'before',
            '1번', '2번', '3번', '첫번째', '두번째', '세번째',
            '더 자세히', '더 설명', '자세하게', 'more detail', 'explain more'
        ])
        
        # Determine if this is a new topic
        is_new_topic = any(word in message_lower for word in [
            '새로운', '다른', '바꿔서', '대신', '말고',
            'new', 'different', 'instead', 'change', 'switch'
        ])
        
        # Strategy selection based on message type
        if is_followup:
            # For follow-up questions, prioritize recent context and similar messages
            strategies = [
                (buffer_messages, 0.5),
                (vector_messages, 0.4),
                (summary_messages, 0.1)
            ]
        elif is_new_topic:
            # For new topics, prioritize semantic similarity and summaries
            strategies = [
                (vector_messages, 0.5),
                (summary_messages, 0.3),
                (buffer_messages, 0.2)
            ]
        else:
            # Default balanced approach
            strategies = [
                (buffer_messages, self.buffer_weight),
                (summary_messages, self.summary_weight),
                (vector_messages, self.vector_weight)
            ]
        
        # Sort strategies by weight
        strategies.sort(key=lambda x: x[1], reverse=True)
        
        # Add messages from each strategy
        for messages, weight in strategies:
            if weight <= 0:
                continue
                
            # Calculate how many messages to take from this strategy
            max_from_strategy = max(1, int(self.max_context_messages * weight))
            added_from_strategy = 0
            
            for msg in messages:
                if len(combined) >= self.max_context_messages:
                    break
                if added_from_strategy >= max_from_strategy:
                    break
                
                # Avoid duplicates based on content similarity
                content_key = self._normalize_content(msg['content'])
                if content_key not in seen_content:
                    combined.append(msg)
                    seen_content.add(content_key)
                    added_from_strategy += 1
        
        # Ensure chronological order for conversation flow
        return self._sort_messages_chronologically(combined)
    
    async def _weighted_combine_messages(
        self,
        buffer_messages: List[Dict[str, str]],
        summary_messages: List[Dict[str, str]],
        vector_messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Simple weighted combination of messages."""
        combined = []
        seen_content = set()
        
        # Calculate message counts for each strategy
        buffer_count = int(self.max_context_messages * self.buffer_weight)
        summary_count = int(self.max_context_messages * self.summary_weight)
        vector_count = int(self.max_context_messages * self.vector_weight)
        
        # Add messages from each strategy
        strategies = [
            (buffer_messages, buffer_count),
            (summary_messages, summary_count),
            (vector_messages, vector_count)
        ]
        
        for messages, count in strategies:
            added = 0
            for msg in messages:
                if len(combined) >= self.max_context_messages or added >= count:
                    break
                
                content_key = self._normalize_content(msg['content'])
                if content_key not in seen_content:
                    combined.append(msg)
                    seen_content.add(content_key)
                    added += 1
        
        return self._sort_messages_chronologically(combined)
    
    def _normalize_content(self, content: str) -> str:
        """Normalize content for duplicate detection."""
        return content.lower().strip()[:100]  # First 100 chars, normalized
    
    def _sort_messages_chronologically(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Sort messages chronologically if timestamp info is available."""
        # For now, maintain the order as provided
        # In a real implementation, you might want to sort by timestamp
        return messages
    
    async def add_message(self, message: ChatMessage) -> None:
        """Process message with all sub-strategies."""
        try:
            # Process with all enabled strategies
            tasks = []
            
            if self.buffer_weight > 0:
                tasks.append(self.buffer_strategy.add_message(message))
            
            if self.summary_weight > 0:
                tasks.append(self.summary_strategy.add_message(message))
            
            if self.vector_weight > 0:
                tasks.append(self.vector_strategy.add_message(message))
            
            # Execute all tasks
            import asyncio
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Hybrid memory add_message failed: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup all sub-strategies."""
        try:
            tasks = [
                self.buffer_strategy.cleanup(),
                self.summary_strategy.cleanup(),
                self.vector_strategy.cleanup()
            ]
            
            import asyncio
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Hybrid memory cleanup failed: {e}")