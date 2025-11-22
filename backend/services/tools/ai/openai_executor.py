"""OpenAI Chat tool executor."""

import os
from typing import Dict, Any, Optional
import httpx

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class OpenAIChatExecutor(BaseToolExecutor):
    """Executor for OpenAI Chat tool."""
    
    def __init__(self):
        super().__init__("openai_chat", "OpenAI Chat")
        self.category = "ai"
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        
        # Define parameter schema
        self.params_schema = {
            "prompt": {
                "type": "textarea",
                "description": "Prompt or message to send",
                "required": True,
                "placeholder": "Enter your prompt here"
            },
            "model": {
                "type": "select",
                "description": "OpenAI model to use",
                "required": False,
                "default": "gpt-4",
                "enum": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]
            },
            "temperature": {
                "type": "number",
                "description": "Sampling temperature (0-2)",
                "required": False,
                "default": 0.7,
                "min": 0,
                "max": 2
            },
            "max_tokens": {
                "type": "number",
                "description": "Maximum tokens to generate",
                "required": False,
                "default": 1000,
                "min": 1,
                "max": 4096
            }
        }
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute OpenAI Chat completion."""
        
        # Validate required parameters
        self.validate_params(params, ["messages"])
        
        # Get API key
        api_key = credentials.get("api_key") if credentials else self.api_key
        if not api_key:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="OpenAI API key not configured"
            )
        
        # Prepare request
        model = params.get("model", "gpt-4")
        messages = params.get("messages")
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 1000)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Make API request
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    return ToolExecutionResult(
                        success=False,
                        output=None,
                        error=f"OpenAI API error: {response.status_code} - {response.text}"
                    )
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                return ToolExecutionResult(
                    success=True,
                    output={
                        "content": content,
                        "usage": data.get("usage", {})
                    },
                    metadata={
                        "model": model,
                        "finish_reason": data["choices"][0].get("finish_reason")
                    }
                )
                
        except httpx.TimeoutException:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="Request timeout"
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Execution failed: {str(e)}"
            )
