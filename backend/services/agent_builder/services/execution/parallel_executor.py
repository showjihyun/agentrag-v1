"""
Parallel Node Executor

Optimized parallel execution for workflow nodes with:
- Dynamic parallelism based on node dependencies
- Configurable concurrency limits
- Resource-aware scheduling
- Batch processing for similar nodes
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Set, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time

logger = logging.getLogger(__name__)


class ExecutionPriority(Enum):
    """Node execution priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class NodeTask:
    """Represents a node execution task."""
    node_id: str
    node_type: str
    config: Dict[str, Any]
    dependencies: Set[str] = field(default_factory=set)
    priority: ExecutionPriority = ExecutionPriority.NORMAL
    timeout: float = 30.0
    retries: int = 0
    max_retries: int = 3
    
    # Execution state
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


@dataclass
class ExecutionBatch:
    """Batch of nodes that can execute in parallel."""
    batch_id: int
    tasks: List[NodeTask]
    max_concurrency: int = 10


class DependencyGraph:
    """Manages node dependencies for parallel execution."""
    
    def __init__(self, nodes: List[Dict], edges: List[Dict]):
        self.nodes = {n["id"]: n for n in nodes}
        self.edges = edges
        self._dependencies: Dict[str, Set[str]] = {}
        self._dependents: Dict[str, Set[str]] = {}
        self._build_graph()
    
    def _build_graph(self):
        """Build dependency graph from edges."""
        for node_id in self.nodes:
            self._dependencies[node_id] = set()
            self._dependents[node_id] = set()
        
        for edge in self.edges:
            source = edge.get("source")
            target = edge.get("target")
            if source and target:
                self._dependencies[target].add(source)
                self._dependents[source].add(target)
    
    def get_dependencies(self, node_id: str) -> Set[str]:
        """Get all dependencies for a node."""
        return self._dependencies.get(node_id, set())
    
    def get_dependents(self, node_id: str) -> Set[str]:
        """Get all nodes that depend on this node."""
        return self._dependents.get(node_id, set())
    
    def get_execution_batches(self) -> List[ExecutionBatch]:
        """
        Group nodes into batches for parallel execution.
        Nodes in the same batch have no dependencies on each other.
        """
        batches = []
        completed: Set[str] = set()
        remaining = set(self.nodes.keys())
        batch_id = 0
        
        while remaining:
            # Find nodes with all dependencies satisfied
            ready = []
            for node_id in remaining:
                deps = self._dependencies.get(node_id, set())
                if deps.issubset(completed):
                    ready.append(node_id)
            
            if not ready:
                # Circular dependency detected
                logger.error(f"Circular dependency detected in nodes: {remaining}")
                break
            
            # Create batch
            tasks = []
            for node_id in ready:
                node = self.nodes[node_id]
                tasks.append(NodeTask(
                    node_id=node_id,
                    node_type=node.get("type", "unknown"),
                    config=node.get("data", {}),
                    dependencies=self._dependencies.get(node_id, set()),
                    priority=self._get_priority(node),
                    timeout=self._get_timeout(node),
                ))
            
            batches.append(ExecutionBatch(
                batch_id=batch_id,
                tasks=tasks,
                max_concurrency=self._calculate_concurrency(tasks),
            ))
            
            completed.update(ready)
            remaining -= set(ready)
            batch_id += 1
        
        return batches
    
    def _get_priority(self, node: Dict) -> ExecutionPriority:
        """Determine node priority based on type and config."""
        node_type = node.get("type", "")
        
        # Triggers and conditions are high priority
        if "trigger" in node_type.lower():
            return ExecutionPriority.CRITICAL
        if node_type in ["condition", "switch"]:
            return ExecutionPriority.HIGH
        if node_type in ["delay", "wait"]:
            return ExecutionPriority.LOW
        
        return ExecutionPriority.NORMAL
    
    def _get_timeout(self, node: Dict) -> float:
        """Get timeout for node based on type."""
        node_type = node.get("type", "")
        config = node.get("data", {})
        
        # Custom timeout from config
        if "timeout" in config:
            return float(config["timeout"])
        
        # Type-based defaults
        timeouts = {
            "ai_agent": 120.0,
            "openai_chat": 60.0,
            "http_request": 30.0,
            "python_code": 60.0,
            "database": 30.0,
            "delay": 300.0,
        }
        
        return timeouts.get(node_type, 30.0)
    
    def _calculate_concurrency(self, tasks: List[NodeTask]) -> int:
        """Calculate optimal concurrency for batch."""
        # Base concurrency
        base = min(len(tasks), 10)
        
        # Reduce for resource-intensive nodes
        heavy_types = {"ai_agent", "openai_chat", "python_code"}
        heavy_count = sum(1 for t in tasks if t.node_type in heavy_types)
        
        if heavy_count > 0:
            return max(3, base - heavy_count)
        
        return base


