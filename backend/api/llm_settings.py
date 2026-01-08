"""
LLM Settings API
Endpoints for managing LLM provider configuration
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
# Authentication will be added later
from backend.services.llm_manager import LLMManager
from backend.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["LLM Settings"])


class LLMProvider(BaseModel):
    """LLM Provider configuration"""
    name: str = Field(..., description="Provider name")
    display_name: str = Field(..., description="Display name")
    models: List[str] = Field(..., description="Available models")
    requires_api_key: bool = Field(..., description="Whether API key is required")
    is_available: bool = Field(..., description="Whether provider is available")


class LLMConfiguration(BaseModel):
    """Current LLM configuration"""
    provider: str = Field(..., description="Current provider")
    model: str = Field(..., description="Current model")
    providers: List[LLMProvider] = Field(..., description="Available providers")


class LLMSettingsUpdate(BaseModel):
    """LLM Settings update request"""
    api_keys: Optional[Dict[str, str]] = Field(None, description="API keys for providers")
    ollama: Optional[Dict[str, Any]] = Field(None, description="Ollama configuration")
    default_provider: Optional[str] = Field(None, description="Default provider")
    default_model: Optional[str] = Field(None, description="Default model")


class LLMSettings(BaseModel):
    """LLM Settings response"""
    api_keys: Dict[str, str] = Field(..., description="API keys (masked)")
    ollama: Dict[str, Any] = Field(..., description="Ollama configuration")
    default_provider: str = Field(..., description="Default provider")
    default_model: str = Field(..., description="Default model")


# In-memory storage for demo (in production, use database)
_llm_settings = {
    "api_keys": {
        "openai": "",
        "anthropic": "",
        "gemini": ""
    },
    "ollama": {
        "enabled": True,
        "base_url": "http://localhost:11434",
        "default_model": "llama3.1:8b"
    },
    "default_provider": "ollama",
    "default_model": "llama3.1:8b"
}


@router.get("/settings", response_model=LLMSettings)
async def get_llm_settings():
    """
    Get current LLM settings
    """
    try:
        # Mask API keys for security
        masked_keys = {}
        for provider, key in _llm_settings["api_keys"].items():
            if key:
                masked_keys[provider] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
            else:
                masked_keys[provider] = ""
        
        return LLMSettings(
            api_keys=masked_keys,
            ollama=_llm_settings["ollama"],
            default_provider=_llm_settings["default_provider"],
            default_model=_llm_settings["default_model"]
        )
    except Exception as e:
        logger.error(f"Failed to get LLM settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_llm_settings(settings_update: LLMSettingsUpdate):
    """
    Update LLM settings
    """
    try:
        if settings_update.api_keys:
            _llm_settings["api_keys"].update(settings_update.api_keys)
        
        if settings_update.ollama:
            _llm_settings["ollama"].update(settings_update.ollama)
        
        if settings_update.default_provider:
            _llm_settings["default_provider"] = settings_update.default_provider
        
        if settings_update.default_model:
            _llm_settings["default_model"] = settings_update.default_model
        
        return {"success": True, "message": "Settings updated successfully"}
    except Exception as e:
        logger.error(f"Failed to update LLM settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configuration", response_model=LLMConfiguration)
async def get_llm_configuration():
    """
    Get current LLM configuration and available providers
    """
    try:
        # Get available providers
        providers = []
        
        # Ollama provider
        ollama_models = []
        ollama_available = False
        if _llm_settings["ollama"]["enabled"]:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{_llm_settings['ollama']['base_url']}/api/tags")
                    if response.status_code == 200:
                        data = response.json()
                        ollama_models = [model["name"] for model in data.get("models", [])]
                        ollama_available = True
            except Exception as e:
                logger.warning(f"Ollama not available: {e}")
        
        providers.append(LLMProvider(
            name="ollama",
            display_name="Ollama (Local)",
            models=ollama_models or ["llama3.3:70b", "llama3.1:8b", "mistral:7b"],
            requires_api_key=False,
            is_available=ollama_available
        ))
        
        # OpenAI provider
        openai_available = bool(_llm_settings["api_keys"]["openai"])
        providers.append(LLMProvider(
            name="openai",
            display_name="OpenAI",
            models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
            requires_api_key=True,
            is_available=openai_available
        ))
        
        # Anthropic provider
        anthropic_available = bool(_llm_settings["api_keys"]["anthropic"])
        providers.append(LLMProvider(
            name="anthropic",
            display_name="Anthropic Claude",
            models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            requires_api_key=True,
            is_available=anthropic_available
        ))
        
        # Google provider
        google_available = bool(_llm_settings["api_keys"]["gemini"])
        providers.append(LLMProvider(
            name="google",
            display_name="Google AI",
            models=["gemini-pro", "gemini-pro-vision"],
            requires_api_key=True,
            is_available=google_available
        ))
        
        return LLMConfiguration(
            provider=_llm_settings["default_provider"],
            model=_llm_settings["default_model"],
            providers=providers
        )
        
    except Exception as e:
        logger.error(f"Failed to get LLM configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ollama/models")
async def get_ollama_models():
    """
    Get available Ollama models
    """
    try:
        if not _llm_settings["ollama"]["enabled"]:
            return {"models": [], "message": "Ollama is disabled"}
        
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{_llm_settings['ollama']['base_url']}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return {"models": models, "message": f"Found {len(models)} models"}
            else:
                return {"models": [], "message": f"Ollama server returned status {response.status_code}"}
                
    except Exception as e:
        logger.error(f"Failed to get Ollama models: {e}")
        return {"models": [], "message": f"Error: {str(e)}"}


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


class ChatflowLLMConfig(BaseModel):
    """Chatflow-specific LLM configuration"""
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature")
    max_tokens: int = Field(2000, ge=1, le=8000, description="Max tokens")
    system_prompt: Optional[str] = Field(None, description="System prompt")


class ChatflowLLMConfigResponse(BaseModel):
    """Response for chatflow LLM configuration"""
    success: bool
    config: Optional[ChatflowLLMConfig] = None
    message: str


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
            ollama_url = request.ollamaUrl or _llm_settings["ollama"]["base_url"]
            
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
            api_key = request.apiKey or _llm_settings["api_keys"]["openai"]
            if not api_key:
                return LLMTestResponse(
                    success=False,
                    message="API key is required for OpenAI"
                )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
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
            api_key = request.apiKey or _llm_settings["api_keys"]["anthropic"]
            if not api_key:
                return LLMTestResponse(
                    success=False,
                    message="API key is required for Anthropic"
                )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
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
            api_key = request.apiKey or _llm_settings["api_keys"]["gemini"]
            if not api_key:
                return LLMTestResponse(
                    success=False,
                    message="API key is required for Google Gemini"
                )
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{request.model}:generateContent?key={api_key}",
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


@router.get("/chatflow/{chatflow_id}/config", response_model=ChatflowLLMConfigResponse)
async def get_chatflow_llm_config(
    chatflow_id: str,
    # current_user: User = Depends(get_current_user),  # Authentication will be added later
):
    """
    Get LLM configuration for a specific chatflow
    """
    try:
        # For now, return default configuration
        # In the future, this will be stored in database per chatflow
        default_config = ChatflowLLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            temperature=0.7,
            max_tokens=2000,
            system_prompt=None
        )
        
        return ChatflowLLMConfigResponse(
            success=True,
            config=default_config,
            message="Configuration retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get chatflow LLM config: {e}")
        return ChatflowLLMConfigResponse(
            success=False,
            config=None,
            message=f"Failed to retrieve configuration: {str(e)}"
        )


@router.put("/chatflow/{chatflow_id}/config", response_model=ChatflowLLMConfigResponse)
async def update_chatflow_llm_config(
    chatflow_id: str,
    config: ChatflowLLMConfig,
    # current_user: User = Depends(get_current_user),  # Authentication will be added later
):
    """
    Update LLM configuration for a specific chatflow
    """
    try:
        # For now, just validate the configuration
        # In the future, this will be stored in database per chatflow
        
        # Validate provider is available
        available_providers = []
        
        # Check Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    available_providers.append("ollama")
        except:
            pass
        
        # Check other providers
        if settings.OPENAI_API_KEY:
            available_providers.append("openai")
        if settings.ANTHROPIC_API_KEY:
            available_providers.append("anthropic")
        if settings.GOOGLE_API_KEY:
            available_providers.append("google")
        
        if config.provider not in available_providers:
            return ChatflowLLMConfigResponse(
                success=False,
                config=None,
                message=f"Provider '{config.provider}' is not available. Available providers: {', '.join(available_providers)}"
            )
        
        # TODO: Store configuration in database
        # For now, just return success
        
        return ChatflowLLMConfigResponse(
            success=True,
            config=config,
            message="Configuration updated successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to update chatflow LLM config: {e}")
        return ChatflowLLMConfigResponse(
            success=False,
            config=None,
            message=f"Failed to update configuration: {str(e)}"
        )
