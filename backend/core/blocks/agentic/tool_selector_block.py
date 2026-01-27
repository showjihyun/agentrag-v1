"""
Tool Selector Block - Dynamic Tool Selection

Implements intelligent tool selection based on task requirements.
Agents can dynamically choose the best tools for each subtask.

Key Features:
- Automatic tool capability analysis
- Context-aware tool selection
- Tool combination strategies
- Fallback mechanisms
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from backend.services.llm_manager import LLMManager

logger = logging.getLogger(__name__)


class Tool:
    """Represents a tool with its capabilities."""
    
    def __init__(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        executor: Callable,
        cost: float = 1.0,
        reliability: float = 0.9,
    ):
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.executor = executor
        self.cost = cost
        self.reliability = reliability
        self.usage_count = 0
        self.success_count = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.usage_count == 0:
            return self.reliability
        return self.success_count / self.usage_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "cost": self.cost,
            "reliability": self.reliability,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
        }


class ToolSelectorBlock:
    """
    Tool Selector Block for dynamic tool selection.
    
    Analyzes task requirements and selects the most appropriate
    tools from available options.
    """
    
    def __init__(
        self,
        llm_manager: LLMManager,
        enable_learning: bool = True,
        max_tools_per_task: int = 3,
    ):
        """
        Initialize Tool Selector Block.
        
        Args:
            llm_manager: LLM manager for tool selection
            enable_learning: Learn from tool usage patterns
            max_tools_per_task: Maximum tools to select per task
        """
        self.llm_manager = llm_manager
        self.enable_learning = enable_learning
        self.max_tools_per_task = max_tools_per_task
        
        self.available_tools: Dict[str, Tool] = {}
        self.selection_history: List[Dict[str, Any]] = []

    
    def register_tool(self, tool: Tool):
        """Register a tool for selection."""
        self.available_tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    async def select_tools(
        self,
        task: str,
        context: Dict[str, Any],
        required_capabilities: List[str] = None,
    ) -> List[Tool]:
        """
        Select best tools for the task.
        
        Args:
            task: Task description
            context: Task context
            required_capabilities: Required capabilities (optional)
            
        Returns:
            List of selected Tool objects
        """
        logger.info(f"Selecting tools for task: {task}")
        
        # Filter tools by required capabilities
        candidate_tools = self._filter_by_capabilities(required_capabilities)
        
        if not candidate_tools:
            logger.warning("No tools match required capabilities")
            candidate_tools = list(self.available_tools.values())
        
        # Use LLM to select best tools
        selected_tools = await self._llm_select_tools(
            task=task,
            context=context,
            candidates=candidate_tools,
        )
        
        # Record selection
        self.selection_history.append({
            "task": task,
            "selected_tools": [t.name for t in selected_tools],
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        return selected_tools
    
    async def execute_with_tools(
        self,
        task: str,
        context: Dict[str, Any],
        tools: List[Tool] = None,
    ) -> Dict[str, Any]:
        """
        Execute task with selected tools.
        
        Args:
            task: Task to execute
            context: Execution context
            tools: Pre-selected tools (optional)
            
        Returns:
            Execution results
        """
        # Select tools if not provided
        if tools is None:
            tools = await self.select_tools(task, context)
        
        results = []
        errors = []
        
        for tool in tools:
            tool.usage_count += 1
            
            try:
                logger.info(f"Executing tool: {tool.name}")
                result = await tool.executor(task, context)
                
                tool.success_count += 1
                results.append({
                    "tool": tool.name,
                    "success": True,
                    "result": result,
                })
                
            except Exception as e:
                logger.error(f"Tool {tool.name} failed: {e}", exc_info=True)
                errors.append({
                    "tool": tool.name,
                    "error": str(e),
                })
        
        return {
            "success": len(results) > 0,
            "results": results,
            "errors": errors,
            "tools_used": [t.name for t in tools],
        }
    
    async def _llm_select_tools(
        self,
        task: str,
        context: Dict[str, Any],
        candidates: List[Tool],
    ) -> List[Tool]:
        """Use LLM to select best tools."""
        tools_description = "\n".join([
            f"- {t.name}: {t.description} (success rate: {t.success_rate:.2f}, cost: {t.cost})"
            for t in candidates
        ])
        
        selection_prompt = f"""Select the best tools for this task.

Task: {task}

Context: {context}

Available Tools:
{tools_description}

Select up to {self.max_tools_per_task} tools that are most suitable.
Consider:
1. Tool capabilities match task requirements
2. Success rate and reliability
3. Cost efficiency
4. Tool combinations that work well together

Respond with JSON:
{{
    "selected_tools": ["tool1", "tool2"],
    "reasoning": "Why these tools were selected"
}}"""
        
        try:
            response = await self.llm_manager.generate(
                prompt=selection_prompt,
                temperature=0.3,
            )
            
            import json
            selection = json.loads(response)
            
            selected_names = selection.get("selected_tools", [])
            selected_tools = [
                t for t in candidates 
                if t.name in selected_names
            ][:self.max_tools_per_task]
            
            logger.info(f"Selected tools: {[t.name for t in selected_tools]}")
            logger.info(f"Reasoning: {selection.get('reasoning', 'N/A')}")
            
            return selected_tools if selected_tools else candidates[:1]
            
        except Exception as e:
            logger.error(f"Error in tool selection: {e}", exc_info=True)
            # Fallback: select top tool by success rate
            sorted_tools = sorted(candidates, key=lambda t: t.success_rate, reverse=True)
            return sorted_tools[:1]
    
    def _filter_by_capabilities(
        self,
        required_capabilities: List[str] = None,
    ) -> List[Tool]:
        """Filter tools by required capabilities."""
        if not required_capabilities:
            return list(self.available_tools.values())
        
        matching_tools = []
        for tool in self.available_tools.values():
            if any(cap in tool.capabilities for cap in required_capabilities):
                matching_tools.append(tool)
        
        return matching_tools
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get statistics about tool usage."""
        stats = {
            "total_tools": len(self.available_tools),
            "total_selections": len(self.selection_history),
            "tools": {}
        }
        
        for name, tool in self.available_tools.items():
            stats["tools"][name] = {
                "usage_count": tool.usage_count,
                "success_count": tool.success_count,
                "success_rate": tool.success_rate,
                "cost": tool.cost,
            }
        
        return stats
