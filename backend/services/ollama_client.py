"""
Direct Ollama Client - Replaces litellm for Ollama interactions
"""

import httpx
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio

from backend.config import settings

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Ollama-specific error"""
    pass


class OllamaClient:
    """Direct Ollama API client without litellm dependency"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL (default: from settings)
            model: Model name (default: from settings)
            timeout: Request timeout in seconds
        """
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip('/')
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
        
        logger.info(f"Initialized OllamaClient with base_url={self.base_url}, model={self.model}")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def validate_connection(self) -> bool:
        """
        Validate Ollama server is accessible.
        
        Returns:
            True if connection is valid
            
        Raises:
            OllamaError: If connection fails
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            logger.info("Ollama connection validated successfully")
            return True
        except httpx.ConnectError:
            raise OllamaError(
                f"Cannot connect to Ollama at {self.base_url}. Is Ollama running?"
            )
        except httpx.TimeoutException:
            raise OllamaError(f"Timeout connecting to Ollama at {self.base_url}")
        except Exception as e:
            raise OllamaError(f"Ollama connection error: {str(e)}")
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Returns:
            List of model information dictionaries
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise OllamaError(f"Failed to list models: {str(e)}")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate completion (non-streaming).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Must be False for this method
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters
            
        Returns:
            Generated text
            
        Raises:
            OllamaError: If generation fails
        """
        if stream:
            raise ValueError("Use generate_stream() for streaming responses")
        
        # Convert messages to Ollama format
        prompt = self._messages_to_prompt(messages)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Add any additional options
        if kwargs:
            payload["options"].update(kwargs)
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            content = data.get("response", "")
            
            logger.debug(f"Generated response: {len(content)} characters")
            return content
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Ollama HTTP error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise OllamaError(error_msg)
        except Exception as e:
            logger.error(f"Ollama generation error: {str(e)}")
            raise OllamaError(f"Failed to generate completion: {str(e)}")
    
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate completion with streaming.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters
            
        Yields:
            Token strings as they are generated
            
        Raises:
            OllamaError: If generation fails
        """
        # Convert messages to Ollama format
        prompt = self._messages_to_prompt(messages)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Add any additional options
        if kwargs:
            payload["options"].update(kwargs)
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        
                        # Check if done
                        if data.get("done", False):
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse streaming response: {line}")
                        continue
                        
        except httpx.HTTPStatusError as e:
            error_msg = f"Ollama HTTP error: {e.response.status_code}"
            logger.error(error_msg)
            raise OllamaError(error_msg)
        except Exception as e:
            logger.error(f"Ollama streaming error: {str(e)}")
            raise OllamaError(f"Failed to stream completion: {str(e)}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate chat completion using Ollama's chat API (non-streaming).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Must be False for this method
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters
            
        Returns:
            Generated text
            
        Raises:
            OllamaError: If generation fails
        """
        if stream:
            raise ValueError("Use chat_stream() for streaming responses")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Add any additional options
        if kwargs:
            payload["options"].update(kwargs)
        
        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            content = data.get("message", {}).get("content", "")
            
            logger.debug(f"Generated chat response: {len(content)} characters")
            return content
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Ollama HTTP error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise OllamaError(error_msg)
        except Exception as e:
            logger.error(f"Ollama chat error: {str(e)}")
            raise OllamaError(f"Failed to generate chat completion: {str(e)}")
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate chat completion with streaming using Ollama's chat API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Ollama parameters
            
        Yields:
            Token strings as they are generated
            
        Raises:
            OllamaError: If generation fails
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Add any additional options
        if kwargs:
            payload["options"].update(kwargs)
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                        
                        # Check if done
                        if data.get("done", False):
                            break
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse streaming response: {line}")
                        continue
                        
        except httpx.HTTPStatusError as e:
            error_msg = f"Ollama HTTP error: {e.response.status_code}"
            logger.error(error_msg)
            raise OllamaError(error_msg)
        except Exception as e:
            logger.error(f"Ollama chat streaming error: {str(e)}")
            raise OllamaError(f"Failed to stream chat completion: {str(e)}")
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert messages to a single prompt string.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
