"""Anthropic Claude tool executor."""

import os
from typing import Dict, Any, Optional
import httpx

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class AnthropicExecutor(BaseToolExecutor):
    """Executor for Anthropic Claude tool."""
    
    def __init__(self):
        super().__init__("anthropic_claude", "Anthropic Claude")
        self.category = "ai"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"
        
        # Define parameter schema with Select Boxes
        self.params_schema = {
            "prompt": {
                "type": "textarea",
                "description": "Message or prompt to send to Claude",
                "required": True,
                "placeholder": "Enter your prompt here...",
                "helpText": "The main input text for Claude to process"
            },
            "model": {
                "type": "select",  # ✅ Select Box
                "description": "Claude model to use",
                "required": False,
                "default": "claude-3-5-sonnet-20241022",
                "enum": [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-haiku-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307"
                ],
                "helpText": "Sonnet: Balanced, Opus: Most capable, Haiku: Fastest"
            },
            "max_tokens": {
                "type": "number",
                "description": "Maximum tokens to generate",
                "required": False,
                "default": 1024,
                "min": 1,
                "max": 4096,
                "helpText": "Higher values allow longer responses"
            },
            "temperature": {
                "type": "number",
                "description": "Sampling temperature (0-1)",
                "required": False,
                "default": 1.0,
                "min": 0,
                "max": 1,
                "helpText": "Lower = more focused, Higher = more creative"
            },
            "system": {
                "type": "textarea",
                "description": "System prompt (optional)",
                "required": False,
                "placeholder": "You are a helpful assistant...",
                "helpText": "Sets the behavior and context for Claude"
            }
        }
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute Claude completion."""
        
        self.validate_params(params, ["messages"])
        
        api_key = credentials.get("api_key") if credentials else self.api_key
        if not api_key:
            return ToolExecutionResult(
                success=False,
                output=None,
                error="Anthropic API key not configured"
            )
        
        model = params.get("model", "claude-3-sonnet-20240229")
        messages = params.get("messages")
        max_tokens = params.get("max_tokens", 1024)
        temperature = params.get("temperature", 1.0)
        
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    return ToolExecutionResult(
                        success=False,
                        output=None,
                        error=f"Anthropic API error: {response.status_code}"
                    )
                
                data = response.json()
                content = data["content"][0]["text"]
                
                return ToolExecutionResult(
                    success=True,
                    output={
                        "content": content,
                        "usage": data.get("usage", {})
                    },
                    metadata={"model": model}
                )
                
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Execution failed: {str(e)}"
            )
