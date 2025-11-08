"""Tool Registry for managing tool integrations.

This registry manages 70+ tool integrations that can be used in workflow blocks.
"""

import logging
import os
from typing import Dict, List, Optional, Type, Any, Callable
from functools import wraps
import httpx

from .base import (
    BaseTool,
    ToolConfig,
    ToolExecutionError,
    ParamConfig,
    OutputConfig,
    RequestConfig,
    OAuthConfig
)
from .response_transformer import ResponseTransformer

logger = logging.getLogger(__name__)


class HTTPTool(BaseTool):
    """Generic HTTP-based tool implementation."""
    
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute HTTP request with given parameters.
        
        Args:
            params: Tool parameters
            credentials: Authentication credentials
            
        Returns:
            Transformed response data
        """
        if not self.config.request:
            raise ToolExecutionError(
                "Tool has no request configuration",
                tool_id=self.config.id
            )
        
        request_config = self.config.request
        
        # Build URL with parameter substitution
        url = self._substitute_params(request_config.url, params)
        
        # Build headers
        headers = dict(request_config.headers)
        
        # Add authentication
        if credentials:
            if "api_key" in credentials:
                # API key authentication
                if "Authorization" not in headers:
                    headers["Authorization"] = f"Bearer {credentials['api_key']}"
            elif "access_token" in credentials:
                # OAuth token
                headers["Authorization"] = f"Bearer {credentials['access_token']}"
        elif self.config.api_key_env:
            # Get API key from environment
            api_key = os.getenv(self.config.api_key_env)
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
        
        # Build query parameters
        query_params = {}
        if request_config.query_params:
            for key, value_template in request_config.query_params.items():
                query_params[key] = self._substitute_params(value_template, params)
        
        # Build request body
        body = None
        if request_config.body_template:
            body = self._substitute_params_recursive(
                request_config.body_template,
                params
            )
        
        # Make HTTP request
        try:
            async with httpx.AsyncClient(timeout=request_config.timeout) as client:
                response = await client.request(
                    method=request_config.method,
                    url=url,
                    headers=headers,
                    params=query_params,
                    json=body if body else None
                )
                
                # Check for errors
                if response.status_code >= 400:
                    error_message = self._extract_error(response)
                    raise ToolExecutionError(
                        error_message or f"HTTP {response.status_code}",
                        tool_id=self.config.id,
                        status_code=response.status_code,
                        response_data=response.json() if response.text else None
                    )
                
                # Parse response
                try:
                    response_data = response.json()
                except Exception:
                    response_data = {"text": response.text}
                
                # Transform response
                if self.config.transform_response:
                    return self.config.transform_response(response_data)
                
                return response_data
                
        except httpx.TimeoutException:
            raise ToolExecutionError(
                f"Request timeout after {request_config.timeout}s",
                tool_id=self.config.id
            )
        except httpx.RequestError as e:
            raise ToolExecutionError(
                f"Request failed: {str(e)}",
                tool_id=self.config.id,
                original_error=e
            )
    
    def _substitute_params(self, template: str, params: Dict[str, Any]) -> str:
        """Substitute {{param}} placeholders in template."""
        result = template
        for key, value in params.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result
    
    def _substitute_params_recursive(
        self,
        template: Any,
        params: Dict[str, Any]
    ) -> Any:
        """Recursively substitute parameters in nested structures."""
        if isinstance(template, str):
            return self._substitute_params(template, params)
        elif isinstance(template, dict):
            return {
                key: self._substitute_params_recursive(value, params)
                for key, value in template.items()
            }
        elif isinstance(template, list):
            return [
                self._substitute_params_recursive(item, params)
                for item in template
            ]
        else:
            return template
    
    def _extract_error(self, response: httpx.Response) -> Optional[str]:
        """Extract error message from response."""
        if self.config.error_extractor:
            try:
                response_data = response.json()
                return self.config.error_extractor(response_data)
            except Exception:
                pass
        
        # Try common error paths
        try:
            response_data = response.json()
            return ResponseTransformer.extract_error(response_data)
        except Exception:
            return response.text


class ToolRegistry:
    """
    Registry for managing tool integrations.
    
    Supports registration, lookup, and execution of 70+ tools.
    """
    
    _tools: Dict[str, ToolConfig] = {}
    _tool_instances: Dict[str, BaseTool] = {}
    
    @classmethod
    def register(
        cls,
        tool_id: str,
        name: str,
        description: str,
        category: str,
        params: Dict[str, ParamConfig],
        outputs: Dict[str, OutputConfig],
        request: Optional[RequestConfig] = None,
        oauth: Optional[OAuthConfig] = None,
        api_key_env: Optional[str] = None,
        transform_response: Optional[Callable] = None,
        error_extractor: Optional[Callable] = None,
        icon: str = "tool",
        bg_color: str = "#10B981",
        docs_link: Optional[str] = None,
        tool_class: Optional[Type[BaseTool]] = None
    ) -> Callable:
        """
        Decorator to register a tool.
        
        Args:
            tool_id: Unique tool identifier
            name: Tool display name
            description: Tool description
            category: Tool category
            params: Parameter configurations
            outputs: Output configurations
            request: HTTP request configuration
            oauth: OAuth configuration
            api_key_env: Environment variable for API key
            transform_response: Response transformation function
            error_extractor: Error extraction function
            icon: Icon name
            bg_color: Background color
            docs_link: Documentation link
            tool_class: Custom tool class (defaults to HTTPTool)
            
        Returns:
            Decorator function
        """
        def decorator(func_or_class):
            # Create tool configuration
            config = ToolConfig(
                id=tool_id,
                name=name,
                description=description,
                category=category,
                params=params,
                outputs=outputs,
                request=request,
                oauth=oauth,
                api_key_env=api_key_env,
                transform_response=transform_response,
                error_extractor=error_extractor,
                icon=icon,
                bg_color=bg_color,
                docs_link=docs_link
            )
            
            # Store configuration
            cls._tools[tool_id] = config
            
            # Create tool instance
            if tool_class:
                # Custom tool class
                tool_instance = tool_class(config)
            elif isinstance(func_or_class, type) and issubclass(func_or_class, BaseTool):
                # Decorated class
                tool_instance = func_or_class(config)
            else:
                # Use HTTPTool for HTTP-based tools
                tool_instance = HTTPTool(config)
            
            cls._tool_instances[tool_id] = tool_instance
            
            logger.info(f"Registered tool: {tool_id} ({name})")
            
            return func_or_class
        
        return decorator
    
    @classmethod
    def register_tool_config(cls, config: ToolConfig, tool_class: Optional[Type[BaseTool]] = None):
        """
        Register a tool using a ToolConfig object.
        
        Args:
            config: Tool configuration
            tool_class: Tool class (defaults to HTTPTool)
        """
        cls._tools[config.id] = config
        
        if tool_class:
            tool_instance = tool_class(config)
        else:
            tool_instance = HTTPTool(config)
        
        cls._tool_instances[config.id] = tool_instance
        
        logger.info(f"Registered tool: {config.id} ({config.name})")
    
    @classmethod
    def get_tool(cls, tool_id: str) -> Optional[BaseTool]:
        """
        Get tool instance by ID.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Tool instance or None if not found
        """
        return cls._tool_instances.get(tool_id)
    
    @classmethod
    def get_tool_config(cls, tool_id: str) -> Optional[ToolConfig]:
        """
        Get tool configuration by ID.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Tool configuration or None if not found
        """
        return cls._tools.get(tool_id)
    
    @classmethod
    def list_tools(
        cls,
        category: Optional[str] = None
    ) -> List[ToolConfig]:
        """
        List all registered tools.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of tool configurations
        """
        tools = list(cls._tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        return tools
    
    @classmethod
    def list_by_category(cls) -> Dict[str, List[ToolConfig]]:
        """
        List tools grouped by category.
        
        Returns:
            Dict mapping category to list of tool configurations
        """
        categorized = {}
        
        for tool in cls._tools.values():
            category = tool.category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(tool)
        
        return categorized
    
    @classmethod
    def get_tool_ids(cls) -> List[str]:
        """
        Get list of all registered tool IDs.
        
        Returns:
            List of tool identifiers
        """
        return list(cls._tools.keys())
    
    @classmethod
    def is_registered(cls, tool_id: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            True if registered, False otherwise
        """
        return tool_id in cls._tools
    
    @classmethod
    async def execute_tool(
        cls,
        tool_id: str,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool by ID.
        
        Args:
            tool_id: Tool identifier
            params: Tool parameters
            credentials: Authentication credentials
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
            ToolExecutionError: If execution fails
        """
        tool = cls.get_tool(tool_id)
        if not tool:
            raise ValueError(f"Tool not found: {tool_id}")
        
        return await tool.execute_with_error_handling(params, credentials)
    
    @classmethod
    def clear_registry(cls):
        """Clear all registered tools (useful for testing)."""
        cls._tools.clear()
        cls._tool_instances.clear()
        logger.info("Cleared tool registry")


# Convenience function for external use
def register_tool(
    tool_id: str,
    name: str,
    description: str,
    category: str,
    **kwargs
) -> Callable:
    """
    Convenience function to register a tool.
    
    This is an alias for ToolRegistry.register() for easier imports.
    """
    return ToolRegistry.register(
        tool_id=tool_id,
        name=name,
        description=description,
        category=category,
        **kwargs
    )
