"""Tool executor registry for managing tool execution services."""

from typing import Dict, Optional
import logging

from .base_executor import BaseToolExecutor
from .ai import OpenAIChatExecutor, AnthropicExecutor, AIAgentExecutor
from .search import DuckDuckGoExecutor, GoogleSearchExecutor
from .developer import HTTPRequestExecutor, GitHubExecutor
from .data import DatabaseQueryExecutor
from .communication import EmailExecutor, SlackExecutor
from .productivity import CalendarExecutor, NotionExecutor
from .code import PythonCodeExecutor

logger = logging.getLogger(__name__)


class ToolExecutorRegistry:
    """Registry for tool executors."""
    
    _executors: Dict[str, BaseToolExecutor] = {}
    
    @classmethod
    def initialize(cls):
        """Initialize all tool executors."""
        executors = [
            # AI
            AIAgentExecutor(),
            OpenAIChatExecutor(),
            AnthropicExecutor(),
            
            # Search
            DuckDuckGoExecutor(),
            GoogleSearchExecutor(),
            
            # Developer
            HTTPRequestExecutor(),
            GitHubExecutor(),
            
            # Data
            DatabaseQueryExecutor(),
            
            # Communication
            EmailExecutor(),
            SlackExecutor(),
            
            # Productivity
            CalendarExecutor(),
            NotionExecutor(),
            
            # Code
            PythonCodeExecutor(),
        ]
        
        for executor in executors:
            cls._executors[executor.tool_id] = executor
            logger.info(f"Registered executor: {executor.tool_id}")
        
        logger.info(f"Initialized {len(cls._executors)} tool executors")
    
    @classmethod
    def get_executor(cls, tool_id: str) -> Optional[BaseToolExecutor]:
        """Get executor for a tool."""
        return cls._executors.get(tool_id)
    
    @classmethod
    def has_executor(cls, tool_id: str) -> bool:
        """Check if executor exists for a tool."""
        return tool_id in cls._executors
    
    @classmethod
    def list_executors(cls) -> Dict[str, BaseToolExecutor]:
        """List all registered executors."""
        return cls._executors.copy()


# Initialize on import
ToolExecutorRegistry.initialize()