class ParallelExecutor:
    """
    Executes workflow nodes in parallel with optimizations.
    
    Features:
    - Automatic batching based on dependencies
    - Configurable concurrency limits
    - Priority-based scheduling
    - Resource-aware execution
    - Progress tracking
    """
    
    def __init__(
        self,
        max_concurrency: int = 10,
        default_timeout: float = 30.0,
        enable_batching: bool = True,
    ):
        self.max_concurrency = max_concurrency
        self.default_timeout = default_timeout
        self.enable_batching = enable_batching
        
        # Execution state
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, str] = {}
        self._progress_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable[[str, str, Any], Awaitable[None]]):
        """Set callback for progress updates."""
        self._progress_callback = callback
    
    async def execute_graph(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        input_data: Dict[str, Any],
        node_executor: Callable[[Dict, Dict[str, Any]], Awaitable[Any]],
    ) -> Dict[str, Any]:
        """
        Execute workflow graph with parallel optimization.
        
        Args:
            nodes: List of node definitions
            edges: List of edge definitions
            input_data: Initial input data
            node_executor: Function to execute individual nodes
            
        Returns:
            Execution results
        """
        start_time = time.time()
        self._results = {"__input__": input_data}
        self._errors = {}
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        
        # Build dependency graph
        graph = DependencyGraph(nodes, edges)
        batches = graph.get_execution_batches()
        
        logger.info(f"Executing {len(nodes)} nodes in {len(batches)} batches")
        
        # Execute batches sequentially, nodes within batch in parallel
        for batch in batches:
            await self._execute_batch(batch, node_executor)
            
            # Check for critical errors
            if self._has_critical_error(batch):
                logger.error("Critical error in batch, stopping execution")
                break
        
        duration = time.time() - start_time
        
        return {
            "success": len(self._errors) == 0,
            "results": self._results,
            "errors": self._errors,
            "duration": duration,
            "batches_executed": len(batches),
            "nodes_executed": len(self._results) - 1,  # Exclude __input__
        }
    
    async def _execute_batch(
        self,
        batch: ExecutionBatch,
        node_executor: Callable,
    ):
        """Execute a batch of nodes in parallel."""
        if not batch.tasks:
            return
        
        logger.debug(f"Executing batch {batch.batch_id} with {len(batch.tasks)} tasks")
        
        # Sort by priority
        sorted_tasks = sorted(batch.tasks, key=lambda t: t.priority.value)
        
        # Create semaphore for batch-level concurrency
        batch_semaphore = asyncio.Semaphore(batch.max_concurrency)
        
        # Execute all tasks in parallel
        await asyncio.gather(*[
            self._execute_task(task, node_executor, batch_semaphore)
            for task in sorted_tasks
        ], return_exceptions=True)
    
    async def _execute_task(
        self,
        task: NodeTask,
        node_executor: Callable,
        batch_semaphore: asyncio.Semaphore,
    ):
        """Execute a single node task."""
        async with self._semaphore:
            async with batch_semaphore:
                task.started_at = time.time()
                task.status = "running"
                
                # Notify progress
                if self._progress_callback:
                    await self._progress_callback(task.node_id, "running", None)
                
                try:
                    # Gather input from dependencies
                    node_input = self._gather_input(task)
                    
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        node_executor(
                            {"id": task.node_id, "type": task.node_type, "data": task.config},
                            node_input,
                        ),
                        timeout=task.timeout,
                    )
                    
                    task.result = result
                    task.status = "success"
                    self._results[task.node_id] = result
                    
                    # Notify progress
                    if self._progress_callback:
                        await self._progress_callback(task.node_id, "success", result)
                    
                except asyncio.TimeoutError:
                    task.status = "timeout"
                    task.error = f"Node timed out after {task.timeout}s"
                    self._errors[task.node_id] = task.error
                    
                    if self._progress_callback:
                        await self._progress_callback(task.node_id, "timeout", task.error)
                    
                except Exception as e:
                    task.status = "error"
                    task.error = str(e)
                    self._errors[task.node_id] = task.error
                    logger.error(f"Node {task.node_id} failed: {e}")
                    
                    if self._progress_callback:
                        await self._progress_callback(task.node_id, "error", task.error)
                
                finally:
                    task.completed_at = time.time()
    
    def _gather_input(self, task: NodeTask) -> Dict[str, Any]:
        """Gather input data from dependencies."""
        input_data = {}
        
        # Start with initial input
        if "__input__" in self._results:
            input_data.update(self._results["__input__"])
        
        # Add results from dependencies
        for dep_id in task.dependencies:
            if dep_id in self._results:
                dep_result = self._results[dep_id]
                if isinstance(dep_result, dict):
                    input_data.update(dep_result)
                else:
                    input_data[f"_{dep_id}_output"] = dep_result
        
        return input_data
    
    def _has_critical_error(self, batch: ExecutionBatch) -> bool:
        """Check if batch has critical errors that should stop execution."""
        for task in batch.tasks:
            if task.status == "error" and task.priority == ExecutionPriority.CRITICAL:
                return True
        return False


