"""Chat trigger for workflow execution."""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from backend.core.triggers.base import BaseTrigger

logger = logging.getLogger(__name__)


class ChatTrigger(BaseTrigger):
    """
    Chat trigger for executing workflows via chat interface.
    
    Features:
    - Chat message handling
    - Conversation context management
    - Response streaming
    - Message history
    """
    
    def __init__(
        self,
        workflow_id: str,
        config: Dict[str, Any],
        db_session: Session
    ):
        """
        Initialize chat trigger.
        
        Args:
            workflow_id: Workflow identifier
            config: Chat configuration
            db_session: Database session
        """
        super().__init__(workflow_id, config)
        self.db = db_session
        self.chat_id = config.get("chat_id")
        self.session_id = config.get("session_id")
        self.enable_streaming = config.get("enable_streaming", True)
        self.max_history = config.get("max_history", 10)
        self._conversation_history: List[Dict[str, Any]] = []
    
    async def register(self) -> Dict[str, Any]:
        """
        Register chat trigger.
        
        Creates chat interface configuration.
        
        Returns:
            Registration result with chat details
        """
        logger.info(f"Registering chat trigger for workflow: {self.workflow_id}")
        
        try:
            # Generate chat ID if not provided
            if not self.chat_id:
                self.chat_id = str(uuid.uuid4())
            
            # Generate session ID if not provided
            if not self.session_id:
                self.session_id = str(uuid.uuid4())
            
            logger.info(
                f"Chat trigger registered: chat_id={self.chat_id}, "
                f"session_id={self.session_id}"
            )
            
            return {
                "trigger_id": self.chat_id,
                "trigger_type": "chat",
                "chat_id": self.chat_id,
                "session_id": self.session_id,
                "chat_url": f"/chat/{self.chat_id}",
                "enable_streaming": self.enable_streaming,
                "is_active": self.is_active,
            }
            
        except Exception as e:
            logger.error(
                f"Failed to register chat trigger: workflow_id={self.workflow_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            raise
    
    async def unregister(self):
        """Unregister chat trigger."""
        logger.info(f"Unregistering chat trigger: chat_id={self.chat_id}")
        
        # Clear conversation history
        self._conversation_history.clear()
        self.is_active = False
        
        logger.info(f"Chat trigger unregistered: chat_id={self.chat_id}")
    
    async def execute(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow in response to chat message.
        
        Args:
            trigger_data: Chat message data
            
        Returns:
            Execution result
        """
        logger.info(
            f"Executing chat trigger: chat_id={self.chat_id}, "
            f"workflow_id={self.workflow_id}"
        )
        
        try:
            # Extract message from trigger data
            message = trigger_data.get("message", "")
            
            # Add message to conversation history
            self._add_to_history("user", message)
            
            # Log trigger execution
            self.log_trigger(
                trigger_type="chat",
                success=True,
                trigger_data=trigger_data
            )
            
            return {
                "success": True,
                "chat_id": self.chat_id,
                "workflow_id": self.workflow_id,
                "session_id": self.session_id,
            }
            
        except Exception as e:
            logger.error(
                f"Chat execution failed: chat_id={self.chat_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            
            self.log_trigger(
                trigger_type="chat",
                success=False,
                trigger_data=trigger_data,
                error=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get chat trigger status.
        
        Returns:
            Status information
        """
        return {
            "active": self.is_active,
            "chat_id": self.chat_id,
            "session_id": self.session_id,
            "workflow_id": self.workflow_id,
            "enable_streaming": self.enable_streaming,
            "message_count": len(self._conversation_history),
        }
    
    def handle_message(
        self,
        message: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle incoming chat message.
        
        Args:
            message: Chat message text
            user_id: User identifier
            metadata: Additional message metadata
            
        Returns:
            Message handling result
        """
        logger.info(f"Handling chat message: chat_id={self.chat_id}")
        
        try:
            # Add message to history
            self._add_to_history(
                role="user",
                content=message,
                user_id=user_id,
                metadata=metadata
            )
            
            # Prepare trigger data
            trigger_data = {
                "message": message,
                "user_id": user_id,
                "session_id": self.session_id,
                "conversation_history": self.get_conversation_context(),
                "metadata": metadata or {},
            }
            
            return {
                "success": True,
                "trigger_data": trigger_data,
            }
            
        except Exception as e:
            logger.error(
                f"Failed to handle message: chat_id={self.chat_id}, "
                f"error={str(e)}",
                exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
            }
    
    def add_response(
        self,
        response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add workflow response to conversation history.
        
        Args:
            response: Response text
            metadata: Additional response metadata
        """
        self._add_to_history(
            role="assistant",
            content=response,
            metadata=metadata
        )
    
    def get_conversation_context(self) -> List[Dict[str, Any]]:
        """
        Get conversation context for workflow execution.
        
        Returns:
            List of recent messages
        """
        # Return last N messages based on max_history
        return self._conversation_history[-self.max_history:]
    
    def get_full_history(self) -> List[Dict[str, Any]]:
        """
        Get full conversation history.
        
        Returns:
            Complete conversation history
        """
        return self._conversation_history.copy()
    
    def clear_history(self):
        """Clear conversation history."""
        logger.info(f"Clearing conversation history: chat_id={self.chat_id}")
        self._conversation_history.clear()
    
    def stream_response(self, response_generator):
        """
        Stream response from workflow execution.
        
        Args:
            response_generator: Generator yielding response chunks
            
        Yields:
            Response chunks
        """
        if not self.enable_streaming:
            # If streaming disabled, collect all chunks and return at once
            chunks = list(response_generator)
            full_response = "".join(chunks)
            yield full_response
            return
        
        # Stream chunks
        for chunk in response_generator:
            yield chunk
    
    def _add_to_history(
        self,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add message to conversation history.
        
        Args:
            role: Message role (user, assistant, system)
            content: Message content
            user_id: User identifier
            metadata: Additional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if user_id:
            message["user_id"] = user_id
        
        if metadata:
            message["metadata"] = metadata
        
        self._conversation_history.append(message)
        
        # Trim history if exceeds max
        if len(self._conversation_history) > self.max_history * 2:
            # Keep last max_history * 2 messages
            self._conversation_history = self._conversation_history[-(self.max_history * 2):]
