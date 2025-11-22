"""HTTP Request tool executor."""

from typing import Dict, Any, Optional
import httpx

from ..base_executor import BaseToolExecutor, ToolExecutionResult


class HTTPRequestExecutor(BaseToolExecutor):
    """Executor for HTTP Request tool."""
    
    def __init__(self):
        super().__init__("http_request", "HTTP Request")
        self.category = "developer"
        
        # Define parameter schema
        self.params_schema = {
            "url": {
                "type": "string",
                "description": "Request URL",
                "required": True,
                "placeholder": "https://api.example.com/endpoint"
            },
            "method": {
                "type": "select",
                "description": "HTTP method",
                "required": False,
                "default": "GET",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
            },
            "headers": {
                "type": "json",
                "description": "Request headers (JSON)",
                "required": False,
                "default": {},
                "placeholder": '{"Content-Type": "application/json"}'
            },
            "body": {
                "type": "json",
                "description": "Request body (JSON)",
                "required": False,
                "placeholder": '{"key": "value"}'
            },
            "timeout": {
                "type": "number",
                "description": "Request timeout in seconds",
                "required": False,
                "default": 30,
                "min": 1,
                "max": 300
            }
        }
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute HTTP request."""
        
        self.validate_params(params, ["url"])
        
        url = params.get("url")
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
                
                return ToolExecutionResult(
                    success=response.status_code < 400,
                    output={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "body": response_body,
                        "text": response.text
                    },
                    metadata={
                        "method": method,
                        "url": url
                    }
                )
                
        except httpx.TimeoutException:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Request timeout after {timeout}s"
            )
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                output=None,
                error=f"Request failed: {str(e)}"
            )
