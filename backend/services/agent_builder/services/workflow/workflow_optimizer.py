"""
Workflow Optimizer

Analyzes and optimizes workflow execution for better performance.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class OptimizationType(str, Enum):
    """Types of optimizations."""
    PARALLEL_EXECUTION = "parallel_execution"
    NODE_CACHING = "node_caching"
    BATCH_PROCESSING = "batch_processing"
    LAZY_EVALUATION = "lazy_evaluation"
    CONNECTION_POOLING = "connection_pooling"
    RESULT_STREAMING = "result_streaming"


@dataclass
class OptimizationSuggestion:
    """A single optimization suggestion."""
    type: OptimizationType
    node_ids: List[str]
    description: str
    estimated_improvement: str  # e.g., "30% faster"
    priority: int  # 1-5, 5 being highest
    auto_applicable: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "node_ids": self.node_ids,
            "description": self.description,
            "estimated_improvement": self.estimated_improvement,
            "priority": self.priority,
            "auto_applicable": self.auto_applicable,
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for a workflow."""
    workflow_id: str
    avg_execution_time_ms: float
    p50_execution_time_ms: float
    p95_execution_time_ms: float
    p99_execution_time_ms: float
    total_executions: int
    success_rate: float
    node_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    bottleneck_nodes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "p50_execution_time_ms": self.p50_execution_time_ms,
            "p95_execution_time_ms": self.p95_execution_time_ms,
            "p99_execution_time_ms": self.p99_execution_time_ms,
            "total_executions": self.total_executions,
            "success_rate": self.success_rate,
            "node_metrics": self.node_metrics,
            "bottleneck_nodes": self.bottleneck_nodes,
        }


@dataclass
class OptimizationReport:
    """Complete optimization report."""
    workflow_id: str
    analyzed_at: str
    metrics: PerformanceMetrics
    suggestions: List[OptimizationSuggestion]
    optimized_graph: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "analyzed_at": self.analyzed_at,
            "metrics": self.metrics.to_dict(),
            "suggestions": [s.to_dict() for s in self.suggestions],
            "has_optimized_graph": self.optimized_graph is not None,
            "total_suggestions": len(self.suggestions),
            "high_priority_count": sum(1 for s in self.suggestions if s.priority >= 4),
        }


