"""
Agent Workflow Execution Service
통합 워크플로우 실행 서비스 - 모든 구성 요소를 연결
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from backend.services.agent_builder.execution.agent_execution_engine import (
    AgentExecutionEngine, 
    AgentConfig, 
    AgentType, 
    ExecutionContext, 
    ExecutionResult as AgentExecutionResult,
    ExecutionMode
)
from backend.services.agent_builder.orchestration.base_orchestrator import (
    BaseOrchestrator,
    ExecutionResult as OrchestrationResult,
    ExecutionStatus,
    StreamingUpdate
)
from backend.services.agent_builder.orchestration.orchestration_factory import OrchestrationFactory
from backend.core.execution.timeout_manager import (
    TimeoutManager,
    TimeoutContext,
    TimeoutType
)
from backend.core.resilience.circuit_breaker import (
    ResilienceManager,
    CircuitBreakerConfig,
    RetryConfig
)
from backend.core.error_handling.plugin_errors import (
    PluginException,
    PluginErrorCode,
    handle_plugin_errors
)

logger = logging.getLogger(__name__)


class WorkflowNodeType(Enum):
    """워크플로우 노드 타입"""
    INPUT = "input"
    OUTPUT = "output"
    LLM = "llm"
    TOOL = "tool"
    CONDITION = "condition"
    AGENT = "agent"
    ORCHESTRATION = "orchestration"
    LOOP = "loop"
    PARALLEL = "parallel"


class WorkflowExecutionStatus(Enum):
    """워크플로우 실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    PAUSED = "paused"


@dataclass
class WorkflowNode:
    """워크플로우 노드"""
    id: str
    type: WorkflowNodeType
    position: Dict[str, float]
    data: Dict[str, Any]
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)


