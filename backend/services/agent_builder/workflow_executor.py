"""
Workflow Executor for LangGraph-based agent workflows.

This module provides the core execution engine for agent workflows using LangGraph.
"""

import logging
import uuid
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, List, Callable
from datetime import datetime
from functools import lru_cache
from sqlalchemy.orm import Session

from langgraph.graph import StateGraph, END, Send

from backend.services.llm_manager import LLMManager
from backend.memory.manager import MemoryManager
from backend.services.agent_builder.variable_resolver import VariableResolver
from backend.services.agent_builder.knowledgebase_service import KnowledgebaseService
from backend.services.agent_builder.block_executor import BlockExecutor
from backend.services.agent_builder.tool_registry import ToolRegistry
from backend.services.retry_handler import RetryHandler
from backend.models.agent import AgentStep

logger = logging.getLogger(__name__)


class ExecutionContext:
    """Context for workflow execution."""
    
    def __init__(
        self,
        execution_id: str,
        user_id: str,
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        session_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        variables: Optional[Dict[str, Any]] = None,
        knowledgebases: Optional[List[str]] = None,
    ):
        self.execution_id = execution_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.workflow_id = workflow_id
        self.workspace_id = workspace_id
        self.session_id = session_id
        self.input_data = input_data or {}
        self.variables = variables or {}
        self.knowledgebases = knowledgebases or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "workflow_id": self.workflow_id,
            "workspace_id": self.workspace_id,
            "session_id": self.session_id,
            "input_data": self.input_data,
            "variables": self.variables,
            "knowledgebases": self.knowledgebases,
        }


