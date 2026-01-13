"""
Chatflow Service

Provides LLM chat functionality for Chatflows with conversation history,
streaming responses, and token usage tracking.
"""

import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from backend.db.models.flows import TokenUsage
from backend.services.llm_manager import LLMManager, LLMProvider

logger = logging.getLogger(__name__)


class ChatMessage:
    """Represents a chat message."""
    
    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            metadata=data.get("metadata", {}),
        )


class ConversationHistory:
    """Manages conversation history for a chat session."""
    
    def __init__(self, max_messages: int = 50, max_tokens: int = 4000):
        self.messages: List[ChatMessage] = []
        self.max_messages = max_messages
        self.max_tokens = max_tokens
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the history."""
        message = ChatMessage(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        
        # Trim if exceeds max messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Get messages formatted for LLM API."""
        return [{"role": m.role, "content": m.content} for m in self.messages]
    
    def clear(self):
        """Clear conversation history."""
        self.messages = []
    
    def to_dict(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self.messages]
    
    @classmethod
    def from_dict(cls, data: List[Dict[str, Any]], max_messages: int = 50) -> "ConversationHistory":
        history = cls(max_messages=max_messages)
        for msg_data in data:
            history.messages.append(ChatMessage.from_dict(msg_data))
        return history


class ChatflowService:
    """Service for handling Chatflow LLM interactions."""
    
    # In-memory session storage (should be Redis in production)
    _sessions: Dict[str, ConversationHistory] = {}
    
    def __init__(self, db: Session):
        self.db = db
    
    async def chat(
        self,
        session_id: str,
        user_message: str,
        config: Dict[str, Any],
        user_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a chat message and return the response.
        
        Args:
            session_id: Unique session identifier
            user_message: User's message
            config: Chatflow configuration (provider, model, system_prompt, etc.)
            user_id: User ID for tracking
            workflow_id: Workflow ID for tracking
            
        Returns:
            Response with assistant message and metadata
        """
        try:
            # Get or create conversation history
            history = self._get_or_create_session(session_id)
            
            # Add system prompt if not already present
            system_prompt = config.get("system_prompt", "")
            if system_prompt and (not history.messages or history.messages[0].role != "system"):
                history.messages.insert(0, ChatMessage(role="system", content=system_prompt))
            
            # Add user message
            history.add_message("user", user_message)
            
            # Get LLM configuration
            provider = config.get("provider", "ollama")
            model = config.get("model", "llama3.3:70b")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 1000)
            
            # Initialize LLM manager
            api_key = config.get("api_key")
            llm_manager = LLMManager(
                provider=LLMProvider(provider),
                model=model,
                api_key=api_key,
            )
            
            # Get messages for LLM
            messages = history.get_messages_for_llm()
            
            # Generate response
            response_content = ""
            input_tokens = 0
            output_tokens = 0
            
            try:
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
                
            except Exception as e:
                logger.error(f"LLM generation failed: {e}", exc_info=True)
                raise
            
            # Add assistant response to history
            history.add_message("assistant", response_content)
            
            # Record token usage
            if user_id:
                await self._record_token_usage(
                    user_id=user_id,
                    workflow_id=workflow_id,
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            
            return {
                "success": True,
                "response": response_content,
                "session_id": session_id,
                "message_count": len(history.messages),
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                },
            }
            
        except Exception as e:
            logger.error(f"Chat failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "session_id": session_id,
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
        Process a chat message and stream the response.
        
        Yields:
            SSE formatted chunks
        """
        try:
            # Get or create conversation history
            history = self._get_or_create_session(session_id)
            
            # Add system prompt if not already present
            system_prompt = config.get("system_prompt", "")
            if system_prompt and (not history.messages or history.messages[0].role != "system"):
                history.messages.insert(0, ChatMessage(role="system", content=system_prompt))
            
            # Add user message
            history.add_message("user", user_message)
            
            # Get LLM configuration
            provider = config.get("provider", "ollama")
            model = config.get("model", "llama3.3:70b")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 1000)
            
            # Initialize LLM manager
            api_key = config.get("api_key")
            llm_manager = LLMManager(
                provider=LLMProvider(provider),
                model=model,
                api_key=api_key,
            )
            
            # Get messages for LLM
            messages = history.get_messages_for_llm()
            
            # Stream response
            accumulated_content = ""
            input_tokens = sum(len(m["content"]) // 4 for m in messages)
            
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"
            
            try:
                response_stream = await llm_manager.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                
                async for chunk in response_stream:
                    if chunk:
                        accumulated_content += chunk
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                        await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"LLM streaming failed: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                return
            
            # Add assistant response to history
            history.add_message("assistant", accumulated_content)
            
            # Calculate output tokens
            output_tokens = len(accumulated_content) // 4
            
            # Record token usage
            if user_id:
                await self._record_token_usage(
                    user_id=user_id,
                    workflow_id=workflow_id,
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            
            # Send completion
            yield f"data: {json.dumps({'type': 'done', 'usage': {'input_tokens': input_tokens, 'output_tokens': output_tokens}})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Chat stream failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        history = self._sessions.get(session_id)
        if history:
            return history.to_dict()
        return []
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a chat session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def _get_or_create_session(self, session_id: str) -> ConversationHistory:
        """Get or create a conversation history for a session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationHistory()
        return self._sessions[session_id]
    
    async def execute_streaming(
        self,
        chatflow_id: str,
        message: str,
        session_id: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute chatflow with streaming response for SSE integration.
        
        Args:
            chatflow_id: Chatflow ID
            message: User message
            session_id: Session ID
            user_id: User ID
            context: Optional context data
            
        Yields:
            Dict with streaming events (type, content, etc.)
        """
        try:
            # Get chatflow configuration (mock for now)
            config = {
                "provider": "ollama",
                "model": "llama3.3:70b",
                "temperature": 0.7,
                "max_tokens": 1000,
                "system_prompt": "You are a helpful AI assistant."
            }
            
            # Get or create conversation history
            history = self._get_or_create_session(session_id)
            
            # Add system prompt if not already present
            system_prompt = config.get("system_prompt", "")
            if system_prompt and (not history.messages or history.messages[0].role != "system"):
                history.messages.insert(0, ChatMessage(role="system", content=system_prompt))
            
            # Add user message
            history.add_message("user", message)
            
            # Yield thinking event
            yield {
                "type": "thinking",
                "step": "processing",
                "description": "AI가 응답을 준비하고 있습니다..."
            }
            
            # Get LLM configuration
            provider = config.get("provider", "ollama")
            model = config.get("model", "llama3.3:70b")
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens", 1000)
            
            # Initialize LLM manager
            api_key = config.get("api_key")
            llm_manager = LLMManager(
                provider=LLMProvider(provider),
                model=model,
                api_key=api_key,
            )
            
            # Get messages for LLM
            messages = history.get_messages_for_llm()
            
            # Stream response
            accumulated_content = ""
            input_tokens = sum(len(m["content"]) // 4 for m in messages)
            
            try:
                response_stream = await llm_manager.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                
                async for chunk in response_stream:
                    if chunk:
                        accumulated_content += chunk
                        yield {
                            "type": "token",
                            "content": chunk
                        }
                        await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"LLM streaming failed: {e}", exc_info=True)
                yield {
                    "type": "error",
                    "error": str(e)
                }
                return
            
            # Add assistant response to history
            history.add_message("assistant", accumulated_content)
            
            # Calculate output tokens
            output_tokens = len(accumulated_content) // 4
            
            # Record token usage
            if user_id:
                await self._record_token_usage(
                    user_id=user_id,
                    workflow_id=chatflow_id,
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
            
            # Yield completion
            yield {
                "type": "complete",
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Execute streaming failed: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e)
            }

    async def get_chatflow(self, chatflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get chatflow configuration by ID.
        
        Args:
            chatflow_id: Chatflow ID
            
        Returns:
            Chatflow configuration or None if not found
        """
        # Mock implementation - in real app, this would query the database
        return {
            "id": chatflow_id,
            "name": f"Chatflow {chatflow_id[:8]}",
            "user_id": "test-user",
            "is_public": True,
            "config": {
                "provider": "ollama",
                "model": "llama3.3:70b",
                "temperature": 0.7,
                "max_tokens": 1000,
                "system_prompt": "You are a helpful AI assistant."
            }
        }

    async def _record_token_usage(
        self,
        user_id: str,
        workflow_id: Optional[str],
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ):
        """Record token usage to database."""
        try:
            # Get pricing
            from backend.api.agent_builder.cost_tracking import calculate_cost
            cost = calculate_cost(self.db, provider, model, input_tokens, output_tokens)
            
            record = TokenUsage(
                user_id=uuid.UUID(user_id) if user_id else None,
                workflow_id=uuid.UUID(workflow_id) if workflow_id else None,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost,
                node_type="chatflow",
            )
            
            self.db.add(record)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to record token usage: {e}")
            self.db.rollback()
