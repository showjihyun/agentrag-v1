"""
Code Node Handler

Handles code execution in workflows.
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

logger = logging.getLogger(__name__)


@register_handler
class CodeNodeHandler(BaseNodeHandler):
    """Handler for Code nodes."""
    
    @property
    def node_type(self) -> str:
        return "code"
    
    async def validate(self, node: NodeEntity) -> tuple[bool, list[str]]:
        """Validate code node configuration."""
        errors = []
        config = node.config
        
        code = config.code or config.extra.get("code", "")
        if not code:
            errors.append(f"Code node '{node.id}' has no code")
        
        language = config.language or config.extra.get("language", "python")
        if language not in ["python", "javascript"]:
            errors.append(f"Unsupported language: {language}")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute code securely."""
        start_time = time.time()
        
        try:
            config = node.config
            code = config.code or config.extra.get("code", "")
            language = config.language or config.extra.get("language", "python")
            
            if language == "python":
                result = await self._execute_python(code, input_data, context)
            else:
                result = {"error": f"Language {language} not yet supported"}
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            return NodeExecutionResult(
                success=True,
                output=result if isinstance(result, dict) else {"output": result},
                duration_ms=duration_ms,
                metadata={"language": language},
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Code execution failed: {e}", exc_info=True)
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="CODE_EXECUTION_ERROR",
                duration_ms=duration_ms,
            )
    
    async def _execute_python(
        self,
        code: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> Any:
        """Execute Python code securely."""
        from backend.services.agent_builder.block_executor_secure import get_block_executor
        
        executor = get_block_executor(use_docker=False)
        return executor.execute_logic_block(
            code=code,
            input_data=input_data,
            context={"vars": context.variables, "nodes": context.node_results},
        )
