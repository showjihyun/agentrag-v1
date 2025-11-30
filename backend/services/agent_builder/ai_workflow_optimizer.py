"""
AI Workflow Optimizer Service

Intelligent workflow optimization with:
- Parallelization detection
- Caching recommendations
- Redundant node removal
- Cost optimization
- Performance analysis
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import asyncio
import json


class OptimizationType(str, Enum):
    PARALLELIZATION = "parallelization"
    CACHING = "caching"
    REDUNDANT_REMOVAL = "redundant_removal"
    BATCH_PROCESSING = "batch_processing"
    COST_OPTIMIZATION = "cost_optimization"
    ERROR_HANDLING = "error_handling"
    TIMEOUT_ADJUSTMENT = "timeout_adjustment"


class ImpactLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Impact:
    level: ImpactLevel
    time_reduction: Optional[float] = None  # seconds
    cost_reduction: Optional[float] = None  # dollars


@dataclass
class OptimizationSuggestion:
    id: str
    type: OptimizationType
    title: str
    description: str
    impact: Impact
    affected_nodes: List[str]
    estimated_savings: Optional[Dict[str, str]] = None
    auto_applicable: bool = True
    applied: bool = False
    details: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "impact": {
                "level": self.impact.level.value,
                "timeReduction": self.impact.time_reduction,
                "costReduction": self.impact.cost_reduction,
            },
            "affectedNodes": self.affected_nodes,
            "estimatedSavings": self.estimated_savings,
            "autoApplicable": self.auto_applicable,
            "applied": self.applied,
            "details": self.details,
        }


@dataclass
class WorkflowMetrics:
    total_nodes: int
    estimated_duration: str
    estimated_cost: str
    parallelizable_nodes: int
    cacheable_nodes: int
    redundant_nodes: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "totalNodes": self.total_nodes,
            "estimatedDuration": self.estimated_duration,
            "estimatedCost": self.estimated_cost,
            "parallelizableNodes": self.parallelizable_nodes,
            "cacheableNodes": self.cacheable_nodes,
            "redundantNodes": self.redundant_nodes,
        }


@dataclass
class WorkflowNode:
    id: str
    type: str
    name: str
    config: Dict[str, Any] = field(default_factory=dict)
    estimated_duration: float = 1.0  # seconds
    estimated_cost: float = 0.0  # dollars
    is_cacheable: bool = False
    dependencies: List[str] = field(default_factory=list)


@dataclass
class WorkflowEdge:
    source: str
    target: str
    condition: Optional[str] = None


class AIWorkflowOptimizer:
    """
    AI-powered workflow optimization service.
    
    Analyzes workflows and suggests optimizations for:
    - Performance (parallelization, caching)
    - Cost (model selection, batching)
    - Reliability (error handling, timeouts)
    """
    
    # Node types that can be parallelized
    PARALLELIZABLE_TYPES = {
        "http_request", "api_call", "ai_agent", "openai_chat",
        "anthropic_claude", "google_gemini", "web_search",
    }
    
    # Node types that benefit from caching
    CACHEABLE_TYPES = {
        "ai_agent", "openai_chat", "anthropic_claude", "google_gemini",
        "web_search", "http_request", "database_query",
    }
    
    # Expensive node types (for cost optimization)
    EXPENSIVE_TYPES = {
        "ai_agent": 0.01,
        "openai_chat": 0.02,
        "anthropic_claude": 0.015,
        "google_gemini": 0.01,
    }
    
    def __init__(self):
        self.suggestion_counter = 0
    
    def _generate_suggestion_id(self) -> str:
        self.suggestion_counter += 1
        return f"opt_{self.suggestion_counter}"
    
    def analyze_workflow(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> Tuple[List[OptimizationSuggestion], WorkflowMetrics]:
        """
        Analyze a workflow and generate optimization suggestions.
        
        Args:
            nodes: List of workflow nodes
            edges: List of workflow edges
            
        Returns:
            Tuple of (suggestions, metrics)
        """
        # Parse nodes and edges
        parsed_nodes = self._parse_nodes(nodes)
        parsed_edges = self._parse_edges(edges)
        
        # Build dependency graph
        dependencies = self._build_dependency_graph(parsed_nodes, parsed_edges)
        
        # Generate suggestions
        suggestions: List[OptimizationSuggestion] = []
        
        # 1. Parallelization opportunities
        parallel_suggestions = self._find_parallelization_opportunities(
            parsed_nodes, dependencies
        )
        suggestions.extend(parallel_suggestions)
        
        # 2. Caching recommendations
        cache_suggestions = self._find_caching_opportunities(parsed_nodes)
        suggestions.extend(cache_suggestions)
        
        # 3. Redundant node detection
        redundant_suggestions = self._find_redundant_nodes(parsed_nodes, parsed_edges)
        suggestions.extend(redundant_suggestions)
        
        # 4. Cost optimization
        cost_suggestions = self._find_cost_optimizations(parsed_nodes)
        suggestions.extend(cost_suggestions)
        
        # 5. Error handling suggestions
        error_suggestions = self._find_error_handling_gaps(parsed_nodes, parsed_edges)
        suggestions.extend(error_suggestions)
        
        # 6. Timeout adjustments
        timeout_suggestions = self._find_timeout_issues(parsed_nodes)
        suggestions.extend(timeout_suggestions)
        
        # Calculate metrics
        metrics = self._calculate_metrics(parsed_nodes, suggestions)
        
        return suggestions, metrics
    
    def _parse_nodes(self, nodes: List[Dict[str, Any]]) -> List[WorkflowNode]:
        """Parse raw node data into WorkflowNode objects."""
        parsed = []
        for node in nodes:
            node_type = node.get("type", "unknown")
            parsed.append(WorkflowNode(
                id=node.get("id", ""),
                type=node_type,
                name=node.get("data", {}).get("label", node.get("name", "Unknown")),
                config=node.get("data", {}).get("config", {}),
                estimated_duration=self._estimate_duration(node_type),
                estimated_cost=self.EXPENSIVE_TYPES.get(node_type, 0),
                is_cacheable=node_type in self.CACHEABLE_TYPES,
            ))
        return parsed
    
    def _parse_edges(self, edges: List[Dict[str, Any]]) -> List[WorkflowEdge]:
        """Parse raw edge data into WorkflowEdge objects."""
        return [
            WorkflowEdge(
                source=edge.get("source", ""),
                target=edge.get("target", ""),
                condition=edge.get("data", {}).get("condition"),
            )
            for edge in edges
        ]
    
    def _estimate_duration(self, node_type: str) -> float:
        """Estimate execution duration for a node type."""
        durations = {
            "ai_agent": 3.0,
            "openai_chat": 2.0,
            "anthropic_claude": 2.5,
            "google_gemini": 2.0,
            "http_request": 1.0,
            "web_search": 2.0,
            "database_query": 0.5,
            "transform": 0.1,
            "condition": 0.05,
            "code": 0.5,
        }
        return durations.get(node_type, 0.5)
    
    def _build_dependency_graph(
        self,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
    ) -> Dict[str, List[str]]:
        """Build a dependency graph from nodes and edges."""
        dependencies: Dict[str, List[str]] = {node.id: [] for node in nodes}
        
        for edge in edges:
            if edge.target in dependencies:
                dependencies[edge.target].append(edge.source)
        
        return dependencies
    
    def _find_parallelization_opportunities(
        self,
        nodes: List[WorkflowNode],
        dependencies: Dict[str, List[str]],
    ) -> List[OptimizationSuggestion]:
        """Find nodes that can be executed in parallel."""
        suggestions = []
        
        # Group nodes by their dependencies
        dep_groups: Dict[str, List[WorkflowNode]] = {}
        for node in nodes:
            if node.type not in self.PARALLELIZABLE_TYPES:
                continue
            
            deps_key = ",".join(sorted(dependencies.get(node.id, [])))
            if deps_key not in dep_groups:
                dep_groups[deps_key] = []
            dep_groups[deps_key].append(node)
        
        # Find groups with multiple nodes (can be parallelized)
        for deps_key, group_nodes in dep_groups.items():
            if len(group_nodes) >= 2:
                total_time = sum(n.estimated_duration for n in group_nodes)
                max_time = max(n.estimated_duration for n in group_nodes)
                time_saved = total_time - max_time
                
                suggestions.append(OptimizationSuggestion(
                    id=self._generate_suggestion_id(),
                    type=OptimizationType.PARALLELIZATION,
                    title="병렬 실행 가능",
                    description=f"{len(group_nodes)}개의 노드를 병렬로 실행할 수 있습니다.",
                    impact=Impact(
                        level=ImpactLevel.HIGH if time_saved > 2 else ImpactLevel.MEDIUM,
                        time_reduction=time_saved,
                    ),
                    affected_nodes=[n.name for n in group_nodes],
                    estimated_savings={
                        "time": f"{time_saved:.1f}초",
                        "percentage": f"{int((time_saved / total_time) * 100)}",
                    },
                    details=f"현재 순차 실행 시간: {total_time:.1f}초 → 병렬 실행 시간: {max_time:.1f}초",
                ))
        
        return suggestions
    
    def _find_caching_opportunities(
        self,
        nodes: List[WorkflowNode],
    ) -> List[OptimizationSuggestion]:
        """Find nodes that would benefit from caching."""
        suggestions = []
        
        cacheable_nodes = [n for n in nodes if n.is_cacheable and n.estimated_cost > 0]
        
        if cacheable_nodes:
            total_cost = sum(n.estimated_cost for n in cacheable_nodes)
            
            # Group by type for better suggestions
            by_type: Dict[str, List[WorkflowNode]] = {}
            for node in cacheable_nodes:
                if node.type not in by_type:
                    by_type[node.type] = []
                by_type[node.type].append(node)
            
            for node_type, type_nodes in by_type.items():
                if len(type_nodes) >= 1:
                    type_cost = sum(n.estimated_cost for n in type_nodes)
                    suggestions.append(OptimizationSuggestion(
                        id=self._generate_suggestion_id(),
                        type=OptimizationType.CACHING,
                        title="캐싱 추천",
                        description=f"{len(type_nodes)}개의 {node_type} 노드에 캐싱을 적용하면 비용을 절감할 수 있습니다.",
                        impact=Impact(
                            level=ImpactLevel.MEDIUM,
                            cost_reduction=type_cost * 0.6,  # Assume 60% cache hit rate
                        ),
                        affected_nodes=[n.name for n in type_nodes],
                        estimated_savings={
                            "cost": f"${type_cost * 0.6:.3f}/실행",
                        },
                        details="동일한 입력에 대해 캐시된 응답을 재사용합니다. 예상 캐시 적중률: 60%",
                    ))
        
        return suggestions
    
    def _find_redundant_nodes(
        self,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
    ) -> List[OptimizationSuggestion]:
        """Find potentially redundant nodes."""
        suggestions = []
        
        # Find nodes with same type and similar config
        by_type: Dict[str, List[WorkflowNode]] = {}
        for node in nodes:
            if node.type not in by_type:
                by_type[node.type] = []
            by_type[node.type].append(node)
        
        for node_type, type_nodes in by_type.items():
            if len(type_nodes) >= 2:
                # Check for similar configurations
                for i, node1 in enumerate(type_nodes):
                    for node2 in type_nodes[i+1:]:
                        if self._configs_similar(node1.config, node2.config):
                            suggestions.append(OptimizationSuggestion(
                                id=self._generate_suggestion_id(),
                                type=OptimizationType.REDUNDANT_REMOVAL,
                                title="중복 노드 감지",
                                description=f"'{node1.name}'과 '{node2.name}'이 유사한 설정을 가지고 있습니다.",
                                impact=Impact(
                                    level=ImpactLevel.LOW,
                                    time_reduction=node2.estimated_duration,
                                    cost_reduction=node2.estimated_cost,
                                ),
                                affected_nodes=[node1.name, node2.name],
                                auto_applicable=False,
                                details="두 노드를 하나로 통합하거나, 결과를 공유하는 것을 고려하세요.",
                            ))
        
        return suggestions
    
    def _find_cost_optimizations(
        self,
        nodes: List[WorkflowNode],
    ) -> List[OptimizationSuggestion]:
        """Find cost optimization opportunities."""
        suggestions = []
        
        # Find expensive AI nodes that could use cheaper alternatives
        expensive_nodes = [n for n in nodes if n.type in self.EXPENSIVE_TYPES]
        
        for node in expensive_nodes:
            if node.type == "openai_chat":
                # Suggest using a cheaper model
                suggestions.append(OptimizationSuggestion(
                    id=self._generate_suggestion_id(),
                    type=OptimizationType.COST_OPTIMIZATION,
                    title="비용 최적화 가능",
                    description=f"'{node.name}'에서 더 저렴한 모델을 사용할 수 있습니다.",
                    impact=Impact(
                        level=ImpactLevel.MEDIUM,
                        cost_reduction=node.estimated_cost * 0.5,
                    ),
                    affected_nodes=[node.name],
                    estimated_savings={
                        "cost": f"${node.estimated_cost * 0.5:.3f}/실행",
                    },
                    auto_applicable=False,
                    details="GPT-4 대신 GPT-3.5-turbo를 사용하면 비용을 50% 절감할 수 있습니다. 단, 복잡한 작업에서는 품질이 저하될 수 있습니다.",
                ))
        
        return suggestions
    
    def _find_error_handling_gaps(
        self,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
    ) -> List[OptimizationSuggestion]:
        """Find nodes that need error handling."""
        suggestions = []
        
        # Find nodes that make external calls but don't have error handling
        external_call_types = {"http_request", "api_call", "web_search", "database_query"}
        
        for node in nodes:
            if node.type in external_call_types:
                # Check if there's error handling configured
                has_error_handling = node.config.get("error_handling") or node.config.get("retry")
                
                if not has_error_handling:
                    suggestions.append(OptimizationSuggestion(
                        id=self._generate_suggestion_id(),
                        type=OptimizationType.ERROR_HANDLING,
                        title="에러 처리 추가 권장",
                        description=f"'{node.name}'에 에러 처리를 추가하면 안정성이 향상됩니다.",
                        impact=Impact(level=ImpactLevel.MEDIUM),
                        affected_nodes=[node.name],
                        auto_applicable=True,
                        details="재시도 로직과 폴백 처리를 추가하여 일시적인 오류에 대응할 수 있습니다.",
                    ))
        
        return suggestions
    
    def _find_timeout_issues(
        self,
        nodes: List[WorkflowNode],
    ) -> List[OptimizationSuggestion]:
        """Find nodes with potential timeout issues."""
        suggestions = []
        
        slow_types = {"ai_agent", "web_search", "http_request"}
        
        for node in nodes:
            if node.type in slow_types:
                timeout = node.config.get("timeout", 30)
                
                if timeout < 10 and node.estimated_duration > 5:
                    suggestions.append(OptimizationSuggestion(
                        id=self._generate_suggestion_id(),
                        type=OptimizationType.TIMEOUT_ADJUSTMENT,
                        title="타임아웃 조정 권장",
                        description=f"'{node.name}'의 타임아웃이 너무 짧을 수 있습니다.",
                        impact=Impact(level=ImpactLevel.LOW),
                        affected_nodes=[node.name],
                        auto_applicable=True,
                        details=f"현재 타임아웃: {timeout}초, 권장: {int(node.estimated_duration * 3)}초",
                    ))
        
        return suggestions
    
    def _configs_similar(self, config1: Dict, config2: Dict) -> bool:
        """Check if two configurations are similar."""
        # Simple similarity check - can be enhanced
        key_fields = ["url", "endpoint", "model", "prompt"]
        
        for field in key_fields:
            if field in config1 and field in config2:
                if config1[field] == config2[field]:
                    return True
        
        return False
    
    def _calculate_metrics(
        self,
        nodes: List[WorkflowNode],
        suggestions: List[OptimizationSuggestion],
    ) -> WorkflowMetrics:
        """Calculate workflow metrics."""
        total_duration = sum(n.estimated_duration for n in nodes)
        total_cost = sum(n.estimated_cost for n in nodes)
        
        parallelizable = len([
            s for s in suggestions 
            if s.type == OptimizationType.PARALLELIZATION
        ])
        cacheable = len([n for n in nodes if n.is_cacheable])
        redundant = len([
            s for s in suggestions 
            if s.type == OptimizationType.REDUNDANT_REMOVAL
        ])
        
        return WorkflowMetrics(
            total_nodes=len(nodes),
            estimated_duration=f"{total_duration:.1f}초",
            estimated_cost=f"${total_cost:.3f}",
            parallelizable_nodes=parallelizable,
            cacheable_nodes=cacheable,
            redundant_nodes=redundant,
        )
    
    async def apply_optimization(
        self,
        workflow_id: str,
        suggestion_id: str,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Apply an optimization suggestion to a workflow.
        
        Returns:
            Tuple of (modified_nodes, modified_edges)
        """
        # This would implement the actual optimization logic
        # For now, return the original workflow
        return nodes, edges


# Singleton instance
_optimizer: Optional[AIWorkflowOptimizer] = None


def get_workflow_optimizer() -> AIWorkflowOptimizer:
    """Get the singleton AIWorkflowOptimizer instance."""
    global _optimizer
    if _optimizer is None:
        _optimizer = AIWorkflowOptimizer()
    return _optimizer