class WorkflowExecutor:
    """
    Executes agent workflows using LangGraph.
    
    Features:
    - Compiles workflow definitions to LangGraph StateGraph
    - Executes workflows with streaming support
    - Manages state and data flow between nodes
    - Integrates with existing infrastructure (LLM, Memory, Variables)
    """
    
    def __init__(
        self,
        db: Session,
        llm_manager: LLMManager,
        memory_manager: MemoryManager,
        variable_resolver: VariableResolver,
        knowledgebase_service: KnowledgebaseService,
        tool_registry: ToolRegistry,
    ):
        """
        Initialize WorkflowExecutor.
        
        Args:
            db: Database session
            llm_manager: LLM manager for model interactions
            memory_manager: Memory manager for STM/LTM
            variable_resolver: Variable resolver for context variables
            knowledgebase_service: Knowledgebase service for document retrieval
            tool_registry: Tool registry for tool access
        """
        self.db = db
        self.llm_manager = llm_manager
        self.memory_manager = memory_manager
        self.variable_resolver = variable_resolver
        self.knowledgebase_service = knowledgebase_service
        self.tool_registry = tool_registry
        
        # Initialize BlockExecutor
        self.block_executor = BlockExecutor(
            db=db,
            llm_manager=llm_manager,
            tool_registry=tool_registry
        )
        
        # Initialize RetryHandler
        self.retry_handler = RetryHandler(
            max_retries=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True
        )
        
        # Semaphore to limit concurrent LLM calls
        self.llm_semaphore = asyncio.Semaphore(5)
        
        # Default execution timeout (60 seconds)
        self.default_timeout = 60.0
        
        logger.info("WorkflowExecutor initialized")
    
    @lru_cache(maxsize=100)
    def _get_compiled_graph_cache_key(self, workflow_id: str, updated_at: str) -> str:
        """Generate cache key for compiled graph."""
        return f"{workflow_id}:{updated_at}"
    
    async def compile_workflow(self, workflow: Any) -> StateGraph:
        """
        Compile workflow definition to LangGraph StateGraph.
        
        Args:
            workflow: Workflow model instance with graph_definition
            
        Returns:
            Compiled StateGraph
            
        Raises:
            ValueError: If workflow definition is invalid
        """
        try:
            # Check cache (using workflow ID and updated_at as cache key)
            cache_key = self._get_compiled_graph_cache_key(
                workflow.id,
                str(workflow.updated_at)
            )
            
            # Create StateGraph
            graph = StateGraph(dict)
            
            # Get graph definition
            graph_def = workflow.graph_definition
            if not graph_def:
                raise ValueError(f"Workflow {workflow.id} has no graph definition")
            
            # Add nodes from workflow definition
            nodes = graph_def.get("nodes", [])
            for node in nodes:
                node_id = node["id"]
                node_type = node["type"]
                
                if node_type == "agent":
                    graph.add_node(node_id, self._create_agent_node(node))
                elif node_type == "block":
                    graph.add_node(node_id, self._create_block_node(node))
                elif node_type == "control":
                    graph.add_node(node_id, self._create_control_node(node))
                else:
                    logger.warning(f"Unknown node type: {node_type}")
            
            # Add edges
            edges = graph_def.get("edges", [])
            for edge in edges:
                edge_type = edge.get("type", "normal")
                source = edge["source"]
                target = edge["target"]
                
                if edge_type == "normal":
                    graph.add_edge(source, target)
                elif edge_type == "conditional":
                    condition = edge.get("condition")
                    branches = edge.get("branches", {})
                    graph.add_conditional_edges(
                        source,
                        self._create_condition_function(condition),
                        branches
                    )
            
            # Set entry point
            entry_point = graph_def.get("entry_point")
            if entry_point:
                graph.set_entry_point(entry_point)
            else:
                # Use first node as entry point
                if nodes:
                    graph.set_entry_point(nodes[0]["id"])
            
            # Set finish points (nodes that lead to END)
            finish_points = graph_def.get("finish_points", [])
            for finish_point in finish_points:
                graph.add_edge(finish_point, END)
            
            # Compile graph
            compiled = graph.compile()
            
            logger.info(f"Compiled workflow {workflow.id} with {len(nodes)} nodes")
            
            return compiled
            
        except Exception as e:
            logger.error(f"Failed to compile workflow {workflow.id}: {e}")
            raise ValueError(f"Workflow compilation failed: {str(e)}")
    
    def _create_agent_node(self, node_config: Dict[str, Any]) -> Callable:
        """
        Create agent execution node.
        
        Args:
            node_config: Node configuration from workflow definition
            
        Returns:
            Async function for node execution
        """
        async def agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute agent node."""
            agent_id = node_config.get("agent_id")
            node_id = node_config["id"]
            
            # Add step
            step = AgentStep(
                step_id=f"agent_{uuid.uuid4().hex[:8]}",
                type="action",
                content=f"Executing agent: {node_config.get('name', agent_id)}",
                timestamp=datetime.now(),
                metadata={"agent_id": agent_id, "node_id": node_id}
            )
            
            state.setdefault("steps", []).append(step.model_dump())
            
            try:
                # Load agent from database
                agent = await self._load_agent(agent_id)
                
                if not agent:
                    raise ValueError(f"Agent not found: {agent_id}")
                
                # Prepare input from state
                agent_input = self._map_agent_input(agent, state, node_config)
                
                # Execute agent
                result = await self._execute_agent(agent, agent_input, state)
                
                # Store result in state
                state[f"agent_{agent_id}_output"] = result
                state[f"node_{node_id}_output"] = result
                
                # Add completion step
                completion_step = AgentStep(
                    step_id=f"agent_complete_{uuid.uuid4().hex[:8]}",
                    type="observation",
                    content=f"Agent {agent.name} completed",
                    timestamp=datetime.now(),
                    metadata={
                        "agent_id": agent_id,
                        "node_id": node_id,
                        "result_keys": list(result.keys()) if isinstance(result, dict) else []
                    }
                )
                state.setdefault("steps", []).append(completion_step.model_dump())
                
            except Exception as e:
                logger.error(f"Agent node execution failed: {e}")
                
                # Add error step
                error_step = AgentStep(
                    step_id=f"agent_error_{uuid.uuid4().hex[:8]}",
                    type="error",
                    content=f"Agent execution failed: {str(e)}",
                    timestamp=datetime.now(),
                    metadata={"agent_id": agent_id, "node_id": node_id, "error": str(e)}
                )
                state.setdefault("steps", []).append(error_step.model_dump())
                
                # Store error in state
                state[f"agent_{agent_id}_error"] = str(e)
                state[f"node_{node_id}_error"] = str(e)
            
            return state
        
        return agent_node
    
    def _create_block_node(self, node_config: Dict[str, Any]) -> Callable:
        """
        Create block execution node.
        
        Args:
            node_config: Node configuration from workflow definition
            
        Returns:
            Async function for node execution
        """
        async def block_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute block node."""
            block_id = node_config.get("block_id")
            node_id = node_config["id"]
            
            # Add step
            step = AgentStep(
                step_id=f"block_{uuid.uuid4().hex[:8]}",
                type="action",
                content=f"Executing block: {node_config.get('name', block_id)}",
                timestamp=datetime.now(),
                metadata={"block_id": block_id, "node_id": node_id}
            )
            
            state.setdefault("steps", []).append(step.model_dump())
            
            try:
                # Load block from database
                block = await self._load_block(block_id)
                
                if not block:
                    raise ValueError(f"Block not found: {block_id}")
                
                # Prepare input from state
                block_input = self._map_block_input(block, state, node_config)
                
                # Execute block (will use BlockExecutor in subtask 3.4)
                result = await self._execute_block(block, block_input, state)
                
                # Store result in state
                state[f"block_{block_id}_output"] = result
                state[f"node_{node_id}_output"] = result
                
                # Add completion step
                completion_step = AgentStep(
                    step_id=f"block_complete_{uuid.uuid4().hex[:8]}",
                    type="observation",
                    content=f"Block {block.name} completed",
                    timestamp=datetime.now(),
                    metadata={
                        "block_id": block_id,
                        "node_id": node_id,
                        "result_keys": list(result.keys()) if isinstance(result, dict) else []
                    }
                )
                state.setdefault("steps", []).append(completion_step.model_dump())
                
            except Exception as e:
                logger.error(f"Block node execution failed: {e}")
                
                # Add error step
                error_step = AgentStep(
                    step_id=f"block_error_{uuid.uuid4().hex[:8]}",
                    type="error",
                    content=f"Block execution failed: {str(e)}",
                    timestamp=datetime.now(),
                    metadata={"block_id": block_id, "node_id": node_id, "error": str(e)}
                )
                state.setdefault("steps", []).append(error_step.model_dump())
                
                # Store error in state
                state[f"block_{block_id}_error"] = str(e)
                state[f"node_{node_id}_error"] = str(e)
            
            return state
        
        return block_node
    
    def _create_control_node(self, node_config: Dict[str, Any]) -> Callable:
        """
        Create control flow node (conditional, loop, parallel).
        
        Args:
            node_config: Node configuration from workflow definition
            
        Returns:
            Async function for node execution
        """
        control_type = node_config.get("control_type", "conditional")
        node_id = node_config["id"]
        
        async def control_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute control node."""
            # Add step
            step = AgentStep(
                step_id=f"control_{uuid.uuid4().hex[:8]}",
                type="planning",
                content=f"Control flow: {control_type}",
                timestamp=datetime.now(),
                metadata={"control_type": control_type, "node_id": node_id}
            )
            
            state.setdefault("steps", []).append(step.model_dump())
            
            try:
                if control_type == "conditional":
                    # Conditional logic - evaluate condition
                    condition = node_config.get("condition")
                    result = self._evaluate_condition(condition, state)
                    state[f"control_{node_id}_result"] = result
                    
                elif control_type == "loop":
                    # Loop logic - iterate over collection
                    collection_key = node_config.get("collection_key")
                    collection = state.get(collection_key, [])
                    max_iterations = node_config.get("max_iterations", 100)
                    
                    # Store loop metadata
                    state[f"control_{node_id}_iterations"] = min(len(collection), max_iterations)
                    state[f"control_{node_id}_collection"] = collection[:max_iterations]
                    
                elif control_type == "parallel":
                    # Parallel logic - mark for parallel execution
                    parallel_branches = node_config.get("branches", [])
                    state[f"control_{node_id}_branches"] = parallel_branches
                    
                else:
                    logger.warning(f"Unknown control type: {control_type}")
                
                # Store control output
                state[f"control_{node_id}_output"] = {
                    "control_type": control_type,
                    "executed": True
                }
                state[f"node_{node_id}_output"] = state[f"control_{node_id}_output"]
                
            except Exception as e:
                logger.error(f"Control node execution failed: {e}")
                
                # Add error step
                error_step = AgentStep(
                    step_id=f"control_error_{uuid.uuid4().hex[:8]}",
                    type="error",
                    content=f"Control flow failed: {str(e)}",
                    timestamp=datetime.now(),
                    metadata={"control_type": control_type, "node_id": node_id, "error": str(e)}
                )
                state.setdefault("steps", []).append(error_step.model_dump())
                
                # Store error in state
                state[f"control_{node_id}_error"] = str(e)
                state[f"node_{node_id}_error"] = str(e)
            
            return state
        
        return control_node
    
    def _evaluate_condition(self, condition: str, state: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression.
        
        Args:
            condition: Python expression to evaluate
            state: Current state
            
        Returns:
            Boolean result of condition
        """
        try:
            # Create safe evaluation context
            eval_context = {
                "state": state,
                **state.get("variables", {})
            }
            
            # Evaluate condition
            result = eval(condition, {"__builtins__": {}}, eval_context)
            
            return bool(result)
        except Exception as e:
            logger.error(f"Condition evaluation failed: {e}")
            return False
    
    async def execute_parallel_branches(
        self,
        branches: List[Dict[str, Any]],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute multiple branches in parallel.
        
        Args:
            branches: List of branch configurations
            state: Current state
            
        Returns:
            Updated state with results from all branches
        """
        try:
            # Create tasks for each branch
            tasks = []
            for branch in branches:
                task = self._execute_branch(branch, state.copy())
                tasks.append(task)
            
            # Execute all branches concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Aggregate results
            aggregated_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Branch {i} failed: {result}")
                    aggregated_results.append({
                        "branch_id": branches[i].get("id"),
                        "error": str(result),
                        "success": False
                    })
                else:
                    aggregated_results.append({
                        "branch_id": branches[i].get("id"),
                        "result": result,
                        "success": True
                    })
            
            # Store aggregated results in state
            state["parallel_results"] = aggregated_results
            
            # Add step for parallel completion
            step = AgentStep(
                step_id=f"parallel_complete_{uuid.uuid4().hex[:8]}",
                type="observation",
                content=f"Completed {len(branches)} parallel branches",
                timestamp=datetime.now(),
                metadata={
                    "branch_count": len(branches),
                    "success_count": sum(1 for r in aggregated_results if r["success"])
                }
            )
            state.setdefault("steps", []).append(step.model_dump())
            
            return state
            
        except Exception as e:
            logger.error(f"Parallel execution failed: {e}")
            raise
    
    async def _execute_branch(
        self,
        branch: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single branch.
        
        Args:
            branch: Branch configuration
            state: Branch state
            
        Returns:
            Branch execution result
        """
        # Use semaphore to limit concurrent LLM calls
        async with self.llm_semaphore:
            try:
                branch_type = branch.get("type")
                
                if branch_type == "agent":
                    agent_id = branch.get("agent_id")
                    agent = await self._load_agent(agent_id)
                    if agent:
                        agent_input = self._map_agent_input(agent, state, branch)
                        return await self._execute_agent(agent, agent_input, state)
                
                elif branch_type == "block":
                    block_id = branch.get("block_id")
                    block = await self._load_block(block_id)
                    if block:
                        block_input = self._map_block_input(block, state, branch)
                        return await self._execute_block(block, block_input, state)
                
                else:
                    logger.warning(f"Unknown branch type: {branch_type}")
                    return {"error": f"Unknown branch type: {branch_type}"}
                
            except Exception as e:
                logger.error(f"Branch execution failed: {e}")
                raise
    
    def _create_condition_function(self, condition: str) -> Callable:
        """
        Create condition evaluation function for conditional edges.
        
        Args:
            condition: Python expression to evaluate
            
        Returns:
            Function that evaluates condition and returns branch name
        """
        def condition_fn(state: Dict[str, Any]) -> str:
            """Evaluate condition."""
            try:
                # Create safe evaluation context
                eval_context = {
                    "state": state,
                    "output": state.get("output"),
                    **state.get("variables", {})
                }
                
                # Evaluate condition
                result = eval(condition, {"__builtins__": {}}, eval_context)
                
                return str(result)
            except Exception as e:
                logger.error(f"Condition evaluation failed: {e}")
                return "error"
        
        return condition_fn
    
    async def _resolve_variables(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Resolve variables for execution context.
        
        Args:
            context: Execution context
            
        Returns:
            Dictionary of resolved variables
        """
        try:
            # Start with context variables
            variables = dict(context.variables)
            
            # Resolve all variables in context using VariableResolver
            for key, value in variables.items():
                if isinstance(value, str) and "${" in value:
                    resolved = await self.variable_resolver.resolve_variables(
                        template=value,
                        context=context
                    )
                    variables[key] = resolved
            
            return variables
        except Exception as e:
            logger.error(f"Failed to resolve variables: {e}")
            return {}
    
    async def _load_knowledgebases(self, workflow: Any) -> List[str]:
        """
        Load knowledgebases associated with workflow.
        
        Args:
            workflow: Workflow model instance
            
        Returns:
            List of knowledgebase IDs
        """
        try:
            # Get knowledgebases from workflow configuration
            kb_ids = workflow.configuration.get("knowledgebase_ids", [])
            
            # Validate all knowledgebases exist
            valid_kbs = []
            for kb_id in kb_ids:
                kb = self.knowledgebase_service.get_knowledgebase(kb_id)
                if kb:
                    valid_kbs.append(kb_id)
                else:
                    logger.warning(f"Knowledgebase {kb_id} not found")
            
            return valid_kbs
        except Exception as e:
            logger.error(f"Failed to load knowledgebases: {e}")
            return []
    
    async def _load_agent(self, agent_id: str) -> Optional[Any]:
        """
        Load agent from database.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent model instance or None
        """
        try:
            from backend.db.models.agent_builder import Agent
            
            agent = self.db.query(Agent).filter(
                Agent.id == agent_id,
                Agent.deleted_at.is_(None)
            ).first()
            
            return agent
        except Exception as e:
            logger.error(f"Failed to load agent {agent_id}: {e}")
            return None
    
    async def _load_block(self, block_id: str) -> Optional[Any]:
        """
        Load block from database.
        
        Args:
            block_id: Block ID
            
        Returns:
            Block model instance or None
        """
        try:
            from backend.db.models.agent_builder import Block
            
            block = self.db.query(Block).filter(
                Block.id == block_id
            ).first()
            
            return block
        except Exception as e:
            logger.error(f"Failed to load block {block_id}: {e}")
            return None
    
    def _map_agent_input(
        self,
        agent: Any,
        state: Dict[str, Any],
        node_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map state to agent input.
        
        Args:
            agent: Agent model instance
            state: Current state
            node_config: Node configuration
            
        Returns:
            Input dictionary for agent
        """
        # Get input mapping from node config
        input_mapping = node_config.get("input_mapping", {})
        
        agent_input = {}
        
        # Map inputs based on configuration
        for agent_key, state_key in input_mapping.items():
            if state_key in state:
                agent_input[agent_key] = state[state_key]
        
        # If no mapping, use default input
        if not agent_input:
            agent_input = state.get("input", {})
        
        return agent_input
    
    def _map_block_input(
        self,
        block: Any,
        state: Dict[str, Any],
        node_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map state to block input.
        
        Args:
            block: Block model instance
            state: Current state
            node_config: Node configuration
            
        Returns:
            Input dictionary for block
        """
        # Get input mapping from node config
        input_mapping = node_config.get("input_mapping", {})
        
        block_input = {}
        
        # Map inputs based on configuration
        for block_key, state_key in input_mapping.items():
            if state_key in state:
                block_input[block_key] = state[state_key]
        
        # If no mapping, use default input
        if not block_input:
            block_input = state.get("input", {})
        
        return block_input
    
    async def _execute_agent(
        self,
        agent: Any,
        agent_input: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute agent with retry and timeout support.
        
        Args:
            agent: Agent model instance
            agent_input: Input for agent
            state: Current state
            
        Returns:
            Agent execution result
        """
        # Get error handling configuration
        error_config = agent.configuration.get("error_handling", {}) if hasattr(agent, 'configuration') and agent.configuration else {}
        retry_enabled = error_config.get("retry_enabled", True)
        retry_count = error_config.get("retry_count", 3)
        timeout = error_config.get("timeout", self.default_timeout)
        fallback_value = error_config.get("fallback_value")
        
        async def execute_with_timeout():
            """Execute agent with timeout."""
            try:
                # TODO: Implement actual agent execution
                # This will integrate with existing agent infrastructure
                # For now, return placeholder
                return {
                    "output": f"Agent {agent.name} executed with input: {agent_input}",
                    "agent_id": agent.id,
                    "agent_name": agent.name
                }
            except Exception as e:
                logger.error(f"Agent execution failed: {e}")
                raise
        
        try:
            if retry_enabled:
                # Execute with retry logic
                result = await self.retry_handler.execute_with_retry(
                    lambda: asyncio.wait_for(execute_with_timeout(), timeout=timeout),
                    retry_on=(TimeoutError, ConnectionError, asyncio.TimeoutError)
                )
            else:
                # Execute without retry
                result = await asyncio.wait_for(execute_with_timeout(), timeout=timeout)
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Agent {agent.id} execution timed out after {timeout}s")
            
            # Use fallback if configured
            if fallback_value is not None:
                logger.info(f"Using fallback value for agent {agent.id}")
                return {"output": fallback_value, "fallback": True}
            
            raise
            
        except Exception as e:
            logger.error(f"Agent execution failed after retries: {e}")
            
            # Use fallback if configured
            if fallback_value is not None:
                logger.info(f"Using fallback value for agent {agent.id}")
                return {"output": fallback_value, "fallback": True}
            
            raise
    
    async def _execute_block(
        self,
        block: Any,
        block_input: Dict[str, Any],
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute block using BlockExecutor with retry and timeout support.
        
        Args:
            block: Block model instance
            block_input: Input for block
            state: Current state
            
        Returns:
            Block execution result
        """
        # Get error handling configuration
        error_config = block.configuration.get("error_handling", {}) if hasattr(block, 'configuration') and block.configuration else {}
        retry_enabled = error_config.get("retry_enabled", True)
        retry_count = error_config.get("retry_count", 3)
        timeout = error_config.get("timeout", self.default_timeout)
        fallback_value = error_config.get("fallback_value")
        
        async def execute_with_timeout():
            """Execute block with timeout."""
            return await self.block_executor.execute_block(
                block=block,
                input_data=block_input,
                context=state.get("context", {})
            )
        
        try:
            if retry_enabled:
                # Execute with retry logic
                result = await self.retry_handler.execute_with_retry(
                    lambda: asyncio.wait_for(execute_with_timeout(), timeout=timeout),
                    retry_on=(TimeoutError, ConnectionError, asyncio.TimeoutError)
                )
            else:
                # Execute without retry
                result = await asyncio.wait_for(execute_with_timeout(), timeout=timeout)
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Block {block.id} execution timed out after {timeout}s")
            
            # Use fallback if configured
            if fallback_value is not None:
                logger.info(f"Using fallback value for block {block.id}")
                return {"output": fallback_value, "fallback": True}
            
            raise
            
        except Exception as e:
            logger.error(f"Block execution failed after retries: {e}")
            
            # Use fallback if configured
            if fallback_value is not None:
                logger.info(f"Using fallback value for block {block.id}")
                return {"output": fallback_value, "fallback": True}
            
            raise
    
    async def execute_workflow(
        self,
        workflow: Any,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> AsyncGenerator[AgentStep, None]:
        """
        Execute workflow and stream results.
        
        Args:
            workflow: Workflow model instance
            input_data: Input data for workflow
            context: Execution context
            
        Yields:
            AgentStep objects for each execution step
            
        Raises:
            ValueError: If workflow execution fails
        """
        execution_start_time = datetime.now()
        execution_status = "running"
        execution_error = None
        
        try:
            # Create execution record (if models are available)
            execution_record = await self._create_execution_record(
                workflow=workflow,
                input_data=input_data,
                context=context,
                status="running"
            )
            
            # Compile workflow
            graph = await self.compile_workflow(workflow)
            
            # Resolve variables
            variables = await self._resolve_variables(context)
            
            # Load knowledgebases
            knowledgebases = await self._load_knowledgebases(workflow)
            
            # Initialize state
            initial_state = {
                "input": input_data,
                "context": context.to_dict(),
                "variables": variables,
                "knowledgebases": knowledgebases,
                "steps": [],
                "output": None
            }
            
            # Yield start step
            start_step = AgentStep(
                step_id=f"start_{uuid.uuid4().hex[:8]}",
                type="planning",
                content=f"Starting workflow execution: {workflow.name}",
                timestamp=datetime.now(),
                metadata={
                    "workflow_id": workflow.id,
                    "execution_id": context.execution_id
                }
            )
            yield start_step
            
            # Log start step to database
            await self._log_execution_step(execution_record, start_step)
            
            # Execute graph with streaming
            previous_step_count = 0
            async for state in graph.astream(initial_state):
                # Extract new steps
                current_steps = state.get("steps", [])
                new_steps = current_steps[previous_step_count:]
                
                # Yield new steps
                for step_data in new_steps:
                    step = AgentStep(**step_data)
                    yield step
                    
                    # Log step to database
                    await self._log_execution_step(execution_record, step)
                
                previous_step_count = len(current_steps)
            
            # Yield final output
            if state.get("output"):
                final_step = AgentStep(
                    step_id=f"output_{uuid.uuid4().hex[:8]}",
                    type="response",
                    content=str(state["output"]),
                    timestamp=datetime.now(),
                    metadata={"final": True}
                )
                yield final_step
                
                # Log final step to database
                await self._log_execution_step(execution_record, final_step)
            
            execution_status = "completed"
            logger.info(f"Workflow {workflow.id} execution completed")
            
        except Exception as e:
            execution_status = "failed"
            execution_error = str(e)
            logger.error(f"Workflow execution failed: {e}")
            
            # Yield error step
            error_step = AgentStep(
                step_id=f"error_{uuid.uuid4().hex[:8]}",
                type="error",
                content=f"Workflow execution failed: {str(e)}",
                timestamp=datetime.now(),
                metadata={"error": str(e)}
            )
            yield error_step
            
            # Log error step to database
            await self._log_execution_step(execution_record, error_step)
            
            raise ValueError(f"Workflow execution failed: {str(e)}")
        
        finally:
            # Update execution record with final status
            execution_end_time = datetime.now()
            duration_ms = int((execution_end_time - execution_start_time).total_seconds() * 1000)
            
            await self._update_execution_record(
                execution_record=execution_record,
                status=execution_status,
                error_message=execution_error,
                duration_ms=duration_ms,
                output_data=state.get("output") if 'state' in locals() else None
            )
    
    async def _create_execution_record(
        self,
        workflow: Any,
        input_data: Dict[str, Any],
        context: ExecutionContext,
        status: str
    ) -> Optional[Any]:
        """
        Create execution record in database.
        
        Args:
            workflow: Workflow model instance
            input_data: Input data
            context: Execution context
            status: Initial status
            
        Returns:
            Execution record or None if models not available
        """
        try:
            # Try to import and create execution record
            # This will work once Phase 1 models are implemented
            from backend.db.models.agent_builder import AgentExecution
            
            execution = AgentExecution(
                id=context.execution_id,
                agent_id=context.agent_id,
                user_id=context.user_id,
                session_id=context.session_id,
                input_data=input_data,
                execution_context=context.to_dict(),
                status=status,
                started_at=datetime.now()
            )
            
            self.db.add(execution)
            self.db.commit()
            
            logger.info(f"Created execution record: {context.execution_id}")
            return execution
            
        except ImportError:
            logger.debug("Execution models not available yet, skipping database logging")
            return None
        except Exception as e:
            logger.warning(f"Failed to create execution record: {e}")
            return None
    
    async def _log_execution_step(
        self,
        execution_record: Optional[Any],
        step: AgentStep
    ) -> None:
        """
        Log execution step to database.
        
        Args:
            execution_record: Execution record
            step: Agent step to log
        """
        if not execution_record:
            return
        
        try:
            from backend.db.models.agent_builder import ExecutionStep
            
            # Get step number
            step_number = len(execution_record.steps) + 1
            
            execution_step = ExecutionStep(
                id=step.step_id,
                execution_id=execution_record.id,
                step_number=step_number,
                step_type=step.type,
                content=step.content,
                metadata=step.metadata,
                timestamp=step.timestamp
            )
            
            self.db.add(execution_step)
            self.db.commit()
            
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Failed to log execution step: {e}")
    
    async def _update_execution_record(
        self,
        execution_record: Optional[Any],
        status: str,
        error_message: Optional[str],
        duration_ms: int,
        output_data: Optional[Any]
    ) -> None:
        """
        Update execution record with final status.
        
        Args:
            execution_record: Execution record
            status: Final status
            error_message: Error message if failed
            duration_ms: Execution duration in milliseconds
            output_data: Output data
        """
        if not execution_record:
            return
        
        try:
            execution_record.status = status
            execution_record.error_message = error_message
            execution_record.duration_ms = duration_ms
            execution_record.output_data = output_data
            execution_record.completed_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"Updated execution record: {execution_record.id} - {status}")
            
        except Exception as e:
            logger.warning(f"Failed to update execution record: {e}")
