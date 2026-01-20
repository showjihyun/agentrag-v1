"""
Test Chat API for Agent Preview
Simple endpoint for testing agent configuration without full execution
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/test-chat",
    tags=["test-chat"],
)


class TestChatRequest(BaseModel):
    """Test chat request"""
    message: str
    provider: str
    model: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2000


class TestChatResponse(BaseModel):
    """Test chat response"""
    response: str
    provider: str
    model: str
    processing_time_ms: int
    timestamp: str


@router.post("", response_model=TestChatResponse)
async def test_chat(request: TestChatRequest):
    """
    Test chat endpoint for agent preview.
    
    This is a simple endpoint that uses the configured LLM to generate a response.
    Used in the Agent Wizard preview panel for testing agent configuration.
    """
    start_time = datetime.now()
    
    try:
        # Import LiteLLM for unified LLM interface
        import litellm
        
        # Prepare messages
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.message})
        
        # Map provider to LiteLLM format
        model_name = request.model
        if request.provider == "ollama":
            model_name = f"ollama/{request.model}"
        elif request.provider == "claude":
            model_name = f"claude/{request.model}"
        elif request.provider == "gemini":
            model_name = f"gemini/{request.model}"
        elif request.provider == "grok":
            model_name = f"grok/{request.model}"
        # OpenAI models don't need prefix
        
        # Call LLM
        response = await litellm.acompletion(
            model=model_name,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        # Extract response
        response_text = response.choices[0].message.content
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return TestChatResponse(
            response=response_text,
            provider=request.provider,
            model=request.model,
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Test chat error: {e}", exc_info=True)
        
        # Return a helpful error message
        error_message = str(e)
        if "ollama" in request.provider.lower() and "connection" in error_message.lower():
            error_message = "Cannot connect to Ollama. Please ensure Ollama is running on your system."
        elif "api_key" in error_message.lower() or "authentication" in error_message.lower():
            error_message = f"API key not configured for {request.provider}. Please set it in LLM Settings."
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {error_message}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "endpoint": "/api/agent-builder/test-chat",
        "timestamp": datetime.now().isoformat()
    }
