"""Base Tool class for tool integrations.

This module provides the abstract base class for all tool integrations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails."""
    
    def __init__(
        self,
        message: str,
        tool_id: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        Initialize ToolExecutionError.
        
        Args:
            message: Error message
            tool_id: Tool identifier
            status_code: HTTP status code (if applicable)
            response_data: Response data from tool
            original_error: Original exception
        """
        self.message = message
        self.tool_id = tool_id
        self.status_code = status_code
        self.response_data = response_data
        self.original_error = original_error
        super().__init__(self.message)


@dataclass
class ParamConfig:
    """Configuration for a tool parameter."""
    
    type: str  # "string", "number", "boolean", "object", "array", "select", "chat", "text"
    description: str
    required: bool = False
    default: Any = None
    enum: Optional[List[Any]] = None
    options: Optional[List[Dict[str, str]]] = None  # For select type: [{"label": "...", "value": "..."}]
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    items: Optional[Dict[str, Any]] = None  # For array types
    properties: Optional[Dict[str, Any]] = None  # For object types
    display_name: Optional[str] = None  # Display name for UI


@dataclass
class OutputConfig:
    """Configuration for a tool output."""
    
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    items: Optional[Dict[str, Any]] = None  # For array types
    properties: Optional[Dict[str, Any]] = None  # For object types


@dataclass
class OAuthConfig:
    """OAuth configuration for a tool."""
    
    auth_url: str
    token_url: str
    scopes: List[str]
    client_id_env: str  # Environment variable name for client ID
    client_secret_env: str  # Environment variable name for client secret


@dataclass
class RequestConfig:
    """HTTP request configuration for a tool."""
    
    method: str  # "GET", "POST", "PUT", "DELETE", "PATCH"
    url: str  # Can include {{param}} placeholders
    headers: Dict[str, str] = field(default_factory=dict)
    body_template: Optional[Dict[str, Any]] = None
    query_params: Optional[Dict[str, str]] = None
    timeout: int = 30


@dataclass
class ToolConfig:
    """Complete tool configuration."""
    
    id: str
    name: str
    description: str
    category: str  # "ai", "communication", "productivity", "data", "search"
    params: Dict[str, ParamConfig]
    outputs: Dict[str, OutputConfig]
    request: Optional[RequestConfig] = None
    oauth: Optional[OAuthConfig] = None
    api_key_env: Optional[str] = None  # Environment variable for API key
    transform_response: Optional[Callable] = None
    error_extractor: Optional[Callable] = None
    icon: str = "tool"
    bg_color: str = "#10B981"
    docs_link: Optional[str] = None


class BaseTool(ABC):
    """
    Abstract base class for all tool integrations.
    
    Tools can be executed as part of workflow blocks and provide
    integrations with external services and APIs.
    """
    
    def __init__(self, config: ToolConfig):
        """
        Initialize BaseTool.
        
        Args:
            config: Tool configuration
        """
        self.config = config
        self.execution_history: List[Dict[str, Any]] = []
    
    @abstractmethod
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            params: Tool parameters
            credentials: Authentication credentials (API keys, OAuth tokens)
            
        Returns:
            Dict containing tool outputs
            
        Raises:
            ToolExecutionError: If execution fails
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate tool parameters against schema.
        
        Args:
            params: Parameters to validate
            
        Returns:
            True if valid
            
        Raises:
            ToolExecutionError: If validation fails
        """
        # Apply default values for missing parameters
        for param_name, param_config in self.config.params.items():
            if param_name not in params and param_config.default is not None:
                params[param_name] = param_config.default
        
        # Check required parameters
        missing_params = []
        for param_name, param_config in self.config.params.items():
            if param_config.required and param_name not in params:
                missing_params.append(param_name)
        
        if missing_params:
            raise ToolExecutionError(
                f"Missing required parameters: {', '.join(missing_params)}",
                tool_id=self.config.id
            )
        
        # Validate enum values
        for param_name, param_value in params.items():
            if param_name in self.config.params:
                param_config = self.config.params[param_name]
                if param_config.enum and param_value not in param_config.enum:
                    raise ToolExecutionError(
                        f"Invalid value for {param_name}: {param_value}. "
                        f"Must be one of: {', '.join(map(str, param_config.enum))}",
                        tool_id=self.config.id
                    )
        
        return True
    
    async def execute_with_error_handling(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute tool with error handling and logging.
        
        Args:
            params: Tool parameters
            credentials: Authentication credentials
            
        Returns:
            Dict containing:
                - success: Boolean indicating success
                - outputs: Tool outputs (if successful)
                - error: Error message (if failed)
                - duration_ms: Execution duration in milliseconds
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate parameters
            self.validate_params(params)
            
            # Execute tool
            logger.info(f"Executing tool {self.config.id}")
            
            outputs = await self.execute(params, credentials)
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Record execution
            execution_record = {
                "timestamp": start_time.isoformat(),
                "success": True,
                "duration_ms": duration_ms,
                "params": params,
                "outputs": outputs,
            }
            self.execution_history.append(execution_record)
            
            logger.info(
                f"Tool {self.config.id} executed successfully in {duration_ms}ms"
            )
            
            return {
                "success": True,
                "outputs": outputs,
                "duration_ms": duration_ms,
            }
            
        except ToolExecutionError as e:
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error(f"Tool {self.config.id} execution failed: {e.message}")
            
            # Record failure
            execution_record = {
                "timestamp": start_time.isoformat(),
                "success": False,
                "duration_ms": duration_ms,
                "error": e.message,
                "status_code": e.status_code,
            }
            self.execution_history.append(execution_record)
            
            return {
                "success": False,
                "error": e.message,
                "status_code": e.status_code,
                "duration_ms": duration_ms,
            }
            
        except Exception as e:
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            logger.error(
                f"Tool {self.config.id} unexpected error: {str(e)}",
                exc_info=True
            )
            
            # Record failure
            execution_record = {
                "timestamp": start_time.isoformat(),
                "success": False,
                "duration_ms": duration_ms,
                "error": str(e),
            }
            self.execution_history.append(execution_record)
            
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "duration_ms": duration_ms,
            }
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get execution history for this tool."""
        return self.execution_history
    
    def clear_execution_history(self):
        """Clear execution history."""
        self.execution_history.clear()
    
    def __repr__(self) -> str:
        """String representation of tool."""
        return f"<{self.__class__.__name__} id={self.config.id}>"
