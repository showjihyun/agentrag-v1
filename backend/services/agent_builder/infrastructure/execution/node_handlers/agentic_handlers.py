"""
Agentic Block Node Handlers

Handles execution of agentic workflow blocks (Reflection, Planning, Tool Selector, Agentic RAG).
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
from backend.core.execution_logging import get_execution_logger

logger = logging.getLogger(__name__)
exec_logger = get_execution_logger(__name__)


@register_handler
class AgenticReflectionHandler(BaseNodeHandler):
    """Handler for Agentic Reflection blocks."""
    
    @property
    def node_type(self) -> str:
        return "agentic_reflection"
    
    async def validate(self, node: NodeEntity) -> tuple[bool, list[str]]:
        """Validate reflection node configuration."""
        errors = []
        config = node.config.extra
        
        # Validate required fields
        if not config.get("input"):
            errors.append("Reflection block requires 'input' field")
        
        # Validate max_iterations
        max_iterations = config.get("max_iterations", 3)
        if not isinstance(max_iterations, int) or max_iterations < 1 or max_iterations > 10:
            errors.append("max_iterations must be between 1 and 10")
        
        # Validate quality_threshold
        quality_threshold = config.get("quality_threshold", 0.8)
        if not isinstance(quality_threshold, (int, float)) or quality_threshold < 0 or quality_threshold > 1:
            errors.append("quality_threshold must be between 0.0 and 1.0")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute reflection block."""
        start_time = time.time()
        
        # Log node start
        exec_logger.node_start(
            node_id=str(node.id),
            node_name=node.name or "Reflection Block",
            node_type="agentic_reflection"
        )
        
        try:
            from backend.core.blocks.agentic.reflection_block import ReflectionBlock
            from backend.services.llm_manager import LLMManager, LLMProvider
            
            config = node.config.extra
            
            # Get input
            input_text = config.get("input") or input_data.get("input") or input_data.get("query", "")
            if "{{" in str(input_text):
                input_text = self.resolve_variables(str(input_text), context)
            
            max_iterations = config.get("max_iterations", 3)
            quality_threshold = config.get("quality_threshold", 0.8)
            
            # Get LLM configuration from node config
            llm_provider = config.get("llm_provider")
            llm_model = config.get("llm_model")
            temperature = config.get("temperature", 0.7)
            
            exec_logger.info(
                f"Reflection 설정 / Config: max_iterations={max_iterations}, threshold={quality_threshold}, "
                f"llm_provider={llm_provider or 'default'}, llm_model={llm_model or 'default'}",
                max_iterations=max_iterations,
                quality_threshold=quality_threshold,
                llm_provider=llm_provider,
                llm_model=llm_model,
                temperature=temperature
            )
            
            # Create LLM manager with user-specified config
            llm_manager_kwargs = {}
            if llm_provider:
                try:
                    llm_manager_kwargs["provider"] = LLMProvider(llm_provider)
                except ValueError:
                    logger.warning(f"Invalid LLM provider '{llm_provider}', using default")
            if llm_model:
                llm_manager_kwargs["model"] = llm_model
            
            llm_manager = LLMManager(**llm_manager_kwargs)
            
            # Create reflection block
            reflection_block = ReflectionBlock(
                llm_manager=llm_manager,
                max_iterations=max_iterations,
                quality_threshold=quality_threshold,
            )
            
            # Execute reflection
            result = await reflection_block.execute(
                initial_output=input_text,
                context=input_data,
                task_description=config.get("task_description", ""),
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log node end
            exec_logger.node_end(
                node_id=str(node.id),
                node_name=node.name or "Reflection Block",
                node_type="agentic_reflection",
                success=True,
                duration_ms=duration_ms,
                quality_score=result.get("quality_score", 0.0),
                iterations=result.get("iterations", 0)
            )
            
            return NodeExecutionResult(
                success=True,
                output={
                    "improved_output": result.get("final_output", ""),
                    "quality_score": result.get("quality_score", 0.0),
                    "iteration_count": result.get("iterations", 0),
                    "reflection_history": result.get("reflection_history", []),
                },
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log error
            exec_logger.error(
                f"Reflection 블록 실행 실패 / Reflection block execution failed: {e}",
                error_type=type(e).__name__,
                node_id=str(node.id)
            )
            
            # Log node end with failure
            exec_logger.node_end(
                node_id=str(node.id),
                node_name=node.name or "Reflection Block",
                node_type="agentic_reflection",
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="REFLECTION_ERROR",
                duration_ms=duration_ms,
            )


@register_handler
class AgenticPlanningHandler(BaseNodeHandler):
    """Handler for Agentic Planning blocks."""
    
    @property
    def node_type(self) -> str:
        return "agentic_planning"
    
    async def validate(self, node: NodeEntity) -> tuple[bool, list[str]]:
        """Validate planning node configuration."""
        errors = []
        config = node.config.extra
        
        if not config.get("task"):
            errors.append("Planning block requires 'task' field")
        
        execution_mode = config.get("execution_mode", "sequential")
        if execution_mode not in ["sequential", "parallel", "adaptive"]:
            errors.append("execution_mode must be 'sequential', 'parallel', or 'adaptive'")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute planning block."""
        start_time = time.time()
        
        # Log node start
        exec_logger.node_start(
            node_id=str(node.id),
            node_name=node.name or "Planning Block",
            node_type="agentic_planning"
        )
        
        try:
            from backend.core.blocks.agentic.planning_block import PlanningBlock
            from backend.services.llm_manager import LLMManager, LLMProvider
            
            config = node.config.extra
            
            # Get task
            task = config.get("task") or input_data.get("task") or input_data.get("query", "")
            if "{{" in str(task):
                task = self.resolve_variables(str(task), context)
            
            execution_mode = config.get("execution_mode", "sequential")
            enable_replanning = config.get("enable_replanning", True)
            
            # Get LLM configuration from node config
            llm_provider = config.get("llm_provider")
            llm_model = config.get("llm_model")
            temperature = config.get("temperature", 0.7)
            
            exec_logger.info(
                f"Planning 설정 / Config: mode={execution_mode}, replanning={enable_replanning}, "
                f"llm_provider={llm_provider or 'default'}, llm_model={llm_model or 'default'}",
                execution_mode=execution_mode,
                enable_replanning=enable_replanning,
                llm_provider=llm_provider,
                llm_model=llm_model,
                temperature=temperature
            )
            
            # Create LLM manager with user-specified config
            llm_manager_kwargs = {}
            if llm_provider:
                try:
                    llm_manager_kwargs["provider"] = LLMProvider(llm_provider)
                except ValueError:
                    logger.warning(f"Invalid LLM provider '{llm_provider}', using default")
            if llm_model:
                llm_manager_kwargs["model"] = llm_model
            
            llm_manager = LLMManager(**llm_manager_kwargs)
            
            # Create planning block
            planning_block = PlanningBlock(llm_manager=llm_manager)
            
            # Execute planning
            result = await planning_block.execute(
                task=task,
                execution_mode=execution_mode,
                enable_replanning=enable_replanning,
                context=input_data,
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log node end
            exec_logger.node_end(
                node_id=str(node.id),
                node_name=node.name or "Planning Block",
                node_type="agentic_planning",
                success=result.get("success", True),
                duration_ms=duration_ms,
                subtasks_count=len(result.get("subtasks", []))
            )
            
            return NodeExecutionResult(
                success=result.get("success", True),
                output={
                    "plan": result.get("plan", {}),
                    "subtasks": result.get("subtasks", []),
                    "execution_results": result.get("execution_results", []),
                    "success": result.get("success", True),
                },
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log error
            exec_logger.error(
                f"Planning 블록 실행 실패 / Planning block execution failed: {e}",
                error_type=type(e).__name__,
                node_id=str(node.id)
            )
            
            # Log node end with failure
            exec_logger.node_end(
                node_id=str(node.id),
                node_name=node.name or "Planning Block",
                node_type="agentic_planning",
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="PLANNING_ERROR",
                duration_ms=duration_ms,
            )


@register_handler
class AgenticToolSelectorHandler(BaseNodeHandler):
    """Handler for Agentic Tool Selector blocks."""
    
    @property
    def node_type(self) -> str:
        return "agentic_tool_selector"
    
    async def validate(self, node: NodeEntity) -> tuple[bool, list[str]]:
        """Validate tool selector node configuration."""
        errors = []
        config = node.config.extra
        
        if not config.get("task"):
            errors.append("Tool Selector block requires 'task' field")
        
        if not config.get("available_tools"):
            errors.append("Tool Selector block requires 'available_tools' field")
        
        selection_strategy = config.get("selection_strategy", "best_match")
        if selection_strategy not in ["best_match", "cost_aware", "success_rate"]:
            errors.append("selection_strategy must be 'best_match', 'cost_aware', or 'success_rate'")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute tool selector block."""
        start_time = time.time()
        
        # Log node start
        exec_logger.node_start(
            node_id=str(node.id),
            node_name=node.name or "Tool Selector Block",
            node_type="agentic_tool_selector"
        )
        
        try:
            from backend.core.blocks.agentic.tool_selector_block import ToolSelectorBlock
            from backend.services.llm_manager import LLMManager, LLMProvider
            
            config = node.config.extra
            
            # Get task
            task = config.get("task") or input_data.get("task") or input_data.get("query", "")
            if "{{" in str(task):
                task = self.resolve_variables(str(task), context)
            
            available_tools = config.get("available_tools", [])
            selection_strategy = config.get("selection_strategy", "best_match")
            
            # Get LLM configuration from node config
            llm_provider = config.get("llm_provider")
            llm_model = config.get("llm_model")
            temperature = config.get("temperature", 0.3)
            
            exec_logger.info(
                f"Tool Selector 설정 / Config: strategy={selection_strategy}, tools={len(available_tools)}, "
                f"llm_provider={llm_provider or 'default'}, llm_model={llm_model or 'default'}",
                selection_strategy=selection_strategy,
                tools_count=len(available_tools),
                llm_provider=llm_provider,
                llm_model=llm_model,
                temperature=temperature
            )
            
            # Create LLM manager with user-specified config
            llm_manager_kwargs = {}
            if llm_provider:
                try:
                    llm_manager_kwargs["provider"] = LLMProvider(llm_provider)
                except ValueError:
                    logger.warning(f"Invalid LLM provider '{llm_provider}', using default")
            if llm_model:
                llm_manager_kwargs["model"] = llm_model
            
            llm_manager = LLMManager(**llm_manager_kwargs)
            
            # Create tool selector block
            tool_selector = ToolSelectorBlock(llm_manager=llm_manager)
            
            # Execute tool selection
            result = await tool_selector.execute(
                task=task,
                available_tools=available_tools,
                selection_strategy=selection_strategy,
                context=input_data,
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log node end
            exec_logger.node_end(
                node_id=str(node.id),
                node_name=node.name or "Tool Selector Block",
                node_type="agentic_tool_selector",
                success=True,
                duration_ms=duration_ms
            )
            
            return NodeExecutionResult(
                success=True,
                output={
                    "selected_tool": result.get("selected_tool", ""),
                    "confidence": result.get("confidence", 0.0),
                    "reasoning": result.get("reasoning", ""),
                    "alternatives": result.get("alternatives", []),
                },
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log error
            exec_logger.error(
                f"Tool Selector 블록 실행 실패 / Tool selector execution failed: {e}",
                error_type=type(e).__name__,
                node_id=str(node.id)
            )
            
            # Log node end with failure
            exec_logger.node_end(
                node_id=str(node.id),
                node_name=node.name or "Tool Selector Block",
                node_type="agentic_tool_selector",
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="TOOL_SELECTOR_ERROR",
                duration_ms=duration_ms,
            )


@register_handler
class AgenticRAGHandler(BaseNodeHandler):
    """Handler for Agentic RAG blocks."""
    
    @property
    def node_type(self) -> str:
        return "agentic_rag"
    
    async def validate(self, node: NodeEntity) -> tuple[bool, list[str]]:
        """Validate agentic RAG node configuration."""
        errors = []
        config = node.config.extra
        
        if not config.get("query"):
            errors.append("Agentic RAG block requires 'query' field")
        
        strategy = config.get("strategy", "adaptive")
        if strategy not in ["adaptive", "hybrid", "vector_only", "web_only"]:
            errors.append("strategy must be 'adaptive', 'hybrid', 'vector_only', or 'web_only'")
        
        top_k = config.get("top_k", 10)
        if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
            errors.append("top_k must be between 1 and 50")
        
        max_iterations = config.get("max_iterations", 3)
        if not isinstance(max_iterations, int) or max_iterations < 1 or max_iterations > 5:
            errors.append("max_iterations must be between 1 and 5")
        
        return len(errors) == 0, errors
    
    async def execute(
        self,
        node: NodeEntity,
        context: ExecutionContext,
        input_data: Dict[str, Any],
    ) -> NodeExecutionResult:
        """Execute agentic RAG block."""
        start_time = time.time()
        
        # Log node start
        exec_logger.node_start(
            node_id=str(node.id),
            node_name=node.name or "Agentic RAG Block",
            node_type="agentic_rag"
        )
        
        try:
            from backend.services.agentic_rag_service import AgenticRAGService
            from backend.services.llm_manager import LLMManager, LLMProvider
            from backend.services.embedding_service import EmbeddingService
            from backend.services.milvus_manager import MilvusManager
            
            config = node.config.extra
            
            # Get query
            query = config.get("query") or input_data.get("query") or input_data.get("input", "")
            if "{{" in str(query):
                query = self.resolve_variables(str(query), context)
            
            strategy = config.get("strategy", "adaptive")
            top_k = config.get("top_k", 10)
            enable_decomposition = config.get("enable_decomposition", True)
            enable_reflection = config.get("enable_reflection", True)
            max_iterations = config.get("max_iterations", 3)
            
            # Get LLM configuration from node config
            llm_provider = config.get("llm_provider")
            llm_model = config.get("llm_model")
            temperature = config.get("temperature", 0.7)
            
            exec_logger.info(
                f"Agentic RAG 설정 / Config: strategy={strategy}, top_k={top_k}, "
                f"llm_provider={llm_provider or 'default'}, llm_model={llm_model or 'default'}",
                strategy=strategy,
                top_k=top_k,
                enable_decomposition=enable_decomposition,
                enable_reflection=enable_reflection,
                max_iterations=max_iterations,
                llm_provider=llm_provider,
                llm_model=llm_model,
                temperature=temperature
            )
            
            # Create LLM manager with user-specified config
            llm_manager_kwargs = {}
            if llm_provider:
                try:
                    llm_manager_kwargs["provider"] = LLMProvider(llm_provider)
                except ValueError:
                    logger.warning(f"Invalid LLM provider '{llm_provider}', using default")
            if llm_model:
                llm_manager_kwargs["model"] = llm_model
            
            llm_manager = LLMManager(**llm_manager_kwargs)
            
            # Create service dependencies
            embedding_service = EmbeddingService()
            milvus_manager = MilvusManager()
            
            # Create agentic RAG service
            service = AgenticRAGService(
                llm_manager=llm_manager,
                embedding_service=embedding_service,
                milvus_manager=milvus_manager,
            )
            
            # Execute agentic RAG
            result = await service.query(
                query=query,
                strategy=strategy,
                top_k=top_k,
                enable_decomposition=enable_decomposition,
                enable_reflection=enable_reflection,
                max_iterations=max_iterations,
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log node end
            exec_logger.node_end(
                node_id=str(node.id),
                node_name=node.name or "Agentic RAG Block",
                node_type="agentic_rag",
                success=True,
                duration_ms=duration_ms,
                sources_count=result.get("total_sources", 0)
            )
            
            return NodeExecutionResult(
                success=True,
                output={
                    "answer": result.get("answer", ""),
                    "sources": result.get("sources", []),
                    "query_complexity": result.get("query_complexity", "simple"),
                    "sub_queries": result.get("sub_queries", []),
                    "confidence_score": result.get("confidence_score", 0.0),
                    "reflection_history": result.get("reflection_history", []),
                    "total_sources": result.get("total_sources", 0),
                },
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log error
            exec_logger.error(
                f"Agentic RAG 블록 실행 실패 / Agentic RAG execution failed: {e}",
                error_type=type(e).__name__,
                node_id=str(node.id)
            )
            
            # Log node end with failure
            exec_logger.node_end(
                node_id=str(node.id),
                node_name=node.name or "Agentic RAG Block",
                node_type="agentic_rag",
                success=False,
                duration_ms=duration_ms,
                error=str(e)
            )
            
            return NodeExecutionResult(
                success=False,
                output={},
                error_message=str(e),
                error_code="AGENTIC_RAG_ERROR",
                duration_ms=duration_ms,
            )
