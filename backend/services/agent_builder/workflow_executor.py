"""
Workflow Execution Engine

Executes workflows by processing nodes in order based on the graph structure.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import time

from sqlalchemy.orm import Session
from backend.core.workflow_metrics import WorkflowMetrics

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Executes a workflow by processing its nodes."""
    
    def __init__(self, workflow: Any, db: Session, execution_id: Optional[str] = None):
        self.workflow = workflow
        self.db = db
        self.execution_id = execution_id  # For SSE status updates
        self.execution_context: Dict[str, Any] = {}
        self.node_results: Dict[str, Any] = {}
        self.retry_counts: Dict[str, int] = {}  # Track retry attempts per node
        self.node_statuses: Dict[str, Dict[str, Any]] = {}  # Track node execution statuses for SSE
        
        # Node result caching
        self.node_cache: Dict[str, tuple[Any, float]] = {}  # {cache_key: (result, timestamp)}
        self.cache_ttl: int = 300  # 5 minutes cache TTL
        self.cache_enabled: bool = True  # Can be disabled for debugging
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            Execution result with output data
        """
        start_time = time.time()
        user_id = None
        
        try:
            logger.info(f"Starting workflow execution: {self.workflow.id}")
            
            # Record execution start
            WorkflowMetrics.record_execution_start(
                workflow_id=str(self.workflow.id),
                user_id=None
            )
            
            # Initialize execution context
            # Extract user_id from input_data if present
            user_id = input_data.pop("_user_id", None) if isinstance(input_data, dict) else None
            
            self.execution_context = {
                "input": input_data,
                "workflow_id": str(self.workflow.id),  # Convert UUID to string for JSON serialization
                "user_id": user_id,  # Store user_id for API key retrieval
                "started_at": datetime.utcnow().isoformat(),
            }
            
            # Get workflow graph
            graph = self.workflow.graph_definition
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            
            logger.info(f"Workflow has {len(nodes)} nodes and {len(edges)} edges")
            if nodes:
                logger.info(f"Node types: {[n.get('type') or n.get('configuration', {}).get('type') for n in nodes]}")
                logger.info(f"Node structures: {[{'id': n.get('id'), 'type': n.get('type'), 'node_type': n.get('node_type'), 'config_type': n.get('configuration', {}).get('type')} for n in nodes]}")
            
            # Find start node - improved detection
            start_nodes = []
            for n in nodes:
                # Get node type from multiple possible fields
                node_type = n.get("type") or n.get("node_type")
                config_type = n.get("configuration", {}).get("type")
                
                # For control nodes, check configuration.type
                if node_type == "control" and config_type:
                    effective_type = config_type
                else:
                    effective_type = node_type or config_type
                
                # Check if it's a start or trigger node
                if effective_type == "start" or (effective_type and effective_type.startswith("trigger")):
                    start_nodes.append(n)
                    logger.info(f"Found start/trigger node: {n.get('id')} (node_type: {node_type}, config_type: {config_type}, effective: {effective_type})")
            
            if not start_nodes:
                # Provide detailed error message
                available_types = [
                    {
                        'id': n.get('id'), 
                        'node_type': n.get('node_type'),
                        'type': n.get('type'),
                        'config_type': n.get('configuration', {}).get('type')
                    } 
                    for n in nodes
                ]
                logger.error(f"No start/trigger node found. Available nodes: {available_types}")
                raise ValueError(
                    f"No start node found in workflow. Please add a Start or Trigger node. "
                    f"Available node types: {[n.get('node_type') or n.get('type') for n in nodes]}"
                )
            
            start_node = start_nodes[0]
            
            # Execute workflow from start node
            result = await self._execute_from_node(start_node, nodes, edges, input_data)
            
            logger.info(f"Workflow execution completed: {self.workflow.id}")
            
            # Record successful execution
            duration = time.time() - start_time
            WorkflowMetrics.record_execution_complete(
                workflow_id=str(self.workflow.id),
                user_id=user_id,
                status="success",
                duration=duration
            )
            
            return {
                "success": True,
                "output": result,
                "execution_context": self.execution_context,
                "node_results": self.node_results,
                "retry_counts": self.retry_counts,
            }
        
        except Exception as e:
            from backend.exceptions import WorkflowPausedException
            
            # Check if workflow was paused for approval
            if isinstance(e, WorkflowPausedException):
                logger.info(f"Workflow paused for approval: {e.approval_id}")
                
                # Record approval request
                WorkflowMetrics.record_approval_request(str(self.workflow.id))
                
                return {
                    "success": False,
                    "paused": True,
                    "approval_id": e.approval_id,
                    "node_id": e.node_id,
                    "message": str(e),
                    "execution_context": self.execution_context,
                    "node_results": self.node_results,
                    "data": e.data,
                }
            
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            
            # Record failed execution
            duration = time.time() - start_time
            WorkflowMetrics.record_execution_complete(
                workflow_id=str(self.workflow.id),
                user_id=user_id,
                status="failed",
                duration=duration
            )
            
            # Record error
            error_type = type(e).__name__
            WorkflowMetrics.record_error(str(self.workflow.id), error_type)
            
            return {
                "success": False,
                "error": str(e),
                "execution_context": self.execution_context,
                "node_results": self.node_results,
                "retry_counts": self.retry_counts,
            }
    
    async def _execute_from_node(
        self,
        current_node: Dict[str, Any],
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        data: Any
    ) -> Any:
        """
        Execute workflow starting from a specific node.
        
        Args:
            current_node: Current node to execute
            nodes: All nodes in the workflow
            edges: All edges in the workflow
            data: Input data for the current node
            
        Returns:
            Output data from the execution path
        """
        node_id = current_node["id"]
        # Check multiple possible fields for node type
        raw_node_type = current_node.get("type") or current_node.get("node_type")
        config_type = current_node.get("configuration", {}).get("type")
        
        # For control nodes, use configuration.type as the effective type
        if raw_node_type == "control" and config_type:
            node_type = config_type
        else:
            node_type = raw_node_type or config_type or "block"
        
        node_data = current_node.get("data") or current_node.get("configuration", {})
        
        logger.info(f"Executing node: {node_id} (type: {node_type})")
        
        node_start_time = time.time()
        
        # Update node status: running
        if self.execution_id:
            await self.update_node_status(
                self.execution_id,
                node_id,
                {
                    "node_name": node_data.get("name", node_type),
                    "status": "running",
                    "start_time": datetime.utcnow().timestamp(),
                }
            )
        
        # Get retry configuration from node data
        max_retries = node_data.get("maxRetries", 3)
        retry_delay = node_data.get("retryDelay", 1)  # seconds
        retry_backoff = node_data.get("retryBackoff", "exponential")  # exponential or linear
        
        try:
            # Execute node with caching and retry logic
            result = await self._execute_node_with_cache(
                node_id=node_id,
                node_type=node_type,
                node_data=node_data,
                data=data,
                nodes=nodes,
                edges=edges,
                max_retries=max_retries,
                retry_delay=retry_delay,
                retry_backoff=retry_backoff,
            )
            
            # Record successful node execution
            node_duration = time.time() - node_start_time
            WorkflowMetrics.record_node_execution(
                workflow_id=str(self.workflow.id),
                node_type=node_type,
                status="success",
                duration=node_duration
            )
            
            # Update node status: success
            if self.execution_id:
                await self.update_node_status(
                    self.execution_id,
                    node_id,
                    {
                        "status": "success",
                        "end_time": datetime.utcnow().timestamp(),
                        "output": str(result)[:500] if result else None,  # Limit output size
                    }
                )
            
            # Store node result
            self.node_results[node_id] = result
            
        except Exception as e:
            # Record failed node execution
            node_duration = time.time() - node_start_time
            WorkflowMetrics.record_node_execution(
                workflow_id=str(self.workflow.id),
                node_type=node_type,
                status="failed",
                duration=node_duration
            )
            
            # Update node status: failed
            if self.execution_id:
                await self.update_node_status(
                    self.execution_id,
                    node_id,
                    {
                        "status": "failed",
                        "end_time": datetime.utcnow().timestamp(),
                        "error": str(e),
                    }
                )
            raise
        
        # Find next nodes
        next_edges = [e for e in edges if e.get("source") == node_id]
        
        if not next_edges:
            # No more nodes, return result
            return result
        
        # Handle condition node (multiple branches)
        if node_type == "condition" and isinstance(result, dict) and "branch" in result:
            branch = result["branch"]
            # Find edge matching the branch
            next_edge = next(
                (e for e in next_edges if e.get("sourceHandle") == branch),
                next_edges[0] if next_edges else None
            )
            if next_edge:
                next_node = next((n for n in nodes if n["id"] == next_edge["target"]), None)
                if next_node:
                    return await self._execute_from_node(next_node, nodes, edges, result.get("data", data))
        else:
            # Execute next node (single path)
            if next_edges:
                next_edge = next_edges[0]
                next_node = next((n for n in nodes if n["id"] == next_edge["target"]), None)
                if next_node:
                    return await self._execute_from_node(next_node, nodes, edges, result)
        
        return result
    
    def _generate_cache_key(self, node_id: str, node_type: str, data: Any) -> str:
        """
        Generate cache key for node execution.
        
        Args:
            node_id: Node ID
            node_type: Node type
            data: Input data
            
        Returns:
            Cache key string
        """
        import hashlib
        import json
        
        try:
            # Create deterministic hash of input data
            data_str = json.dumps(data, sort_keys=True, default=str)
            data_hash = hashlib.md5(data_str.encode()).hexdigest()
            
            # Combine node_id and data hash
            cache_key = f"{node_id}:{node_type}:{data_hash}"
            return cache_key
        except Exception as e:
            logger.warning(f"Failed to generate cache key: {e}")
            # Return unique key that won't match anything
            return f"{node_id}:{node_type}:{id(data)}"
    
    def _is_cacheable_node(self, node_type: str) -> bool:
        """
        Check if node type is cacheable.
        
        Args:
            node_type: Node type
            
        Returns:
            True if cacheable, False otherwise
        """
        # Cacheable node types (deterministic, no side effects)
        cacheable_types = {
            "agent",
            "block", 
            "tool",
            "code",
            "condition",
        }
        
        # Non-cacheable node types (side effects or time-sensitive)
        non_cacheable_types = {
            "http_request",  # External API calls may change
            "database",      # Database state may change
            "s3",           # Storage state may change
            "google_drive", # Storage state may change
            "email",        # Side effect
            "slack",        # Side effect
            "discord",      # Side effect
            "human_approval",  # Interactive
            "webhook_trigger", # External trigger
            "schedule_trigger", # Time-based
        }
        
        return node_type in cacheable_types
    
    async def _execute_node_with_cache(
        self,
        node_id: str,
        node_type: str,
        node_data: Dict[str, Any],
        data: Any,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: str = "exponential",
    ) -> Any:
        """
        Execute node with caching support.
        
        Args:
            node_id: Node ID
            node_type: Node type
            node_data: Node configuration
            data: Input data
            nodes: All workflow nodes
            edges: All workflow edges
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay
            retry_backoff: Backoff strategy
            
        Returns:
            Node execution result
        """
        import time
        
        # Check if caching is enabled and node is cacheable
        if self.cache_enabled and self._is_cacheable_node(node_type):
            # Generate cache key
            cache_key = self._generate_cache_key(node_id, node_type, data)
            
            # Check cache
            if cache_key in self.node_cache:
                cached_result, timestamp = self.node_cache[cache_key]
                
                # Check if cache is still valid
                if time.time() - timestamp < self.cache_ttl:
                    logger.info(f"Cache hit for node {node_id} (type: {node_type})")
                    WorkflowMetrics.record_cache_hit(node_type)
                    return cached_result
                else:
                    logger.debug(f"Cache expired for node {node_id}")
                    del self.node_cache[cache_key]
        
        # Record cache miss
        if self.cache_enabled and self._is_cacheable_node(node_type):
            WorkflowMetrics.record_cache_miss(node_type)
        
        # Execute node (cache miss or not cacheable)
        result = await self._execute_node_with_retry(
            node_id=node_id,
            node_type=node_type,
            node_data=node_data,
            data=data,
            nodes=nodes,
            edges=edges,
            max_retries=max_retries,
            retry_delay=retry_delay,
            retry_backoff=retry_backoff,
        )
        
        # Cache result if applicable
        if self.cache_enabled and self._is_cacheable_node(node_type):
            cache_key = self._generate_cache_key(node_id, node_type, data)
            self.node_cache[cache_key] = (result, time.time())
            logger.debug(f"Cached result for node {node_id}")
        
        return result
    
    async def _execute_node_with_retry(
        self,
        node_id: str,
        node_type: str,
        node_data: Dict[str, Any],
        data: Any,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: str = "exponential",
    ) -> Any:
        """
        Execute a node with retry logic.
        
        Args:
            node_id: Node ID
            node_type: Node type
            node_data: Node configuration data
            data: Input data
            nodes: All workflow nodes
            edges: All workflow edges
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
            retry_backoff: Backoff strategy ('exponential' or 'linear')
            
        Returns:
            Node execution result
        """
        # Check if node is disabled
        if node_data.get("disabled", False):
            logger.info(f"Node {node_id} is disabled, skipping execution")
            # Update node status for SSE
            if self.execution_id:
                self.node_statuses[node_id] = {
                    "status": "skipped",
                    "message": "Node is disabled",
                    "startTime": datetime.utcnow().timestamp() * 1000,
                    "endTime": datetime.utcnow().timestamp() * 1000,
                }
            # Return input data unchanged
            return data
        
        last_error = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Log retry attempt
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{max_retries} for node {node_id}")
                
                # Execute node based on type
                if node_type == "start":
                    result = await self._execute_start_node(node_data, data)
                elif node_type == "trigger":
                    result = await self._execute_trigger_node(node_data, data)
                elif node_type == "end":
                    result = await self._execute_end_node(node_data, data)
                elif node_type == "condition":
                    result = await self._execute_condition_node(node_data, data)
                elif node_type == "agent":
                    result = await self._execute_agent_node(node_data, data)
                elif node_type == "block":
                    result = await self._execute_block_node(node_data, data)
                elif node_type == "tool":
                    result = await self._execute_tool_node(node_data, data)
                elif node_type == "http_request":
                    result = await self._execute_http_request_node(node_data, data)
                elif node_type == "loop":
                    result = await self._execute_loop_node(node_data, data, nodes, edges)
                elif node_type == "parallel":
                    result = await self._execute_parallel_node(node_data, data)
                elif node_type == "delay":
                    result = await self._execute_delay_node(node_data, data)
                elif node_type == "switch":
                    result = await self._execute_switch_node(node_data, data)
                elif node_type == "merge":
                    result = await self._execute_merge_node(node_data, data)
                elif node_type == "code":
                    result = await self._execute_code_node(node_data, data)
                elif node_type == "schedule_trigger":
                    result = await self._execute_schedule_trigger_node(node_data, data)
                elif node_type == "webhook_trigger":
                    result = await self._execute_webhook_trigger_node(node_data, data)
                elif node_type == "webhook_response":
                    result = await self._execute_webhook_response_node(node_data, data)
                elif node_type == "slack":
                    result = await self._execute_slack_node(node_data, data)
                elif node_type == "discord":
                    result = await self._execute_discord_node(node_data, data)
                elif node_type == "email":
                    result = await self._execute_email_node(node_data, data)
                elif node_type == "google_drive":
                    result = await self._execute_google_drive_node(node_data, data)
                elif node_type == "s3":
                    result = await self._execute_s3_node(node_data, data)
                elif node_type == "database":
                    result = await self._execute_database_node(node_data, data)
                elif node_type == "manager_agent":
                    result = await self._execute_manager_agent_node(node_data, data)
                elif node_type == "memory":
                    result = await self._execute_memory_node(node_data, data)
                elif node_type == "consensus":
                    result = await self._execute_consensus_node(node_data, data)
                elif node_type == "human_approval":
                    result = await self._execute_human_approval_node(node_data, data)
                else:
                    logger.warning(f"Unknown node type: {node_type}, passing through data")
                    result = data
                
                # Success - track retry count and return
                if attempt > 0:
                    logger.info(f"Node {node_id} succeeded after {attempt} retries")
                    self.retry_counts[node_id] = attempt
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Node {node_id} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                
                # Record retry
                if attempt > 0:
                    WorkflowMetrics.record_retry(node_type, attempt)
                
                # If this was the last attempt, raise the error
                if attempt >= max_retries:
                    logger.error(f"Node {node_id} failed after {max_retries} retries")
                    self.retry_counts[node_id] = max_retries
                    raise
                
                # Calculate delay for next retry
                if retry_backoff == "exponential":
                    delay = retry_delay * (2 ** attempt)
                else:  # linear
                    delay = retry_delay * (attempt + 1)
                
                logger.info(f"Waiting {delay}s before retry...")
                await asyncio.sleep(delay)
        
        # Should never reach here, but just in case
        raise last_error or Exception("Unknown error during node execution")
    
    async def _execute_start_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """Execute start node (pass through)."""
        return data
    
    async def _execute_trigger_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """Execute trigger node (pass through)."""
        return data
    
    async def _execute_end_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """Execute end node (return final result)."""
        return data
    
    async def _execute_condition_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """
        Execute condition node.
        
        Evaluates a condition and returns which branch to take.
        """
        condition = node_data.get("condition", "")
        branches = node_data.get("branches", [
            {"name": "true", "label": "True"},
            {"name": "false", "label": "False"},
        ])
        
        # Evaluate condition
        try:
            if condition:
                # Safe evaluation with limited context
                context = {
                    "data": data,
                    "context": self.execution_context,
                    "input": self.execution_context.get("input", {}),
                }
                
                # Use safe eval with restricted builtins
                result = self._safe_eval(condition, context)
                
                # Determine branch based on result
                if isinstance(result, bool):
                    branch = "true" if result else "false"
                else:
                    # For non-boolean results, check truthiness
                    branch = "true" if result else "false"
            else:
                # No condition specified, default to true
                import random
                branch = "true" if random.random() > 0.5 else "false"
            
            logger.info(f"Condition evaluated: {condition} -> {branch}")
            
        except Exception as e:
            logger.error(f"Condition evaluation error: {e}")
            # Default to false on error
            branch = "false"
        
        return {
            "branch": branch,
            "data": data,
            "condition": condition,
            "result": branch,
        }
    
    def _safe_eval(self, expression: str, context: Dict[str, Any]) -> Any:
        """
        Safely evaluate a Python expression.
        
        Args:
            expression: Python expression to evaluate
            context: Variables available in the expression
            
        Returns:
            Evaluation result
        """
        # Restricted builtins for safety
        safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "float": float,
            "int": int,
            "len": len,
            "list": list,
            "max": max,
            "min": min,
            "str": str,
            "sum": sum,
            "True": True,
            "False": False,
            "None": None,
        }
        
        try:
            # Evaluate with restricted context
            result = eval(expression, {"__builtins__": safe_builtins}, context)
            return result
        except Exception as e:
            logger.error(f"Expression evaluation failed: {e}")
            raise ValueError(f"Invalid expression: {str(e)}")
    
    async def _execute_agent_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute agent node.
        
        Calls an AI agent to process the data.
        """
        agent_id = node_data.get("agentId")
        agent_type = node_data.get("agentType", "general")
        
        logger.info(f"Executing agent: {agent_id or agent_type}")
        
        # TODO: Implement actual agent execution
        # For now, simulate agent processing
        await asyncio.sleep(0.5)  # Simulate processing time
        
        result = {
            "agent_output": f"Processed by {agent_type} agent",
            "input": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return result
    
    async def _execute_block_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute block node.
        
        Executes a custom block (logic, transformation, etc.).
        """
        block_id = node_data.get("blockId")
        block_type = node_data.get("blockType", "logic")
        
        logger.info(f"Executing block: {block_id or block_type}")
        
        # TODO: Implement actual block execution
        # For now, simulate block processing
        await asyncio.sleep(0.3)  # Simulate processing time
        
        result = {
            "block_output": f"Processed by {block_type} block",
            "input": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return result
    
    async def _execute_tool_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute tool node.
        
        Calls an external tool or API using ToolRegistry with user's API keys.
        """
        from backend.core.tools.registry import ToolRegistry
        from backend.services.api_key_service import APIKeyService
        
        tool_id = node_data.get("toolId") or node_data.get("tool_id")
        tool_name = node_data.get("name", "unknown")
        tool_config = node_data.get("config", {})
        user_id = node_data.get("user_id") or self.execution_context.get("user_id")
        
        logger.info(f"Executing tool: {tool_id or tool_name}")
        logger.info(f"Tool config: {tool_config}")
        logger.info(f"Input data: {data}")
        
        if not tool_id:
            logger.error(f"No tool_id provided for tool node: {tool_name}")
            return {
                "error": "No tool_id provided",
                "tool_name": tool_name,
                "input": data,
            }
        
        try:
            # Prepare parameters for tool execution
            # If data is a string (like a prompt), use it as the query parameter
            if isinstance(data, str):
                params = {"q": data, "query": data}
            elif isinstance(data, dict):
                params = data.copy()
            else:
                params = {"input": str(data)}
            
            # Merge with tool configuration
            params.update(tool_config)
            
            # Get user's API key for this tool if needed
            credentials = None
            if user_id:
                try:
                    api_key_service = APIKeyService(self.db)
                    
                    # Get service name from tool metadata (improved approach)
                    service_name = self._get_tool_service_name(tool_id)
                    
                    if service_name:
                        api_key = api_key_service.get_decrypted_api_key(user_id, service_name)
                        
                        if api_key:
                            credentials = {"api_key": api_key}
                            logger.info(f"Using user's API key for service: {service_name}")
                        else:
                            logger.info(f"No user API key found for service: {service_name}, using environment variable")
                    else:
                        logger.info(f"No service name mapping for tool: {tool_id}")
                except Exception as e:
                    logger.warning(f"Failed to get user API key: {e}")
            
            logger.info(f"Calling ToolRegistry.execute_tool with params: {params}")
            
            # Execute tool using ToolRegistry
            result = await ToolRegistry.execute_tool(
                tool_id=tool_id,
                params=params,
                credentials=credentials
            )
            
            logger.info(f"Tool execution result: {result}")
            
            return {
                "tool_output": result,
                "tool_id": tool_id,
                "tool_name": tool_name,
                "input": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "tool_id": tool_id,
                "tool_name": tool_name,
                "input": data,
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    def _get_tool_service_name(self, tool_id: str) -> Optional[str]:
        """
        Get service name for a tool from ToolRegistry metadata.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Service name for API key lookup, or None if not found
        """
        from backend.core.tools.registry import ToolRegistry
        
        try:
            # Get tool configuration from registry
            tool_config = ToolRegistry.get_tool_config(tool_id)
            
            if not tool_config:
                logger.warning(f"Tool config not found for: {tool_id}")
                return None
            
            # Check if tool has api_key_env configured
            if tool_config.api_key_env:
                # Extract service name from environment variable name
                # e.g., "YOUTUBE_API_KEY" -> "youtube"
                # e.g., "OPENAI_API_KEY" -> "openai"
                env_var = tool_config.api_key_env
                service_name = env_var.replace("_API_KEY", "").replace("_KEY", "").lower()
                logger.info(f"Extracted service name '{service_name}' from env var '{env_var}'")
                return service_name
            
            # Fallback: use tool_id as service name
            # This works for tools like "openai", "anthropic", etc.
            logger.info(f"No api_key_env found, using tool_id as service name: {tool_id}")
            return tool_id
            
        except Exception as e:
            logger.error(f"Failed to get service name for tool {tool_id}: {e}")
            # Fallback to tool_id
            return tool_id
    
    async def _execute_http_request_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute HTTP Request node.
        
        Makes HTTP requests to external APIs with full configuration support.
        """
        import httpx
        import json as json_lib
        
        method = node_data.get("method", "GET").upper()
        url = node_data.get("url", "")
        headers = node_data.get("headers", {})
        query_params = node_data.get("queryParams", {})
        body = node_data.get("body", "")
        body_type = node_data.get("bodyType", "json")
        auth_type = node_data.get("authType", "none")
        auth_config = node_data.get("authConfig", {})
        timeout = node_data.get("timeout", 30)
        follow_redirects = node_data.get("followRedirects", True)
        
        logger.info(f"Executing HTTP Request: {method} {url}")
        
        if not url:
            return {
                "error": "URL is required",
                "status_code": None,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        try:
            # Prepare headers
            request_headers = dict(headers) if headers else {}
            
            # Handle authentication
            if auth_type == "bearer":
                token = auth_config.get("token", "")
                if token:
                    request_headers["Authorization"] = f"Bearer {token}"
            elif auth_type == "basic":
                username = auth_config.get("username", "")
                password = auth_config.get("password", "")
                if username and password:
                    import base64
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    request_headers["Authorization"] = f"Basic {credentials}"
            elif auth_type == "api_key":
                key_name = auth_config.get("keyName", "X-API-Key")
                key_value = auth_config.get("keyValue", "")
                if key_value:
                    request_headers[key_name] = key_value
            
            # Prepare request body
            request_body = None
            if method in ["POST", "PUT", "PATCH"] and body:
                if body_type == "json":
                    try:
                        request_body = json_lib.loads(body) if isinstance(body, str) else body
                        request_headers["Content-Type"] = "application/json"
                    except json_lib.JSONDecodeError:
                        request_body = body
                elif body_type == "form":
                    request_body = body
                    request_headers["Content-Type"] = "application/x-www-form-urlencoded"
                elif body_type == "raw":
                    request_body = body
                else:
                    request_body = body
            
            # Make HTTP request
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=follow_redirects
            ) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    params=query_params,
                    json=request_body if body_type == "json" and request_body else None,
                    data=request_body if body_type != "json" and request_body else None,
                )
                
                # Parse response
                response_data = None
                content_type = response.headers.get("content-type", "")
                
                if "application/json" in content_type:
                    try:
                        response_data = response.json()
                    except:
                        response_data = response.text
                else:
                    response_data = response.text
                
                result = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "data": response_data,
                    "success": 200 <= response.status_code < 300,
                    "method": method,
                    "url": url,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                
                logger.info(f"HTTP Request completed: {response.status_code}")
                return result
                
        except httpx.TimeoutException as e:
            logger.error(f"HTTP Request timeout: {e}")
            return {
                "error": "Request timeout",
                "status_code": None,
                "method": method,
                "url": url,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"HTTP Request failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "status_code": None,
                "method": method,
                "url": url,
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _execute_loop_node(
        self, 
        node_data: Dict[str, Any], 
        data: Any,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Any:
        """
        Execute loop node.
        
        Iterates over a collection and executes child nodes for each item.
        """
        loop_type = node_data.get("loopType", "forEach")
        items = node_data.get("items", [])
        max_iterations = node_data.get("maxIterations", 100)
        condition = node_data.get("condition", "")
        count = node_data.get("count", 1)
        loop_body_nodes = node_data.get("loopBodyNodes", [])
        
        logger.info(f"Executing loop: {loop_type}")
        
        results = []
        iteration = 0
        
        try:
            if loop_type == "forEach":
                # Iterate over items
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = list(data.values())
                else:
                    items = node_data.get("items", [])
                
                for i, item in enumerate(items[:max_iterations]):
                    logger.info(f"Loop iteration {i + 1}/{len(items)}")
                    
                    # Execute loop body if defined
                    if loop_body_nodes:
                        result = await self._execute_loop_body(loop_body_nodes, item, i)
                        results.append(result)
                    else:
                        results.append(item)
                    
                    iteration = i + 1
                    
            elif loop_type == "while":
                # While loop with condition evaluation
                if not condition:
                    logger.warning("While loop has no condition, executing once")
                    results = data
                else:
                    loop_data = data
                    
                    while iteration < max_iterations:
                        # Evaluate condition
                        context = {
                            "data": loop_data,
                            "iteration": iteration,
                            "results": results,
                            "workflow_vars": self.execution_context,
                        }
                        
                        try:
                            should_continue = self._safe_eval(condition, context)
                            
                            if not should_continue:
                                logger.info(f"While loop condition false at iteration {iteration}")
                                break
                        except Exception as e:
                            logger.error(f"While loop condition evaluation failed: {e}")
                            break
                        
                        # Execute loop body
                        if loop_body_nodes:
                            loop_data = await self._execute_loop_body(loop_body_nodes, loop_data, iteration)
                            results.append(loop_data)
                        else:
                            results.append(loop_data)
                        
                        iteration += 1
                    
                    if iteration >= max_iterations:
                        logger.warning(f"While loop reached max iterations: {max_iterations}")
                        
            elif loop_type == "count":
                # Count loop
                for i in range(min(count, max_iterations)):
                    logger.info(f"Count loop iteration {i + 1}/{count}")
                    
                    # Execute loop body if defined
                    if loop_body_nodes:
                        result = await self._execute_loop_body(loop_body_nodes, data, i)
                        results.append(result)
                    else:
                        results.append({"iteration": i + 1, "data": data})
                    
                    iteration = i + 1
            
            return {
                "loop_results": results,
                "iterations": iteration,
                "loop_type": loop_type,
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Loop execution failed: {e}", exc_info=True)
            return {
                "loop_results": results,
                "iterations": iteration,
                "loop_type": loop_type,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _execute_loop_body(
        self,
        loop_body_nodes: List[Dict[str, Any]],
        data: Any,
        iteration: int
    ) -> Any:
        """
        Execute loop body nodes.
        
        Args:
            loop_body_nodes: Nodes to execute in loop body
            data: Input data for this iteration
            iteration: Current iteration number
            
        Returns:
            Loop body execution result
        """
        result = data
        
        for node_config in loop_body_nodes:
            node_type = node_config.get("type") or node_config.get("node_type")
            node_data = node_config.get("data") or node_config.get("configuration", {})
            
            # Add iteration context
            node_data["_iteration"] = iteration
            
            # Execute node
            if node_type == "agent":
                result = await self._execute_agent_node(node_data, result)
            elif node_type == "block":
                result = await self._execute_block_node(node_data, result)
            elif node_type == "tool":
                result = await self._execute_tool_node(node_data, result)
            elif node_type == "http_request":
                result = await self._execute_http_request_node(node_data, result)
            elif node_type == "code":
                result = await self._execute_code_node(node_data, result)
            else:
                logger.warning(f"Unknown node type in loop body: {node_type}")
        
        return result
    
    async def _execute_parallel_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute parallel node.
        
        Executes multiple branches in parallel and combines results.
        """
        branches = node_data.get("branches", [])
        
        logger.info(f"Executing parallel node with {len(branches)} branches")
        
        # Execute branches in parallel (simplified for now)
        results = []
        tasks = []
        
        for i, branch in enumerate(branches):
            # Simulate parallel execution
            task = asyncio.create_task(self._execute_parallel_branch(branch, data, i))
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "parallel_results": results,
            "branch_count": len(branches),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _execute_parallel_branch(
        self, 
        branch: Dict[str, Any], 
        data: Any, 
        index: int
    ) -> Any:
        """
        Execute a single parallel branch.
        
        Args:
            branch: Branch configuration with nodes to execute
            data: Input data for the branch
            index: Branch index
            
        Returns:
            Branch execution result
        """
        branch_name = branch.get("name", f"Branch {index + 1}")
        branch_nodes = branch.get("nodes", [])
        
        logger.info(f"Executing parallel branch {index + 1}: {branch_name} with {len(branch_nodes)} nodes")
        
        try:
            # Execute nodes in the branch sequentially
            result = data
            
            for node_config in branch_nodes:
                node_id = node_config.get("id")
                node_type = node_config.get("type") or node_config.get("node_type")
                node_data = node_config.get("data") or node_config.get("configuration", {})
                
                logger.info(f"Branch {branch_name}: Executing node {node_id} ({node_type})")
                
                # Execute node based on type
                if node_type == "agent":
                    result = await self._execute_agent_node(node_data, result)
                elif node_type == "block":
                    result = await self._execute_block_node(node_data, result)
                elif node_type == "tool":
                    result = await self._execute_tool_node(node_data, result)
                elif node_type == "http_request":
                    result = await self._execute_http_request_node(node_data, result)
                elif node_type == "code":
                    result = await self._execute_code_node(node_data, result)
                elif node_type == "condition":
                    result = await self._execute_condition_node(node_data, result)
                else:
                    logger.warning(f"Unknown node type in branch: {node_type}")
                    # Pass through data
                    pass
            
            return {
                "branch_index": index,
                "branch_name": branch_name,
                "success": True,
                "output": result,
                "nodes_executed": len(branch_nodes),
            }
            
        except Exception as e:
            logger.error(f"Branch {branch_name} execution failed: {e}", exc_info=True)
            return {
                "branch_index": index,
                "branch_name": branch_name,
                "success": False,
                "error": str(e),
                "nodes_executed": 0,
            }
    
    async def _execute_delay_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute delay node.
        
        Pauses execution for a specified duration.
        """
        delay_ms = node_data.get("delayMs", 1000)
        delay_seconds = delay_ms / 1000
        
        logger.info(f"Executing delay: {delay_ms}ms")
        
        await asyncio.sleep(delay_seconds)
        
        return {
            "delayed_data": data,
            "delay_ms": delay_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _execute_switch_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """
        Execute switch node.
        
        Evaluates a variable against multiple cases and returns the matching branch.
        """
        variable = node_data.get("variable", "")
        cases = node_data.get("cases", [])
        default_case = node_data.get("defaultCase", True)
        
        # Get the value to switch on
        try:
            context = {"data": data, "input": self.execution_context.get("input")}
            # Simple template replacement
            value = variable
            if "{{" in variable and "}}" in variable:
                # Extract variable path (e.g., {{$json.status}} -> data.status)
                var_path = variable.replace("{{", "").replace("}}", "").strip()
                if var_path.startswith("$json."):
                    field = var_path.replace("$json.", "")
                    value = data.get(field) if isinstance(data, dict) else None
                else:
                    value = eval(var_path, {"__builtins__": {}}, context)
            
            # Check each case
            for case in cases:
                condition = case.get("condition", "")
                case_id = case.get("id")
                
                # Evaluate condition
                try:
                    # Support simple comparisons
                    if condition.startswith("==="):
                        expected = condition.replace("===", "").strip().strip("'\"")
                        if str(value) == expected:
                            return {"branch": case_id, "data": data, "matched_case": case.get("label")}
                    elif condition.startswith("=="):
                        expected = condition.replace("==", "").strip().strip("'\"")
                        if str(value) == expected:
                            return {"branch": case_id, "data": data, "matched_case": case.get("label")}
                    elif condition.startswith(">"):
                        threshold = float(condition.replace(">", "").strip())
                        if float(value) > threshold:
                            return {"branch": case_id, "data": data, "matched_case": case.get("label")}
                    elif condition.startswith("<"):
                        threshold = float(condition.replace("<", "").strip())
                        if float(value) < threshold:
                            return {"branch": case_id, "data": data, "matched_case": case.get("label")}
                except Exception as e:
                    logger.warning(f"Failed to evaluate case condition: {e}")
                    continue
            
            # No case matched, use default
            if default_case:
                return {"branch": "default", "data": data, "matched_case": "default"}
            else:
                raise ValueError(f"No matching case for value: {value}")
                
        except Exception as e:
            logger.error(f"Switch node evaluation failed: {e}")
            if default_case:
                return {"branch": "default", "data": data, "matched_case": "default"}
            raise
    
    async def _execute_merge_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute merge node.
        
        Merges multiple inputs based on the configured mode.
        Note: In current implementation, this is simplified as we process sequentially.
        """
        mode = node_data.get("mode", "wait_all")
        
        logger.info(f"Executing merge node (mode: {mode})")
        
        # For now, just pass through the data
        # In a full implementation, this would wait for multiple parallel branches
        return data
    
    async def _execute_code_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute code node.
        
        Runs user-provided Python or JavaScript code in a sandboxed environment.
        """
        language = node_data.get("language", "javascript")
        code = node_data.get("code", "")
        timeout = node_data.get("timeout", 5)  # seconds
        
        if not code:
            logger.warning("Code node has no code, passing through data")
            return data
        
        logger.info(f"Executing code node ({language})")
        
        try:
            if language == "python":
                # Execute Python code in restricted environment
                context = {
                    "input_data": data,
                    "workflow_vars": self.execution_context,
                    "output": None,
                }
                
                # Restricted builtins for safety
                safe_builtins = {
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "map": map,
                    "filter": filter,
                    "sum": sum,
                    "min": min,
                    "max": max,
                    "abs": abs,
                    "round": round,
                    "sorted": sorted,
                    "reversed": reversed,
                    "any": any,
                    "all": all,
                }
                
                # Execute with timeout
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Code execution timeout")
                
                # Set timeout (Unix only)
                try:
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(timeout)
                    
                    exec(code, {"__builtins__": safe_builtins}, context)
                    
                    signal.alarm(0)  # Cancel alarm
                except AttributeError:
                    # Windows doesn't support SIGALRM, execute without timeout
                    exec(code, {"__builtins__": safe_builtins}, context)
                
                result = context.get("output", data)
                return result
                
            elif language == "javascript":
                # Execute JavaScript using PyMiniRacer
                try:
                    from py_mini_racer import MiniRacer
                    
                    # Create JavaScript context
                    ctx = MiniRacer()
                    
                    # Prepare input data
                    import json
                    input_json = json.dumps(data) if not isinstance(data, str) else f'"{data}"'
                    
                    # Set up context
                    ctx.eval(f"var input_data = {input_json};")
                    ctx.eval(f"var workflow_vars = {json.dumps(self.execution_context)};")
                    ctx.eval("var output = null;")
                    
                    # Execute user code
                    ctx.eval(code)
                    
                    # Get output
                    output = ctx.eval("output")
                    
                    # If output is null, return input data
                    if output is None:
                        return data
                    
                    return output
                    
                except ImportError:
                    logger.warning("PyMiniRacer not installed, falling back to Node.js subprocess")
                    # Fallback to Node.js subprocess
                    return await self._execute_javascript_subprocess(code, data, timeout)
                    
            else:
                raise ValueError(f"Unsupported language: {language}")
                
        except TimeoutError as e:
            logger.error(f"Code execution timeout: {e}")
            return {
                "error": "Code execution timeout",
                "timeout": timeout,
                "language": language,
            }
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            raise ValueError(f"Code execution error: {str(e)}")
    
    async def _execute_javascript_subprocess(
        self,
        code: str,
        data: Any,
        timeout: int
    ) -> Any:
        """
        Execute JavaScript using Node.js subprocess (fallback).
        
        Args:
            code: JavaScript code
            data: Input data
            timeout: Timeout in seconds
            
        Returns:
            Execution result
        """
        import asyncio
        import json
        import tempfile
        import os
        
        try:
            # Create temporary file with JavaScript code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                # Wrap code with input/output handling
                input_json = json.dumps(data)
                wrapped_code = f"""
                const input_data = {input_json};
                const workflow_vars = {json.dumps(self.execution_context)};
                let output = null;
                
                {code}
                
                // Output result
                if (output !== null) {{
                    console.log(JSON.stringify(output));
                }} else {{
                    console.log(JSON.stringify(input_data));
                }}
                """
                f.write(wrapped_code)
                temp_file = f.name
            
            try:
                # Execute Node.js
                process = await asyncio.create_subprocess_exec(
                    'node',
                    temp_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Wait with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                # Parse output
                if process.returncode == 0:
                    output_str = stdout.decode('utf-8').strip()
                    result = json.loads(output_str)
                    return result
                else:
                    error_msg = stderr.decode('utf-8')
                    logger.error(f"Node.js execution error: {error_msg}")
                    return {
                        "error": "JavaScript execution failed",
                        "details": error_msg,
                    }
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except asyncio.TimeoutError:
            logger.error("Node.js execution timeout")
            return {
                "error": "JavaScript execution timeout",
                "timeout": timeout,
            }
        except FileNotFoundError:
            logger.error("Node.js not found in PATH")
            return {
                "error": "Node.js not installed or not in PATH",
                "message": "Please install Node.js to execute JavaScript code",
            }
        except Exception as e:
            logger.error(f"JavaScript subprocess execution failed: {e}")
            return {
                "error": str(e),
                "language": "javascript",
            }
    
    async def _execute_schedule_trigger_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute schedule trigger node.
        
        Note: Actual scheduling is handled by a separate scheduler service.
        This just passes through the data when triggered.
        """
        cron_expression = node_data.get("cronExpression", "")
        timezone = node_data.get("timezone", "UTC")
        
        logger.info(f"Schedule trigger executed (cron: {cron_expression}, tz: {timezone})")
        
        return {
            "trigger_type": "schedule",
            "cron_expression": cron_expression,
            "timezone": timezone,
            "triggered_at": datetime.utcnow().isoformat(),
            "data": data,
        }
    
    async def _execute_webhook_trigger_node(self, node_data: Dict[str, Any], data: Any) -> Any:
        """
        Execute webhook trigger node.
        
        Receives data from webhook and passes it through.
        """
        webhook_id = node_data.get("webhookId", "")
        method = node_data.get("method", "POST")
        
        logger.info(f"Webhook trigger executed (id: {webhook_id}, method: {method})")
        
        return {
            "trigger_type": "webhook",
            "webhook_id": webhook_id,
            "method": method,
            "triggered_at": datetime.utcnow().isoformat(),
            "data": data,
        }
    
    async def _execute_webhook_response_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """
        Execute webhook response node.
        
        Formats the response to be sent back to the webhook caller.
        """
        status_code = node_data.get("statusCode", 200)
        headers = node_data.get("headers", {"Content-Type": "application/json"})
        response_body = node_data.get("responseBody", '{"success": true, "data": {{$json}}}')
        
        # Template replacement
        try:
            import json
            response_text = response_body.replace("{{$json}}", json.dumps(data))
            response_data = json.loads(response_text)
        except Exception as e:
            logger.warning(f"Failed to parse response template: {e}")
            response_data = {"success": True, "data": data}
        
        return {
            "status_code": status_code,
            "headers": headers,
            "body": response_data,
        }


    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status_update: Dict[str, Any]
    ) -> None:
        """
        Update node execution status for SSE streaming.
        
        Args:
            execution_id: Execution ID
            node_id: Node ID
            status_update: Status update data
        """
        if node_id not in self.node_statuses:
            self.node_statuses[node_id] = {}
        
        self.node_statuses[node_id].update(status_update)
        logger.debug(f"Updated node status: {node_id} -> {status_update.get('status')}")
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current execution status for SSE streaming.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution status with node statuses
        """
        # Determine overall status
        if not self.node_statuses:
            status = "pending"
        elif any(s.get("status") == "failed" for s in self.node_statuses.values()):
            status = "failed"
        elif any(s.get("status") == "running" for s in self.node_statuses.values()):
            status = "running"
        elif all(s.get("status") in ["success", "skipped"] for s in self.node_statuses.values()):
            status = "completed"
        else:
            status = "running"
        
        return {
            "id": execution_id,
            "status": status,
            "node_statuses": self.node_statuses,
            "execution_context": self.execution_context,
        }
    
    async def get_latest_execution(self, workflow_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the latest execution for a workflow.
        
        Args:
            workflow_id: Workflow ID
            user_id: User ID
            
        Returns:
            Latest execution data or None
        """
        # For now, return current execution if it exists
        if self.execution_id:
            return {
                "id": self.execution_id,
                "workflow_id": workflow_id,
                "user_id": user_id,
                "status": "running",
                "created_at": datetime.utcnow().isoformat(),
            }
        return None


async def execute_workflow(workflow: Any, db: Session, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a workflow.
    
    Args:
        workflow: Workflow object
        db: Database session
        input_data: Input data for the workflow
        
    Returns:
        Execution result
    """
    executor = WorkflowExecutor(workflow, db)
    return await executor.execute(input_data)

    
    async def _execute_slack_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute Slack notification node."""
        channel = node_data.get("channel", "general")
        message = node_data.get("message", "")
        username = node_data.get("username", "Workflow Bot")
        icon_emoji = node_data.get("iconEmoji", ":robot_face:")
        
        # Template replacement
        message_text = self._replace_templates(message, data)
        
        logger.info(f"Sending Slack message to #{channel}")
        
        try:
            # Get Slack API key from database
            from backend.services.api_key_service import APIKeyService
            api_key_service = APIKeyService(self.db)
            
            user_id = self.execution_context.get("user_id")
            if not user_id:
                raise ValueError("User ID not found in execution context")
            
            slack_key = await api_key_service.get_api_key(user_id, "slack")
            if not slack_key:
                raise ValueError("Slack API key not configured")
            
            # Use actual Slack service
            from backend.services.integrations.slack_service import SlackService
            slack_service = SlackService(slack_key)
            
            result = await slack_service.send_message(
                channel=channel,
                text=message_text,
                username=username,
                icon_emoji=icon_emoji,
            )
            
            return {
                "success": True,
                "channel": channel,
                "message": message_text,
                "timestamp": result.get("ts"),
                "slack_response": result,
            }
            
        except Exception as e:
            logger.error(f"Slack node execution failed: {e}")
            # Fallback to mock response for development
            return {
                "success": False,
                "error": str(e),
                "channel": channel,
                "message": message_text,
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _execute_discord_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute Discord webhook node."""
        webhook_url = node_data.get("webhookUrl", "")
        message = node_data.get("message", "")
        username = node_data.get("username", "Workflow Bot")
        avatar_url = node_data.get("avatarUrl", "")
        embed_title = node_data.get("embedTitle", "")
        embed_color = node_data.get("embedColor", "#5865F2")
        
        # Template replacement
        message_text = self._replace_templates(message, data)
        embed_title_text = self._replace_templates(embed_title, data) if embed_title else ""
        
        logger.info(f"Sending Discord webhook message")
        
        try:
            from backend.services.integrations.discord_service import DiscordService
            discord_service = DiscordService()
            
            if embed_title_text:
                # Send with embed
                color_int = discord_service.hex_to_int_color(embed_color)
                result = await discord_service.send_embed(
                    webhook_url=webhook_url,
                    title=embed_title_text,
                    description=message_text,
                    color=color_int,
                    username=username,
                    avatar_url=avatar_url if avatar_url else None,
                )
            else:
                # Send simple message
                result = await discord_service.send_webhook(
                    webhook_url=webhook_url,
                    content=message_text,
                    username=username,
                    avatar_url=avatar_url if avatar_url else None,
                )
            
            return {
                "success": result.get("success", False),
                "message": message_text,
                "timestamp": datetime.utcnow().isoformat(),
                "discord_response": result,
            }
            
        except Exception as e:
            logger.error(f"Discord node execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": message_text,
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _execute_email_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute email sending node."""
        to = node_data.get("to", [])
        cc = node_data.get("cc", [])
        bcc = node_data.get("bcc", [])
        subject = node_data.get("subject", "")
        body = node_data.get("body", "")
        body_type = node_data.get("bodyType", "text")
        
        # Template replacement
        subject_text = self._replace_templates(subject, data)
        body_text = self._replace_templates(body, data)
        
        logger.info(f"Sending email to {len(to)} recipients")
        
        try:
            # Get SMTP credentials from database
            from backend.services.api_key_service import APIKeyService
            api_key_service = APIKeyService(self.db)
            
            user_id = self.execution_context.get("user_id")
            if not user_id:
                raise ValueError("User ID not found in execution context")
            
            # Get SMTP configuration
            smtp_config = await api_key_service.get_api_key(user_id, "smtp")
            if not smtp_config:
                raise ValueError("SMTP configuration not found")
            
            # Parse SMTP config (stored as JSON)
            import json
            config = json.loads(smtp_config) if isinstance(smtp_config, str) else smtp_config
            
            from backend.services.integrations.email_service import EmailService
            email_service = EmailService(
                smtp_host=config.get("smtp_host"),
                smtp_port=config.get("smtp_port", 587),
                username=config.get("username"),
                password=config.get("password"),
                use_tls=config.get("use_tls", True),
            )
            
            result = await email_service.send_email(
                to=to,
                subject=subject_text,
                body=body_text,
                body_type=body_type,
                cc=cc if cc else None,
                bcc=bcc if bcc else None,
            )
            
            return {
                "success": True,
                "recipients": result.get("recipients"),
                "to": to,
                "cc": cc,
                "subject": subject_text,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Email node execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipients": len(to),
                "subject": subject_text,
                "timestamp": datetime.utcnow().isoformat(),
            }
    
    async def _execute_google_drive_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute Google Drive operation node."""
        action = node_data.get("action", "upload")
        folder_id = node_data.get("folderId", "root")
        file_name = node_data.get("fileName", "")
        file_content = node_data.get("fileContent", "")
        file_id = node_data.get("fileId", "")
        mime_type = node_data.get("mimeType", "text/plain")
        
        # Template replacement
        file_name_text = self._replace_templates(file_name, data)
        file_content_text = self._replace_templates(file_content, data)
        
        logger.info(f"Google Drive {action} operation")
        
        try:
            # Get Google Drive credentials from API key service
            user_id = self.execution_context.get("user_id")
            if not user_id:
                return {
                    "success": False,
                    "error": "User ID not found in execution context",
                    "action": action,
                }
            
            from backend.services.api_key_service import APIKeyService
            api_key_service = APIKeyService(self.db)
            
            # Get Google Drive credentials
            google_creds = api_key_service.get_decrypted_api_key(user_id, "google_drive")
            if not google_creds:
                return {
                    "success": False,
                    "error": "Google Drive credentials not configured",
                    "action": action,
                }
            
            # Parse credentials
            import json
            creds_dict = json.loads(google_creds) if isinstance(google_creds, str) else google_creds
            
            from backend.services.integrations.google_drive_service import GoogleDriveService
            drive_service = GoogleDriveService(creds_dict)
            
            # Execute operation
            if action == "upload":
                result = await drive_service.upload_file(
                    file_name=file_name_text,
                    content=file_content_text,
                    mime_type=mime_type,
                    folder_id=folder_id if folder_id != "root" else None,
                )
                return result
            
            elif action == "download":
                if not file_id:
                    return {
                        "success": False,
                        "error": "file_id is required for download",
                        "action": action,
                    }
                result = await drive_service.download_file(file_id=file_id)
                return result
            
            elif action == "list":
                result = await drive_service.list_files(
                    folder_id=folder_id if folder_id != "root" else None,
                )
                return result
            
            elif action == "delete":
                if not file_id:
                    return {
                        "success": False,
                        "error": "file_id is required for delete",
                        "action": action,
                    }
                result = await drive_service.delete_file(file_id=file_id)
                return result
            
            elif action == "share":
                email = node_data.get("email", "")
                role = node_data.get("role", "reader")
                
                if not file_id or not email:
                    return {
                        "success": False,
                        "error": "file_id and email are required for share",
                        "action": action,
                    }
                
                result = await drive_service.share_file(
                    file_id=file_id,
                    email=email,
                    role=role,
                )
                return result
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported action: {action}",
                    "action": action,
                }
            
        except Exception as e:
            logger.error(f"Google Drive node execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "action": action,
                "error": str(e),
                "file_name": file_name_text,
            }
    
    async def _execute_s3_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute AWS S3 operation node."""
        action = node_data.get("action", "upload")
        bucket = node_data.get("bucket", "")
        key = node_data.get("key", "")
        content = node_data.get("content", "")
        region = node_data.get("region", "us-east-1")
        aws_access_key_id = node_data.get("awsAccessKeyId", "")
        aws_secret_access_key = node_data.get("awsSecretAccessKey", "")
        prefix = node_data.get("prefix", "")
        
        # Template replacement
        key_text = self._replace_templates(key, data)
        content_text = self._replace_templates(content, data)
        
        logger.info(f"S3 {action} operation on bucket {bucket}")
        
        try:
            from backend.services.integrations.s3_service import S3Service
            
            # Get AWS credentials from API key service if not provided
            if not aws_access_key_id or not aws_secret_access_key:
                user_id = self.execution_context.get("user_id")
                if user_id:
                    try:
                        from backend.services.api_key_service import APIKeyService
                        api_key_service = APIKeyService(self.db)
                        
                        # Try to get AWS credentials
                        aws_creds = api_key_service.get_decrypted_api_key(user_id, "aws")
                        if aws_creds:
                            import json
                            creds = json.loads(aws_creds) if isinstance(aws_creds, str) else aws_creds
                            aws_access_key_id = creds.get("access_key_id", "")
                            aws_secret_access_key = creds.get("secret_access_key", "")
                    except Exception as e:
                        logger.warning(f"Failed to get AWS credentials: {e}")
            
            # Create S3 service
            s3_service = S3Service(
                aws_access_key_id=aws_access_key_id if aws_access_key_id else None,
                aws_secret_access_key=aws_secret_access_key if aws_secret_access_key else None,
                region_name=region,
            )
            
            # Execute operation
            if action == "upload":
                # Convert content to bytes
                content_bytes = content_text.encode('utf-8') if isinstance(content_text, str) else content_text
                result = await s3_service.upload_file(
                    bucket=bucket,
                    key=key_text,
                    file_content=content_bytes,
                )
                return result
            
            elif action == "download":
                result = await s3_service.download_file(
                    bucket=bucket,
                    key=key_text,
                )
                return result
            
            elif action == "list":
                result = await s3_service.list_objects(
                    bucket=bucket,
                    prefix=prefix if prefix else None,
                )
                return result
            
            elif action == "delete":
                result = await s3_service.delete_object(
                    bucket=bucket,
                    key=key_text,
                )
                return result
            
            elif action == "presigned_url":
                expiration = node_data.get("expiration", 3600)
                result = await s3_service.get_presigned_url(
                    bucket=bucket,
                    key=key_text,
                    expiration=expiration,
                )
                return result
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported action: {action}",
                    "action": action,
                }
            
        except Exception as e:
            logger.error(f"S3 node execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "action": action,
                "error": str(e),
                "bucket": bucket,
                "key": key_text,
            }
    
    async def _execute_database_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute database operation node."""
        db_type = node_data.get("dbType", "postgresql")
        operation = node_data.get("operation", "query")
        query = node_data.get("query", "")
        connection_string = node_data.get("connectionString", "")
        host = node_data.get("host", "")
        port = node_data.get("port")
        database = node_data.get("database", "")
        username = node_data.get("username", "")
        password = node_data.get("password", "")
        
        # Template replacement
        query_text = self._replace_templates(query, data)
        
        logger.info(f"Database {operation} on {db_type}")
        
        try:
            from backend.services.integrations.database_service import DatabaseService
            
            # Create database service
            db_service = DatabaseService(
                db_type=db_type,
                connection_string=connection_string if connection_string else None,
                host=host if host else None,
                port=port if port else None,
                database=database if database else None,
                username=username if username else None,
                password=password if password else None,
            )
            
            # Execute operation
            if operation == "query":
                result = await db_service.execute_query(query_text)
                return result
            
            elif operation == "test_connection":
                result = await db_service.test_connection()
                return result
            
            elif operation == "list_tables":
                result = await db_service.list_tables()
                return result
            
            else:
                # Generic query execution
                result = await db_service.execute_query(query_text)
                return result
            
        except Exception as e:
            logger.error(f"Database node execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "operation": operation,
                "error": str(e),
                "db_type": db_type,
            }
    
    def _replace_templates(self, template: str, data: Any) -> str:
        """Replace template variables in a string."""
        if not template or not isinstance(template, str):
            return template
        
        import re
        import json
        
        result = template
        
        # Replace {{$json.field}} patterns
        json_pattern = r'\{\{\$json\.([^}]+)\}\}'
        matches = re.findall(json_pattern, result)
        
        for field in matches:
            try:
                if isinstance(data, dict):
                    value = data.get(field, "")
                    result = result.replace(f"{{{{$json.{field}}}}}", str(value))
            except Exception as e:
                logger.warning(f"Failed to replace template variable $json.{field}: {e}")
        
        # Replace {{$json}} with entire data
        if "{{$json}}" in result:
            try:
                result = result.replace("{{$json}}", json.dumps(data))
            except Exception as e:
                logger.warning(f"Failed to replace $json: {e}")
        
        # Replace {{$workflow.*}} patterns
        workflow_pattern = r'\{\{\$workflow\.([^}]+)\}\}'
        matches = re.findall(workflow_pattern, result)
        
        for field in matches:
            try:
                value = self.execution_context.get(field, "")
                result = result.replace(f"{{{{$workflow.{field}}}}}", str(value))
            except Exception as e:
                logger.warning(f"Failed to replace template variable $workflow.{field}: {e}")
        
        return result

    
    async def _execute_manager_agent_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute manager agent node with hierarchical delegation."""
        role = node_data.get("role", "Manager")
        goal = node_data.get("goal", "")
        delegation_strategy = node_data.get("delegationStrategy", "sequential")
        sub_agents = node_data.get("subAgents", [])
        max_concurrent = node_data.get("maxConcurrent", 3)
        
        logger.info(f"Manager Agent ({role}) delegating to {len(sub_agents)} sub-agents")
        
        results = []
        user_id = self.execution_context.get("user_id")
        
        try:
            from backend.db.models.agent_builder import Agent
            from backend.services.agent_builder.agent_executor import AgentExecutor
            
            if delegation_strategy == "sequential":
                # Execute sub-agents one by one
                for agent_config in sub_agents:
                    agent_id = agent_config.get("agent_id") or agent_config.get("agentId")
                    if not agent_id:
                        logger.warning(f"No agent_id for sub-agent: {agent_config.get('name')}")
                        continue
                    
                    logger.info(f"Delegating to {agent_config.get('name')} ({agent_config.get('role')})")
                    
                    # Get agent from database
                    agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
                    if not agent:
                        logger.error(f"Agent {agent_id} not found")
                        results.append({
                            "agent": agent_config.get("name"),
                            "role": agent_config.get("role"),
                            "error": f"Agent {agent_id} not found",
                            "success": False
                        })
                        continue
                    
                    # Execute agent
                    try:
                        agent_executor = AgentExecutor(self.db)
                        execution = await agent_executor.execute_agent(
                            agent_id=agent_id,
                            user_id=user_id,
                            input_data={"query": str(data), "context": self.execution_context},
                            session_id=self.execution_id
                        )
                        
                        results.append({
                            "agent": agent_config.get("name"),
                            "agent_id": agent_id,
                            "role": agent_config.get("role"),
                            "output": execution.output_data,
                            "success": execution.status == "completed",
                            "execution_id": execution.id
                        })
                    except Exception as e:
                        logger.error(f"Failed to execute agent {agent_id}: {e}")
                        results.append({
                            "agent": agent_config.get("name"),
                            "role": agent_config.get("role"),
                            "error": str(e),
                            "success": False
                        })
                    
            elif delegation_strategy == "parallel":
                # Execute sub-agents in parallel (limited by max_concurrent)
                logger.info(f"Executing up to {max_concurrent} agents in parallel")
                
                # Create tasks for parallel execution
                tasks = []
                for agent_config in sub_agents[:max_concurrent]:
                    agent_id = agent_config.get("agent_id") or agent_config.get("agentId")
                    if not agent_id:
                        continue
                    
                    task = self._execute_sub_agent(
                        agent_id=agent_id,
                        agent_config=agent_config,
                        data=data,
                        user_id=user_id
                    )
                    tasks.append(task)
                
                # Execute in parallel
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle exceptions
                results = [
                    r if not isinstance(r, Exception) else {
                        "error": str(r),
                        "success": False
                    }
                    for r in results
                ]
                    
            elif delegation_strategy == "priority":
                # Execute sub-agents by priority
                sorted_agents = sorted(sub_agents, key=lambda x: x.get("priority", 999))
                for agent_config in sorted_agents:
                    agent_id = agent_config.get("agent_id") or agent_config.get("agentId")
                    if not agent_id:
                        continue
                    
                    logger.info(f"Delegating to {agent_config.get('name')} (priority: {agent_config.get('priority')})")
                    
                    # Get agent from database
                    agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
                    if not agent:
                        results.append({
                            "agent": agent_config.get("name"),
                            "priority": agent_config.get("priority"),
                            "error": f"Agent {agent_id} not found",
                            "success": False
                        })
                        continue
                    
                    # Execute agent
                    try:
                        agent_executor = AgentExecutor(self.db)
                        execution = await agent_executor.execute_agent(
                            agent_id=agent_id,
                            user_id=user_id,
                            input_data={"query": str(data), "context": self.execution_context},
                            session_id=self.execution_id
                        )
                        
                        results.append({
                            "agent": agent_config.get("name"),
                            "agent_id": agent_id,
                            "role": agent_config.get("role"),
                            "priority": agent_config.get("priority"),
                            "output": execution.output_data,
                            "success": execution.status == "completed",
                            "execution_id": execution.id
                        })
                    except Exception as e:
                        logger.error(f"Failed to execute agent {agent_id}: {e}")
                        results.append({
                            "agent": agent_config.get("name"),
                            "priority": agent_config.get("priority"),
                            "error": str(e),
                            "success": False
                        })
            
            return {
                "manager_role": role,
                "goal": goal,
                "delegation_strategy": delegation_strategy,
                "sub_agent_count": len(sub_agents),
                "sub_agent_results": results,
                "aggregated_output": self._aggregate_results(results),
                "success": all(r.get("success", False) for r in results)
            }
            
        except Exception as e:
            logger.error(f"Manager agent node execution failed: {e}", exc_info=True)
            return {
                "manager_role": role,
                "delegation_strategy": delegation_strategy,
                "error": str(e),
                "success": False
            }
    
    async def _execute_sub_agent(
        self,
        agent_id: str,
        agent_config: Dict[str, Any],
        data: Any,
        user_id: str
    ) -> Dict[str, Any]:
        """Execute a single sub-agent (helper for parallel execution)."""
        try:
            from backend.db.models.agent_builder import Agent
            from backend.services.agent_builder.agent_executor import AgentExecutor
            
            # Get agent from database
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return {
                    "agent": agent_config.get("name"),
                    "role": agent_config.get("role"),
                    "error": f"Agent {agent_id} not found",
                    "success": False
                }
            
            # Execute agent
            agent_executor = AgentExecutor(self.db)
            execution = await agent_executor.execute_agent(
                agent_id=agent_id,
                user_id=user_id,
                input_data={"query": str(data), "context": self.execution_context},
                session_id=self.execution_id
            )
            
            return {
                "agent": agent_config.get("name"),
                "agent_id": agent_id,
                "role": agent_config.get("role"),
                "output": execution.output_data,
                "success": execution.status == "completed",
                "execution_id": execution.id
            }
        except Exception as e:
            logger.error(f"Failed to execute sub-agent {agent_id}: {e}")
            return {
                "agent": agent_config.get("name"),
                "role": agent_config.get("role"),
                "error": str(e),
                "success": False
            }
    
    async def _execute_memory_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute memory operation node."""
        memory_type = node_data.get("memoryType", "short_term")
        operation = node_data.get("operation", "store")
        key = node_data.get("key", "")
        value = node_data.get("value", "")
        ttl = node_data.get("ttl", 3600)
        namespace = node_data.get("namespace", "default")
        
        # Template replacement
        key_text = self._replace_templates(key, data)
        value_text = self._replace_templates(value, data)
        
        logger.info(f"Memory {operation} ({memory_type}): {namespace}:{key_text}")
        
        try:
            from backend.services.memory_service import get_memory_service
            memory_service = get_memory_service()
            
            if operation == "store":
                # Parse value if it's JSON
                try:
                    import json
                    if value_text.startswith("{") or value_text.startswith("["):
                        value_data = json.loads(value_text)
                    else:
                        value_data = value_text
                except:
                    value_data = value_text
                
                result = await memory_service.store(
                    namespace=namespace,
                    key=key_text,
                    value=value_data,
                    memory_type=memory_type,
                    ttl=ttl if memory_type == "short_term" else None,
                )
                
                return {
                    "success": True,
                    "operation": "store",
                    "memory_type": memory_type,
                    "key": key_text,
                    "namespace": namespace,
                    "ttl": ttl if memory_type == "short_term" else None,
                }
                
            elif operation == "retrieve":
                result = await memory_service.retrieve(
                    namespace=namespace,
                    key=key_text,
                    memory_type=memory_type,
                )
                
                if result:
                    return {
                        "success": True,
                        "operation": "retrieve",
                        "memory_type": memory_type,
                        "key": key_text,
                        "value": result.get("value"),
                        "namespace": namespace,
                        "created_at": result.get("created_at"),
                        "metadata": result.get("metadata"),
                    }
                else:
                    return {
                        "success": False,
                        "operation": "retrieve",
                        "error": "Key not found",
                        "key": key_text,
                        "namespace": namespace,
                    }
                    
            elif operation == "update":
                # Parse value if it's JSON
                try:
                    import json
                    if value_text.startswith("{") or value_text.startswith("["):
                        value_data = json.loads(value_text)
                    else:
                        value_data = value_text
                except:
                    value_data = value_text
                
                result = await memory_service.update(
                    namespace=namespace,
                    key=key_text,
                    value=value_data,
                    memory_type=memory_type,
                    ttl=ttl if memory_type == "short_term" else None,
                )
                
                return {
                    "success": True,
                    "operation": "update",
                    "memory_type": memory_type,
                    "key": key_text,
                    "namespace": namespace,
                }
                
            elif operation == "clear":
                result = await memory_service.delete(
                    namespace=namespace,
                    key=key_text,
                    memory_type=memory_type,
                )
                
                return {
                    "success": True,
                    "operation": "clear",
                    "memory_type": memory_type,
                    "key": key_text,
                    "namespace": namespace,
                    "deleted": result.get("deleted"),
                }
            
            return {"success": False, "error": "Unknown operation"}
            
        except Exception as e:
            logger.error(f"Memory node execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "operation": operation,
                "key": key_text,
                "namespace": namespace,
            }
    
    async def _execute_consensus_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute consensus node with multiple agents."""
        consensus_type = node_data.get("consensusType", "majority")
        agents = node_data.get("agents", [])
        threshold = node_data.get("threshold", 0.5)
        evaluation_criteria = node_data.get("evaluationCriteria", "")
        
        logger.info(f"Consensus ({consensus_type}) with {len(agents)} agents")
        
        user_id = self.execution_context.get("user_id")
        
        try:
            from backend.db.models.agent_builder import Agent
            from backend.services.agent_builder.agent_executor import AgentExecutor
            
            # Execute all agents in parallel
            tasks = []
            for agent_config in agents:
                agent_id = agent_config.get("agent_id") or agent_config.get("agentId")
                if not agent_id:
                    logger.warning(f"No agent_id for agent: {agent_config.get('name')}")
                    continue
                
                task = self._execute_consensus_agent(
                    agent_id=agent_id,
                    agent_config=agent_config,
                    data=data,
                    user_id=user_id
                )
                tasks.append(task)
            
            # Execute all agents in parallel
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            agent_results = [
                r if not isinstance(r, Exception) else {
                    "error": str(r),
                    "success": False,
                    "output": None,
                    "confidence": 0.0
                }
                for r in agent_results
            ]
            
            # Filter out failed agents
            successful_results = [r for r in agent_results if r.get("success", False)]
            
            if not successful_results:
                return {
                    "consensus_type": consensus_type,
                    "agent_count": len(agents),
                    "agent_results": agent_results,
                    "error": "All agents failed to execute",
                    "success": False
                }
            
            # Apply consensus mechanism
            if consensus_type == "majority":
                # Find most common result
                final_result = self._majority_consensus(successful_results, threshold)
            elif consensus_type == "unanimous":
                # All must agree
                final_result = self._unanimous_consensus(successful_results)
            elif consensus_type == "weighted":
                # Weighted average
                final_result = self._weighted_consensus(successful_results)
            elif consensus_type == "best":
                # Select best based on criteria
                final_result = self._best_result_consensus(successful_results, evaluation_criteria)
            else:
                final_result = successful_results[0] if successful_results else {}
            
            return {
                "consensus_type": consensus_type,
                "agent_count": len(agents),
                "successful_count": len(successful_results),
                "agent_results": agent_results,
                "final_result": final_result,
                "agreement_level": self._calculate_agreement(successful_results),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Consensus node execution failed: {e}", exc_info=True)
            return {
                "consensus_type": consensus_type,
                "agent_count": len(agents),
                "error": str(e),
                "success": False
            }
    
    async def _execute_consensus_agent(
        self,
        agent_id: str,
        agent_config: Dict[str, Any],
        data: Any,
        user_id: str
    ) -> Dict[str, Any]:
        """Execute a single agent for consensus (helper for parallel execution)."""
        try:
            from backend.db.models.agent_builder import Agent
            from backend.services.agent_builder.agent_executor import AgentExecutor
            
            # Get agent from database
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return {
                    "agent": agent_config.get("name"),
                    "weight": agent_config.get("weight", 1),
                    "error": f"Agent {agent_id} not found",
                    "success": False,
                    "output": None,
                    "confidence": 0.0
                }
            
            # Execute agent
            agent_executor = AgentExecutor(self.db)
            execution = await agent_executor.execute_agent(
                agent_id=agent_id,
                user_id=user_id,
                input_data={"query": str(data), "context": self.execution_context},
                session_id=self.execution_id
            )
            
            # Extract confidence from output if available
            output = execution.output_data
            confidence = 0.8  # Default confidence
            
            if isinstance(output, dict):
                confidence = output.get("confidence", 0.8)
                # Get the actual output text
                output_text = output.get("output") or output.get("response") or str(output)
            else:
                output_text = str(output)
            
            return {
                "agent": agent_config.get("name"),
                "agent_id": agent_id,
                "weight": agent_config.get("weight", 1),
                "output": output_text,
                "full_output": output,
                "confidence": confidence,
                "success": execution.status == "completed",
                "execution_id": execution.id
            }
        except Exception as e:
            logger.error(f"Failed to execute consensus agent {agent_id}: {e}")
            return {
                "agent": agent_config.get("name"),
                "weight": agent_config.get("weight", 1),
                "error": str(e),
                "success": False,
                "output": None,
                "confidence": 0.0
            }
    
    async def _execute_human_approval_node(self, node_data: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """Execute human approval node (pauses workflow)."""
        approvers = node_data.get("approvers", [])
        require_all = node_data.get("requireAll", True)
        timeout = node_data.get("timeout", 24)
        message = node_data.get("message", "")
        notification_method = node_data.get("notificationMethod", "email")
        auto_approve_after_timeout = node_data.get("autoApproveAfterTimeout", False)
        
        # Template replacement
        message_text = self._replace_templates(message, data)
        
        logger.info(f"Human approval requested from {len(approvers)} approvers")
        
        try:
            from backend.models.approval import ApprovalRequest
            from backend.exceptions import WorkflowPausedException
            from datetime import timedelta
            
            # Create approval request in database
            approval = ApprovalRequest(
                workflow_id=str(self.workflow.id),
                workflow_execution_id=self.execution_id,
                node_id=node_data.get("node_id", "unknown"),
                approvers=approvers,
                require_all=require_all,
                message=message_text,
                data_for_review=data,
                notification_method=notification_method,
                timeout_at=datetime.utcnow() + timedelta(hours=timeout),
                auto_approve_after_timeout=auto_approve_after_timeout,
            )
            
            self.db.add(approval)
            self.db.commit()
            
            logger.info(f"Created approval request: {approval.id}")
            
            # Send notifications to approvers
            await self._send_approval_notifications(
                approval_id=approval.id,
                approvers=approvers,
                message=message_text,
                notification_method=notification_method,
            )
            
            # Pause workflow execution by raising exception
            # This will be caught by the executor and workflow will be marked as waiting_approval
            raise WorkflowPausedException(
                approval_id=approval.id,
                message=f"Workflow paused for approval from {len(approvers)} approvers",
                node_id=node_data.get("node_id"),
                data=data
            )
            
        except WorkflowPausedException:
            # Re-raise to pause workflow
            raise
        except Exception as e:
            logger.error(f"Human approval node execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "approvers": approvers,
                "message": message_text,
            }
    
    async def _send_approval_notifications(
        self,
        approval_id: str,
        approvers: List[str],
        message: str,
        notification_method: str,
    ):
        """Send notifications to approvers."""
        try:
            approval_url = f"{self.execution_context.get('base_url', '')}/agent-builder/approvals"
            
            notification_text = f"""
Approval Required

{message}

Please review and approve/reject at:
{approval_url}

Approval ID: {approval_id}
"""
            
            if notification_method == "email":
                # Send email notifications
                from backend.services.api_key_service import APIKeyService
                api_key_service = APIKeyService(self.db)
                
                user_id = self.execution_context.get("user_id")
                if user_id:
                    smtp_config = await api_key_service.get_api_key(user_id, "smtp")
                    if smtp_config:
                        from backend.services.integrations.email_service import EmailService
                        import json
                        config = json.loads(smtp_config) if isinstance(smtp_config, str) else smtp_config
                        
                        email_service = EmailService(
                            smtp_host=config.get("smtp_host"),
                            smtp_port=config.get("smtp_port", 587),
                            username=config.get("username"),
                            password=config.get("password"),
                            use_tls=config.get("use_tls", True),
                        )
                        
                        await email_service.send_email(
                            to=approvers,
                            subject="Workflow Approval Required",
                            body=notification_text,
                            body_type="text",
                        )
                        
                        logger.info(f"Sent email notifications to {len(approvers)} approvers")
            
            elif notification_method == "slack":
                # Send Slack notifications
                from backend.services.api_key_service import APIKeyService
                api_key_service = APIKeyService(self.db)
                
                user_id = self.execution_context.get("user_id")
                if user_id:
                    slack_key = await api_key_service.get_api_key(user_id, "slack")
                    if slack_key:
                        from backend.services.integrations.slack_service import SlackService
                        slack_service = SlackService(slack_key)
                        
                        # Send to each approver (assuming they are channel names)
                        for approver in approvers:
                            await slack_service.send_message(
                                channel=approver,
                                text=notification_text,
                                username="Approval Bot",
                                icon_emoji=":bell:",
                            )
                        
                        logger.info(f"Sent Slack notifications to {len(approvers)} approvers")
            
        except Exception as e:
            logger.error(f"Failed to send approval notifications: {e}")
    
    def _aggregate_results(self, results: List[Dict[str, Any]]) -> str:
        """Aggregate results from multiple agents."""
        if not results:
            return ""
        
        # Simple aggregation - concatenate outputs
        outputs = [r.get("output", "") for r in results]
        return " | ".join(outputs)
    
    def _majority_consensus(self, results: List[Dict[str, Any]], threshold: float) -> Dict[str, Any]:
        """Find majority consensus among results."""
        if not results:
            return {}
        
        # Count occurrences of each output
        from collections import Counter
        outputs = [r.get("output") for r in results]
        counter = Counter(outputs)
        most_common = counter.most_common(1)[0]
        
        if most_common[1] / len(results) >= threshold:
            return {"output": most_common[0], "agreement": most_common[1] / len(results)}
        
        return {"output": most_common[0], "agreement": most_common[1] / len(results), "threshold_not_met": True}
    
    def _unanimous_consensus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if all agents agree."""
        if not results:
            return {}
        
        first_output = results[0].get("output")
        all_agree = all(r.get("output") == first_output for r in results)
        
        return {
            "output": first_output if all_agree else "No consensus",
            "unanimous": all_agree,
        }
    
    def _weighted_consensus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate weighted consensus."""
        if not results:
            return {}
        
        # For simplicity, return result with highest weight
        sorted_results = sorted(results, key=lambda x: x.get("weight", 1), reverse=True)
        return {
            "output": sorted_results[0].get("output"),
            "weight": sorted_results[0].get("weight"),
        }
    
    def _best_result_consensus(self, results: List[Dict[str, Any]], criteria: str) -> Dict[str, Any]:
        """Select best result based on criteria."""
        if not results:
            return {}
        
        # For simplicity, return result with highest confidence
        sorted_results = sorted(results, key=lambda x: x.get("confidence", 0), reverse=True)
        return {
            "output": sorted_results[0].get("output"),
            "confidence": sorted_results[0].get("confidence"),
            "criteria": criteria,
        }
    
    def _calculate_agreement(self, results: List[Dict[str, Any]]) -> float:
        """Calculate agreement level among results."""
        if not results:
            return 0.0
        
        from collections import Counter
        outputs = [r.get("output") for r in results]
        counter = Counter(outputs)
        most_common_count = counter.most_common(1)[0][1]
        
        return most_common_count / len(results)


    # SSE Support Methods
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution status with node statuses for SSE streaming.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution status dict or None if not found
        """
        try:
            from backend.db.models.agent_builder import WorkflowExecution
            
            execution = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()
            
            if not execution:
                return None
            
            return {
                "id": str(execution.id),
                "workflow_id": str(execution.workflow_id),
                "status": execution.status,
                "node_statuses": execution.node_statuses or {},
                "created_at": execution.created_at.timestamp() if execution.created_at else None,
                "updated_at": execution.updated_at.timestamp() if execution.updated_at else None,
                "completed_at": execution.completed_at.timestamp() if execution.completed_at else None,
            }
        except Exception as e:
            logger.error(f"Error getting execution status: {e}")
            return None
    
    async def get_latest_execution(
        self,
        workflow_id: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent execution for a workflow.
        
        Args:
            workflow_id: Workflow ID
            user_id: User ID
            
        Returns:
            Latest execution dict or None if not found
        """
        try:
            from backend.db.models.agent_builder import WorkflowExecution
            
            execution = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.user_id == user_id,
            ).order_by(
                WorkflowExecution.created_at.desc()
            ).first()
            
            if not execution:
                return None
            
            return {
                "id": str(execution.id),
                "status": execution.status,
                "created_at": execution.created_at.timestamp() if execution.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error getting latest execution: {e}")
            return None
    
    async def update_node_status(
        self,
        execution_id: str,
        node_id: str,
        status_update: Dict[str, Any]
    ) -> bool:
        """
        Update node status in execution record.
        
        Args:
            execution_id: Execution ID
            node_id: Node ID
            status_update: Status update dict with keys:
                - status: 'pending' | 'running' | 'success' | 'failed' | 'skipped'
                - node_name: Node display name
                - start_time: Start timestamp
                - end_time: End timestamp
                - error: Error message if failed
                - output: Node output data
                
        Returns:
            True if updated successfully
        """
        try:
            from backend.db.models.agent_builder import WorkflowExecution
            
            execution = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.id == execution_id
            ).first()
            
            if not execution:
                logger.warning(f"Execution not found: {execution_id}")
                return False
            
            # Get current node statuses
            node_statuses = execution.node_statuses or {}
            
            # Update or create node status
            if node_id not in node_statuses:
                node_statuses[node_id] = {}
            
            node_statuses[node_id].update(status_update)
            
            # Update execution record
            execution.node_statuses = node_statuses
            execution.updated_at = datetime.utcnow()
            
            self.db.commit()
            logger.debug(f"Updated node status: {node_id} -> {status_update.get('status')}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating node status: {e}")
            self.db.rollback()
            return False
