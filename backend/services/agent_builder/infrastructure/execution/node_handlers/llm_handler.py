"""
LLM Node Handler

Handles direct LLM calls in workflows.
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
class LLMNodeHandler(BaseNodeHandler):
    """Handler for LLM nodes."""
    
    @property
    def node_type(self) -> str:
        return "llm"
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute LLM call."""
        start_time = time.time()
        
        try:
            config = node.config
            
            # Get LLM settings
            provider = config.llm_provider or config.extra.get("llm_provider", "ollama")
            model = config.llm_model or config.extra.get("llm_model", "llama3.1")
            temperature = config.temperature
            max_tokens = config.max_tokens
            
            # Get prompt
            prompt_template = config.prompt_template or config.extra.get("prompt_template", "")
            system_prompt = config.system_prompt or config.extra.get("system_prompt", "")
            
            # Get input text
            input_text = input_data.get("input") or input_data.get("query") or ""
            if isinstance(input_text, dict):
                input_text = input_text.get("text", str(input_text))
            
            # Resolve variables
            if prompt_template and "{{" in prompt_template:
                prompt_template = self.resolve_variables(prompt_template, context)
            
            # Build final prompt
            if prompt_template:
                prompt = prompt_template.replace("{input}", str(input_text))
            else:
                prompt = str(input_text)
            
            logger.info(f"Executing LLM call: {provider}/{model}")
            
            # Call LLM
            from backend.services.llm_manager import LLMManager
            
            llm_manager = LLMManager()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await llm_manager.generate(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            output = {
                "response": response if isinstance(response, str) else str(response),
                "model": model,
                "provider": provider,
            }
            
            return NodeExecutionResult(
                success=True,
                output=output,
                duration_ms=duration_ms,
                metadata={
                    "model": model,
                    "provider": provider,
                    "prompt_length": len(prompt),
                },
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"LLM execution failed: {e}", exc_info=True)
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="LLM_EXECUTION_ERROR",
                duration_ms=duration_ms,
            )
