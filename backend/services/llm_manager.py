"""
LLM Provider Manager with multi-provider support (Ollama, OpenAI, Claude)
"""

# Import warning configuration from main module to avoid duplication
# Warnings are configured globally in main.py
import warnings

# Only suppress LiteLLM-specific warnings here
warnings.filterwarnings("ignore", message=".*StreamingChoices.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*Message.*serialized value.*", category=UserWarning)

from enum import Enum
from typing import Optional, List, Dict, Any, AsyncGenerator, Union
import logging
from litellm import acompletion
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import asyncio

from backend.config import settings

# Define OllamaError if not available from litellm
try:
    from litellm.llms.ollama import OllamaError
except ImportError:
    class OllamaError(Exception):
        """Ollama-specific error"""
        pass

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""

    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"


class LLMError(Exception):
    """Base exception for LLM-related errors"""

    pass


class LLMConnectionError(LLMError):
    """Exception for connection errors"""

    pass


class LLMConfigurationError(LLMError):
    """Exception for configuration errors"""

    pass


class LLMManager:
    """
    Manages LLM interactions with support for multiple providers.
    Uses LiteLLM for unified interface across Ollama, OpenAI, and Claude.
    Supports automatic fallback to alternative providers if primary fails.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        enable_fallback: bool = True,
    ):
        """
        Initialize LLM Manager.

        Args:
            provider: LLM provider (defaults to settings.LLM_PROVIDER)
            model: Model name (defaults to settings.LLM_MODEL)
            api_key: API key for cloud providers (defaults to settings)
            base_url: Base URL for provider (defaults to settings)
            enable_fallback: Whether to enable automatic fallback to other providers
        """
        # Set provider
        provider_str = provider.value if provider else settings.LLM_PROVIDER
        try:
            self.provider = LLMProvider(provider_str)
        except ValueError:
            raise LLMConfigurationError(
                f"Invalid LLM provider: {provider_str}. "
                f"Must be one of: {[p.value for p in LLMProvider]}"
            )

        self.model = model or settings.LLM_MODEL
        self.base_url = base_url or self._get_default_base_url()
        self.api_key = api_key or self._get_default_api_key()
        self.enable_fallback = enable_fallback
        self.fallback_providers = self._get_fallback_providers()

        # Validate configuration
        validation_result = self._validate_configuration()

        if not validation_result["is_valid"]:
            # Try to find a working fallback
            if self.enable_fallback and self.fallback_providers:
                logger.warning(
                    f"Primary provider {self.provider.value} validation failed: "
                    f"{validation_result['error']}. Attempting fallback..."
                )
                self._try_fallback_provider()
            else:
                raise LLMConfigurationError(validation_result["error"])

        logger.info(
            f"Initialized LLMManager with provider={self.provider.value}, "
            f"model={self.model}, fallback_enabled={self.enable_fallback}"
        )

    def _get_default_base_url(self) -> Optional[str]:
        """Get default base URL for provider"""
        if self.provider == LLMProvider.OLLAMA:
            return settings.OLLAMA_BASE_URL
        return None

    def _get_default_api_key(self) -> Optional[str]:
        """Get default API key for provider"""
        if self.provider == LLMProvider.OPENAI:
            return settings.OPENAI_API_KEY
        elif self.provider == LLMProvider.CLAUDE:
            return settings.ANTHROPIC_API_KEY
        return None

    def _get_fallback_providers(self) -> List[str]:
        """Get list of fallback providers from settings"""
        fallbacks = settings.get_fallback_providers()

        # Filter out providers that aren't properly configured
        valid_fallbacks = []
        for provider_name in fallbacks:
            is_valid, _ = settings.validate_provider_config(provider_name)
            if is_valid:
                valid_fallbacks.append(provider_name)
            else:
                logger.debug(
                    f"Skipping fallback provider {provider_name}: not configured"
                )

        return valid_fallbacks

    def _validate_configuration(self) -> Dict[str, Any]:
        """
        Validate provider configuration.

        Returns:
            Dictionary with validation result: {'is_valid': bool, 'error': Optional[str]}
        """
        # Use settings validation
        is_valid, error_msg = settings.validate_provider_config(self.provider.value)

        if not is_valid:
            return {"is_valid": False, "error": error_msg}

        # Additional validation for Ollama - check connection
        if self.provider == LLMProvider.OLLAMA:
            try:
                self._validate_ollama_connection()
            except LLMConnectionError as e:
                return {"is_valid": False, "error": str(e)}

        return {"is_valid": True, "error": None}

    def _try_fallback_provider(self) -> None:
        """
        Attempt to switch to a fallback provider.

        Raises:
            LLMConfigurationError: If no valid fallback provider is found
        """
        for fallback_name in self.fallback_providers:
            try:
                logger.info(f"Trying fallback provider: {fallback_name}")

                # Switch to fallback provider
                self.provider = LLMProvider(fallback_name)
                self.base_url = self._get_default_base_url()
                self.api_key = self._get_default_api_key()

                # Validate fallback
                validation_result = self._validate_configuration()

                if validation_result["is_valid"]:
                    logger.info(
                        f"Successfully switched to fallback provider: {fallback_name}"
                    )
                    return
                else:
                    logger.warning(
                        f"Fallback provider {fallback_name} validation failed: "
                        f"{validation_result['error']}"
                    )

            except Exception as e:
                logger.warning(
                    f"Failed to switch to fallback provider {fallback_name}: {e}"
                )
                continue

        # No valid fallback found
        available_providers = settings.get_available_providers()
        error_msg = (
            f"Primary provider validation failed and no valid fallback providers available. "
            f"Available providers: {', '.join(available_providers) if available_providers else 'none'}. "
            f"Configuration status:\n{self._format_config_status()}"
        )
        raise LLMConfigurationError(error_msg)

    def _format_config_status(self) -> str:
        """Format configuration status for error messages"""
        status = settings.get_provider_config_status()
        lines = []

        for provider, details in status["providers"].items():
            if details["configured"]:
                lines.append(f"  ✓ {provider}: configured")
            else:
                lines.append(f"  ✗ {provider}: {details['error']}")

        return "\n".join(lines)

    def _validate_ollama_connection(self) -> None:
        """Validate Ollama is running and accessible"""
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            response.raise_for_status()
            logger.info("Ollama connection validated successfully")
        except httpx.ConnectError:
            raise LLMConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. " "Is Ollama running?"
            )
        except httpx.TimeoutException:
            raise LLMConnectionError(f"Timeout connecting to Ollama at {self.base_url}")
        except Exception as e:
            raise LLMConnectionError(f"Ollama connection error: {str(e)}")

    def _format_model_name(self) -> str:
        """
        Format model name for LiteLLM based on provider.

        Returns:
            Formatted model name (e.g., "ollama/llama3.1", "gpt-4", "claude-3-opus-20240229")
        """
        if self.provider == LLMProvider.OLLAMA:
            return f"ollama/{self.model}"
        elif self.provider == LLMProvider.CLAUDE:
            # LiteLLM expects "claude-" prefix for Anthropic models
            if not self.model.startswith("claude-"):
                return f"claude-{self.model}"
            return self.model
        else:
            # OpenAI models use their name directly
            return self.model

    async def generate(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Generate completion using configured provider with enforced timeout.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text (string) or async generator for streaming

        Raises:
            LLMError: If generation fails or times out
        """
        import asyncio

        # Get provider-specific timeout
        timeout = self._get_timeout_for_provider()

        try:
            # Enforce timeout with asyncio.wait_for
            # Use retry logic only for cloud providers
            if self.provider == LLMProvider.OLLAMA:
                result = await asyncio.wait_for(
                    self._generate_without_retry(
                        messages, stream, temperature, max_tokens, timeout, **kwargs
                    ),
                    timeout=timeout,
                )
            else:
                result = await asyncio.wait_for(
                    self._generate_with_retry(
                        messages, stream, temperature, max_tokens, timeout, **kwargs
                    ),
                    timeout=timeout,
                )

            return result

        except asyncio.TimeoutError:
            error_msg = (
                f"LLM request timed out after {timeout}s "
                f"(provider: {self.provider.value}, model: {self.model})"
            )
            logger.error(error_msg)
            raise LLMError(error_msg)

    def _get_timeout_for_provider(self) -> float:
        """
        Get appropriate timeout for the provider.

        Returns:
            Timeout in seconds
        """
        if self.provider == LLMProvider.OLLAMA:
            return 10.0  # Local provider - optimized for speculative mode
        else:
            return 60.0  # Cloud providers - longer timeout

    async def _generate_without_retry(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: float,
        max_tokens: Optional[int],
        timeout: float,
        **kwargs,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Generate without retry logic (for local providers)."""
        import asyncio

        model_name = self._format_model_name()

        litellm_params = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
            "timeout": timeout,
            **kwargs,
        }

        if max_tokens:
            litellm_params["max_tokens"] = max_tokens

        if self.api_key:
            litellm_params["api_key"] = self.api_key

        if self.provider == LLMProvider.OLLAMA:
            litellm_params["api_base"] = self.base_url

        try:
            if stream:
                return self._stream_completion(litellm_params)
            else:
                response = await acompletion(**litellm_params)
                content = response.choices[0].message.content
                logger.debug(f"Generated response: {len(content)} characters")
                return content

        except OllamaError as e:
            # Handle Ollama-specific errors (e.g., model loading)
            error_msg = str(e)
            if "loading model" in error_msg.lower():
                logger.warning(f"Ollama model loading, retrying in 3 seconds...")
                await asyncio.sleep(3)
                # Retry once after model loads
                try:
                    response = await acompletion(**litellm_params)
                    content = response.choices[0].message.content
                    logger.info(
                        f"Generated response after model load: {len(content)} characters"
                    )
                    return content
                except Exception as retry_error:
                    logger.error(
                        f"LLM generation error after retry: {str(retry_error)}"
                    )
                    raise LLMError(
                        f"Failed to generate completion after model load: {str(retry_error)}"
                    )
            else:
                logger.error(f"Ollama error: {error_msg}")
                raise LLMError(f"Ollama error: {error_msg}")

        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            raise LLMError(f"Failed to generate completion: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _generate_with_retry(
        self,
        messages: List[Dict[str, str]],
        stream: bool,
        temperature: float,
        max_tokens: Optional[int],
        timeout: float,
        **kwargs,
    ) -> Union[str, AsyncGenerator[str, None]]:
        """Generate with retry logic (for cloud providers)."""
        model_name = self._format_model_name()

        litellm_params = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": stream,
            "timeout": timeout,
            **kwargs,
        }

        if max_tokens:
            litellm_params["max_tokens"] = max_tokens

        if self.api_key:
            litellm_params["api_key"] = self.api_key

        try:
            if stream:
                return self._stream_completion(litellm_params)
            else:
                response = await acompletion(**litellm_params)
                content = response.choices[0].message.content
                logger.debug(f"Generated response: {len(content)} characters")
                return content

        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            raise LLMError(f"Failed to generate completion: {str(e)}")

    async def _stream_completion(
        self, litellm_params: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion tokens.

        Args:
            litellm_params: Parameters for LiteLLM

        Yields:
            Token strings as they are generated
        """
        try:
            response = await acompletion(**litellm_params)

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            raise LLMError(f"Failed to stream completion: {str(e)}")

    async def generate_with_system(
        self, system_prompt: str, user_message: str, stream: bool = False, **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Convenience method to generate with system and user messages.

        Args:
            system_prompt: System prompt
            user_message: User message
            stream: Whether to stream the response
            **kwargs: Additional parameters

        Returns:
            Generated text or async generator
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.generate(messages, stream=stream, **kwargs)

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the current provider configuration.

        Returns:
            Dictionary with provider details
        """
        return {
            "provider": self.provider.value,
            "model": self.model,
            "base_url": self.base_url,
            "has_api_key": bool(self.api_key),
            "formatted_model_name": self._format_model_name(),
        }
