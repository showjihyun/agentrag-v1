"""
LLM Settings API
Endpoints for managing LLM provider configuration
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
# Authentication will be added later
from backend.services.llm_manager import LLMManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["LLM Settings"])


class LLMTestRequest(BaseModel):
    """Request to test LLM connection"""
    provider: str = Field(..., description="LLM provider (openai, anthropic, google, ollama, groq)")
    model: str = Field(..., description="Model name")
    apiKey: Optional[str] = Field(None, description="API key (if required)")
    ollamaUrl: Optional[str] = Field(None, description="Ollama URL (if using Ollama)")


class LLMTestResponse(BaseModel):
    """Response from LLM test"""
    success: bool
    message: str
    latency: Optional[float] = None


@router.post("/test", response_model=LLMTestResponse)
async def test_llm_connection(
    request: LLMTestRequest
):
    """
    Test LLM provider connection
    
    Sends a simple test prompt to verify the configuration works
    """
    try:
        import time
        import httpx
        start_time = time.time()
        
        # Test based on provider
        if request.provider == "ollama":
            # Test Ollama directly
            ollama_url = request.ollamaUrl or "http://localhost:11434"
            
            # First, check if Ollama is running
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    # Check Ollama health
                    health_response = await client.get(f"{ollama_url}/api/tags")
                    
                    if health_response.status_code != 200:
                        return LLMTestResponse(
                            success=False,
                            message=f"Ollama server returned status {health_response.status_code}"
                        )
                    
                    # Test generation
                    test_response = await client.post(
                        f"{ollama_url}/api/generate",
                        json={
                            "model": request.model,
                            "prompt": "Say 'Hello' in one word.",
                            "stream": False
                        },
                        timeout=30.0
                    )
                    
                    if test_response.status_code == 200:
                        latency = time.time() - start_time
                        result = test_response.json()
                        
                        return LLMTestResponse(
                            success=True,
                            message=f"Successfully connected to Ollama ({request.model})",
                            latency=round(latency, 2)
                        )
                    else:
                        error_detail = test_response.text
                        return LLMTestResponse(
                            success=False,
                            message=f"Ollama generation failed: {error_detail}"
                        )
                        
            except httpx.ConnectError:
                return LLMTestResponse(
                    success=False,
                    message=f"Cannot connect to Ollama at {ollama_url}. Make sure Ollama is running."
                )
            except httpx.TimeoutException:
                return LLMTestResponse(
                    success=False,
                    message="Connection to Ollama timed out. The server might be slow or unresponsive."
                )
                
        elif request.provider == "openai":
            # Test OpenAI
            if not request.apiKey:
                return LLMTestResponse(
                    success=False,
                    message="API key is required for OpenAI"
                )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {request.apiKey}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": request.model,
                        "messages": [{"role": "user", "content": "Say 'Hello' in one word."}],
                        "max_tokens": 10
                    }
                )
                
                if response.status_code == 200:
                    latency = time.time() - start_time
                    return LLMTestResponse(
                        success=True,
                        message=f"Successfully connected to OpenAI ({request.model})",
                        latency=round(latency, 2)
                    )
                else:
                    error = response.json()
                    return LLMTestResponse(
                        success=False,
                        message=f"OpenAI error: {error.get('error', {}).get('message', 'Unknown error')}"
                    )
                    
        elif request.provider == "anthropic":
            # Test Anthropic Claude
            if not request.apiKey:
                return LLMTestResponse(
                    success=False,
                    message="API key is required for Anthropic"
                )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": request.apiKey,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": request.model,
                        "messages": [{"role": "user", "content": "Say 'Hello' in one word."}],
                        "max_tokens": 10
                    }
                )
                
                if response.status_code == 200:
                    latency = time.time() - start_time
                    return LLMTestResponse(
                        success=True,
                        message=f"Successfully connected to Anthropic ({request.model})",
                        latency=round(latency, 2)
                    )
                else:
                    error = response.json()
                    return LLMTestResponse(
                        success=False,
                        message=f"Anthropic error: {error.get('error', {}).get('message', 'Unknown error')}"
                    )
                    
        elif request.provider == "google":
            # Test Google Gemini
            if not request.apiKey:
                return LLMTestResponse(
                    success=False,
                    message="API key is required for Google Gemini"
                )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{request.model}:generateContent?key={request.apiKey}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": "Say 'Hello' in one word."}]}]
                    }
                )
                
                if response.status_code == 200:
                    latency = time.time() - start_time
                    return LLMTestResponse(
                        success=True,
                        message=f"Successfully connected to Google Gemini ({request.model})",
                        latency=round(latency, 2)
                    )
                else:
                    error = response.json()
                    return LLMTestResponse(
                        success=False,
                        message=f"Google error: {error.get('error', {}).get('message', 'Unknown error')}"
                    )
                    
        elif request.provider == "groq":
            # Test Groq
            if not request.apiKey:
                return LLMTestResponse(
                    success=False,
                    message="API key is required for Groq"
                )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {request.apiKey}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": request.model,
                        "messages": [{"role": "user", "content": "Say 'Hello' in one word."}],
                        "max_tokens": 10
                    }
                )
                
                if response.status_code == 200:
                    latency = time.time() - start_time
                    return LLMTestResponse(
                        success=True,
                        message=f"Successfully connected to Groq ({request.model})",
                        latency=round(latency, 2)
                    )
                else:
                    error = response.json()
                    return LLMTestResponse(
                        success=False,
                        message=f"Groq error: {error.get('error', {}).get('message', 'Unknown error')}"
                    )
        else:
            return LLMTestResponse(
                success=False,
                message=f"Unsupported provider: {request.provider}"
            )
            
    except Exception as e:
        logger.error(f"LLM test failed: {str(e)}", exc_info=True)
        return LLMTestResponse(
            success=False,
            message=f"Connection failed: {str(e)}"
        )
