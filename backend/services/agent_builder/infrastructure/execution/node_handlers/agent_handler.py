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
from backend.core.execution_logging import get_execution_logger

logger = logging.getLogger(__name__)
exec_logger = get_execution_logger(__name__)


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
        
        # Agent ID is optional if inline LLM configuration is provided
        if not agent_id:
            # Check for inline LLM configuration
            llm_config = config.extra.get("parameters") or config.extra.get("config") or {}
            if not llm_config.get("provider") and not llm_config.get("model"):
                # 🔧 TEMPORARY FIX: Auto-add default LLM config
                exec_logger.warning(
                    f"⚠️  Agent 노드에 LLM 설정이 없어 기본값 적용 / No LLM config found, applying defaults",
                    node_id=str(node.id),
                    node_name=node.name
                )
                
                # Set default LLM configuration
                if "config" not in config.extra:
                    config.extra["config"] = {}
                
                config.extra["config"]["provider"] = "ollama"
                config.extra["config"]["model"] = "llama3.3:70b"
                config.extra["config"]["temperature"] = 0.7
                config.extra["config"]["max_tokens"] = 1000
                
                exec_logger.info(
                    f"✅ 기본 LLM 설정 적용됨 / Default LLM config applied: ollama/llama3.3:70b",
                    node_id=str(node.id)
                )
        
        return True, []
    
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
            query = input_data.get("query") or input_data.get("input") or input_data.get("user_query") or ""
            if isinstance(query, dict):
                query = query.get("query", str(query))
            
            # Resolve variables in query
            if "{{" in str(query):
                query = self.resolve_variables(str(query), context)
            
            exec_logger.info(
                f"Agent 노드 실행 / Executing agent node",
                node_id=str(node.id),
                node_name=node.name or "Unnamed",
                agent_id=agent_id or "inline",
                query_length=len(str(query)),
                query_preview=str(query)[:100]
            )
            
            # If no agent_id, use inline LLM configuration
            if not agent_id:
                exec_logger.info(
                    f"Inline LLM 사용 / Using inline LLM configuration",
                    node_id=str(node.id)
                )
                result = await self._execute_inline_llm(node, query, input_data, context)
                duration_ms = int((time.time() - start_time) * 1000)
                
                exec_logger.info(
                    f"Inline LLM 완료 / Inline LLM completed",
                    node_id=str(node.id),
                    duration_ms=duration_ms,
                    response_length=len(result.get("response", ""))
                )
                
                return NodeExecutionResult(
                    success=True,
                    output=result,
                    duration_ms=duration_ms,
                    metadata={
                        "inline_llm": True,
                    },
                )
            
            exec_logger.info(
                f"Agent 실행 중 / Executing agent",
                agent_id=agent_id,
                node_id=str(node.id)
            )
            
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
                
                exec_logger.info(
                    f"Agent 실행 완료 / Agent execution completed",
                    agent_id=agent_id,
                    node_id=str(node.id),
                    status=result.status,
                    duration_ms=duration_ms,
                    tokens_used=result.execution_context.get("tokens_used", 0)
                )
                
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
            
            exec_logger.error(
                f"Agent 실행 실패 / Agent execution failed: {e}",
                error_type=type(e).__name__,
                node_id=str(node.id),
                node_name=node.name or "Unnamed",
                agent_id=agent_id if 'agent_id' in locals() else "unknown"
            )
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="AGENT_EXECUTION_ERROR",
                duration_ms=duration_ms,
            )
    
    async def _execute_inline_llm(
        self,
        node: NodeEntity,
        query: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute LLM with inline configuration."""
        from backend.services.llm_service import LLMService
        
        # Get LLM configuration from node
        llm_config = node.config.extra.get("parameters") or node.config.extra.get("config") or {}
        
        provider = llm_config.get("provider", "ollama")
        model = llm_config.get("model", "llama3.3:70b")
        system_prompt = llm_config.get("system_prompt", "You are a helpful AI assistant.")
        temperature = llm_config.get("temperature", 0.7)
        max_tokens = llm_config.get("max_tokens", 1000)
        
        logger.info(f"Using inline LLM: {provider}/{model}")
        
        # Create LLM service
        llm_service = LLMService()
        
        # Execute LLM
        response = await llm_service.generate(
            prompt=query,
            system_prompt=system_prompt,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return {
            "response": response.get("content", ""),
            "model": model,
            "provider": provider,
            "tokens_used": response.get("tokens_used", 0),
        }


@register_handler
class AIAgentNodeHandler(AgentNodeHandler):
    """Handler for AI Agent nodes (alias for agent)."""
    
    @property
    def node_type(self) -> str:
        return "ai_agent"
