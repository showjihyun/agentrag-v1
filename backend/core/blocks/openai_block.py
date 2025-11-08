"""OpenAI Block for calling OpenAI API in workflows."""

import logging
from typing import Dict, Any
import httpx

from backend.core.blocks.base import BaseBlock, BlockExecutionError
from backend.core.blocks.registry import BlockRegistry

logger = logging.getLogger(__name__)


@BlockRegistry.register(
    block_type="openai",
    name="OpenAI",
    description="Call OpenAI API for chat completions",
    category="tools",
    sub_blocks=[
        {
            "id": "api_key",
            "type": "oauth-input",
            "title": "API Key",
            "placeholder": "sk-...",
            "required": True,
        },
        {
            "id": "model",
            "type": "dropdown",
            "title": "Model",
            "required": True,
            "default_value": "gpt-4",
            "options": [
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
            ],
        },
        {
            "id": "prompt",
            "type": "long-input",
            "title": "Prompt",
            "placeholder": "Enter your prompt here...",
            "required": True,
        },
        {
            "id": "temperature",
            "type": "number-input",
            "title": "Temperature",
            "default_value": 0.7,
            "required": False,
        },
        {
            "id": "max_tokens",
            "type": "number-input",
            "title": "Max Tokens",
            "default_value": 1000,
            "required": False,
        },
        {
            "id": "system_message",
            "type": "long-input",
            "title": "System Message",
            "placeholder": "You are a helpful assistant...",
            "required": False,
        },
    ],
    inputs={
        "prompt": {"type": "string", "description": "The prompt to send to OpenAI"},
        "variables": {
            "type": "object",
            "description": "Variables to interpolate in prompt",
        },
    },
    outputs={
        "response": {"type": "string", "description": "OpenAI response text"},
        "usage": {"type": "object", "description": "Token usage information"},
        "model": {"type": "string", "description": "Model used"},
    },
    bg_color="#10A37F",
    icon="openai",
    auth_mode="api_key",
    docs_link="https://platform.openai.com/docs/api-reference/chat",
)
class OpenAIBlock(BaseBlock):
    """
    Block for calling OpenAI Chat Completion API.
    
    This block sends prompts to OpenAI's API and returns the response.
    It supports variable interpolation in prompts and configurable parameters.
    """
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute OpenAI API call.
        
        Args:
            inputs: Input data containing:
                - prompt: The prompt text (optional if using sub_blocks)
                - variables: Variables for prompt interpolation (optional)
            context: Execution context
            
        Returns:
            Dict containing:
                - response: OpenAI response text
                - usage: Token usage information
                - model: Model used
                
        Raises:
            BlockExecutionError: If API call fails
        """
        try:
            # Get configuration from SubBlocks
            api_key = self.sub_blocks.get("api_key")
            model = self.sub_blocks.get("model", "gpt-4")
            prompt_template = self.sub_blocks.get("prompt", inputs.get("prompt", ""))
            temperature = float(self.sub_blocks.get("temperature", 0.7))
            max_tokens = int(self.sub_blocks.get("max_tokens", 1000))
            system_message = self.sub_blocks.get("system_message")
            
            if not api_key:
                raise BlockExecutionError(
                    "OpenAI API key is required",
                    block_type="openai",
                    block_id=self.block_id
                )
            
            if not prompt_template:
                raise BlockExecutionError(
                    "Prompt is required",
                    block_type="openai",
                    block_id=self.block_id
                )
            
            # Interpolate variables in prompt
            variables = inputs.get("variables", {})
            prompt = self._interpolate_variables(prompt_template, variables)
            
            # Build messages
            messages = []
            if system_message:
                messages.append({
                    "role": "system",
                    "content": system_message
                })
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Call OpenAI API
            logger.info(f"Calling OpenAI API with model {model}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    }
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    raise BlockExecutionError(
                        f"OpenAI API error: {response.status_code} - {error_detail}",
                        block_type="openai",
                        block_id=self.block_id
                    )
                
                result = response.json()
            
            # Extract response
            response_text = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            
            logger.info(
                f"OpenAI API call successful. "
                f"Tokens used: {usage.get('total_tokens', 0)}"
            )
            
            return {
                "response": response_text,
                "usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
                "model": model,
            }
            
        except BlockExecutionError:
            raise
        except Exception as e:
            logger.error(f"OpenAI block execution failed: {str(e)}", exc_info=True)
            raise BlockExecutionError(
                f"Failed to execute OpenAI block: {str(e)}",
                block_type="openai",
                block_id=self.block_id,
                original_error=e
            )
    
    def _interpolate_variables(
        self,
        template: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Interpolate variables in template string.
        
        Supports {{variable_name}} syntax.
        
        Args:
            template: Template string
            variables: Variables to interpolate
            
        Returns:
            Interpolated string
        """
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