class NodeResultCache:
    """
    Cache for node execution results with configurable TTL.
    
    Features:
    - Per-node-type TTL configuration
    - LRU eviction
    - Cache key generation based on input
    """
    
    def __init__(self, redis_client=None, default_ttl: int = 300):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self._local_cache: Dict[str, Any] = {}
        self._cache_times: Dict[str, float] = {}
        self._max_local_size = 1000
        
        # Per-type TTL configuration (seconds)
        self.ttl_config = {
            "http_request": 60,      # External API calls - short TTL
            "database": 120,         # DB queries - medium TTL
            "openai_chat": 300,      # LLM responses - longer TTL
            "ai_agent": 300,
            "transform": 600,        # Deterministic transforms - long TTL
            "filter": 600,
            "calculator": 3600,      # Pure functions - very long TTL
            "json_transform": 3600,
        }
    
    def get_ttl(self, node_type: str) -> int:
        """Get TTL for node type."""
        return self.ttl_config.get(node_type, self.default_ttl)
    
    def set_ttl(self, node_type: str, ttl: int):
        """Set TTL for node type."""
        self.ttl_config[node_type] = ttl
    
    def _generate_key(self, node_id: str, node_type: str, input_hash: str) -> str:
        """Generate cache key."""
        return f"node_cache:{node_type}:{node_id}:{input_hash}"
    
    async def get(
        self,
        node_id: str,
        node_type: str,
        input_data: Dict[str, Any],
    ) -> Optional[Any]:
        """Get cached result if available."""
        import hashlib
        import json
        
        input_hash = hashlib.md5(
            json.dumps(input_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        
        key = self._generate_key(node_id, node_type, input_hash)
        
        # Check Redis first
        if self.redis:
            try:
                data = await self.redis.get(key)
                if data:
                    import json
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")
        
        # Check local cache
        if key in self._local_cache:
            cache_time = self._cache_times.get(key, 0)
            ttl = self.get_ttl(node_type)
            if time.time() - cache_time < ttl:
                return self._local_cache[key]
            else:
                # Expired
                del self._local_cache[key]
                del self._cache_times[key]
        
        return None
    
    async def set(
        self,
        node_id: str,
        node_type: str,
        input_data: Dict[str, Any],
        result: Any,
    ):
        """Cache node result."""
        import hashlib
        import json
        
        input_hash = hashlib.md5(
            json.dumps(input_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        
        key = self._generate_key(node_id, node_type, input_hash)
        ttl = self.get_ttl(node_type)
        
        # Save to Redis
        if self.redis:
            try:
                await self.redis.set(key, json.dumps(result, default=str), ex=ttl)
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
        
        # Save to local cache
        self._evict_if_needed()
        self._local_cache[key] = result
        self._cache_times[key] = time.time()
    
    def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        if len(self._local_cache) >= self._max_local_size:
            # Remove oldest 10%
            sorted_keys = sorted(
                self._cache_times.keys(),
                key=lambda k: self._cache_times[k]
            )
            for key in sorted_keys[:self._max_local_size // 10]:
                self._local_cache.pop(key, None)
                self._cache_times.pop(key, None)
    
    async def invalidate(self, node_id: str, node_type: str):
        """Invalidate all cache entries for a node."""
        pattern = f"node_cache:{node_type}:{node_id}:*"
        
        if self.redis:
            try:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis cache invalidate failed: {e}")
        
        # Clear local cache
        to_delete = [k for k in self._local_cache if k.startswith(f"node_cache:{node_type}:{node_id}:")]
        for key in to_delete:
            self._local_cache.pop(key, None)
            self._cache_times.pop(key, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "local_size": len(self._local_cache),
            "max_size": self._max_local_size,
            "ttl_config": self.ttl_config,
        }


# Global instances
_parallel_executor: Optional[ParallelExecutor] = None
_node_cache: Optional[NodeResultCache] = None


def get_parallel_executor(
    max_concurrency: int = 10,
    default_timeout: float = 30.0,
) -> ParallelExecutor:
    """Get or create parallel executor."""
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelExecutor(max_concurrency, default_timeout)
    return _parallel_executor


def get_node_cache(redis_client=None) -> NodeResultCache:
    """Get or create node cache."""
    global _node_cache
    if _node_cache is None:
        _node_cache = NodeResultCache(redis_client)
    return _node_cache