@dataclass
class WorkflowEdge:
    """워크플로우 엣지"""
    id: str
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """워크플로우 정의"""
    id: str
    name: str
    description: str
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecutionResult:
    """워크플로우 실행 결과"""
    workflow_id: str
    execution_id: str
    status: WorkflowExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    node_results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class WorkflowExecutionService:
    """워크플로우 실행 서비스"""
    
    def __init__(self):
        self.agent_engine = AgentExecutionEngine()
        self.orchestration_factory = OrchestrationFactory()
        self.timeout_manager = TimeoutManager()
        self.resilience_manager = ResilienceManager()
        
        # 활성 실행 추적
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        
        # 실행 통계
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "node_execution_counts": {}
        }
    
    @handle_plugin_errors(attempt_recovery=True, max_retries=2)
    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        input_data: Dict[str, Any],
        user_id: str,
        execution_mode: str = "async",
        timeout_seconds: Optional[int] = None
    ) -> Union[WorkflowExecutionResult, AsyncGenerator[StreamingUpdate, None]]:
        """워크플로우 실행"""
        
        execution_id = f"workflow_{workflow.id}_{int(time.time())}"
        start_time = datetime.now()
        
        try:
            # 실행 컨텍스트 생성
            context = ExecutionContext(
                user_id=user_id,
                session_id=f"session_{user_id}_{int(time.time())}",
                workflow_id=workflow.id,
                execution_id=execution_id
            )
            
            # 타임아웃 설정
            timeout_seconds = timeout_seconds or 600  # 기본 10분
            
            # 실행 모드에 따른 처리
            if execution_mode == "streaming":
                return self._execute_workflow_streaming(
                    workflow, input_data, context, timeout_seconds
                )
            else:
                return await self._execute_workflow_sync(
                    workflow, input_data, context, timeout_seconds
                )
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {execution_id}, error: {e}")
            
            return WorkflowExecutionResult(
                workflow_id=workflow.id,
                execution_id=execution_id,
                status=WorkflowExecutionStatus.FAILED,
                started_at=start_time,
                completed_at=datetime.now(),
                error=str(e)
            )
    
    async def _execute_workflow_sync(
        self,
        workflow: WorkflowDefinition,
        input_data: Dict[str, Any],
        context: ExecutionContext,
        timeout_seconds: int
    ) -> WorkflowExecutionResult:
        """동기 워크플로우 실행"""
        
        start_time = datetime.now()
        
        # 타임아웃 컨텍스트로 실행
        async with TimeoutContext(
            self.timeout_manager,
            context.execution_id,
            timeout_seconds,
            TimeoutType.EXECUTION
        ):
            # 실행 그래프 구성
            execution_graph = self._build_execution_graph(workflow)
            
            # 노드 실행 순서 결정 (토폴로지 정렬)
            execution_order = self._topological_sort(execution_graph)
            
            # 노드별 실행
            node_results = {}
            current_data = input_data.copy()
            
            for node_id in execution_order:
                node = next(n for n in workflow.nodes if n.id == node_id)
                
                try:
                    # 노드 실행
                    node_result = await self._execute_node(
                        node, current_data, context
                    )
                    
                    node_results[node_id] = node_result
                    
                    # 결과를 다음 노드로 전달
                    if node_result.get("output"):
                        current_data.update(node_result["output"])
                
                except Exception as e:
                    logger.error(f"Node execution failed: {node_id}, error: {e}")
                    
                    return WorkflowExecutionResult(
                        workflow_id=workflow.id,
                        execution_id=context.execution_id,
                        status=WorkflowExecutionStatus.FAILED,
                        started_at=start_time,
                        completed_at=datetime.now(),
                        node_results=node_results,
                        error=f"Node {node_id} failed: {str(e)}"
                    )
            
            # 성공적 완료
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # 통계 업데이트
            self._update_execution_stats(execution_time, True, node_results)
            
            return WorkflowExecutionResult(
                workflow_id=workflow.id,
                execution_id=context.execution_id,
                status=WorkflowExecutionStatus.COMPLETED,
                started_at=start_time,
                completed_at=end_time,
                results=current_data,
                node_results=node_results,
                metrics={
                    "execution_time_seconds": execution_time,
                    "nodes_executed": len(node_results),
                    "total_nodes": len(workflow.nodes)
                }
            )
    
    async def _execute_workflow_streaming(
        self,
        workflow: WorkflowDefinition,
        input_data: Dict[str, Any],
        context: ExecutionContext,
        timeout_seconds: int
    ) -> AsyncGenerator[StreamingUpdate, None]:
        """스트리밍 워크플로우 실행"""
        
        start_time = datetime.now()
        
        try:
            # 시작 업데이트
            yield StreamingUpdate(
                execution_id=context.execution_id,
                timestamp=datetime.now(),
                update_type="workflow_start",
                data={
                    "workflow_id": workflow.id,
                    "total_nodes": len(workflow.nodes),
                    "status": WorkflowExecutionStatus.RUNNING.value
                }
            )
            
            # 실행 그래프 구성
            execution_graph = self._build_execution_graph(workflow)
            execution_order = self._topological_sort(execution_graph)
            
            node_results = {}
            current_data = input_data.copy()
            
            for i, node_id in enumerate(execution_order):
                node = next(n for n in workflow.nodes if n.id == node_id)
                
                # 노드 시작 업데이트
                yield StreamingUpdate(
                    execution_id=context.execution_id,
                    timestamp=datetime.now(),
                    update_type="node_start",
                    data={
                        "node_id": node_id,
                        "node_type": node.type.value,
                        "progress": i / len(execution_order)
                    }
                )
                
                try:
                    # 노드 실행
                    node_result = await self._execute_node(
                        node, current_data, context
                    )
                    
                    node_results[node_id] = node_result
                    
                    # 노드 완료 업데이트
                    yield StreamingUpdate(
                        execution_id=context.execution_id,
                        timestamp=datetime.now(),
                        update_type="node_complete",
                        data={
                            "node_id": node_id,
                            "result": node_result,
                            "progress": (i + 1) / len(execution_order)
                        }
                    )
                    
                    # 결과 전달
                    if node_result.get("output"):
                        current_data.update(node_result["output"])
                
                except Exception as e:
                    # 노드 실패 업데이트
                    yield StreamingUpdate(
                        execution_id=context.execution_id,
                        timestamp=datetime.now(),
                        update_type="node_error",
                        data={
                            "node_id": node_id,
                            "error": str(e)
                        }
                    )
                    
                    # 워크플로우 실패 업데이트
                    yield StreamingUpdate(
                        execution_id=context.execution_id,
                        timestamp=datetime.now(),
                        update_type="workflow_error",
                        data={
                            "status": WorkflowExecutionStatus.FAILED.value,
                            "error": f"Node {node_id} failed: {str(e)}"
                        }
                    )
                    return
            
            # 워크플로우 완료 업데이트
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            yield StreamingUpdate(
                execution_id=context.execution_id,
                timestamp=end_time,
                update_type="workflow_complete",
                data={
                    "status": WorkflowExecutionStatus.COMPLETED.value,
                    "results": current_data,
                    "node_results": node_results,
                    "execution_time_seconds": execution_time,
                    "progress": 1.0
                }
            )
            
            # 통계 업데이트
            self._update_execution_stats(execution_time, True, node_results)
        
        except Exception as e:
            # 전체 워크플로우 오류
            yield StreamingUpdate(
                execution_id=context.execution_id,
                timestamp=datetime.now(),
                update_type="workflow_error",
                data={
                    "status": WorkflowExecutionStatus.FAILED.value,
                    "error": str(e)
                }
            )
    
    async def _execute_node(
        self,
        node: WorkflowNode,
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """개별 노드 실행"""
        
        node_type = node.type
        node_data = node.data
        
        try:
            if node_type == WorkflowNodeType.INPUT:
                return {"output": input_data}
            
            elif node_type == WorkflowNodeType.OUTPUT:
                return {"output": input_data}
            
            elif node_type == WorkflowNodeType.LLM:
                return await self._execute_llm_node(node_data, input_data, context)
            
            elif node_type == WorkflowNodeType.TOOL:
                return await self._execute_tool_node(node_data, input_data, context)
            
            elif node_type == WorkflowNodeType.CONDITION:
                return await self._execute_condition_node(node_data, input_data, context)
            
            elif node_type == WorkflowNodeType.AGENT:
                return await self._execute_agent_node(node_data, input_data, context)
            
            elif node_type == WorkflowNodeType.ORCHESTRATION:
                return await self._execute_orchestration_node(node_data, input_data, context)
            
            else:
                raise ValueError(f"Unsupported node type: {node_type}")
        
        except Exception as e:
            logger.error(f"Node execution error: {node.id}, type: {node_type}, error: {e}")
            raise
    
    async def _execute_llm_node(
        self,
        node_data: Dict[str, Any],
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """LLM 노드 실행"""
        
        # Agent 설정 생성
        agent_config = AgentConfig(
            agent_type=AgentType.OPENAI_FUNCTIONS,
            model_name=node_data.get("model", "gpt-3.5-turbo"),
            temperature=node_data.get("temperature", 0.7),
            max_tokens=node_data.get("maxTokens", 1000)
        )
        
        # 프롬프트 구성
        prompt = node_data.get("prompt", "")
        if "{input}" in prompt:
            prompt = prompt.replace("{input}", str(input_data))
        
        query_data = {"query": prompt}
        
        # Agent 실행
        result = await self.agent_engine.execute_agent(
            agent_config,
            query_data,
            context,
            ExecutionMode.ASYNC
        )
        
        if result.success:
            return {
                "output": {"llm_response": result.result.get("output", "")},
                "metadata": {
                    "execution_time": result.execution_time,
                    "token_usage": result.token_usage
                }
            }
        else:
            raise Exception(f"LLM execution failed: {result.error}")
    
    async def _execute_tool_node(
        self,
        node_data: Dict[str, Any],
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """도구 노드 실행"""
        
        tool_type = node_data.get("toolType", "")
        parameters = node_data.get("parameters", {})
        
        # 파라미터에 입력 데이터 병합
        merged_params = {**parameters, **input_data}
        
        # 도구별 실행 로직
        if tool_type == "web_search":
            query = merged_params.get("query", "")
            results = await self.agent_engine.web_search.search(query, max_results=5)
            return {"output": {"search_results": results}}
        
        elif tool_type == "vector_search":
            query = merged_params.get("query", "")
            results = await self.agent_engine.vector_search.search(query, top_k=5)
            return {"output": {"search_results": results}}
        
        elif tool_type == "local_data":
            query = merged_params.get("query", "")
            results = await self.agent_engine.local_data.query(query)
            return {"output": {"data_results": results}}
        
        else:
            raise ValueError(f"Unsupported tool type: {tool_type}")
    
    async def _execute_condition_node(
        self,
        node_data: Dict[str, Any],
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """조건 노드 실행"""
        
        condition = node_data.get("condition", "")
        operator = node_data.get("operator", "equals")
        
        # 간단한 조건 평가 (실제로는 더 복잡한 로직 필요)
        if operator == "equals":
            result = str(input_data.get("value", "")) == condition
        elif operator == "contains":
            result = condition in str(input_data.get("value", ""))
        elif operator == "greater_than":
            try:
                result = float(input_data.get("value", 0)) > float(condition)
            except ValueError:
                result = False
        else:
            result = False
        
        return {
            "output": {"condition_result": result},
            "metadata": {"condition": condition, "operator": operator}
        }
    
    async def _execute_agent_node(
        self,
        node_data: Dict[str, Any],
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Agent 노드 실행"""
        
        # Agent 설정
        agent_config = AgentConfig(
            agent_type=AgentType(node_data.get("agentType", "openai_functions")),
            model_name=node_data.get("model", "gpt-3.5-turbo"),
            tools=node_data.get("tools", []),
            system_prompt=node_data.get("systemPrompt", "")
        )
        
        # 실행
        result = await self.agent_engine.execute_agent(
            agent_config,
            input_data,
            context,
            ExecutionMode.ASYNC
        )
        
        if result.success:
            return {
                "output": result.result,
                "metadata": {
                    "execution_time": result.execution_time,
                    "token_usage": result.token_usage
                }
            }
        else:
            raise Exception(f"Agent execution failed: {result.error}")
    
    async def _execute_orchestration_node(
        self,
        node_data: Dict[str, Any],
        input_data: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """오케스트레이션 노드 실행"""
        
        pattern = node_data.get("pattern", "sequential")
        config = node_data.get("config", {})
        
        # 오케스트레이터 생성
        orchestrator = await self.orchestration_factory.create_orchestrator(pattern)
        
        # 실행
        result = await orchestrator.execute(
            config,
            input_data,
            context.user_id,
            context.execution_id
        )
        
        if result.status == ExecutionStatus.COMPLETED:
            return {
                "output": result.results,
                "metadata": result.metrics
            }
        else:
            raise Exception(f"Orchestration failed: {result.error}")
    
    def _build_execution_graph(self, workflow: WorkflowDefinition) -> Dict[str, List[str]]:
        """실행 그래프 구성"""
        graph = {node.id: [] for node in workflow.nodes}
        
        for edge in workflow.edges:
            graph[edge.source].append(edge.target)
        
        return graph
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """토폴로지 정렬"""
        in_degree = {node: 0 for node in graph}
        
        # 진입 차수 계산
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] += 1
        
        # 진입 차수가 0인 노드들로 시작
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # 인접 노드들의 진입 차수 감소
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 순환 참조 확인
        if len(result) != len(graph):
            raise ValueError("Workflow contains circular dependencies")
        
        return result
    
    def _update_execution_stats(
        self,
        execution_time: float,
        success: bool,
        node_results: Dict[str, Any]
    ) -> None:
        """실행 통계 업데이트"""
        self.execution_stats["total_executions"] += 1
        
        if success:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1
        
        # 평균 실행 시간 업데이트
        total = self.execution_stats["total_executions"]
        current_avg = self.execution_stats["average_execution_time"]
        self.execution_stats["average_execution_time"] = (
            (current_avg * (total - 1) + execution_time) / total
        )
        
        # 노드 실행 횟수 업데이트
        for node_id in node_results:
            if node_id not in self.execution_stats["node_execution_counts"]:
                self.execution_stats["node_execution_counts"][node_id] = 0
            self.execution_stats["node_execution_counts"][node_id] += 1
    
    async def cancel_workflow_execution(self, execution_id: str) -> bool:
        """워크플로우 실행 취소"""
        try:
            # 타임아웃 매니저에서 취소
            success = await self.timeout_manager.cancel_execution(
                execution_id, "User cancelled"
            )
            
            if execution_id in self.active_executions:
                self.active_executions[execution_id]["status"] = WorkflowExecutionStatus.CANCELLED
            
            return success
        except Exception as e:
            logger.error(f"Failed to cancel workflow execution {execution_id}: {e}")
            return False
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """실행 상태 조회"""
        return self.active_executions.get(execution_id)
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """실행 통계 조회"""
        return {
            **self.execution_stats,
            "timeout_manager_stats": self.timeout_manager.get_statistics(),
            "circuit_breaker_stats": self.resilience_manager.get_all_states()
        }


# 전역 인스턴스
workflow_execution_service = WorkflowExecutionService()