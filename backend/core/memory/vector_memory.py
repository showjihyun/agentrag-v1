"""Vector memory strategy - semantic similarity based message retrieval."""

from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
import json

from backend.core.memory.base import BaseMemoryStrategy
from backend.db.models.flows import ChatMessage
from backend.db.repositories.chat_message_repository import ChatMessageRepository

logger = logging.getLogger(__name__)

class VectorMemoryStrategy(BaseMemoryStrategy):
    """Vector memory strategy - uses semantic similarity to retrieve relevant messages."""
    
    def __init__(self, session_id: UUID, config: Dict[str, Any], db_session):
        super().__init__(session_id, config)
        self.vector_top_k = config.get('vector_top_k', 5)
        self.buffer_size = config.get('buffer_size', 5)  # Keep some recent messages too
        self.db_session = db_session
        self.message_repo = ChatMessageRepository(db_session)
        
        # Initialize embedding service
        self.embedding_service = None
        try:
            from backend.services.embedding_service import get_embedding_service
            self.embedding_service = get_embedding_service()
        except ImportError:
            logger.warning("EmbeddingService not available, falling back to buffer memory")
    
    async def get_context_messages(
        self,
        current_message: str,
        message_history: List[ChatMessage]
    ) -> List[Dict[str, str]]:
        """Get context with semantic similarity + recent messages."""
        context_messages = []
        
        if not self.embedding_service:
            # Fallback to buffer memory if embedding service is not available
            recent_messages = await self.message_repo.get_recent_messages(
                self.session_id,
                count=self.buffer_size * 2
            )
            
            for message in recent_messages:
                if message.role in ['user', 'assistant', 'system']:
                    context_messages.append(self._message_to_dict(message))
            
            return context_messages
        
        try:
            # 1. Get recent messages (always include for continuity)
            recent_messages = await self.message_repo.get_recent_messages(
                self.session_id,
                count=self.buffer_size
            )
            
            # 2. Get semantically similar messages
            similar_messages = await self._get_similar_messages(current_message)
            
            # 3. Combine and deduplicate
            all_messages = {}
            
            # Add recent messages first (higher priority)
            for msg in recent_messages:
                if msg.role in ['user', 'assistant']:
                    all_messages[str(msg.id)] = msg
            
            # Add similar messages (if not already included)
            for msg in similar_messages:
                if str(msg.id) not in all_messages and msg.role in ['user', 'assistant']:
                    all_messages[str(msg.id)] = msg
            
            # 4. Sort by creation time and convert to LLM format
            sorted_messages = sorted(all_messages.values(), key=lambda x: x.created_at)
            
            for message in sorted_messages:
                context_messages.append(self._message_to_dict(message))
            
            # Limit total context size
            max_context = self.vector_top_k + self.buffer_size
            if len(context_messages) > max_context:
                # Keep most recent messages
                context_messages = context_messages[-max_context:]
            
            return context_messages
            
        except Exception as e:
            logger.error(f"Vector memory retrieval failed: {e}")
            # Fallback to recent messages
            recent_messages = await self.message_repo.get_recent_messages(
                self.session_id,
                count=self.buffer_size * 2
            )
            
            for message in recent_messages:
                if message.role in ['user', 'assistant']:
                    context_messages.append(self._message_to_dict(message))
            
            return context_messages
    
    async def add_message(self, message: ChatMessage) -> None:
        """Process new message and create embedding."""
        # Calculate and update importance score
        importance_score = self._calculate_importance_score(message)
        
        # Create embedding for the message
        embedding_id = None
        if self.embedding_service and message.role in ['user', 'assistant']:
            try:
                embedding_id = await self._create_message_embedding(message)
            except Exception as e:
                logger.error(f"Failed to create embedding for message {message.id}: {e}")
        
        metadata_updates = {
            'importance_score': importance_score,
            'processed_at': message.created_at.isoformat(),
            'embedding_created': embedding_id is not None
        }
        
        await self.message_repo.update_message_metadata(
            message.id,
            metadata_updates
        )
        
        # Update message with embedding ID
        if embedding_id:
            message.embedding_id = embedding_id
            self.db_session.commit()
    
    async def _get_similar_messages(self, query_text: str) -> List[ChatMessage]:
        """Get semantically similar messages using vector search."""
        if not self.embedding_service:
            return []
        
        try:
            # Create embedding for query
            query_embedding = await self.embedding_service.create_embedding(query_text)
            
            # Search for similar messages in Milvus
            similar_embedding_ids = await self.embedding_service.search_similar(
                query_embedding,
                collection_name=f"chat_session_{self.session_id}",
                top_k=self.vector_top_k
            )
            
            if not similar_embedding_ids:
                return []
            
            # Get messages by embedding IDs
            messages = []
            for embedding_id, score in similar_embedding_ids:
                message = await self.message_repo.get_message_by_embedding_id(embedding_id)
                if message and score > 0.7:  # Similarity threshold
                    messages.append(message)
            
            return messages
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def _create_message_embedding(self, message: ChatMessage) -> Optional[str]:
        """Create and store embedding for a message."""
        if not self.embedding_service:
            return None
        
        try:
            # Create embedding
            embedding = await self.embedding_service.create_embedding(message.content)
            
            # Store in Milvus
            embedding_id = await self.embedding_service.store_embedding(
                embedding,
                collection_name=f"chat_session_{self.session_id}",
                metadata={
                    'message_id': str(message.id),
                    'session_id': str(self.session_id),
                    'role': message.role,
                    'created_at': message.created_at.isoformat(),
                    'importance_score': message.message_metadata.get('importance_score', 0.5)
                }
            )
            
            return embedding_id
            
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            return None
    
    async def cleanup(self) -> None:
        """Cleanup vector data if needed."""
        if self.embedding_service:
            try:
                # Optionally cleanup old embeddings
                await self.embedding_service.cleanup_collection(
                    f"chat_session_{self.session_id}"
                )
            except Exception as e:
                logger.error(f"Vector cleanup failed: {e}")