"""
Agentflow Agent Executor

Executes individual agents within an agentflow with proper context management,
data mapping, and error handling.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.orm import Session

from backend.db.models.agent_builder import Agent, AgentTool, Tool
from backend.db.models.flows import AgentflowAgent
from backend.services.agent_builder.shared.errors import ExecutionError

logger = logging.getLogger(__name__)


class AgentflowAgentExecutor:
    """
    Executes agents within an agentflow context.
    
    Handles:
    - Agent execution with proper configuration
    - Input/output data mapping
    - Context management
    - Tool execution
    - Error handling and retries
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def execute_agent(
        self,
        agentflow_agent: AgentflowAgent,
        input_data: Dict[str, Any],
        execution_context: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Execute an agent within an agentflow.
        
        Args:
            agentflow_agent: AgentflowAgent configuration
            input_data: Input data for the agent
            execution_context: Shared execution context
            user_id: User ID for API key retrieval
            
        Returns:
            Execution result with output data
        """
        start_time = datetime.utcnow()
        
        logger.info(f"Executing agent {agentflow_agent.name} (role: {agentflow_agent.role})")
        
        # Get the actual agent
        agent = self.db.query(Agent).filter(
            Agent.id == agentflow_agent.agent_id
        ).first()
        
        if not agent:
            raise ExecutionError(f"Agent {agentflow_agent.agent_id} not found")
        
        # Apply input mapping
        mapped_input = self._apply_input_mapping(
            input_data,
            agentflow_agent.input_mapping,
            execution_context,
        )
        
        # Check conditional logic
        if not self._check_conditions(agentflow_agent.conditional_logic, execution_context):
            logger.info(f"Agent {agentflow_agent.name} skipped due to conditions")
            return {
                "success": True,
                "skipped": True,
                "reason": "Conditions not met",
                "output": {},
            }
        
        # Execute with retries
        max_retries = agentflow_agent.max_retries
        timeout = agentflow_agent.timeout_seconds
        
        for attempt in range(max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self._execute_agent_internal(
                        agent=agent,
                        input_data=mapped_input,
                        execution_context=execution_context,
                        user_id=user_id,
                    ),
                    timeout=timeout,
                )
                
                # Apply output mapping
                mapped_output = self._apply_output_mapping(
                    result.get("output", {}),
                    agentflow_agent.output_mapping,
                )
                
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return {
                    "success": True,
                    "agent_id": str(agentflow_agent.id),
                    "agent_name": agentflow_agent.name,
                    "role": agentflow_agent.role,
                    "output": mapped_output,
                    "raw_output": result.get("output", {}),
                    "duration_ms": duration_ms,
                    "attempts": attempt + 1,
                    "metadata": {
                        "llm_provider": agent.llm_provider,
                        "llm_model": agent.llm_model,
                        "capabilities": agentflow_agent.capabilities,
                    },
                }
                
            except asyncio.TimeoutError:
                logger.warning(f"Agent {agentflow_agent.name} timed out (attempt {attempt + 1}/{max_retries + 1})")
                if attempt >= max_retries:
                    return {
                        "success": False,
                        "agent_id": str(agentflow_agent.id),
                        "agent_name": agentflow_agent.name,
                        "error": f"Agent execution timed out after {timeout} seconds",
                        "attempts": attempt + 1,
                    }
                await asyncio.sleep(1)  # Brief delay before retry
                
            except Exception as e:
                logger.error(f"Agent {agentflow_agent.name} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                if attempt >= max_retries:
                    return {
                        "success": False,
                        "agent_id": str(agentflow_agent.id),
                        "agent_name": agentflow_agent.name,
                        "error": str(e),
                        "attempts": attempt + 1,
                    }
                await asyncio.sleep(1)
    
    async def _execute_agent_internal(
        self,
        agent: Agent,
        input_data: Dict[str, Any],
        execution_context: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Internal agent execution logic.
        
        This uses the agent's configuration to execute with proper LLM and tools.
        """
        # Import here to avoid circular dependencies
        from backend.agents.agent_plugin_manager import AgentPluginManager
        
        # Get agent tools
        agent_tools = self.db.query(AgentTool).filter(
            AgentTool.agent_id == agent.id
        ).all()
        
        tool_configs = []
        for at in agent_tools:
            tool = self.db.query(Tool).filter(Tool.id == at.tool_id).first()
            if tool:
                tool_configs.append({
                    "tool_id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "configuration": at.configuration,
                })
        
        # Build agent configuration
        agent_config = {
            "agent_id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "llm_provider": agent.llm_provider,
            "llm_model": agent.llm_model,
            "configuration": agent.configuration,
            "tools": tool_configs,
            "context_items": agent.context_items,
            "mcp_servers": agent.mcp_servers,
        }
        
        # Get prompt template
        prompt_template = agent.configuration.get("prompt_template", "")
        if not prompt_template and agent.prompt_template_id:
            from backend.db.models.agent_builder import PromptTemplate
            pt = self.db.query(PromptTemplate).filter(
                PromptTemplate.id == agent.prompt_template_id
            ).first()
            if pt:
                prompt_template = pt.template_text
        
        # Build input message
        input_text = input_data.get("input", "")
        if isinstance(input_data, dict) and "message" in input_data:
            input_text = input_data["message"]
        
        # Execute agent using plugin manager
        plugin_manager = AgentPluginManager(self.db)
        
        try:
            result = await plugin_manager.execute_agent(
                agent_config=agent_config,
                input_text=input_text,
                context=execution_context,
                user_id=user_id,
                system_prompt=prompt_template,
            )
            
            return {
                "success": True,
                "output": {
                    "response": result.get("response", ""),
                    "metadata": result.get("metadata", {}),
                },
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            raise
    
    def _apply_input_mapping(
        self,
        input_data: Dict[str, Any],
        input_mapping: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply input mapping to transform data for the agent.
        
        Input mapping format:
        {
            "target_field": "source_field",
            "target_field2": {"from": "context.previous_agent.output"},
        }
        """
        if not input_mapping:
            return input_data
        
        mapped = {}
        
        for target_field, source_spec in input_mapping.items():
            if isinstance(source_spec, str):
                # Simple field mapping
                if source_spec in input_data:
                    mapped[target_field] = input_data[source_spec]
                elif source_spec.startswith("context."):
                    # Get from execution context
                    path = source_spec[8:].split(".")
                    value = execution_context
                    for key in path:
                        if isinstance(value, dict) and key in value:
                            value = value[key]
                        else:
                            value = None
                            break
                    if value is not None:
                        mapped[target_field] = value
            elif isinstance(source_spec, dict):
                # Complex mapping with transformations
                source = source_spec.get("from", "")
                if source.startswith("context."):
                    path = source[8:].split(".")
                    value = execution_context
                    for key in path:
                        if isinstance(value, dict) and key in value:
                            value = value[key]
                        else:
                            value = None
                            break
                    if value is not None:
                        mapped[target_field] = value
        
        # Merge with original input
        result = {**input_data, **mapped}
        
        return result
    
    def _apply_output_mapping(
        self,
        output_data: Dict[str, Any],
        output_mapping: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply output mapping to transform agent output.
        
        Output mapping format:
        {
            "target_field": "source_field",
            "target_field2": {"from": "response.data"},
        }
        """
        if not output_mapping:
            return output_data
        
        mapped = {}
        
        for target_field, source_spec in output_mapping.items():
            if isinstance(source_spec, str):
                # Simple field mapping
                if source_spec in output_data:
                    mapped[target_field] = output_data[source_spec]
            elif isinstance(source_spec, dict):
                # Complex mapping
                source = source_spec.get("from", "")
                path = source.split(".")
                value = output_data
                for key in path:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break
                if value is not None:
                    mapped[target_field] = value
        
        return mapped
    
    def _check_conditions(
        self,
        conditional_logic: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> bool:
        """
        Check if conditions are met for agent execution.
        
        Conditional logic format:
        {
            "type": "and" | "or",
            "conditions": [
                {"field": "context.previous_result", "operator": "equals", "value": "success"},
                {"field": "input.type", "operator": "contains", "value": "research"},
            ]
        }
        """
        if not conditional_logic or not conditional_logic.get("conditions"):
            return True  # No conditions means always execute
        
        conditions = conditional_logic.get("conditions", [])
        logic_type = conditional_logic.get("type", "and")
        
        results = []
        for condition in conditions:
            field = condition.get("field", "")
            operator = condition.get("operator", "equals")
            expected_value = condition.get("value")
            
            # Get actual value from context
            if field.startswith("context."):
                path = field[8:].split(".")
                actual_value = execution_context
                for key in path:
                    if isinstance(actual_value, dict) and key in actual_value:
                        actual_value = actual_value[key]
                    else:
                        actual_value = None
                        break
            else:
                actual_value = None
            
            # Evaluate condition
            if operator == "equals":
                results.append(actual_value == expected_value)
            elif operator == "not_equals":
                results.append(actual_value != expected_value)
            elif operator == "contains":
                if isinstance(actual_value, str):
                    results.append(expected_value in actual_value)
                else:
                    results.append(False)
            elif operator == "exists":
                results.append(actual_value is not None)
            else:
                results.append(False)
        
        # Combine results based on logic type
        if logic_type == "and":
            return all(results)
        elif logic_type == "or":
            return any(results)
        else:
            return True
