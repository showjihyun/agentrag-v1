"""HTTP Block for making API requests in workflows."""

import logging
import json
from typing import Dict, Any, Optional
import httpx

from backend.core.blocks.base import BaseBlock, BlockExecutionError
from backend.core.blocks.registry import BlockRegistry

logger = logging.getLogger(__name__)


@BlockRegistry.register(
    block_type="http",
    name="HTTP Request",
    description="Make HTTP API requests",
    category="tools",
    sub_blocks=[
        {
            "id": "url",
            "type": "short-input",
            "title": "URL",
            "placeholder": "https://api.example.com/endpoint",
            "required": True,
        },
        {
            "id": "method",
            "type": "dropdown",
            "title": "Method",
            "required": True,
            "default_value": "GET",
            "options": ["GET", "POST", "PUT", "PATCH", "DELETE"],
        },
        {
            "id": "headers",
            "type": "code",
            "title": "Headers (JSON)",
            "language": "json",
            "placeholder": '{"Content-Type": "application/json"}',
            "required": False,
        },
        {
            "id": "body",
            "type": "code",
            "title": "Body (JSON)",
            "language": "json",
            "placeholder": '{"key": "value"}',
            "required": False,
            "condition": {
                "field": "method",
                "operator": "in",
                "value": ["POST", "PUT", "PATCH"]
            },
        },
        {
            "id": "timeout",
            "type": "number-input",
            "title": "Timeout (seconds)",
            "default_value": 30,
            "required": False,
        },
        {
            "id": "follow_redirects",
            "type": "checkbox",
            "title": "Follow Redirects",
            "default_value": True,
            "required": False,
        },
    ],
    inputs={
        "url": {"type": "string", "description": "Request URL (optional if in sub_blocks)"},
        "variables": {
            "type": "object",
            "description": "Variables to interpolate in URL/body",
        },
    },
    outputs={
        "status_code": {"type": "integer", "description": "HTTP status code"},
        "body": {"type": "string", "description": "Response body"},
        "headers": {"type": "object", "description": "Response headers"},
        "json": {"type": "object", "description": "Parsed JSON response (if applicable)"},
    },
    bg_color="#3B82F6",
    icon="globe",
    docs_link="https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods",
)
class HTTPBlock(BaseBlock):
    """
    Block for making HTTP API requests.
    
    This block supports GET, POST, PUT, PATCH, and DELETE methods with
    configurable headers, body, and timeout. It can parse JSON responses
    and supports variable interpolation.
    """
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute HTTP request.
        
        Args:
            inputs: Input data containing:
                - url: Request URL (optional if in sub_blocks)
                - variables: Variables for interpolation (optional)
            context: Execution context
            
        Returns:
            Dict containing:
                - status_code: HTTP status code
                - body: Response body as string
                - headers: Response headers
                - json: Parsed JSON response (if applicable)
                
        Raises:
            BlockExecutionError: If request fails
        """
        try:
            # Get configuration from SubBlocks
            url_template = self.sub_blocks.get("url", inputs.get("url", ""))
            method = self.sub_blocks.get("method", "GET").upper()
            headers_str = self.sub_blocks.get("headers", "{}")
            body_str = self.sub_blocks.get("body", "{}")
            timeout = float(self.sub_blocks.get("timeout", 30))
            follow_redirects = self.sub_blocks.get("follow_redirects", True)
            
            if not url_template:
                raise BlockExecutionError(
                    "URL is required",
                    block_type="http",
                    block_id=self.block_id
                )
            
            # Interpolate variables
            variables = inputs.get("variables", {})
            url = self._interpolate_variables(url_template, variables)
            
            # Parse headers
            headers = self._parse_json(headers_str, "headers")
            
            # Parse body (for POST, PUT, PATCH)
            body = None
            if method in ["POST", "PUT", "PATCH"]:
                body_dict = self._parse_json(body_str, "body")
                # Interpolate variables in body
                body = self._interpolate_dict_variables(body_dict, variables)
            
            # Make HTTP request
            logger.info(f"Making {method} request to {url}")
            
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=follow_redirects
            ) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body else None,
                )
            
            # Parse response
            response_body = response.text
            response_headers = dict(response.headers)
            
            # Try to parse JSON
            response_json = None
            content_type = response_headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    response_json = response.json()
                except Exception as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
            
            logger.info(
                f"HTTP request completed with status {response.status_code}"
            )
            
            return {
                "status_code": response.status_code,
                "body": response_body,
                "headers": response_headers,
                "json": response_json,
            }
            
        except BlockExecutionError:
            raise
        except httpx.TimeoutException as e:
            logger.error(f"HTTP request timeout: {str(e)}")
            raise BlockExecutionError(
                f"HTTP request timeout after {timeout}s",
                block_type="http",
                block_id=self.block_id,
                original_error=e
            )
        except httpx.HTTPError as e:
            logger.error(f"HTTP request failed: {str(e)}")
            raise BlockExecutionError(
                f"HTTP request failed: {str(e)}",
                block_type="http",
                block_id=self.block_id,
                original_error=e
            )
        except Exception as e:
            logger.error(f"HTTP block execution failed: {str(e)}", exc_info=True)
            raise BlockExecutionError(
                f"Failed to execute HTTP block: {str(e)}",
                block_type="http",
                block_id=self.block_id,
                original_error=e
            )
    
    def _parse_json(self, json_str: str, field_name: str) -> Dict[str, Any]:
        """
        Parse JSON string.
        
        Args:
            json_str: JSON string to parse
            field_name: Field name for error messages
            
        Returns:
            Parsed dict
            
        Raises:
            BlockExecutionError: If JSON is invalid
        """
        if not json_str or json_str.strip() == "":
            return {}
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise BlockExecutionError(
                f"Invalid JSON in {field_name}: {str(e)}",
                block_type="http",
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
    
    def _interpolate_dict_variables(
        self,
        data: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively interpolate variables in dict values.
        
        Args:
            data: Dict to interpolate
            variables: Variables to interpolate
            
        Returns:
            Dict with interpolated values
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._interpolate_variables(value, variables)
            elif isinstance(value, dict):
                result[key] = self._interpolate_dict_variables(value, variables)
            elif isinstance(value, list):
                result[key] = [
                    self._interpolate_variables(item, variables)
                    if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
