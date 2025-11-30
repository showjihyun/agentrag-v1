"""
AI Agent Streaming API

Provides Server-Sent Events (SSE) streaming for AI Agent responses
"""

import logging
import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/ai-agent",
    tags=["ai-agent-streaming"]
)


class AIAgentStreamRequest(BaseModel):
    """Request model for AI Agent streaming"""
    provider: str
    model: str
    user_message: str
    system_prompt: str | None = None
    session_id: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


async def stream_ai_response(
    request: AIAgentStreamRequest,
    user_id: str,
    db: Session
) -> AsyncGenerator[str, None]:
    """
    Stream AI Agent response using SSE format
    
    Yields:
        SSE formatted messages with AI response chunks
    """
    try:
        # Import here to avoid circular imports
        from backend.services.llm_manager import LLMManager, LLMProvider
        from backend.services.api_key_service import APIKeyService
        
        logger.info(f"Starting AI Agent stream: {request.provider}/{request.model}")
        
        # Get user's API key if needed
        api_key = None
        if request.provider in ["openai", "anthropic", "gemini", "grok"]:
            api_key_service = APIKeyService(db)
            api_key = api_key_service.get_decrypted_api_key(user_id, request.provider)
            
            if not api_key:
                yield f"data: {json.dumps({'type': 'error', 'error': f'{request.provider.upper()} API key not found'})}\n\n"
                return
        
        # Initialize LLM Manager with provider
        provider_enum = LLMProvider(request.provider)
        llm_manager = LLMManager(
            provider=provider_enum,
            model=request.model,
            api_key=api_key
        )
        
        # Build messages
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.user_message})
        
        # Stream response using existing generate method
        accumulated_content = ""
        
        response_stream = await llm_manager.generate(
            messages=messages,
            stream=True,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        async for chunk in response_stream:
            if chunk:
                accumulated_content += chunk
                
                # Send chunk to client
                yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
        
        # Send completion signal
        yield f"data: {json.dumps({'type': 'done', 'total_length': len(accumulated_content)})}\n\n"
        yield "data: [DONE]\n\n"
        
        logger.info(f"AI Agent stream completed: {len(accumulated_content)} chars")
        
    except Exception as e:
        logger.error(f"AI Agent stream error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


@router.post("/stream")
async def stream_ai_agent(
    request: AIAgentStreamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stream AI Agent response using Server-Sent Events
    
    Returns:
        StreamingResponse with SSE format
    """
    return StreamingResponse(
        stream_ai_response(request, str(current_user.id), db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
