"""
Helper for executing tools within agent workflows.
"""
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import AgentTool
from backend.services.tools.tool_executor_registry import ToolExecutorRegistry

logger = logging.getLogger(__name__)


class ToolExecutionHelper:
    """Helper for executing tools in agent workflows."""
    
    def __init__(self, db: Session):
        self.db = db
        self.registry = ToolExecutorRegistry()
    
    async def execute_agent_tool(
        self,
        agent_id: str,
        tool_id: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a tool configured for an agent.
        
        Args:
            agent_id: Agent ID
            tool_id: Tool ID
            parameters: Execution parameters
            
        Returns:
            Execution result
        """
        # Get agent tool configuration
        agent_tool = self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent_id,
            AgentTool.tool_id == tool_id
        ).first()
        
        if not agent_tool:
            raise ValueError(f"Tool {tool_id} not configured for agent {agent_id}")
        
        # Get tool name from tool record
        from backend.db.models.agent_builder import Tool
        tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
        
        if not tool:
            raise ValueError(f"Tool {tool_id} not found")
        
        # Execute tool
        try:
            result = await self.registry.execute_tool(
                tool_name=tool.name,
                parameters=parameters,
                config=agent_tool.configuration or {}
            )
            
            return {
                "success": True,
                "tool_id": tool_id,
                "tool_name": tool.name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed: {tool.name}", exc_info=True)
            return {
                "success": False,
                "tool_id": tool_id,
                "tool_name": tool.name,
                "error": str(e)
            }
    
    async def execute_tools_parallel(
        self,
        agent_id: str,
        tool_executions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tools in parallel.
        
        Args:
            agent_id: Agent ID
            tool_executions: List of tool execution configs
                [{"tool_id": "...", "parameters": {...}}, ...]
                
        Returns:
            List of execution results
        """
        import asyncio
        
        tasks = [
            self.execute_agent_tool(
                agent_id=agent_id,
                tool_id=exec_config["tool_id"],
                parameters=exec_config["parameters"]
            )
            for exec_config in tool_executions
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "tool_id": tool_executions[i]["tool_id"],
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def validate_tool_config(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate tool configuration.
        
        Args:
            tool_name: Tool name
            parameters: Execution parameters
            config: Tool configuration
            
        Returns:
            Validation result
        """
        try:
            executor = self.registry.get_executor(tool_name)
            if not executor:
                return {
                    "valid": False,
                    "error": f"Tool executor not found: {tool_name}"
                }
            
            is_valid = await executor.validate_parameters(parameters)
            
            return {
                "valid": is_valid,
                "tool_name": tool_name,
                "message": "Valid" if is_valid else "Invalid parameters"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "tool_name": tool_name,
                "error": str(e)
            }
    
    def get_available_executors(self) -> Dict[str, List[str]]:
        """Get available tool executors by category."""
        return self.registry.list_executors()