class WorkflowOptimizer:
    """
    Analyzes workflows and suggests optimizations.
    
    Features:
    - Parallel execution detection
    - Bottleneck identification
    - Caching opportunities
    - Graph restructuring
    """
    
    def __init__(self, db_session=None):
        """
        Initialize optimizer.
        
        Args:
            db_session: Database session for metrics
        """
        self.db = db_session
        self._execution_cache: Dict[str, List[Dict]] = {}
    
    async def analyze(
        self,
        workflow: Any,
        include_metrics: bool = True,
    ) -> OptimizationReport:
        """
        Analyze workflow and generate optimization report.
        
        Args:
            workflow: Workflow to analyze
            include_metrics: Include historical metrics
            
        Returns:
            Optimization report
        """
        workflow_id = str(workflow.id)
        graph = workflow.graph_definition or {}
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        
        suggestions = []
        
        # Analyze for parallel execution opportunities
        parallel_suggestions = self._find_parallel_opportunities(nodes, edges)
        suggestions.extend(parallel_suggestions)
        
        # Analyze for caching opportunities
        cache_suggestions = self._find_caching_opportunities(nodes)
        suggestions.extend(cache_suggestions)
        
        # Analyze for batch processing
        batch_suggestions = self._find_batch_opportunities(nodes, edges)
        suggestions.extend(batch_suggestions)
        
        # Get performance metrics
        metrics = await self._get_metrics(workflow_id) if include_metrics else None
        
        if metrics:
            # Add bottleneck-based suggestions
            bottleneck_suggestions = self._analyze_bottlenecks(metrics, nodes)
            suggestions.extend(bottleneck_suggestions)
        
        # Sort by priority
        suggestions.sort(key=lambda s: s.priority, reverse=True)
        
        return OptimizationReport(
            workflow_id=workflow_id,
            analyzed_at=datetime.utcnow().isoformat(),
            metrics=metrics or PerformanceMetrics(
                workflow_id=workflow_id,
                avg_execution_time_ms=0,
                p50_execution_time_ms=0,
                p95_execution_time_ms=0,
                p99_execution_time_ms=0,
                total_executions=0,
                success_rate=0,
            ),
            suggestions=suggestions,
        )
    
    def _find_parallel_opportunities(
        self,
        nodes: List[Dict],
        edges: List[Dict],
    ) -> List[OptimizationSuggestion]:
        """Find nodes that can be executed in parallel."""
        suggestions = []
        
        # Build dependency graph
        dependencies = {n["id"]: set() for n in nodes}
        dependents = {n["id"]: set() for n in nodes}
        
        for edge in edges:
            source = edge.get("source") or edge.get("source_node_id")
            target = edge.get("target") or edge.get("target_node_id")
            if source and target:
                dependencies[target].add(source)
                dependents[source].add(target)
        
        # Find nodes with same dependencies (can run in parallel)
        dep_groups: Dict[frozenset, List[str]] = {}
        for node_id, deps in dependencies.items():
            dep_key = frozenset(deps)
            if dep_key not in dep_groups:
                dep_groups[dep_key] = []
            dep_groups[dep_key].append(node_id)
        
        # Suggest parallelization for groups > 1
        for deps, node_ids in dep_groups.items():
            if len(node_ids) > 1:
                # Check if nodes are independent (no edges between them)
                independent = True
                for i, n1 in enumerate(node_ids):
                    for n2 in node_ids[i+1:]:
                        if n2 in dependents.get(n1, set()) or n1 in dependents.get(n2, set()):
                            independent = False
                            break
                
                if independent:
                    suggestions.append(OptimizationSuggestion(
                        type=OptimizationType.PARALLEL_EXECUTION,
                        node_ids=node_ids,
                        description=f"Nodes {', '.join(node_ids[:3])}{'...' if len(node_ids) > 3 else ''} can be executed in parallel",
                        estimated_improvement=f"Up to {len(node_ids)}x faster for this section",
                        priority=4,
                        auto_applicable=True,
                    ))
        
        return suggestions
    
    def _find_caching_opportunities(
        self,
        nodes: List[Dict],
    ) -> List[OptimizationSuggestion]:
        """Find nodes that could benefit from caching."""
        suggestions = []
        
        cacheable_types = {"ai_agent", "tool", "http_request", "database"}
        
        for node in nodes:
            node_type = node.get("type") or node.get("node_type")
            node_id = node.get("id")
            config = node.get("configuration", {}) or node.get("data", {})
            
            if node_type in cacheable_types:
                # Check if caching is already enabled
                cache_enabled = config.get("cache_enabled", False)
                
                if not cache_enabled:
                    suggestions.append(OptimizationSuggestion(
                        type=OptimizationType.NODE_CACHING,
                        node_ids=[node_id],
                        description=f"Enable caching for {node_type} node '{node_id}'",
                        estimated_improvement="Reduce redundant API calls by 60-80%",
                        priority=3,
                        auto_applicable=True,
                    ))
        
        return suggestions
    
    def _find_batch_opportunities(
        self,
        nodes: List[Dict],
        edges: List[Dict],
    ) -> List[OptimizationSuggestion]:
        """Find opportunities for batch processing."""
        suggestions = []
        
        # Find consecutive nodes of same type
        node_types = {n["id"]: n.get("type") or n.get("node_type") for n in nodes}
        
        # Build execution order
        execution_order = self._topological_sort(nodes, edges)
        
        # Find consecutive same-type nodes
        batch_candidates = []
        current_batch = []
        current_type = None
        
        for node_id in execution_order:
            node_type = node_types.get(node_id)
            
            if node_type == current_type and node_type in {"http_request", "database"}:
                current_batch.append(node_id)
            else:
                if len(current_batch) > 1:
                    batch_candidates.append((current_type, current_batch))
                current_batch = [node_id]
                current_type = node_type
        
        if len(current_batch) > 1:
            batch_candidates.append((current_type, current_batch))
        
        for batch_type, node_ids in batch_candidates:
            suggestions.append(OptimizationSuggestion(
                type=OptimizationType.BATCH_PROCESSING,
                node_ids=node_ids,
                description=f"Batch {len(node_ids)} consecutive {batch_type} operations",
                estimated_improvement="Reduce network overhead by 40-60%",
                priority=3,
                auto_applicable=False,
            ))
        
        return suggestions
    
    def _analyze_bottlenecks(
        self,
        metrics: PerformanceMetrics,
        nodes: List[Dict],
    ) -> List[OptimizationSuggestion]:
        """Analyze bottlenecks from metrics."""
        suggestions = []
        
        if not metrics.bottleneck_nodes:
            return suggestions
        
        for node_id in metrics.bottleneck_nodes:
            node = next((n for n in nodes if n["id"] == node_id), None)
            if not node:
                continue
            
            node_type = node.get("type") or node.get("node_type")
            node_metrics = metrics.node_metrics.get(node_id, {})
            avg_time = node_metrics.get("avg_time_ms", 0)
            
            if node_type == "ai_agent":
                suggestions.append(OptimizationSuggestion(
                    type=OptimizationType.RESULT_STREAMING,
                    node_ids=[node_id],
                    description=f"AI Agent node '{node_id}' is a bottleneck (avg {avg_time:.0f}ms). Consider streaming responses.",
                    estimated_improvement="Improve perceived latency by 50%",
                    priority=5,
                    auto_applicable=False,
                ))
            elif node_type == "http_request":
                suggestions.append(OptimizationSuggestion(
                    type=OptimizationType.CONNECTION_POOLING,
                    node_ids=[node_id],
                    description=f"HTTP node '{node_id}' is slow (avg {avg_time:.0f}ms). Enable connection pooling.",
                    estimated_improvement="Reduce connection overhead by 30%",
                    priority=4,
                    auto_applicable=True,
                ))
        
        return suggestions
    
    def _topological_sort(
        self,
        nodes: List[Dict],
        edges: List[Dict],
    ) -> List[str]:
        """Topological sort of nodes."""
        # Build adjacency list
        graph = {n["id"]: [] for n in nodes}
        in_degree = {n["id"]: 0 for n in nodes}
        
        for edge in edges:
            source = edge.get("source") or edge.get("source_node_id")
            target = edge.get("target") or edge.get("target_node_id")
            if source in graph and target in graph:
                graph[source].append(target)
                in_degree[target] += 1
        
        # Kahn's algorithm
        queue = [n for n, d in in_degree.items() if d == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    async def _get_metrics(self, workflow_id: str) -> Optional[PerformanceMetrics]:
        """Get performance metrics from execution history."""
        if not self.db:
            return None
        
        try:
            from backend.db.models.agent_builder import WorkflowExecution
            from sqlalchemy import func
            
            # Get recent executions
            executions = self.db.query(WorkflowExecution).filter(
                WorkflowExecution.workflow_id == workflow_id,
                WorkflowExecution.started_at >= datetime.utcnow() - timedelta(days=7),
            ).all()
            
            if not executions:
                return None
            
            # Calculate metrics
            durations = []
            node_times: Dict[str, List[float]] = {}
            success_count = 0
            
            for exec in executions:
                if exec.completed_at and exec.started_at:
                    duration = (exec.completed_at - exec.started_at).total_seconds() * 1000
                    durations.append(duration)
                
                if exec.status == "completed":
                    success_count += 1
                
                # Extract node times from execution context
                context = exec.execution_context or {}
                for node_exec in context.get("node_executions", []):
                    node_id = node_exec.get("node_id")
                    duration_ms = node_exec.get("duration_ms", 0)
                    if node_id:
                        if node_id not in node_times:
                            node_times[node_id] = []
                        node_times[node_id].append(duration_ms)
            
            if not durations:
                return None
            
            durations.sort()
            
            # Calculate percentiles
            def percentile(data, p):
                idx = int(len(data) * p / 100)
                return data[min(idx, len(data) - 1)]
            
            # Calculate node metrics and find bottlenecks
            node_metrics = {}
            bottleneck_nodes = []
            
            for node_id, times in node_times.items():
                avg_time = sum(times) / len(times)
                node_metrics[node_id] = {
                    "avg_time_ms": avg_time,
                    "max_time_ms": max(times),
                    "call_count": len(times),
                }
                
                # Mark as bottleneck if avg time > 1 second
                if avg_time > 1000:
                    bottleneck_nodes.append(node_id)
            
            # Sort bottlenecks by avg time
            bottleneck_nodes.sort(
                key=lambda n: node_metrics[n]["avg_time_ms"],
                reverse=True,
            )
            
            return PerformanceMetrics(
                workflow_id=workflow_id,
                avg_execution_time_ms=sum(durations) / len(durations),
                p50_execution_time_ms=percentile(durations, 50),
                p95_execution_time_ms=percentile(durations, 95),
                p99_execution_time_ms=percentile(durations, 99),
                total_executions=len(executions),
                success_rate=success_count / len(executions) * 100,
                node_metrics=node_metrics,
                bottleneck_nodes=bottleneck_nodes[:5],  # Top 5 bottlenecks
            )
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return None
    
    async def apply_optimizations(
        self,
        workflow: Any,
        optimization_types: List[OptimizationType],
    ) -> Dict[str, Any]:
        """
        Apply automatic optimizations to workflow.
        
        Args:
            workflow: Workflow to optimize
            optimization_types: Types of optimizations to apply
            
        Returns:
            Optimized graph definition
        """
        graph = workflow.graph_definition.copy()
        applied = []
        
        if OptimizationType.NODE_CACHING in optimization_types:
            # Enable caching on cacheable nodes
            for node in graph.get("nodes", []):
                node_type = node.get("type") or node.get("node_type")
                if node_type in {"ai_agent", "tool", "http_request"}:
                    config = node.get("configuration", {})
                    if not config.get("cache_enabled"):
                        config["cache_enabled"] = True
                        config["cache_ttl"] = 300  # 5 minutes
                        node["configuration"] = config
                        applied.append(f"Enabled caching for {node['id']}")
        
        if OptimizationType.CONNECTION_POOLING in optimization_types:
            # Enable connection pooling for HTTP nodes
            for node in graph.get("nodes", []):
                node_type = node.get("type") or node.get("node_type")
                if node_type == "http_request":
                    config = node.get("configuration", {})
                    config["use_connection_pool"] = True
                    config["pool_size"] = 10
                    node["configuration"] = config
                    applied.append(f"Enabled connection pooling for {node['id']}")
        
        return {
            "optimized_graph": graph,
            "applied_optimizations": applied,
            "optimization_count": len(applied),
        }


# Global optimizer
_optimizer: Optional[WorkflowOptimizer] = None


def get_optimizer(db_session=None) -> WorkflowOptimizer:
    """Get or create global optimizer."""
    global _optimizer
    if _optimizer is None:
        _optimizer = WorkflowOptimizer(db_session)
    return _optimizer
