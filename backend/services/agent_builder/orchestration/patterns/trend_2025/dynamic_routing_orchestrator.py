"""
Dynamic Routing Orchestrator
동적 라우팅 오케스트레이션 패턴
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import deque, defaultdict
import statistics

from backend.services.agent_builder.orchestration.base_orchestrator import BaseOrchestrator
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class RoutingStrategy(Enum):
    PERFORMANCE_BASED = "performance_based"
    LOAD_BALANCING = "load_balancing"
    COST_OPTIMIZATION = "cost_optimization"
    LATENCY_OPTIMIZATION = "latency_optimization"
    ADAPTIVE_LEARNING = "adaptive_learning"


class AgentStatus(Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


@dataclass
class AgentMetrics:
    """Agent 성능 메트릭"""
    agent_id: str
    agent_name: str
    status: AgentStatus
    current_load: float  # 0.0 - 1.0
    avg_response_time: float  # milliseconds
    success_rate: float  # 0.0 - 1.0
    cost_per_request: float
    queue_length: int
    last_updated: str
    capabilities: List[str]
    performance_score: float = 0.0
    
    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()
        self.performance_score = self._calculate_performance_score()
    
    def _calculate_performance_score(self) -> float:
        """성능 점수 계산"""
        if self.status == AgentStatus.OFFLINE:
            return 0.0
        
        # 가중 평균으로 성능 점수 계산
        load_score = 1.0 - self.current_load  # 낮은 부하가 좋음
        response_score = max(0.0, 1.0 - (self.avg_response_time / 10000))  # 10초 기준
        success_score = self.success_rate
        
        # 가중치 적용
        score = (load_score * 0.3 + response_score * 0.4 + success_score * 0.3)
        return max(0.0, min(1.0, score))


@dataclass
class RoutingDecision:
    """라우팅 결정 정보"""
    decision_id: str
    task_id: str
    selected_agent: str
    routing_strategy: RoutingStrategy
    decision_time: str
    confidence: float
    reasoning: str
    alternatives: List[str]
    expected_performance: Dict[str, float]
    
    def __post_init__(self):
        if not self.decision_time:
            self.decision_time = datetime.now().isoformat()


@dataclass
class TaskRequest:
    """작업 요청 정보"""
    task_id: str
    task_type: str
    priority: int  # 1-10 (10이 최고 우선순위)
    required_capabilities: List[str]
    estimated_complexity: float  # 0.0 - 1.0
    max_response_time: Optional[float] = None
    cost_budget: Optional[float] = None
    retry_count: int = 0


class DynamicRoutingOrchestrator(BaseOrchestrator):
    """동적 라우팅 오케스트레이터 (메모리 최적화)"""
    
    def __init__(self):
        super().__init__()
        self.pattern_type = "dynamic_routing"
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        
        # 메모리 효율적인 히스토리 관리
        self.routing_history = deque(maxlen=1000)  # 최대 1000개 제한
        self.performance_history = defaultdict(lambda: deque(maxlen=50))  # Agent별 최대 50개 제한
        
        self.learning_enabled = True
        
        # 자동 정리 설정
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(hours=1)  # 1시간마다 정리
        
    async def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """설정 검증"""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # 필수 필드 검증
            required_fields = ["routing_strategy", "agents", "performance_thresholds"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")
            
            # Agent 설정 검증
            agents = config.get("agents", [])
            if len(agents) < 2:
                errors.append("At least 2 agents required for dynamic routing")
            elif len(agents) > 50:
                warnings.append("Large number of agents may impact routing performance")
            
            # 라우팅 전략 검증
            strategy = config.get("routing_strategy", "performance_based")
            valid_strategies = [s.value for s in RoutingStrategy]
            if strategy not in valid_strategies:
                errors.append(f"Invalid routing strategy. Must be one of: {valid_strategies}")
            
            # 성능 임계값 검증
            thresholds = config.get("performance_thresholds", {})
            if "max_response_time" in thresholds:
                if thresholds["max_response_time"] <= 0:
                    errors.append("Max response time must be positive")
            
            if "min_success_rate" in thresholds:
                rate = thresholds["min_success_rate"]
                if not 0.0 <= rate <= 1.0:
                    errors.append("Min success rate must be between 0.0 and 1.0")
            
            # 부하 분산 설정 검증
            if strategy == "load_balancing":
                if "load_threshold" not in config:
                    suggestions.append("Consider setting load_threshold for load balancing")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": warnings,
                "suggestions": suggestions
            }
    
    async def execute(self, config: Dict[str, Any], input_data: Dict[str, Any], 
                     user_id: str, execution_id: str) -> Dict[str, Any]:
        """동적 라우팅 실행"""
        try:
            logger.info(f"Starting dynamic routing orchestration: {execution_id}")
            
            # Agent 메트릭 초기화
            await self._initialize_agent_metrics(config)
            
            # 작업 요청 처리
            tasks = input_data.get("tasks", [])
            if not tasks:
                # 단일 작업으로 처리
                tasks = [input_data]
            
            results = []
            for task_data in tasks:
                task_request = await self._create_task_request(task_data, execution_id)
                result = await self._process_task_request(task_request, config)
                results.append(result)
            
            # 실행 결과 요약
            summary = await self._generate_execution_summary(results, config)
            
            return {
                "success": True,
                "execution_id": execution_id,
                "tasks_processed": len(results),
                "results": results,
                "summary": summary,
                "routing_decisions": [asdict(d) for d in self.routing_history[-len(results):]]
            }
            
        except Exception as e:
            logger.error(f"Dynamic routing orchestration error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_id": execution_id
            }
    
    async def _initialize_agent_metrics(self, config: Dict[str, Any]) -> None:
        """Agent 메트릭 초기화"""
        try:
            agents = config.get("agents", [])
            
            for agent_config in agents:
                agent_id = agent_config["id"]
                
                # 기존 메트릭이 있으면 업데이트, 없으면 생성
                if agent_id in self.agent_metrics:
                    await self._update_agent_metrics(agent_id)
                else:
                    metrics = AgentMetrics(
                        agent_id=agent_id,
                        agent_name=agent_config.get("name", f"Agent_{agent_id}"),
                        status=AgentStatus.AVAILABLE,
                        current_load=0.0,
                        avg_response_time=agent_config.get("baseline_response_time", 1000),
                        success_rate=agent_config.get("baseline_success_rate", 0.9),
                        cost_per_request=agent_config.get("cost_per_request", 0.01),
                        queue_length=0,
                        capabilities=agent_config.get("capabilities", []),
                        last_updated=datetime.now().isoformat()
                    )
                    self.agent_metrics[agent_id] = metrics
            
            logger.info(f"Initialized metrics for {len(self.agent_metrics)} agents")
            
        except Exception as e:
            logger.error(f"Error initializing agent metrics: {e}")
            raise
    
    async def _update_agent_metrics(self, agent_id: str) -> None:
        """Agent 메트릭 업데이트"""
        try:
            # 실제 구현에서는 Agent 상태를 실시간으로 조회
            # 여기서는 시뮬레이션된 메트릭 업데이트
            
            metrics = self.agent_metrics.get(agent_id)
            if not metrics:
                return
            
            # 시뮬레이션된 메트릭 업데이트
            import random
            
            # 부하 상태 시뮬레이션
            metrics.current_load = max(0.0, min(1.0, metrics.current_load + random.uniform(-0.1, 0.1)))
            
            # 응답 시간 변동
            base_time = 1000
            variation = random.uniform(0.8, 1.2)
            load_factor = 1 + metrics.current_load
            metrics.avg_response_time = base_time * variation * load_factor
            
            # 성공률 변동
            metrics.success_rate = max(0.7, min(1.0, metrics.success_rate + random.uniform(-0.05, 0.05)))
            
            # 상태 업데이트
            if metrics.current_load > 0.9:
                metrics.status = AgentStatus.OVERLOADED
            elif metrics.current_load > 0.7:
                metrics.status = AgentStatus.BUSY
            else:
                metrics.status = AgentStatus.AVAILABLE
            
            metrics.last_updated = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error updating agent metrics for {agent_id}: {e}")
    
    async def _create_task_request(self, task_data: Dict[str, Any], 
                                 execution_id: str) -> TaskRequest:
        """작업 요청 생성"""
        import uuid
        
        return TaskRequest(
            task_id=task_data.get("task_id", str(uuid.uuid4())),
            task_type=task_data.get("task_type", "general"),
            priority=task_data.get("priority", 5),
            required_capabilities=task_data.get("required_capabilities", []),
            estimated_complexity=task_data.get("estimated_complexity", 0.5),
            max_response_time=task_data.get("max_response_time"),
            cost_budget=task_data.get("cost_budget"),
            retry_count=task_data.get("retry_count", 0)
        )
    
    async def _process_task_request(self, task_request: TaskRequest, 
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """작업 요청 처리"""
        try:
            # 라우팅 결정
            routing_decision = await self._make_routing_decision(task_request, config)
            
            if not routing_decision:
                return {
                    "task_id": task_request.task_id,
                    "success": False,
                    "error": "No suitable agent found",
                    "routing_decision": None
                }
            
            # 선택된 Agent에게 작업 할당
            execution_result = await self._execute_task_on_agent(
                task_request, routing_decision.selected_agent, config
            )
            
            # 성능 피드백 수집
            await self._collect_performance_feedback(routing_decision, execution_result)
            
            # 학습 업데이트
            if self.learning_enabled:
                await self._update_learning_model(routing_decision, execution_result)
            
            return {
                "task_id": task_request.task_id,
                "success": execution_result["success"],
                "selected_agent": routing_decision.selected_agent,
                "execution_time": execution_result.get("execution_time"),
                "routing_decision": asdict(routing_decision),
                "result": execution_result.get("result")
            }
            
        except Exception as e:
            logger.error(f"Error processing task request {task_request.task_id}: {e}")
            return {
                "task_id": task_request.task_id,
                "success": False,
                "error": str(e),
                "routing_decision": None
            }
    
    async def _make_routing_decision(self, task_request: TaskRequest, 
                                   config: Dict[str, Any]) -> Optional[RoutingDecision]:
        """라우팅 결정"""
        try:
            strategy = RoutingStrategy(config.get("routing_strategy", "performance_based"))
            
            # 후보 Agent 필터링
            candidates = await self._filter_candidate_agents(task_request, config)
            
            if not candidates:
                logger.warning(f"No candidate agents found for task {task_request.task_id}")
                return None
            
            # 전략별 Agent 선택
            if strategy == RoutingStrategy.PERFORMANCE_BASED:
                selected_agent, reasoning = await self._select_by_performance(candidates, task_request)
            elif strategy == RoutingStrategy.LOAD_BALANCING:
                selected_agent, reasoning = await self._select_by_load_balancing(candidates, task_request)
            elif strategy == RoutingStrategy.COST_OPTIMIZATION:
                selected_agent, reasoning = await self._select_by_cost(candidates, task_request)
            elif strategy == RoutingStrategy.LATENCY_OPTIMIZATION:
                selected_agent, reasoning = await self._select_by_latency(candidates, task_request)
            elif strategy == RoutingStrategy.ADAPTIVE_LEARNING:
                selected_agent, reasoning = await self._select_by_learning(candidates, task_request)
            else:
                selected_agent, reasoning = await self._select_by_performance(candidates, task_request)
            
            if not selected_agent:
                return None
            
            # 라우팅 결정 생성
            import uuid
            decision = RoutingDecision(
                decision_id=str(uuid.uuid4()),
                task_id=task_request.task_id,
                selected_agent=selected_agent,
                routing_strategy=strategy,
                decision_time=datetime.now().isoformat(),
                confidence=0.8,  # 실제로는 더 정교한 계산 필요
                reasoning=reasoning,
                alternatives=[agent_id for agent_id in candidates if agent_id != selected_agent][:3],
                expected_performance=await self._estimate_performance(selected_agent, task_request)
            )
            
            self.routing_history.append(decision)
            logger.info(f"Routing decision made: {selected_agent} for task {task_request.task_id}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error making routing decision: {e}")
            return None
    
    async def _filter_candidate_agents(self, task_request: TaskRequest, 
                                     config: Dict[str, Any]) -> List[str]:
        """후보 Agent 필터링"""
        candidates = []
        
        for agent_id, metrics in self.agent_metrics.items():
            # 상태 확인
            if metrics.status in [AgentStatus.OFFLINE, AgentStatus.MAINTENANCE]:
                continue
            
            # 능력 확인
            if task_request.required_capabilities:
                if not all(cap in metrics.capabilities for cap in task_request.required_capabilities):
                    continue
            
            # 성능 임계값 확인
            thresholds = config.get("performance_thresholds", {})
            
            if "max_response_time" in thresholds:
                if metrics.avg_response_time > thresholds["max_response_time"]:
                    continue
            
            if "min_success_rate" in thresholds:
                if metrics.success_rate < thresholds["min_success_rate"]:
                    continue
            
            # 부하 확인
            if metrics.status == AgentStatus.OVERLOADED:
                # 높은 우선순위 작업만 허용
                if task_request.priority < 8:
                    continue
            
            candidates.append(agent_id)
        
        return candidates
    
    async def _select_by_performance(self, candidates: List[str], 
                                   task_request: TaskRequest) -> Tuple[Optional[str], str]:
        """성능 기반 선택"""
        if not candidates:
            return None, "No candidates available"
        
        # 성능 점수로 정렬
        scored_candidates = []
        for agent_id in candidates:
            metrics = self.agent_metrics[agent_id]
            score = metrics.performance_score
            
            # 우선순위 보정
            if task_request.priority > 7:
                score *= 1.2  # 높은 우선순위 작업에 보너스
            
            scored_candidates.append((agent_id, score))
        
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        selected_agent = scored_candidates[0][0]
        
        return selected_agent, f"Selected based on highest performance score: {scored_candidates[0][1]:.3f}"
    
    async def _select_by_load_balancing(self, candidates: List[str], 
                                      task_request: TaskRequest) -> Tuple[Optional[str], str]:
        """부하 분산 기반 선택"""
        if not candidates:
            return None, "No candidates available"
        
        # 부하가 가장 낮은 Agent 선택
        load_candidates = []
        for agent_id in candidates:
            metrics = self.agent_metrics[agent_id]
            load_candidates.append((agent_id, metrics.current_load))
        
        load_candidates.sort(key=lambda x: x[1])
        selected_agent = load_candidates[0][0]
        
        return selected_agent, f"Selected for load balancing: current load {load_candidates[0][1]:.3f}"
    
    async def _select_by_cost(self, candidates: List[str], 
                            task_request: TaskRequest) -> Tuple[Optional[str], str]:
        """비용 최적화 기반 선택"""
        if not candidates:
            return None, "No candidates available"
        
        # 비용이 가장 낮은 Agent 선택 (성능도 고려)
        cost_candidates = []
        for agent_id in candidates:
            metrics = self.agent_metrics[agent_id]
            # 비용 대비 성능 비율 계산
            cost_performance_ratio = metrics.cost_per_request / max(0.1, metrics.performance_score)
            cost_candidates.append((agent_id, cost_performance_ratio))
        
        cost_candidates.sort(key=lambda x: x[1])
        selected_agent = cost_candidates[0][0]
        
        return selected_agent, f"Selected for cost optimization: cost/performance ratio {cost_candidates[0][1]:.3f}"
    
    async def _select_by_latency(self, candidates: List[str], 
                               task_request: TaskRequest) -> Tuple[Optional[str], str]:
        """지연시간 최적화 기반 선택"""
        if not candidates:
            return None, "No candidates available"
        
        # 응답 시간이 가장 빠른 Agent 선택
        latency_candidates = []
        for agent_id in candidates:
            metrics = self.agent_metrics[agent_id]
            latency_candidates.append((agent_id, metrics.avg_response_time))
        
        latency_candidates.sort(key=lambda x: x[1])
        selected_agent = latency_candidates[0][0]
        
        return selected_agent, f"Selected for latency optimization: avg response time {latency_candidates[0][1]:.0f}ms"
    
    async def _select_by_learning(self, candidates: List[str], 
                                task_request: TaskRequest) -> Tuple[Optional[str], str]:
        """학습 기반 선택"""
        # 학습 모델이 없으면 성능 기반으로 폴백
        return await self._select_by_performance(candidates, task_request)
    
    async def _estimate_performance(self, agent_id: str, 
                                  task_request: TaskRequest) -> Dict[str, float]:
        """성능 예측"""
        metrics = self.agent_metrics.get(agent_id)
        if not metrics:
            return {}
        
        # 복잡도에 따른 응답 시간 조정
        complexity_factor = 1 + task_request.estimated_complexity
        estimated_response_time = metrics.avg_response_time * complexity_factor
        
        return {
            "estimated_response_time": estimated_response_time,
            "estimated_success_rate": metrics.success_rate,
            "estimated_cost": metrics.cost_per_request,
            "current_load": metrics.current_load
        }
    
    async def _execute_task_on_agent(self, task_request: TaskRequest, 
                                   agent_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Agent에서 작업 실행"""
        try:
            start_time = time.time()
            
            # Agent 부하 업데이트
            metrics = self.agent_metrics[agent_id]
            metrics.current_load = min(1.0, metrics.current_load + 0.1)
            metrics.queue_length += 1
            
            # 실제 구현에서는 Agent API 호출
            # 여기서는 시뮬레이션
            await asyncio.sleep(0.1)  # 시뮬레이션 지연
            
            execution_time = (time.time() - start_time) * 1000  # ms
            
            # 성공/실패 시뮬레이션
            import random
            success = random.random() < metrics.success_rate
            
            # Agent 부하 감소
            metrics.current_load = max(0.0, metrics.current_load - 0.1)
            metrics.queue_length = max(0, metrics.queue_length - 1)
            
            return {
                "success": success,
                "execution_time": execution_time,
                "result": f"Task {task_request.task_id} executed on {agent_id}",
                "agent_id": agent_id
            }
            
        except Exception as e:
            logger.error(f"Error executing task on agent {agent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id
            }
    
    async def _collect_performance_feedback(self, routing_decision: RoutingDecision, 
                                          execution_result: Dict[str, Any]) -> None:
        """성능 피드백 수집 (메모리 최적화)"""
        try:
            agent_id = routing_decision.selected_agent
            
            # 자동 정리 실행
            await self._cleanup_old_data()
            
            # 성능 히스토리 업데이트 (deque 사용으로 자동 크기 제한)
            if execution_result["success"]:
                performance_score = 1.0 - (execution_result.get("execution_time", 1000) / 10000)
                performance_score = max(0.0, min(1.0, performance_score))
            else:
                performance_score = 0.0
            
            self.performance_history[agent_id].append(performance_score)
            
        except Exception as e:
            logger.error(f"Error collecting performance feedback: {e}")
    
    async def _cleanup_old_data(self) -> None:
        """오래된 데이터 정리"""
        now = datetime.now()
        
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        try:
            # Agent 메트릭에서 오래된 데이터 정리
            cutoff_time = now - timedelta(hours=24)  # 24시간 이전 데이터
            
            for agent_id, metrics in list(self.agent_metrics.items()):
                last_updated = datetime.fromisoformat(metrics.last_updated)
                if last_updated < cutoff_time:
                    # 24시간 이상 업데이트되지 않은 Agent는 오프라인으로 처리
                    metrics.status = AgentStatus.OFFLINE
            
            # 성능 히스토리는 deque로 자동 관리되므로 추가 정리 불필요
            
            self._last_cleanup = now
            logger.debug(f"Cleaned up old data at {now}")
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
    
    async def _update_learning_model(self, routing_decision: RoutingDecision, 
                                   execution_result: Dict[str, Any]) -> None:
        """학습 모델 업데이트"""
        try:
            # 간단한 학습 업데이트 (실제로는 더 복잡한 ML 모델 사용)
            agent_id = routing_decision.selected_agent
            metrics = self.agent_metrics[agent_id]
            
            if execution_result["success"]:
                # 성공 시 메트릭 개선
                actual_time = execution_result.get("execution_time", metrics.avg_response_time)
                metrics.avg_response_time = (metrics.avg_response_time * 0.9 + actual_time * 0.1)
                metrics.success_rate = min(1.0, metrics.success_rate * 1.01)
            else:
                # 실패 시 메트릭 악화
                metrics.success_rate = max(0.5, metrics.success_rate * 0.95)
            
            logger.debug(f"Updated learning model for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error updating learning model: {e}")
    
    async def _generate_execution_summary(self, results: List[Dict[str, Any]], 
                                        config: Dict[str, Any]) -> Dict[str, Any]:
        """실행 요약 생성"""
        try:
            total_tasks = len(results)
            successful_tasks = sum(1 for r in results if r["success"])
            
            # Agent별 작업 분배
            agent_distribution = {}
            execution_times = []
            
            for result in results:
                if result["success"]:
                    agent_id = result.get("selected_agent")
                    if agent_id:
                        agent_distribution[agent_id] = agent_distribution.get(agent_id, 0) + 1
                    
                    exec_time = result.get("execution_time")
                    if exec_time:
                        execution_times.append(exec_time)
            
            avg_execution_time = statistics.mean(execution_times) if execution_times else 0
            
            return {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
                "avg_execution_time": avg_execution_time,
                "agent_distribution": agent_distribution,
                "routing_strategy": config.get("routing_strategy"),
                "active_agents": len([m for m in self.agent_metrics.values() 
                                    if m.status == AgentStatus.AVAILABLE])
            }
            
        except Exception as e:
            logger.error(f"Error generating execution summary: {e}")
            return {"error": str(e)}
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Agent 상태 조회"""
        metrics = self.agent_metrics.get(agent_id)
        if not metrics:
            return None
        
        return asdict(metrics)
    
    async def update_agent_configuration(self, agent_id: str, 
                                       updates: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 설정 업데이트"""
        try:
            metrics = self.agent_metrics.get(agent_id)
            if not metrics:
                return {"success": False, "error": "Agent not found"}
            
            # 업데이트 가능한 필드들
            updatable_fields = ["status", "capabilities", "cost_per_request"]
            
            for field, value in updates.items():
                if field in updatable_fields:
                    if field == "status":
                        metrics.status = AgentStatus(value)
                    else:
                        setattr(metrics, field, value)
            
            metrics.last_updated = datetime.now().isoformat()
            
            return {"success": True, "message": f"Agent {agent_id} updated"}
            
        except Exception as e:
            logger.error(f"Error updating agent configuration: {e}")
            return {"success": False, "error": str(e)}