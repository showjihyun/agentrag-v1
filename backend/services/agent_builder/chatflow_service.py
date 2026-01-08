"""Service for handling Chatflow LLM interactions with persistent memory."""

from typing import Dict, Any, Optional, AsyncGenerator, List
from uuid import UUID
import logging
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from backend.core.memory.memory_factory import MemoryStrategyFactory
from backend.db.repositories.chat_session_repository import ChatSessionRepository
from backend.db.repositories.chat_message_repository import ChatMessageRepository
from backend.services.llm_manager import LLMManager, LLMProvider
from backend.services.performance_monitor import PerformanceTracker

logger = logging.getLogger(__name__)

class ChatflowService:
    """Enhanced service for handling Chatflow LLM interactions with persistent memory."""
    
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = ChatSessionRepository(db)
        self.message_repo = ChatMessageRepository(db)
        self.memory_factory = MemoryStrategyFactory()
    
    async def chat(
        self,
        session_id: str,
        user_message: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a chat message with persistent memory management and context awareness.
        """
        memory_type = config.get('memory_type', 'buffer')
        
        with PerformanceTracker('chat_response', memory_type, session_id) as tracker:
            try:
                start_time = datetime.utcnow()
                
                # Get or create session
                session = await self._get_or_create_session(
                    session_id, user_id, workflow_id, config
                )
                
                # Get memory strategy
                with PerformanceTracker('memory_retrieval', memory_type, session_id):
                    memory_strategy = self.memory_factory.create_strategy(
                        session.memory_type,
                        session.id,
                        session.memory_config,
                        self.db
                    )
                
                # Get conversation history for context analysis
                message_history = await self.message_repo.get_session_messages(session.id)
                
                # Analyze message context and intent
                with PerformanceTracker('context_analysis', memory_type, session_id):
                    from backend.core.context.context_analyzer import ContextAnalyzer
                    context_analyzer = ContextAnalyzer()
                    
                    # Convert message history to format expected by analyzer
                    history_for_analysis = [
                        {
                            'role': msg.role,
                            'content': msg.content,
                            'created_at': msg.created_at.isoformat()
                        }
                        for msg in message_history
                    ]
                    
                    message_analysis = context_analyzer.analyze_message(
                        user_message, 
                        history_for_analysis
                    )
                
                # Add user message to database with analysis metadata
                user_msg = await self.message_repo.add_message(
                    session_id=session.id,
                    role="user",
                    content=user_message,
                    metadata={
                        'timestamp': datetime.utcnow().isoformat(),
                        'user_id': user_id,
                        'intent': message_analysis.intent.value,
                        'is_followup': message_analysis.is_followup,
                        'requires_context': message_analysis.requires_context,
                        'references': [
                            {
                                'type': ref.reference_type,
                                'text': ref.reference_text,
                                'target_index': ref.target_index,
                                'confidence': ref.confidence
                            }
                            for ref in message_analysis.references
                        ],
                        'keywords': message_analysis.keywords,
                        'confidence': message_analysis.confidence
                    }
                )
                
                # Get conversation context using memory strategy
                # Enhanced with context analysis
                with PerformanceTracker('memory_context_retrieval', memory_type, session_id):
                    context_messages = await memory_strategy.get_context_messages(
                        user_message, message_history
                    )
                
                # Enhance context based on message analysis
                if message_analysis.requires_context and message_analysis.references:
                    context_messages = await self._enhance_context_with_references(
                        context_messages, 
                        message_analysis, 
                        message_history
                    )
                
                # Add system prompt if configured
                system_prompt = config.get("system_prompt", "")
                
                # Enhance system prompt with context awareness
                if message_analysis.is_followup or message_analysis.requires_context:
                    context_prompt = self._build_context_aware_prompt(
                        system_prompt, 
                        message_analysis, 
                        user_message
                    )
                else:
                    context_prompt = system_prompt
                
                if context_prompt and (not context_messages or context_messages[0]["role"] != "system"):
                    context_messages.insert(0, {"role": "system", "content": context_prompt})
                
                # Generate LLM response
                with PerformanceTracker('llm_generation', memory_type, session_id):
                    response_content, tokens_used = await self._generate_llm_response(
                        context_messages, config
                    )
                
                # Calculate response time
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Add assistant message to database
                assistant_msg = await self.message_repo.add_message(
                    session_id=session.id,
                    role="assistant",
                    content=response_content,
                    metadata={
                        'timestamp': datetime.utcnow().isoformat(),
                        'tokens_used': tokens_used,
                        'response_time': response_time,
                        'model_used': config.get('model', ''),
                        'temperature': config.get('temperature', 0.7),
                        'context_enhanced': message_analysis.requires_context,
                        'responding_to_intent': message_analysis.intent.value
                    }
                )
                
                # Process message with memory strategy
                with PerformanceTracker('memory_processing', memory_type, session_id):
                    await memory_strategy.add_message(user_msg)
                    await memory_strategy.add_message(assistant_msg)
                
                # Update session activity
                await self.session_repo.update_session_activity(
                    session.id,
                    message_count_delta=2,  # user + assistant
                    tokens_used=tokens_used.get('total_tokens', 0),
                    response_time=response_time
                )
                
                # Add performance metadata to tracker
                tracker.metadata.update({
                    'tokens_used': tokens_used.get('total_tokens', 0),
                    'context_messages_count': len(context_messages),
                    'intent': message_analysis.intent.value,
                    'requires_context': message_analysis.requires_context
                })
                
                return {
                    "success": True,
                    "response": response_content,
                    "session_id": str(session.id),
                    "message_count": session.message_count + 2,
                    "usage": tokens_used,
                    "response_time": response_time,
                    "context_analysis": {
                        "intent": message_analysis.intent.value,
                        "is_followup": message_analysis.is_followup,
                        "requires_context": message_analysis.requires_context,
                        "references_found": len(message_analysis.references),
                        "confidence": message_analysis.confidence
                    }
                }
                
            except Exception as e:
                logger.error(f"Chat failed: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": str(e),
                    "session_id": session_id,
                }
    
    async def _get_or_create_session(
        self,
        session_token: str,
        user_id: Optional[str],
        workflow_id: Optional[str],
        config: Dict[str, Any]
    ):
        """Get existing session or create new one."""
        # Try to get existing session
        session = await self.session_repo.get_session_by_token(
            session_token,
            UUID(user_id) if user_id else None
        )
        
        if session:
            return session
        
        # Create new session
        memory_type = config.get('memory_type', 'buffer')
        memory_config = config.get('memory_config', {})
        
        return await self.session_repo.create_session(
            chatflow_id=UUID(workflow_id) if workflow_id else UUID('00000000-0000-0000-0000-000000000000'),
            user_id=UUID(user_id) if user_id else None,
            memory_type=memory_type,
            memory_config=memory_config
        )
    
    async def _generate_llm_response(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any]
    ) -> tuple[str, Dict[str, int]]:
        """Generate LLM response and return content + token usage."""
        provider = config.get("provider", "ollama")
        model = config.get("model", "llama3.3:70b")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 1000)
        api_key = config.get("api_key")
        
        llm_manager = LLMManager(
            provider=LLMProvider(provider),
            model=model,
            api_key=api_key,
        )
        
        response = await llm_manager.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        
        if isinstance(response, str):
            response_content = response
        elif hasattr(response, 'content'):
            response_content = response.content
        else:
            response_content = str(response)
        
        # Estimate tokens (rough estimation)
        input_tokens = sum(len(m["content"]) // 4 for m in messages)
        output_tokens = len(response_content) // 4
        
        return response_content, {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens
        }
    
    # Session management methods
    async def list_user_sessions(
        self,
        user_id: str,
        chatflow_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List user's chat sessions."""
        sessions = await self.session_repo.list_user_sessions(
            UUID(user_id),
            UUID(chatflow_id) if chatflow_id else None,
            limit=limit,
            offset=offset
        )
        
        return [
            {
                'id': str(session.id),
                'title': session.title,
                'memory_type': session.memory_type,
                'message_count': session.message_count,
                'created_at': session.created_at.isoformat(),
                'last_activity_at': session.last_activity_at.isoformat() if session.last_activity_at else None,
                'total_tokens_used': session.total_tokens_used
            }
            for session in sessions
        ]
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session."""
        from backend.utils.common import parse_uuid
        
        session_uuid = parse_uuid(session_id)
        user_uuid = parse_uuid(user_id)
        
        if not session_uuid:
            logger.error(f"Invalid UUID format for session_id: {session_id}")
            raise ValueError(f"Invalid session ID format: {session_id}")
        
        if not user_uuid:
            logger.error(f"Invalid UUID format for user_id: {user_id}")
            raise ValueError(f"Invalid user ID format: {user_id}")
        
        return await self.session_repo.delete_session(session_uuid, user_uuid)
    
    async def get_session_history(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get session history with messages."""
        try:
            from backend.utils.common import parse_uuid
            
            # Validate UUIDs
            session_uuid = parse_uuid(session_id)
            user_uuid = parse_uuid(user_id)
            
            if not session_uuid:
                logger.error(f"Invalid UUID format for session_id: {session_id}")
                raise ValueError(f"Invalid session ID format: {session_id}")
            
            if not user_uuid:
                logger.error(f"Invalid UUID format for user_id: {user_id}")
                raise ValueError(f"Invalid user ID format: {user_id}")
            
            # Get session details
            session = await self.session_repo.get_session(session_uuid, user_uuid)
            if not session:
                return None
            
            # Get session messages
            messages = await self.message_repo.get_session_messages(session.id)
            
            return {
                "success": True,
                "session": {
                    "id": str(session.id),
                    "chatflow_id": str(session.chatflow_id),
                    "title": session.title,
                    "memory_type": session.memory_type,
                    "memory_config": session.memory_config,
                    "status": session.status,
                    "message_count": session.message_count,
                    "created_at": session.created_at.isoformat(),
                    "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None,
                },
                "messages": [
                    {
                        "id": str(msg.id),
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                        "message_metadata": msg.message_metadata
                    }
                    for msg in messages
                ],
                "message_count": len(messages)
            }
        except Exception as e:
            logger.error(f"Failed to get session history: {e}", exc_info=True)
            return None
    
    async def export_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Export session data."""
        from backend.utils.common import parse_uuid
        
        session_uuid = parse_uuid(session_id)
        user_uuid = parse_uuid(user_id)
        
        if not session_uuid:
            logger.error(f"Invalid UUID format for session_id: {session_id}")
            raise ValueError(f"Invalid session ID format: {session_id}")
        
        if not user_uuid:
            logger.error(f"Invalid UUID format for user_id: {user_id}")
            raise ValueError(f"Invalid user ID format: {user_id}")
        
        session = await self.session_repo.get_session(
            session_uuid,
            user_uuid,
            include_messages=True
        )
        
        if not session:
            return None
        
        messages = await self.message_repo.get_session_messages(session.id)
        
        return {
            'session': {
                'id': str(session.id),
                'title': session.title,
                'memory_type': session.memory_type,
                'created_at': session.created_at.isoformat(),
                'message_count': session.message_count,
                'total_tokens_used': session.total_tokens_used
            },
            'messages': [
                {
                    'id': str(msg.id),
                    'role': msg.role,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat(),
                    'metadata': msg.message_metadata
                }
                for msg in messages
            ]
        }
    
    async def chat_stream(
        self,
        session_id: str,
        user_message: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Process a chat message with streaming response and persistent memory.
        """
        try:
            start_time = datetime.utcnow()
            
            # Get or create session
            session = await self._get_or_create_session(
                session_id, user_id, workflow_id, config
            )
            
            # Get memory strategy
            memory_strategy = self.memory_factory.create_strategy(
                session.memory_type,
                session.id,
                session.memory_config,
                self.db
            )
            
            # Add user message to database
            user_msg = await self.message_repo.add_message(
                session_id=session.id,
                role="user",
                content=user_message,
                metadata={
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_id': user_id
                }
            )
            
            # Get conversation context using memory strategy
            message_history = await self.message_repo.get_session_messages(session.id)
            context_messages = await memory_strategy.get_context_messages(
                user_message, message_history
            )
            
            # Add system prompt if configured
            system_prompt = config.get("system_prompt", "")
            if system_prompt and (not context_messages or context_messages[0]["role"] != "system"):
                context_messages.insert(0, {"role": "system", "content": system_prompt})
            
            # Generate streaming LLM response
            provider = config.get("provider", "ollama")
            model = config.get("model", "llama3.1:8b")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 1000)
            api_key = config.get("api_key")
            
            llm_manager = LLMManager(
                provider=LLMProvider(provider),
                model=model,
                api_key=api_key,
            )
            
            # Stream response
            full_response = ""
            stream_generator = await llm_manager.generate(
                messages=context_messages,
                stream=True,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            async for chunk in stream_generator:
                if chunk:
                    full_response += chunk
                    yield chunk
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Estimate tokens
            input_tokens = sum(len(m["content"]) // 4 for m in context_messages)
            output_tokens = len(full_response) // 4
            tokens_used = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens
            }
            
            # Add assistant message to database
            assistant_msg = await self.message_repo.add_message(
                session_id=session.id,
                role="assistant",
                content=full_response,
                metadata={
                    'timestamp': datetime.utcnow().isoformat(),
                    'tokens_used': tokens_used,
                    'response_time': response_time,
                    'model_used': model,
                    'temperature': temperature
                }
            )
            
            # Process messages with memory strategy
            await memory_strategy.add_message(user_msg)
            await memory_strategy.add_message(assistant_msg)
            
            # Update session activity
            await self.session_repo.update_session_activity(
                session.id,
                message_count_delta=2,
                tokens_used=tokens_used.get('total_tokens', 0),
                response_time=response_time
            )
            
        except Exception as e:
            logger.error(f"Chat stream failed: {e}", exc_info=True)
            yield f"data: {{'error': '{str(e)}'}}\n\n"
    async def _enhance_context_with_references(
        self,
        context_messages: List[Dict[str, str]],
        message_analysis,
        message_history: List
    ) -> List[Dict[str, str]]:
        """Enhance context messages based on specific references found."""
        enhanced_messages = context_messages.copy()
        
        for reference in message_analysis.references:
            if reference.target_index is not None and reference.confidence > 0.5:
                # Find the referenced message
                if 0 <= reference.target_index < len(message_history):
                    referenced_msg = message_history[reference.target_index]
                    
                    # Add a context note about the reference
                    context_note = {
                        "role": "system",
                        "content": f"사용자가 다음 메시지를 참조하고 있습니다 ({reference.reference_text}): \"{referenced_msg.content}\""
                    }
                    
                    # Insert context note before the last user message
                    enhanced_messages.insert(-1, context_note)
        
        return enhanced_messages
    
    def _build_context_aware_prompt(
        self,
        base_prompt: str,
        message_analysis,
        user_message: str
    ) -> str:
        """Build a context-aware system prompt."""
        context_additions = []
        
        if message_analysis.intent.value == 'elaboration':
            context_additions.append(
                "사용자가 이전 답변에 대한 더 자세한 설명을 요청하고 있습니다. "
                "구체적인 예시, 단계별 설명, 또는 추가 세부사항을 제공해주세요."
            )
        
        elif message_analysis.intent.value == 'clarification':
            context_additions.append(
                "사용자가 이전 답변에 대한 명확한 설명을 요청하고 있습니다. "
                "더 쉽고 이해하기 쉬운 방식으로 다시 설명해주세요."
            )
        
        elif message_analysis.intent.value == 'reference':
            context_additions.append(
                "사용자가 이전 대화의 특정 부분을 참조하고 있습니다. "
                "해당 컨텍스트를 고려하여 연관성 있는 답변을 제공해주세요."
            )
        
        elif message_analysis.is_followup:
            context_additions.append(
                "이것은 이전 대화의 연속입니다. "
                "이전 컨텍스트를 고려하여 일관성 있는 답변을 제공해주세요."
            )
        
        if context_additions:
            enhanced_prompt = base_prompt + "\n\n" + " ".join(context_additions)
            return enhanced_prompt
        
        return base_prompt