"""HTTP and API tool integrations.

This module provides generic HTTP request tools for API integration.
"""

import logging
from typing import Dict, Any, Optional
import httpx

from backend.core.tools.registry import ToolRegistry
from backend.core.tools.base import BaseTool, ToolConfig, ParamConfig, OutputConfig, ToolExecutionError

logger = logging.getLogger(__name__)


class GenericHTTPTool(BaseTool):
    """Generic HTTP request tool that accepts dynamic URLs and methods."""
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with given parameters.
        
        Args:
            params: Tool parameters including url, method, headers, etc.
            credentials: Authentication credentials (optional)
            
        Returns:
            Response data with status_code, headers, body, and text
        """
        url = params.get("url")
        if not url:
            raise ToolExecutionError("URL is required", tool_id=self.config.id)
        
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        query_params = params.get("params", {})
        body = params.get("body")
        timeout = params.get("timeout", 30)
        
        # Add credentials if provided
        if credentials and "api_key" in credentials:
            headers["Authorization"] = f"Bearer {credentials['api_key']}"
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=query_params,
                    json=body if body and method in ["POST", "PUT", "PATCH"] else None
                )
                
                # Parse response
                try:
                    response_body = response.json()
                except Exception:
                    response_body = None
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_body,
                    "text": response.text
                }
                
        except httpx.TimeoutException:
            raise ToolExecutionError(
                f"Request timeout after {timeout}s",
                tool_id=self.config.id
            )
        except httpx.RequestError as e:
            raise ToolExecutionError(
                f"Request failed: {str(e)}",
                tool_id=self.config.id,
                original_error=e
            )


# Register the tool
tool_config = ToolConfig(
    id="http_request",
    name="HTTP Request",
    description="Make HTTP requests to external APIs and services",
    category="developer",
    params={
        "url": ParamConfig(
            type="string",
            description="Request URL",
            required=True
        ),
        "method": ParamConfig(
            type="string",
            description="HTTP method",
            enum=["GET", "POST", "PUT", "PATCH", "DELETE"],
            default="GET"
        ),
        "headers": ParamConfig(
            type="object",
            description="Request headers",
            default={}
        ),
        "params": ParamConfig(
            type="object",
            description="Query parameters",
            default={}
        ),
        "body": ParamConfig(
            type="object",
            description="Request body (for POST/PUT/PATCH)",
            default={}
        ),
        "timeout": ParamConfig(
            type="number",
            description="Request timeout in seconds",
            default=30,
            min_value=1,
            max_value=300
        )
    },
    outputs={
        "status_code": OutputConfig(type="number", description="HTTP status code"),
        "headers": OutputConfig(type="object", description="Response headers"),
        "body": OutputConfig(type="object", description="Response body"),
        "text": OutputConfig(type="string", description="Response text")
    },
    icon="globe",
    bg_color="#3B82F6",
    docs_link="https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods"
)

ToolRegistry.register_tool_config(tool_config, GenericHTTPTool)

logger.info("Registered 1 HTTP tool")
