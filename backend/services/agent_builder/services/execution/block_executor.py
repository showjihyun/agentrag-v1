"""
Block Executor for executing different types of blocks.

This module provides execution logic for LLM, Tool, Logic, and Composite blocks.
"""

import logging
import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.services.llm_manager import LLMManager
from backend.services.agent_builder.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class BlockExecutor:
    """
    Executes individual blocks based on their type.
    
    Supports:
    - LLM blocks: Execute LLM calls with prompt templates
    - Tool blocks: Execute tool invocations
    - Logic blocks: Execute custom Python code in restricted environment
    - Composite blocks: Execute nested workflows
    """
    
    def __init__(
        self,
        db: Session,
        llm_manager: LLMManager,
        tool_registry: ToolRegistry,
    ):
        """
        Initialize BlockExecutor.
        
        Args:
            db: Database session
            llm_manager: LLM manager for model interactions
            tool_registry: Tool registry for tool access
        """
        self.db = db
        self.llm_manager = llm_manager
        self.tool_registry = tool_registry
        
        logger.info("BlockExecutor initialized")
    
    async def execute_block(
        self,
        block: Any,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a block based on its type.
        
        Args:
            block: Block model instance
            input_data: Input data for block
            context: Execution context
            
        Returns:
            Block execution result
            
        Raises:
            ValueError: If block type is unknown
        """
        block_type = block.block_type
        
        if block_type == "llm":
            return await self._execute_llm_block(block, input_data, context)
        elif block_type == "tool":
            return await self._execute_tool_block(block, input_data, context)
        elif block_type == "logic":
            return await self._execute_logic_block(block, input_data, context)
        elif block_type == "composite":
            return await self._execute_composite_block(block, input_data, context)
        else:
            raise ValueError(f"Unknown block type: {block_type}")
    
    async def _execute_llm_block(
        self,
        block: Any,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute LLM block.
        
        Args:
            block: Block model instance
            input_data: Input data
            context: Execution context
            
        Returns:
            LLM execution result with output
        """
        try:
            # Get configuration
            config = block.configuration or {}
            prompt_template = config.get("prompt_template", "")
            
            # Substitute variables in prompt
            prompt = self._substitute_variables(prompt_template, input_data, context)
            
            # Get LLM parameters
            temperature = config.get("temperature", 0.7)
            max_tokens = config.get("max_tokens")
            
            # Call LLM
            messages = [{"role": "user", "content": prompt}]
            
            # Add system message if provided
            system_message = config.get("system_message")
            if system_message:
                messages.insert(0, {"role": "system", "content": system_message})
            
            response = await self.llm_manager.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            logger.info(f"LLM block {block.id} executed successfully")
            
            return {
                "output": response,
                "block_id": block.id,
                "block_type": "llm"
            }
            
        except Exception as e:
            logger.error(f"LLM block execution failed: {e}")
            raise
    
    async def _execute_tool_block(
        self,
        block: Any,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute tool block.
        
        Args:
            block: Block model instance
            input_data: Input data
            context: Execution context
            
        Returns:
            Tool execution result
        """
        try:
            # Get configuration
            config = block.configuration or {}
            tool_id = config.get("tool_id")
            
            if not tool_id:
                raise ValueError("Tool block missing tool_id in configuration")
            
            # Get tool from registry
            tool = self.tool_registry.get_tool(tool_id)
            
            # Prepare tool input
            tool_input = self._map_tool_input(tool, input_data, config)
            
            # Execute tool
            result = await tool.arun(tool_input)
            
            logger.info(f"Tool block {block.id} executed successfully")
            
            return {
                "output": result,
                "block_id": block.id,
                "block_type": "tool",
                "tool_id": tool_id
            }
            
        except Exception as e:
            logger.error(f"Tool block execution failed: {e}")
            raise
    
    async def _execute_logic_block(
        self,
        block: Any,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute logic block (custom Python code).
        
        Args:
            block: Block model instance
            input_data: Input data
            context: Execution context
            
        Returns:
            Logic execution result
        """
        try:
            # Get implementation code
            code = block.implementation
            
            if not code:
                raise ValueError("Logic block missing implementation code")
            
            # Create safe execution environment
            # Only allow safe built-in functions
            exec_globals = {
                "__builtins__": {
                    # Type constructors
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    # Iteration
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "sorted": sorted,
                    "reversed": reversed,
                    # Utilities
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "any": any,
                    "all": all,
                    # JSON for data manipulation
                    "json": json,
                }
            }
            
            # Create local execution context
            exec_locals = {
                "input": input_data,
                "context": context,
                "output": None
            }
            
            # Execute code
            exec(code, exec_globals, exec_locals)
            
            # Get output
            output = exec_locals.get("output")
            
            logger.info(f"Logic block {block.id} executed successfully")
            
            return {
                "output": output,
                "block_id": block.id,
                "block_type": "logic"
            }
            
        except Exception as e:
            logger.error(f"Logic block execution failed: {e}")
            raise
    
    async def _execute_composite_block(
        self,
        block: Any,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute composite block (nested workflow).
        
        Args:
            block: Block model instance
            input_data: Input data
            context: Execution context
            
        Returns:
            Composite block execution result
        """
        try:
            # Get workflow definition from block configuration
            config = block.configuration or {}
            workflow_definition = config.get("workflow_definition")
            
            if not workflow_definition:
                raise ValueError("Composite block missing workflow_definition")
            
            # Import WorkflowExecutor (lazy import to avoid circular dependency)
            from backend.services.agent_builder.workflow_executor import WorkflowExecutor, ExecutionContext
            from backend.services.llm_manager import LLMManager
            from backend.memory.manager import MemoryManager
            from backend.services.agent_builder.variable_resolver import VariableResolver
            from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
            from backend.services.agent_builder.tool_registry import ToolRegistry
            
            # Initialize services for workflow execution
            llm_manager = LLMManager()
            memory_manager = MemoryManager()
            variable_resolver = VariableResolver(self.db)
            kb_service = KnowledgebaseService(self.db)
            tool_registry = ToolRegistry()
            
            # Create workflow executor
            workflow_executor = WorkflowExecutor(
                db=self.db,
                llm_manager=llm_manager,
                memory_manager=memory_manager,
                variable_resolver=variable_resolver,
                knowledgebase_service=kb_service,
                tool_registry=tool_registry
            )
            
            # Create nested execution context
            nested_context = ExecutionContext(
                execution_id=f"{context.get('execution_id', 'unknown')}_composite_{block.id}",
                user_id=context.get('user_id'),
                agent_id=context.get('agent_id'),
                workflow_id=None,
                session_id=context.get('session_id'),
                input_data=input_data,
                variables=context.get('variables', {}),
                knowledgebases=context.get('knowledgebases', [])
            )
            
            # Execute nested workflow
            result = await workflow_executor.execute_workflow(
                workflow_definition=workflow_definition,
                context=nested_context
            )
            
            logger.info(f"Composite block {block.id} executed successfully")
            
            return {
                "output": result.get("output"),
                "block_id": block.id,
                "block_type": "composite",
                "nested_execution_id": nested_context.execution_id,
                "steps": result.get("steps", [])
            }
            
        except Exception as e:
            logger.error(f"Composite block execution failed: {e}")
            raise
    
    def _substitute_variables(
        self,
        template: str,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Substitute variables in template string.
        
        Args:
            template: Template string with ${variable} placeholders
            input_data: Input data
            context: Execution context
            
        Returns:
            String with variables substituted
        """
        import re
        
        # Combine input and context for variable resolution
        variables = {
            **input_data,
            **context.get("variables", {})
        }
        
        # Find all variable references: ${variable_name}
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            # Support nested access like ${input.query}
            parts = var_name.split(".")
            value = variables
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part, match.group(0))
                else:
                    return match.group(0)
            return str(value)
        
        result = re.sub(pattern, replace_var, template)
        
        return result
    
    def _map_tool_input(
        self,
        tool: Any,
        input_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map input data to tool input format.
        
        Args:
            tool: Tool instance
            input_data: Input data
            config: Block configuration
            
        Returns:
            Mapped tool input
        """
        # Get input mapping from config
        input_mapping = config.get("input_mapping", {})
        
        tool_input = {}
        
        # Map inputs based on configuration
        for tool_key, input_key in input_mapping.items():
            if input_key in input_data:
                tool_input[tool_key] = input_data[input_key]
        
        # If no mapping, use input data directly
        if not tool_input:
            tool_input = input_data
        
        return tool_input
