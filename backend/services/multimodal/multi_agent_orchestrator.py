"""
Multi-Agent Orchestrator Service
다중 AI 에이전트 오케스트레이션 및 지능형 작업 분배 시스템
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import heapq

from backend.services.multimodal.gemini_service import get_gemini_service
from backend.services.multimodal.predictive_router import get_predictive_router
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class AgentType(Enum):
    """에이전트 유형"""
    VISION_SPECIALIST = "vision_specialist"        # 이미지/비디오 전문
    AUDIO_SPECIALIST = "audio_specialist"          # 음성/오디오 전문
    TEXT_SPECIALIST = "text_specialist"            # 텍스트/언어 전문
    CODE_SPECIALIST = "code_specialist"            # 코드/개발 전문
    MULTIMODAL_GENERALIST = "multimodal_generalist" # 멀티모달 범용
    REASONING_SPECIALIST = "reasoning_specialist"   # 추론/분석 전문
    CREATIVE_SPECIALIST = "creative_specialist"     # 창작/생성 전문
    RESEARCH_SPECIALIST = "research_specialist"     # 연구/조사 전문

class AgentStatus(Enum):
    """에이전트 상태"""
    IDLE = "idle"                    # 대기 중
    BUSY = "busy"                    # 작업 중
    OVERLOADED = "overloaded"        # 과부하
    MAINTENANCE = "maintenance"       # 유지보수
    ERROR = "error"                  # 오류 상태

class TaskPriority(Enum):
    """작업 우선순위"""
    CRITICAL = "critical"    # 긴급
    HIGH = "high"           # 높음
    MEDIUM = "medium"       # 보통
    LOW = "low"            # 낮음

class OrchestrationStrategy(Enum):
    """오케스트레이션 전략"""
    LOAD_BALANCED = "load_balanced"          # 부하 분산
    CAPABILITY_MATCHED = "capability_matched" # 능력 매칭
    PERFORMANCE_OPTIMIZED = "performance_optimized" # 성능 최적화
    COST_MINIMIZED = "cost_minimized"        # 비용 최소화
    DEADLINE_AWARE = "deadline_aware"        # 데드라인 인식
    COLLABORATIVE = "collaborative"          # 협업형

@dataclass
class AgentCapability:
    """에이전트 능력"""
    agent_type: AgentType
    specializations: List[str]
    performance_metrics: Dict[str, float]
    resource_requirements: Dict[str, Any]
    max_concurrent_tasks: int
    average_processing_time: float
    accuracy_score: float
    cost_per_task: float

@dataclass
class AgentInstance:
    """에이전트 인스턴스"""
    agent_id: str
    agent_type: AgentType
    capabilities: AgentCapability
    current_status: AgentStatus
    current_load: float
    active_tasks: List[str]
    performance_history: List[Dict[str, Any]]
    last_health_check: datetime
    endpoint_url: Optional[str] = None
    model_config: Optional[Dict[str, Any]] = None

@dataclass
class Task:
    """작업 정의"""
    task_id: str
    task_type: str
    priority: TaskPriority
    requirements: Dict[str, Any]
    input_data: Dict[str, Any]
    deadline: Optional[datetime]
    estimated_duration: float
    dependencies: List[str]
    assigned_agent: Optional[str] = None
    status: str = "pending"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class OrchestrationPlan:
    """오케스트레이션 계획"""
    plan_id: str
    strategy: OrchestrationStrategy
    task_assignments: Dict[str, str]  # task_id -> agent_id
    execution_order: List[List[str]]  # 병렬 실행 그룹
    estimated_completion_time: float
    resource_allocation: Dict[str, Dict[str, Any]]
    fallback_plans: List[Dict[str, Any]]
    monitoring_checkpoints: List[float]

class MultiAgentOrchestrator:
    """다중 에이전트 오케스트레이터"""
    
    def __init__(self):
        self.agents: Dict[str, AgentInstance] = {}
        self.task_queue: List[Task] = []
        self.active_executions: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # 서비스 연동
        self.gemini_service = None
        self.predictive_router = None
        try:
            self.gemini_service = get_gemini_service()
            self.predictive_router = get_predictive_router()
        except Exception as e:
            logger.warning(f"Failed to initialize services: {e}")
        
        # 오케스트레이션 설정
        self.orchestration_config = {
            "max_concurrent_executions": 10,
            "task_timeout_seconds": 300,
            "health_check_interval": 30,
            "load_balancing_threshold": 0.8,
            "auto_scaling_enabled": True,
            "failure_retry_attempts": 3
        }
        
        # 에이전트 초기화
        self._initialize_default_agents()
        
        # 모니터링 및 스케줄링
        self._start_background_tasks()
    
    def _initialize_default_agents(self):
        """기본 에이전트 초기화"""
        default_agents = [
            {
                "agent_id": "gemini_vision_01",
                "agent_type": AgentType.VISION_SPECIALIST,
                "capabilities": AgentCapability(
                    agent_type=AgentType.VISION_SPECIALIST,
                    specializations=["image_analysis", "object_detection", "scene_understanding", "ocr"],
                    performance_metrics={"accuracy": 0.94, "speed": 0.85, "reliability": 0.92},
                    resource_requirements={"gpu": True, "memory_gb": 8, "cpu_cores": 4},
                    max_concurrent_tasks=3,
                    average_processing_time=15.0,
                    accuracy_score=0.94,
                    cost_per_task=0.05
                ),
                "model_config": {"model": "gemini-1.5-pro", "temperature": 0.7}
            },
            {
                "agent_id": "gemini_audio_01",
                "agent_type": AgentType.AUDIO_SPECIALIST,
                "capabilities": AgentCapability(
                    agent_type=AgentType.AUDIO_SPECIALIST,
                    specializations=["speech_to_text", "audio_analysis", "music_understanding", "sound_classification"],
                    performance_metrics={"accuracy": 0.91, "speed": 0.88, "reliability": 0.89},
                    resource_requirements={"gpu": False, "memory_gb": 4, "cpu_cores": 2},
                    max_concurrent_tasks=5,
                    average_processing_time=12.0,
                    accuracy_score=0.91,
                    cost_per_task=0.03
                ),
                "model_config": {"model": "gemini-1.5-flash", "temperature": 0.5}
            },
            {
                "agent_id": "gemini_text_01",
                "agent_type": AgentType.TEXT_SPECIALIST,
                "capabilities": AgentCapability(
                    agent_type=AgentType.TEXT_SPECIALIST,
                    specializations=["text_analysis", "summarization", "translation", "sentiment_analysis"],
                    performance_metrics={"accuracy": 0.96, "speed": 0.92, "reliability": 0.95},
                    resource_requirements={"gpu": False, "memory_gb": 2, "cpu_cores": 2},
                    max_concurrent_tasks=8,
                    average_processing_time=8.0,
                    accuracy_score=0.96,
                    cost_per_task=0.02
                ),
                "model_config": {"model": "gemini-1.5-flash", "temperature": 0.3}
            },
            {
                "agent_id": "gemini_multimodal_01",
                "agent_type": AgentType.MULTIMODAL_GENERALIST,
                "capabilities": AgentCapability(
                    agent_type=AgentType.MULTIMODAL_GENERALIST,
                    specializations=["multimodal_fusion", "cross_modal_reasoning", "complex_analysis"],
                    performance_metrics={"accuracy": 0.93, "speed": 0.75, "reliability": 0.90},
                    resource_requirements={"gpu": True, "memory_gb": 16, "cpu_cores": 8},
                    max_concurrent_tasks=2,
                    average_processing_time=25.0,
                    accuracy_score=0.93,
                    cost_per_task=0.08
                ),
                "model_config": {"model": "gemini-1.5-pro", "temperature": 0.7}
            },
            {
                "agent_id": "gemini_reasoning_01",
                "agent_type": AgentType.REASONING_SPECIALIST,
                "capabilities": AgentCapability(
                    agent_type=AgentType.REASONING_SPECIALIST,
                    specializations=["logical_reasoning", "problem_solving", "decision_making", "analysis"],
                    performance_metrics={"accuracy": 0.95, "speed": 0.70, "reliability": 0.93},
                    resource_requirements={"gpu": True, "memory_gb": 12, "cpu_cores": 6},
                    max_concurrent_tasks=2,
                    average_processing_time=30.0,
                    accuracy_score=0.95,
                    cost_per_task=0.10
                ),
                "model_config": {"model": "gemini-1.5-pro", "temperature": 0.2}
            }
        ]
        
        for agent_config in default_agents:
            agent = AgentInstance(
                agent_id=agent_config["agent_id"],
                agent_type=agent_config["agent_type"],
                capabilities=agent_config["capabilities"],
                current_status=AgentStatus.IDLE,
                current_load=0.0,
                active_tasks=[],
                performance_history=[],
                last_health_check=datetime.now(),
                model_config=agent_config.get("model_config")
            )
            self.agents[agent.agent_id] = agent
        
        logger.info(f"Initialized {len(self.agents)} default agents")
    
    def _start_background_tasks(self):
        """백그라운드 작업 시작"""
        # 실제 구현에서는 asyncio.create_task 사용
        logger.info("Background monitoring tasks started")
    
    async def orchestrate_workflow(
        self,
        tasks: List[Task],
        strategy: OrchestrationStrategy = OrchestrationStrategy.PERFORMANCE_OPTIMIZED,
        constraints: Optional[Dict[str, Any]] = None
    ) -> OrchestrationPlan:
        """
        워크플로우 오케스트레이션
        
        Args:
            tasks: 실행할 작업 목록
            strategy: 오케스트레이션 전략
            constraints: 제약 조건
            
        Returns:
            오케스트레이션 계획
        """
        try:
            logger.info(f"Starting workflow orchestration with {len(tasks)} tasks")
            
            # 1. 작업 분석 및 의존성 해결
            task_graph = self._analyze_task_dependencies(tasks)
            
            # 2. 에이전트 능력 평가
            agent_capabilities = await self._evaluate_agent_capabilities(tasks)
            
            # 3. 최적 할당 계획 생성
            assignment_plan = await self._generate_assignment_plan(
                tasks, agent_capabilities, strategy, constraints
            )
            
            # 4. 실행 순서 최적화
            execution_order = self._optimize_execution_order(tasks, assignment_plan, task_graph)
            
            # 5. 리소스 할당 계획
            resource_allocation = self._plan_resource_allocation(assignment_plan)
            
            # 6. 폴백 계획 생성
            fallback_plans = await self._generate_fallback_plans(assignment_plan, tasks)
            
            # 7. 모니터링 체크포인트 설정
            monitoring_checkpoints = self._setup_monitoring_checkpoints(execution_order)
            
            # 8. 오케스트레이션 계획 생성
            plan = OrchestrationPlan(
                plan_id=f"plan_{uuid.uuid4().hex[:8]}",
                strategy=strategy,
                task_assignments=assignment_plan,
                execution_order=execution_order,
                estimated_completion_time=self._estimate_completion_time(tasks, assignment_plan),
                resource_allocation=resource_allocation,
                fallback_plans=fallback_plans,
                monitoring_checkpoints=monitoring_checkpoints
            )
            
            logger.info(
                f"Orchestration plan generated",
                extra={
                    "plan_id": plan.plan_id,
                    "strategy": strategy.value,
                    "tasks_count": len(tasks),
                    "estimated_time": plan.estimated_completion_time
                }
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"Workflow orchestration failed: {str(e)}", exc_info=True)
            raise
    
    def _analyze_task_dependencies(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """작업 의존성 분석"""
        task_graph = {}
        
        for task in tasks:
            task_graph[task.task_id] = task.dependencies.copy()
        
        # 순환 의존성 검사
        if self._has_circular_dependencies(task_graph):
            raise ValueError("Circular dependencies detected in task graph")
        
        return task_graph
    
    def _has_circular_dependencies(self, graph: Dict[str, List[str]]) -> bool:
        """순환 의존성 검사"""
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if dfs(node):
                    return True
        
        return False
    
    async def _evaluate_agent_capabilities(self, tasks: List[Task]) -> Dict[str, Dict[str, float]]:
        """에이전트 능력 평가"""
        capabilities = {}
        
        for agent_id, agent in self.agents.items():
            if agent.current_status == AgentStatus.MAINTENANCE:
                continue
                
            agent_scores = {}
            
            for task in tasks:
                # 기본 점수 계산
                base_score = 0.0
                
                # 전문 분야 매칭
                task_type = task.task_type.lower()
                specializations = [spec.lower() for spec in agent.capabilities.specializations]
                
                if any(spec in task_type for spec in specializations):
                    base_score += 0.4
                
                # 에이전트 타입 매칭
                type_match_scores = {
                    "image": {AgentType.VISION_SPECIALIST: 0.9, AgentType.MULTIMODAL_GENERALIST: 0.7},
                    "video": {AgentType.VISION_SPECIALIST: 0.9, AgentType.MULTIMODAL_GENERALIST: 0.8},
                    "audio": {AgentType.AUDIO_SPECIALIST: 0.9, AgentType.MULTIMODAL_GENERALIST: 0.7},
                    "text": {AgentType.TEXT_SPECIALIST: 0.9, AgentType.MULTIMODAL_GENERALIST: 0.6},
                    "code": {AgentType.CODE_SPECIALIST: 0.9, AgentType.TEXT_SPECIALIST: 0.5},
                    "reasoning": {AgentType.REASONING_SPECIALIST: 0.9, AgentType.MULTIMODAL_GENERALIST: 0.6},
                    "creative": {AgentType.CREATIVE_SPECIALIST: 0.9, AgentType.MULTIMODAL_GENERALIST: 0.7}
                }
                
                for task_keyword, type_scores in type_match_scores.items():
                    if task_keyword in task_type:
                        base_score += type_scores.get(agent.agent_type, 0.1)
                        break
                
                # 성능 메트릭 반영
                performance_score = (
                    agent.capabilities.performance_metrics.get("accuracy", 0.5) * 0.4 +
                    agent.capabilities.performance_metrics.get("speed", 0.5) * 0.3 +
                    agent.capabilities.performance_metrics.get("reliability", 0.5) * 0.3
                )
                
                # 현재 부하 고려
                load_penalty = agent.current_load * 0.2
                
                # 최종 점수
                final_score = (base_score + performance_score) * (1 - load_penalty)
                agent_scores[task.task_id] = max(0.0, min(1.0, final_score))
            
            capabilities[agent_id] = agent_scores
        
        return capabilities
    
    async def _generate_assignment_plan(
        self,
        tasks: List[Task],
        agent_capabilities: Dict[str, Dict[str, float]],
        strategy: OrchestrationStrategy,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """최적 할당 계획 생성"""
        assignment_plan = {}
        constraints = constraints or {}
        
        # 우선순위별 작업 정렬
        sorted_tasks = sorted(tasks, key=lambda t: (
            t.priority.value,
            t.deadline.timestamp() if t.deadline else float('inf'),
            -t.estimated_duration
        ))
        
        if strategy == OrchestrationStrategy.PERFORMANCE_OPTIMIZED:
            # 성능 최적화: 가장 적합한 에이전트에 할당
            for task in sorted_tasks:
                best_agent = None
                best_score = 0.0
                
                for agent_id, scores in agent_capabilities.items():
                    agent = self.agents[agent_id]
                    
                    # 용량 체크
                    if len(agent.active_tasks) >= agent.capabilities.max_concurrent_tasks:
                        continue
                    
                    score = scores.get(task.task_id, 0.0)
                    if score > best_score:
                        best_score = score
                        best_agent = agent_id
                
                if best_agent:
                    assignment_plan[task.task_id] = best_agent
                    self.agents[best_agent].active_tasks.append(task.task_id)
        
        elif strategy == OrchestrationStrategy.LOAD_BALANCED:
            # 부하 분산: 가장 여유로운 에이전트에 할당
            for task in sorted_tasks:
                best_agent = None
                min_load = float('inf')
                
                for agent_id, agent in self.agents.items():
                    if agent.current_status == AgentStatus.MAINTENANCE:
                        continue
                    
                    if len(agent.active_tasks) >= agent.capabilities.max_concurrent_tasks:
                        continue
                    
                    # 능력 점수가 최소 임계값 이상인지 확인
                    capability_score = agent_capabilities[agent_id].get(task.task_id, 0.0)
                    if capability_score < 0.3:
                        continue
                    
                    if agent.current_load < min_load:
                        min_load = agent.current_load
                        best_agent = agent_id
                
                if best_agent:
                    assignment_plan[task.task_id] = best_agent
                    self.agents[best_agent].active_tasks.append(task.task_id)
                    self.agents[best_agent].current_load += 0.1
        
        elif strategy == OrchestrationStrategy.COST_MINIMIZED:
            # 비용 최소화: 가장 저렴한 에이전트에 할당
            for task in sorted_tasks:
                best_agent = None
                min_cost = float('inf')
                
                for agent_id, agent in self.agents.items():
                    if agent.current_status == AgentStatus.MAINTENANCE:
                        continue
                    
                    if len(agent.active_tasks) >= agent.capabilities.max_concurrent_tasks:
                        continue
                    
                    capability_score = agent_capabilities[agent_id].get(task.task_id, 0.0)
                    if capability_score < 0.3:
                        continue
                    
                    cost = agent.capabilities.cost_per_task
                    if cost < min_cost:
                        min_cost = cost
                        best_agent = agent_id
                
                if best_agent:
                    assignment_plan[task.task_id] = best_agent
                    self.agents[best_agent].active_tasks.append(task.task_id)
        
        return assignment_plan
    
    def _optimize_execution_order(
        self,
        tasks: List[Task],
        assignment_plan: Dict[str, str],
        task_graph: Dict[str, List[str]]
    ) -> List[List[str]]:
        """실행 순서 최적화"""
        execution_order = []
        completed_tasks = set()
        remaining_tasks = {task.task_id for task in tasks}
        
        while remaining_tasks:
            # 현재 실행 가능한 작업 찾기
            ready_tasks = []
            
            for task_id in remaining_tasks:
                dependencies = task_graph.get(task_id, [])
                if all(dep in completed_tasks for dep in dependencies):
                    ready_tasks.append(task_id)
            
            if not ready_tasks:
                # 데드락 상황 - 순환 의존성 또는 누락된 의존성
                logger.warning(f"Deadlock detected with remaining tasks: {remaining_tasks}")
                ready_tasks = list(remaining_tasks)  # 강제 실행
            
            # 에이전트별로 그룹화하여 병렬 실행 최적화
            agent_groups = {}
            for task_id in ready_tasks:
                agent_id = assignment_plan.get(task_id)
                if agent_id:
                    if agent_id not in agent_groups:
                        agent_groups[agent_id] = []
                    agent_groups[agent_id].append(task_id)
            
            # 병렬 실행 그룹 생성
            parallel_group = []
            for agent_id, task_list in agent_groups.items():
                agent = self.agents[agent_id]
                # 에이전트의 동시 실행 능력 고려
                max_concurrent = agent.capabilities.max_concurrent_tasks
                parallel_group.extend(task_list[:max_concurrent])
            
            if parallel_group:
                execution_order.append(parallel_group)
                completed_tasks.update(parallel_group)
                remaining_tasks -= set(parallel_group)
        
        return execution_order
    
    def _plan_resource_allocation(self, assignment_plan: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """리소스 할당 계획"""
        resource_allocation = {}
        
        for task_id, agent_id in assignment_plan.items():
            agent = self.agents[agent_id]
            
            resource_allocation[task_id] = {
                "agent_id": agent_id,
                "agent_type": agent.agent_type.value,
                "resource_requirements": agent.capabilities.resource_requirements.copy(),
                "estimated_cost": agent.capabilities.cost_per_task,
                "estimated_duration": agent.capabilities.average_processing_time,
                "priority_weight": 1.0
            }
        
        return resource_allocation
    
    async def _generate_fallback_plans(
        self,
        assignment_plan: Dict[str, str],
        tasks: List[Task]
    ) -> List[Dict[str, Any]]:
        """폴백 계획 생성"""
        fallback_plans = []
        
        # 각 작업에 대한 대체 에이전트 찾기
        for task in tasks:
            task_id = task.task_id
            primary_agent = assignment_plan.get(task_id)
            
            if not primary_agent:
                continue
            
            # 대체 가능한 에이전트 찾기
            alternative_agents = []
            
            for agent_id, agent in self.agents.items():
                if agent_id == primary_agent:
                    continue
                
                if agent.current_status == AgentStatus.MAINTENANCE:
                    continue
                
                # 기본적인 호환성 체크
                task_type = task.task_type.lower()
                agent_specializations = [spec.lower() for spec in agent.capabilities.specializations]
                
                compatibility_score = 0.0
                if any(spec in task_type for spec in agent_specializations):
                    compatibility_score = 0.6
                elif agent.agent_type == AgentType.MULTIMODAL_GENERALIST:
                    compatibility_score = 0.4
                
                if compatibility_score > 0.3:
                    alternative_agents.append({
                        "agent_id": agent_id,
                        "compatibility_score": compatibility_score,
                        "estimated_delay": agent.capabilities.average_processing_time * 1.2
                    })
            
            # 호환성 점수로 정렬
            alternative_agents.sort(key=lambda x: x["compatibility_score"], reverse=True)
            
            fallback_plans.append({
                "task_id": task_id,
                "primary_agent": primary_agent,
                "alternatives": alternative_agents[:3],  # 상위 3개만
                "fallback_triggers": [
                    "agent_failure",
                    "timeout",
                    "overload",
                    "quality_threshold"
                ]
            })
        
        return fallback_plans
    
    def _setup_monitoring_checkpoints(self, execution_order: List[List[str]]) -> List[float]:
        """모니터링 체크포인트 설정"""
        checkpoints = []
        
        # 각 병렬 실행 그룹 완료 시점을 체크포인트로 설정
        cumulative_time = 0.0
        
        for group in execution_order:
            # 그룹 내 최대 실행 시간 계산
            max_duration = 0.0
            
            for task_id in group:
                # 작업에 할당된 에이전트의 평균 처리 시간 사용
                for agent in self.agents.values():
                    if task_id in agent.active_tasks:
                        max_duration = max(max_duration, agent.capabilities.average_processing_time)
                        break
            
            cumulative_time += max_duration
            checkpoints.append(cumulative_time)
        
        # 추가 중간 체크포인트 (긴 작업의 경우)
        detailed_checkpoints = []
        for checkpoint in checkpoints:
            if checkpoint > 60.0:  # 1분 이상인 경우
                # 30초 간격으로 중간 체크포인트 추가
                intermediate_points = int(checkpoint // 30)
                for i in range(1, intermediate_points + 1):
                    detailed_checkpoints.append(i * 30.0)
            detailed_checkpoints.append(checkpoint)
        
        return sorted(set(detailed_checkpoints))
    
    def _estimate_completion_time(self, tasks: List[Task], assignment_plan: Dict[str, str]) -> float:
        """완료 시간 추정"""
        agent_workloads = {}
        
        # 각 에이전트의 작업 부하 계산
        for task in tasks:
            agent_id = assignment_plan.get(task.task_id)
            if not agent_id:
                continue
            
            agent = self.agents[agent_id]
            duration = agent.capabilities.average_processing_time
            
            if agent_id not in agent_workloads:
                agent_workloads[agent_id] = []
            
            agent_workloads[agent_id].append(duration)
        
        # 각 에이전트의 총 실행 시간 계산 (병렬 처리 고려)
        max_completion_time = 0.0
        
        for agent_id, durations in agent_workloads.items():
            agent = self.agents[agent_id]
            max_concurrent = agent.capabilities.max_concurrent_tasks
            
            # 병렬 처리를 고려한 실행 시간 계산
            total_duration = sum(durations)
            parallel_duration = total_duration / max_concurrent
            
            max_completion_time = max(max_completion_time, parallel_duration)
        
        # 오버헤드 추가 (통신, 스케줄링 등)
        overhead_factor = 1.15
        return max_completion_time * overhead_factor
    
    async def execute_orchestration_plan(self, plan: OrchestrationPlan) -> Dict[str, Any]:
        """오케스트레이션 계획 실행"""
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        
        try:
            logger.info(f"Starting orchestration execution: {execution_id}")
            
            execution_context = {
                "execution_id": execution_id,
                "plan_id": plan.plan_id,
                "start_time": datetime.now(),
                "status": "running",
                "completed_tasks": [],
                "failed_tasks": [],
                "current_checkpoint": 0,
                "results": {}
            }
            
            self.active_executions[execution_id] = execution_context
            
            # 병렬 실행 그룹별로 순차 실행
            for group_index, task_group in enumerate(plan.execution_order):
                logger.info(f"Executing group {group_index + 1}/{len(plan.execution_order)}")
                
                # 그룹 내 작업들을 병렬로 실행
                group_tasks = []
                for task_id in task_group:
                    agent_id = plan.task_assignments.get(task_id)
                    if agent_id:
                        task_coroutine = self._execute_single_task(task_id, agent_id, execution_context)
                        group_tasks.append(task_coroutine)
                
                # 그룹 완료 대기
                if group_tasks:
                    group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
                    
                    # 결과 처리
                    for i, result in enumerate(group_results):
                        task_id = task_group[i]
                        if isinstance(result, Exception):
                            execution_context["failed_tasks"].append({
                                "task_id": task_id,
                                "error": str(result),
                                "timestamp": datetime.now()
                            })
                        else:
                            execution_context["completed_tasks"].append(task_id)
                            execution_context["results"][task_id] = result
                
                # 체크포인트 업데이트
                execution_context["current_checkpoint"] = group_index + 1
            
            # 실행 완료
            execution_context["status"] = "completed"
            execution_context["end_time"] = datetime.now()
            execution_context["total_duration"] = (
                execution_context["end_time"] - execution_context["start_time"]
            ).total_seconds()
            
            logger.info(
                f"Orchestration execution completed: {execution_id}",
                extra={
                    "execution_id": execution_id,
                    "completed_tasks": len(execution_context["completed_tasks"]),
                    "failed_tasks": len(execution_context["failed_tasks"]),
                    "duration": execution_context["total_duration"]
                }
            )
            
            return execution_context
            
        except Exception as e:
            logger.error(f"Orchestration execution failed: {execution_id}", exc_info=True)
            execution_context["status"] = "failed"
            execution_context["error"] = str(e)
            execution_context["end_time"] = datetime.now()
            raise
    
    async def _execute_single_task(
        self,
        task_id: str,
        agent_id: str,
        execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """단일 작업 실행"""
        try:
            agent = self.agents[agent_id]
            
            # 에이전트 상태 업데이트
            agent.current_status = AgentStatus.BUSY
            agent.current_load = min(1.0, agent.current_load + 0.2)
            
            # 작업 실행 시뮬레이션 (실제로는 에이전트 API 호출)
            await asyncio.sleep(agent.capabilities.average_processing_time / 10)  # 시뮬레이션용 단축
            
            # 결과 생성
            result = {
                "task_id": task_id,
                "agent_id": agent_id,
                "status": "completed",
                "execution_time": agent.capabilities.average_processing_time,
                "quality_score": agent.capabilities.accuracy_score,
                "output": f"Task {task_id} completed by {agent_id}",
                "timestamp": datetime.now()
            }
            
            # 에이전트 상태 복원
            agent.current_status = AgentStatus.IDLE
            agent.current_load = max(0.0, agent.current_load - 0.2)
            if task_id in agent.active_tasks:
                agent.active_tasks.remove(task_id)
            
            return result
            
        except Exception as e:
            # 에이전트 상태 복원
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.current_status = AgentStatus.ERROR
                if task_id in agent.active_tasks:
                    agent.active_tasks.remove(task_id)
            
            raise Exception(f"Task {task_id} failed on agent {agent_id}: {str(e)}")
    
    def get_orchestration_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """오케스트레이션 상태 조회"""
        return self.active_executions.get(execution_id)
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """모든 에이전트 상태 조회"""
        status = {}
        
        for agent_id, agent in self.agents.items():
            status[agent_id] = {
                "agent_type": agent.agent_type.value,
                "status": agent.current_status.value,
                "current_load": agent.current_load,
                "active_tasks": len(agent.active_tasks),
                "max_concurrent_tasks": agent.capabilities.max_concurrent_tasks,
                "specializations": agent.capabilities.specializations,
                "performance_metrics": agent.capabilities.performance_metrics,
                "last_health_check": agent.last_health_check.isoformat()
            }
        
        return status
    
    async def add_agent(self, agent_config: Dict[str, Any]) -> str:
        """새 에이전트 추가"""
        agent_id = agent_config.get("agent_id", f"agent_{uuid.uuid4().hex[:8]}")
        
        # 에이전트 인스턴스 생성
        capabilities = AgentCapability(**agent_config["capabilities"])
        
        agent = AgentInstance(
            agent_id=agent_id,
            agent_type=AgentType(agent_config["agent_type"]),
            capabilities=capabilities,
            current_status=AgentStatus.IDLE,
            current_load=0.0,
            active_tasks=[],
            performance_history=[],
            last_health_check=datetime.now(),
            endpoint_url=agent_config.get("endpoint_url"),
            model_config=agent_config.get("model_config")
        )
        
        self.agents[agent_id] = agent
        
        logger.info(f"Added new agent: {agent_id} ({agent.agent_type.value})")
        return agent_id
    
    async def remove_agent(self, agent_id: str) -> bool:
        """에이전트 제거"""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        
        # 활성 작업이 있는 경우 제거 불가
        if agent.active_tasks:
            raise ValueError(f"Cannot remove agent {agent_id}: has active tasks")
        
        del self.agents[agent_id]
        logger.info(f"Removed agent: {agent_id}")
        return True

# 전역 인스턴스
_orchestrator_instance = None

def get_multi_agent_orchestrator() -> MultiAgentOrchestrator:
    """멀티 에이전트 오케스트레이터 인스턴스 반환"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MultiAgentOrchestrator()
    return _orchestrator_instance