"""
Agent Node Handler

Handles execution of AI Agent nodes in workflows.
"""

import logging
import time
from typing import Dict, Any

from backend.services.agent_builder.domain.workflow.value_objects import ExecutionContext
from backend.services.agent_builder.domain.workflow.entities import NodeEntity
from backend.services.agent_builder.infrastructure.execution.base_handler import (
    BaseNodeHandler, NodeExecutionResult
)
from backend.services.agent_builder.infrastructure.execution.node_handler_registry import register_handler
from backend.db.session_utils import get_db_session

logger = logging.getLogger(__name__)


@register_handler
class AgentNodeHandler(BaseNodeHandler):
    """Handler for Agent/AI Agent nodes."""
    
    @property
    def node_type(self) -> str:
        return "agent"
    
    async def validate(self, node: NodeEntity) -> tuple[bool, list[str]]:
        """Validate agent node configuration."""
        errors = []
        config = node.config
        
        agent_id = config.agent_id or config.extra.get("agentId")
        if not agent_id:
            errors.append(f"Agent node '{node.id}' missing agentId")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute agent node."""
        start_time = time.time()
        
        try:
            config = node.config
            agent_id = config.agent_id or config.extra.get("agentId")
            
            # Get query from input
            query = input_data.get("query") or input_data.get("input") or ""
            if isinstance(query, dict):
                query = query.get("query", str(query))
            
            # Resolve variables in query
            if "{{" in str(query):
                query = self.resolve_variables(str(query), context)
            
            logger.info(f"Executing agent {agent_id} with query: {query[:100]}...")
            
            # Import and execute agent
            from backend.services.agent_builder.agent_executor import AgentExecutor
            
            # Get DB session with proper cleanup
            with get_db_session() as db:
                executor = AgentExecutor(db)
                result = await executor.execute_agent(
                    agent_id=agent_id,
                    user_id=context.user_id,
                    input_data={"query": query, **input_data},
                    session_id=context.execution_id,
                )
                
                duration_ms = int((time.time() - start_time) * 1000)
                
                output = {
                    "response": result.output_data.get("response", ""),
                    "execution_id": str(result.id),
                    "status": result.status,
                }
                
                return NodeExecutionResult(
                    success=result.status == "completed",
                    output=output,
                    duration_ms=duration_ms,
                    metadata={
                        "agent_id": agent_id,
                        "tokens_used": result.execution_context.get("tokens_used", 0),
                    },
                )
                
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="AGENT_EXECUTION_ERROR",
                duration_ms=duration_ms,
            )


@register_handler
class AIAgentNodeHandler(AgentNodeHandler):
    """Handler for AI Agent nodes (alias for agent)."""
    
    @property
    def node_type(self) -> str:
        return "ai_agent"
