"""Summary memory strategy - summarizes old conversations."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from backend.core.memory.base import BaseMemoryStrategy
from backend.db.models.flows import ChatMessage, ChatSummary
from backend.db.repositories.chat_message_repository import ChatMessageRepository
from backend.services.llm_manager import LLMManager, LLMProvider

class SummaryMemoryStrategy(BaseMemoryStrategy):
    """Summary memory strategy - summarizes old conversations."""
    
    def __init__(self, session_id: UUID, config: Dict[str, Any], db_session):
        super().__init__(session_id, config)
        self.summary_threshold = config.get('summary_threshold', 50)
        self.summary_interval = config.get('summary_interval', 20)
        self.buffer_size = config.get('buffer_size', 10)
        self.db_session = db_session
        self.message_repo = ChatMessageRepository(db_session)
    
    async def get_context_messages(
        self,
        current_message: str,
        message_history: List[ChatMessage]
    ) -> List[Dict[str, str]]:
        """Get context with summary + recent messages."""
        context_messages = []
        
        # 1. Add latest summary if exists
        latest_summary = self._get_latest_summary()
        if latest_summary:
            context_messages.append({
                "role": "system",
                "content": f"이전 대화 요약: {latest_summary.summary_text}"
            })
        
        # 2. Add recent messages
        recent_messages = await self.message_repo.get_recent_messages(
            self.session_id,
            count=self.buffer_size
        )
        
        for message in recent_messages:
            if message.role in ['user', 'assistant']:
                context_messages.append(self._message_to_dict(message))
        
        return context_messages
    
    async def add_message(self, message: ChatMessage) -> None:
        """Process new message and check if summarization is needed."""
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
        
        # Check if we need to create a summary
        unsummarized_count = len(await self.message_repo.get_unsummarized_messages(
            self.session_id
        ))
        
        if unsummarized_count >= self.summary_threshold:
            await self._create_summary()
    
    async def _create_summary(self) -> None:
        """Create a summary of unsummarized messages."""
        unsummarized_messages = await self.message_repo.get_unsummarized_messages(
            self.session_id,
            limit=self.summary_interval
        )
        
        if len(unsummarized_messages) < 5:  # Need minimum messages to summarize
            return
        
        # Prepare messages for summarization
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in unsummarized_messages
            if msg.role in ['user', 'assistant']
        ])
        
        # Create summary using LLM
        try:
            llm_manager = LLMManager(
                provider=LLMProvider.OLLAMA,
                model="llama3.3:70b"
            )
            
            summary_prompt = f"""다음 대화를 간결하게 요약해주세요. 주요 주제, 결정사항, 중요한 정보를 포함해주세요:

{conversation_text}

요약:"""
            
            summary_text = await llm_manager.generate(
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            if isinstance(summary_text, str):
                summary_content = summary_text
            elif hasattr(summary_text, 'content'):
                summary_content = summary_text.content
            else:
                summary_content = str(summary_text)
            
            # Save summary to database
            summary = ChatSummary(
                session_id=self.session_id,
                summary_text=summary_content,
                start_message_id=unsummarized_messages[0].id,
                end_message_id=unsummarized_messages[-1].id,
                message_count=len(unsummarized_messages)
            )
            
            self.db_session.add(summary)
            
            # Mark messages as summarized
            message_ids = [msg.id for msg in unsummarized_messages]
            await self.message_repo.mark_messages_summarized(message_ids)
            
            self.db_session.commit()
            
        except Exception as e:
            # Log error but don't fail the conversation
            print(f"Summary creation failed: {e}")
    
    def _get_latest_summary(self) -> Optional[ChatSummary]:
        """Get the latest summary for this session."""
        return self.db_session.query(ChatSummary)\
                             .filter(ChatSummary.session_id == self.session_id)\
                             .order_by(ChatSummary.created_at.desc())\
                             .first()
    
    async def cleanup(self) -> None:
        """Create final summary if needed."""
        await self._create_summary()