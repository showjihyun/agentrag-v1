"""Base tool executor for all tool services."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseToolExecutor(ABC):
    """Base class for tool executors."""
    
    def __init__(self, tool_id: str, tool_name: str):
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.logger = logging.getLogger(f"{__name__}.{tool_id}")
    
    @abstractmethod
    async def execute(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """
        Execute the tool with given parameters.
        
        Args:
            params: Tool parameters
            credentials: Optional credentials for authentication
            
        Returns:
            ToolExecutionResult with success status and output
        """
        pass
    
    def validate_params(self, params: Dict[str, Any], required: list) -> None:
        """Validate required parameters."""
        missing = [p for p in required if p not in params or params[p] is None]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")
    
    async def execute_with_error_handling(
        self,
        params: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> ToolExecutionResult:
        """Execute tool with error handling."""
        try:
            self.logger.info(f"Executing {self.tool_name} with params: {list(params.keys())}")
            result = await self.execute(params, credentials)
            self.logger.info(f"{self.tool_name} execution completed: success={result.success}")
            return result
        except Exception as e:
            self.logger.error(f"{self.tool_name} execution failed: {e}", exc_info=True)
            return ToolExecutionResult(
                success=False,
                output=None,
                error=str(e)
            )
