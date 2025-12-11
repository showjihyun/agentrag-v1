"""
HTTP Request Node Handler

Handles HTTP requests in workflows.
"""

import logging
import time
from typing import Dict, Any

import httpx

from backend.services.agent_builder.domain.workflow.value_objects import ExecutionContext
from backend.services.agent_builder.domain.workflow.entities import NodeEntity
from backend.services.agent_builder.infrastructure.execution.base_handler import (
    BaseNodeHandler, NodeExecutionResult
)
from backend.services.agent_builder.infrastructure.execution.node_handler_registry import register_handler

logger = logging.getLogger(__name__)


@register_handler
class HTTPNodeHandler(BaseNodeHandler):
    """Handler for HTTP Request nodes."""
    
    @property
    def node_type(self) -> str:
        return "http_request"
    
    async def validate(self, node: NodeEntity) -> tuple[bool, list[str]]:
        """Validate HTTP node configuration."""
        errors = []
        config = node.config
        
        url = config.url or config.extra.get("url", "")
        if not url:
            errors.append(f"HTTP node '{node.id}' missing URL")
        
        method = config.method or config.extra.get("method", "GET")
        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        if method.upper() not in valid_methods:
            errors.append(f"Invalid HTTP method: {method}")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute HTTP request."""
        start_time = time.time()
        
        try:
            config = node.config
            
            # Get request config
            url = config.url or config.extra.get("url", "")
            method = (config.method or config.extra.get("method", "GET")).upper()
            headers = dict(config.headers) if config.headers else {}
            headers.update(config.extra.get("headers", {}))
            
            timeout = config.timeout_seconds or config.extra.get("timeout", 30)
            
            # Get body
            body = config.extra.get("body") or input_data.get("body")
            
            # Resolve variables
            if "{{" in url:
                url = self.resolve_variables(url, context)
            
            if body and isinstance(body, str) and "{{" in body:
                body = self.resolve_variables(body, context)
            
            logger.info(f"HTTP {method} {url}")
            
            # Make request
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method in ["POST", "PUT", "PATCH"]:
                    if isinstance(body, dict):
                        response = await client.request(
                            method=method,
                            url=url,
                            headers=headers,
                            json=body,
                        )
                    else:
                        response = await client.request(
                            method=method,
                            url=url,
                            headers=headers,
                            content=body,
                        )
                else:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=input_data.get("params"),
                    )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            output = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_data,
                "success": 200 <= response.status_code < 300,
            }
            
            return NodeExecutionResult(
                success=output["success"],
                output=output,
                duration_ms=duration_ms,
                metadata={"url": url, "method": method, "status_code": response.status_code},
            )
            
        except httpx.TimeoutException:
            duration_ms = int((time.time() - start_time) * 1000)
            return NodeExecutionResult(
                success=False,
                output={},
                error_message="Request timed out",
                error_code="HTTP_TIMEOUT",
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"HTTP request failed: {e}", exc_info=True)
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="HTTP_ERROR",
                duration_ms=duration_ms,
            )
