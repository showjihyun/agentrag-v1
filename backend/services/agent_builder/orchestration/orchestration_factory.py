"""
Orchestration Factory
오케스트레이션 패턴별 조정자 생성 팩토리
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.core.structured_logging import get_logger
from .base_orchestrator import BaseOrchestrator, ValidationResult, ExecutionResult, ExecutionStatus
from .patterns.trend_2025.consensus_orchestrator import ConsensusOrchestrator
from .patterns.trend_2025.dynamic_routing_orchestrator import DynamicRoutingOrchestrator
from .patterns.trend_2025.swarm_orchestrator import SwarmOrchestrator
from .patterns.trend_2025.event_driven_orchestrator import EventDrivenOrchestrator
from .patterns.trend_2025.reflection_orchestrator import ReflectionOrchestrator

logger = get_logger(__name__)


class SequentialOrchestrator(BaseOrchestrator):
    """순차 실행 오케스트레이터"""
    
    def __init__(self):
        super().__init__("sequential")
    
    async def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """순차 실행 설정 검증"""
        errors = []
        warnings = []
        suggestions = []
        
        # 필수 필드 검증
        missing_fields = self._validate_required_fields(config, ["agent_roles"])
        errors.extend([f"Missing required field: {field}" for field in missing_fields])
        
        agent_roles = config.get("agent_roles", [])
        
        # Agent 수 검증
        agent_errors = self._validate_list_length(agent_roles, "agent_roles", min_length=2)
        errors.extend(agent_errors)
        
        if not errors:
            # 우선순위 중복 검사
            priorities = [agent["priority"] for agent in agent_roles if "priority" in agent]
            if len(priorities) != len(set(priorities)):
                warnings.append("Duplicate priorities detected. Agents may execute in unexpected order")
            
            # 의존성 순환 검사
            dependencies = {agent.get("id", f"agent_{i}"): agent.get("dependencies", []) 
                          for i, agent in enumerate(agent_roles)}
            if self._has_circular_dependency(dependencies):
                errors.append("Circular dependencies detected in agent configuration")
        
        if not errors:
            suggestions.append("Consider adding timeout settings for better reliability")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _has_circular_dependency(self, dependencies: Dict[str, list]) -> bool:
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
            
            for neighbor in dependencies.get(node, []):
                if dfs(neighbor):
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in dependencies:
            if dfs(node):
                return True
        return False
    
    async def execute(
        self, 
        config: Dict[str, Any], 
        input_data: Dict[str, Any], 
        user_id: str, 
        execution_id: str
    ) -> ExecutionResult:
        """순차 실행"""
        start_time = datetime.now()
        self.logger.info(f"Starting sequential orchestration {execution_id}")
        
        try:
            agent_roles = config.get("agent_roles", [])
            # 우선순위 순으로 정렬
            sorted_agents = sorted(agent_roles, key=lambda x: x.get("priority", 1))
            
            results = {}
            current_data = input_data
            
            for i, agent in enumerate(sorted_agents):
                self.logger.info(f"Executing agent {agent.get('name', f'Agent_{i}')} (step {i+1}/{len(sorted_agents)})")
                
                # 진행률 업데이트
                progress = (i + 1) / len(sorted_agents)
                self._update_execution_progress(execution_id, progress, f"Executing {agent.get('name', f'Agent_{i}')}")
                
                # TODO: 실제 Agent 실행 로직 구현
                # 현재는 mock 결과 반환
                agent_result = {
                    "agent_id": agent.get("id", f"agent_{i}"),
                    "agent_name": agent.get("name", f"Agent_{i}"),
                    "status": "completed",
                    "output": f"Result from {agent.get('name', f'Agent_{i}')}",
                    "execution_time": 2.5,
                    "tokens_used": 150
                }
                
                results[agent.get("id", f"agent_{i}")] = agent_result
                current_data = {**current_data, **agent_result["output"]} if isinstance(agent_result["output"], dict) else current_data
            
            end_time = datetime.now()
            metrics = self._calculate_execution_metrics(start_time, end_time, len(sorted_agents), len(sorted_agents))
            
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED,
                orchestration_type="sequential",
                started_at=start_time,
                completed_at=end_time,
                results={
                    "orchestration_type": "sequential",
                    "results": results,
                    "final_output": current_data,
                    "metrics": {
                        "total_agents": len(sorted_agents),
                        "total_execution_time": sum(r["execution_time"] for r in results.values()),
                        "total_tokens": sum(r["tokens_used"] for r in results.values()),
                        **metrics
                    }
                },
                metrics=metrics
            )
            
        except Exception as e:
            self.logger.error(f"Sequential orchestration failed: {e}")
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                orchestration_type="sequential",
                started_at=start_time,
                completed_at=datetime.now(),
                error=str(e)
            )


class ParallelOrchestrator(BaseOrchestrator):
    """병렬 실행 오케스트레이터"""
    
    def __init__(self):
        super().__init__("parallel")
    
    async def validate_configuration(self, config: Dict[str, Any]) -> ValidationResult:
        """병렬 실행 설정 검증"""
        errors = []
        warnings = []
        suggestions = []
        
        # 필수 필드 검증
        missing_fields = self._validate_required_fields(config, ["agent_roles"])
        errors.extend([f"Missing required field: {field}" for field in missing_fields])
        
        agent_roles = config.get("agent_roles", [])
        
        # Agent 수 검증
        agent_errors = self._validate_list_length(agent_roles, "agent_roles", min_length=2)
        errors.extend(agent_errors)
        
        # 병렬 실행에서는 의존성이 있으면 안됨
        for agent in agent_roles:
            if agent.get("dependencies"):
                warnings.append(f"Agent {agent.get('name', 'Unknown')} has dependencies, which may affect parallel execution")
        
        performance_thresholds = config.get("performance_thresholds", {})
        max_execution_time = performance_thresholds.get("max_execution_time", 300000)
        if max_execution_time < 30000:  # 30초 미만
            warnings.append("Very short execution timeout may cause parallel agents to fail")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    async def execute(
        self, 
        config: Dict[str, Any], 
        input_data: Dict[str, Any], 
        user_id: str, 
        execution_id: str
    ) -> ExecutionResult:
        """병렬 실행"""
        import asyncio
        
        start_time = datetime.now()
        self.logger.info(f"Starting parallel orchestration {execution_id}")
        
        try:
            agent_roles = config.get("agent_roles", [])
            
            async def execute_agent(agent, index):
                """개별 Agent 실행"""
                agent_name = agent.get("name", f"Agent_{index}")
                self.logger.info(f"Executing agent {agent_name} in parallel")
                
                # TODO: 실제 Agent 실행 로직 구현
                await asyncio.sleep(1)  # 실행 시뮬레이션
                
                return {
                    "agent_id": agent.get("id", f"agent_{index}"),
                    "agent_name": agent_name,
                    "status": "completed",
                    "output": f"Parallel result from {agent_name}",
                    "execution_time": 1.8,
                    "tokens_used": 120
                }
            
            # 모든 Agent를 병렬로 실행
            tasks = [execute_agent(agent, i) for i, agent in enumerate(agent_roles)]
            agent_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            results = {}
            successful_results = []
            failed_results = []
            
            for i, result in enumerate(agent_results):
                if isinstance(result, Exception):
                    failed_results.append({
                        "agent_id": agent_roles[i].get("id", f"agent_{i}"),
                        "agent_name": agent_roles[i].get("name", f"Agent_{i}"),
                        "status": "failed",
                        "error": str(result)
                    })
                else:
                    results[result["agent_id"]] = result
                    successful_results.append(result)
            
            # 결과 집계
            aggregated_output = {}
            for result in successful_results:
                if isinstance(result["output"], dict):
                    aggregated_output.update(result["output"])
                else:
                    aggregated_output[result["agent_id"]] = result["output"]
            
            end_time = datetime.now()
            metrics = self._calculate_execution_metrics(start_time, end_time, len(agent_roles), len(successful_results))
            
            status = ExecutionStatus.COMPLETED if not failed_results else ExecutionStatus.FAILED
            
            return ExecutionResult(
                execution_id=execution_id,
                status=status,
                orchestration_type="parallel",
                started_at=start_time,
                completed_at=end_time,
                results={
                    "orchestration_type": "parallel",
                    "results": results,
                    "failed_results": failed_results,
                    "final_output": aggregated_output,
                    "metrics": {
                        "total_agents": len(agent_roles),
                        "successful_agents": len(successful_results),
                        "failed_agents": len(failed_results),
                        "max_execution_time": max(r["execution_time"] for r in successful_results) if successful_results else 0,
                        "total_tokens": sum(r["tokens_used"] for r in successful_results),
                        **metrics
                    }
                },
                metrics=metrics
            )
            
        except Exception as e:
            self.logger.error(f"Parallel orchestration failed: {e}")
            return ExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.FAILED,
                orchestration_type="parallel",
                started_at=start_time,
                completed_at=datetime.now(),
                error=str(e)
            )


class HierarchicalOrchestrator(BaseOrchestrator):
    """계층적 관리 오케스트레이터"""
    
    def __init__(self):
        super().__init__("hierarchical")
    
    async def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """계층적 관리 설정 검증"""
        errors = []
        warnings = []
        suggestions = []
        
        agent_roles = config.get("agent_roles", [])
        if len(agent_roles) < 3:
            errors.append("Hierarchical orchestration requires at least 3 agents (1 manager + 2 workers)")
        
        # 매니저 역할 확인
        managers = [agent for agent in agent_roles if agent.get("role") == "manager"]
        if len(managers) == 0:
            errors.append("Hierarchical orchestration requires at least one manager agent")
        elif len(managers) > 1:
            warnings.append("Multiple managers detected. Consider using a single manager for clarity")
        
        # 워커 역할 확인
        workers = [agent for agent in agent_roles if agent.get("role") == "worker"]
        if len(workers) < 2:
            warnings.append("Hierarchical orchestration works best with multiple worker agents")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    async def execute(
        self, 
        config: Dict[str, Any], 
        input_data: Dict[str, Any], 
        user_id: str, 
        execution_id: str
    ) -> Dict[str, Any]:
        """계층적 실행"""
        self.logger.info(f"Starting hierarchical orchestration {execution_id}")
        
        agent_roles = config.get("agent_roles", [])
        
        # 역할별 Agent 분류
        managers = [agent for agent in agent_roles if agent.get("role") == "manager"]
        workers = [agent for agent in agent_roles if agent.get("role") == "worker"]
        critics = [agent for agent in agent_roles if agent.get("role") == "critic"]
        
        results = {}
        
        # 1단계: 매니저가 작업 계획 수립
        if managers:
            manager = managers[0]
            self.logger.info(f"Manager {manager['name']} planning tasks")
            
            manager_result = {
                "agent_id": manager["id"],
                "agent_name": manager["name"],
                "status": "completed",
                "output": {
                    "task_plan": f"Task plan from {manager['name']}",
                    "worker_assignments": {worker["id"]: f"Task for {worker['name']}" for worker in workers}
                },
                "execution_time": 3.0,
                "tokens_used": 200
            }
            results[manager["id"]] = manager_result
        
        # 2단계: 워커들이 할당된 작업 수행
        worker_results = []
        for worker in workers:
            self.logger.info(f"Worker {worker['name']} executing assigned task")
            
            worker_result = {
                "agent_id": worker["id"],
                "agent_name": worker["name"],
                "status": "completed",
                "output": f"Work result from {worker['name']}",
                "execution_time": 2.2,
                "tokens_used": 180
            }
            results[worker["id"]] = worker_result
            worker_results.append(worker_result)
        
        # 3단계: 비평가가 결과 검토 (있는 경우)
        if critics:
            critic = critics[0]
            self.logger.info(f"Critic {critic['name']} reviewing results")
            
            critic_result = {
                "agent_id": critic["id"],
                "agent_name": critic["name"],
                "status": "completed",
                "output": {
                    "review": f"Quality review from {critic['name']}",
                    "approved": True,
                    "suggestions": ["Good work overall", "Minor improvements possible"]
                },
                "execution_time": 1.5,
                "tokens_used": 100
            }
            results[critic["id"]] = critic_result
        
        # 최종 결과 집계
        final_output = {
            "management_plan": results.get(managers[0]["id"], {}).get("output", {}) if managers else {},
            "work_results": [r["output"] for r in worker_results],
            "quality_review": results.get(critics[0]["id"], {}).get("output", {}) if critics else {}
        }
        
        return {
            "execution_id": execution_id,
            "status": "completed",
            "orchestration_type": "hierarchical",
            "results": results,
            "final_output": final_output,
            "metrics": {
                "total_agents": len(agent_roles),
                "managers": len(managers),
                "workers": len(workers),
                "critics": len(critics),
                "total_execution_time": sum(r["execution_time"] for r in results.values()),
                "total_tokens": sum(r["tokens_used"] for r in results.values())
            }
        }


class OrchestrationFactory:
    """오케스트레이션 팩토리"""
    
    _orchestrators = {
        "sequential": SequentialOrchestrator,
        "parallel": ParallelOrchestrator,
        "hierarchical": HierarchicalOrchestrator,
        "adaptive": SequentialOrchestrator,  # 임시로 Sequential 사용
        
        # 2025년 트렌드 패턴들 - 실제 구현체 사용
        "consensus_building": ConsensusOrchestrator,
        "dynamic_routing": DynamicRoutingOrchestrator,
        "swarm_intelligence": SwarmOrchestrator,
        "event_driven": EventDrivenOrchestrator,
        "reflection": ReflectionOrchestrator,
        
        # 2026년 차세대 패턴들도 임시로 기본 패턴 사용
        "neuromorphic": ParallelOrchestrator,
        "quantum_enhanced": ParallelOrchestrator,
        "bio_inspired": HierarchicalOrchestrator,
        "self_evolving": SequentialOrchestrator,
        "federated": ParallelOrchestrator,
        "emotional_ai": HierarchicalOrchestrator,
        "predictive": SequentialOrchestrator,
    }
    
    @classmethod
    def create(cls, pattern_type: str) -> BaseOrchestrator:
        """오케스트레이터 생성"""
        if pattern_type not in cls._orchestrators:
            raise ValueError(f"Unknown orchestration pattern: {pattern_type}")
        
        orchestrator_class = cls._orchestrators[pattern_type]
        return orchestrator_class()
    
    @classmethod
    def get_available_patterns(cls) -> list:
        """사용 가능한 패턴 목록 반환"""
        return list(cls._orchestrators.keys())
    
    @classmethod
    def register_pattern(cls, pattern_type: str, orchestrator_class):
        """새로운 패턴 등록"""
        cls._orchestrators[pattern_type] = orchestrator_class
        logger.info(f"Registered new orchestration pattern: {pattern_type}")