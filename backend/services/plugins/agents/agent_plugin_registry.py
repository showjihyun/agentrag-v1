"""
Agent Plugin Registry

Agent Plugin들을 관리하고 이벤트 기반 통신을 지원하는 레지스트리
"""
from typing import Dict, List, Any, Optional, Type
import asyncio
from datetime import datetime

from backend.services.plugins.plugin_registry import PluginRegistry
from backend.services.plugins.agents.base_agent_plugin import IAgentPlugin, AgentExecutionContext
from backend.models.plugin import PluginInfo, PluginStatus
from backend.core.event_bus import EventBus


class AgentPluginRegistry(PluginRegistry):
    """Agent Plugin 전용 레지스트리"""
    
    def __init__(self, event_bus: EventBus, db_session=None, cache_manager=None, security_manager=None):
        # 기본값 설정 (실제 운영에서는 의존성 주입으로 처리)
        if db_session is None:
            from backend.core.dependencies import get_db_session
            db_session = get_db_session()
        
        if cache_manager is None:
            from backend.core.cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            
        super().__init__(db_session, cache_manager, security_manager)
        self.event_bus = event_bus
        self._agent_plugins: Dict[str, IAgentPlugin] = {}
        self._agent_communication_channels: Dict[str, str] = {}
        self._orchestration_sessions: Dict[str, Dict[str, Any]] = {}
        
        # 이벤트 핸들러 등록
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """이벤트 기반 통신을 위한 핸들러 설정"""
        # Agent 간 통신 이벤트 핸들러
        self.event_bus.subscribe("agent_communication", self._handle_agent_communication)
        self.event_bus.subscribe("orchestration_request", self._handle_orchestration_request)
        self.event_bus.subscribe("agent_status_update", self._handle_agent_status_update)
        
        # 패턴별 특화 이벤트 핸들러
        self.event_bus.subscribe("vote_request", self._handle_vote_request)
        self.event_bus.subscribe("vote_response", self._handle_vote_response)
        self.event_bus.subscribe("consensus_reached", self._handle_consensus_reached)
        self.event_bus.subscribe("pheromone_deposit", self._handle_pheromone_deposit)
        self.event_bus.subscribe("swarm_convergence", self._handle_swarm_convergence)
        self.event_bus.subscribe("performance_metrics", self._handle_performance_metrics)
        self.event_bus.subscribe("routing_decision", self._handle_routing_decision)
    
    async def register_agent_plugin(
        self, 
        plugin: IAgentPlugin, 
        config: Dict[str, Any] = None
    ) -> bool:
        """Agent Plugin 등록"""
        try:
            # 기본 플러그인 등록
            success = self.register_plugin(plugin, config or {})
            if not success:
                return False
            
            # Agent 특화 등록
            agent_type = plugin.get_agent_type()
            self._agent_plugins[agent_type] = plugin
            
            # 통신 채널 설정
            channel_name = f"agent_{agent_type}_{datetime.now().timestamp()}"
            self._agent_communication_channels[agent_type] = channel_name
            
            # Agent 등록 이벤트 발행
            await self.event_bus.publish(
                "agent_registered",
                {
                    "agent_type": agent_type,
                    "agent_id": plugin.get_manifest().name,
                    "capabilities": [cap.name for cap in plugin.get_capabilities()],
                    "communication_channel": channel_name,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Failed to register agent plugin: {e}")
            return False
    
    async def execute_agent_with_communication(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        context: AgentExecutionContext,
        communication_mode: str = "direct"
    ) -> Dict[str, Any]:
        """이벤트 기반 통신을 사용한 Agent 실행"""
        if agent_type not in self._agent_plugins:
            raise ValueError(f"Agent plugin not found: {agent_type}")
        
        plugin = self._agent_plugins[agent_type]
        
        # 실행 전 이벤트 발행
        execution_id = f"exec_{agent_type}_{datetime.now().timestamp()}"
        await self.event_bus.publish(
            "agent_execution_started",
            {
                "execution_id": execution_id,
                "agent_type": agent_type,
                "input_data": input_data,
                "context": context.dict(),
                "communication_mode": communication_mode
            }
        )
        
        try:
            # Agent 실행
            if communication_mode == "event_driven":
                result = await self._execute_with_event_communication(plugin, input_data, context, execution_id)
            else:
                result = plugin.execute_agent(input_data, context)
            
            # 실행 완료 이벤트 발행
            await self.event_bus.publish(
                "agent_execution_completed",
                {
                    "execution_id": execution_id,
                    "agent_type": agent_type,
                    "result": result,
                    "success": result.get("success", False)
                }
            )
            
            return result
            
        except Exception as e:
            # 실행 실패 이벤트 발행
            await self.event_bus.publish(
                "agent_execution_failed",
                {
                    "execution_id": execution_id,
                    "agent_type": agent_type,
                    "error": str(e)
                }
            )
            raise
    
    async def orchestrate_agents(
        self,
        orchestration_pattern: str,
        agents: List[str],
        task: Dict[str, Any],
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """다중 Agent 오케스트레이션"""
        session_id = f"orch_{orchestration_pattern}_{datetime.now().timestamp()}"
        
        # 오케스트레이션 세션 생성
        self._orchestration_sessions[session_id] = {
            "pattern": orchestration_pattern,
            "agents": agents,
            "task": task,
            "context": context.dict(),
            "status": "started",
            "results": {},
            "communication_log": []
        }
        
        # 오케스트레이션 시작 이벤트
        await self.event_bus.publish(
            "orchestration_started",
            {
                "session_id": session_id,
                "pattern": orchestration_pattern,
                "agents": agents,
                "task": task
            }
        )
        
        try:
            if orchestration_pattern == "consensus":
                result = await self._execute_consensus_orchestration(session_id, agents, task, context)
            elif orchestration_pattern == "swarm":
                result = await self._execute_swarm_orchestration(session_id, agents, task, context)
            elif orchestration_pattern == "dynamic_routing":
                result = await self._execute_dynamic_routing_orchestration(session_id, agents, task, context)
            elif orchestration_pattern == "parallel":
                result = await self._execute_parallel_orchestration(session_id, agents, task, context)
            else:
                result = await self._execute_sequential_orchestration(session_id, agents, task, context)
            
            # 오케스트레이션 완료 이벤트
            await self.event_bus.publish(
                "orchestration_completed",
                {
                    "session_id": session_id,
                    "result": result,
                    "communication_log": self._orchestration_sessions[session_id]["communication_log"]
                }
            )
            
            return result
            
        except Exception as e:
            await self.event_bus.publish(
                "orchestration_failed",
                {
                    "session_id": session_id,
                    "error": str(e)
                }
            )
            raise
        finally:
            # 세션 정리
            if session_id in self._orchestration_sessions:
                del self._orchestration_sessions[session_id]
    
    async def _execute_consensus_orchestration(
        self,
        session_id: str,
        agents: List[str],
        task: Dict[str, Any],
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """합의 기반 오케스트레이션"""
        # 투표 요청 발행
        vote_request_id = f"vote_{session_id}"
        await self.event_bus.publish(
            "vote_request",
            {
                "vote_id": vote_request_id,
                "session_id": session_id,
                "topic": task.get("decision_topic", "Task execution approach"),
                "agents": agents,
                "options": task.get("options", ["approve", "reject", "modify"])
            }
        )
        
        # 투표 수집 (실제 구현에서는 비동기 대기)
        votes = {}
        for agent_type in agents:
            if agent_type in self._agent_plugins:
                # 각 Agent에게 투표 요청
                vote_result = await self.execute_agent_with_communication(
                    agent_type,
                    {"vote_request": vote_request_id, "task": task},
                    context,
                    "event_driven"
                )
                votes[agent_type] = vote_result.get("vote", "abstain")
        
        # 합의 결과 계산
        consensus_threshold = task.get("consensus_threshold", 0.7)
        approve_votes = sum(1 for vote in votes.values() if vote == "approve")
        consensus_reached = (approve_votes / len(votes)) >= consensus_threshold
        
        # 합의 결과 이벤트 발행
        await self.event_bus.publish(
            "consensus_reached" if consensus_reached else "consensus_failed",
            {
                "session_id": session_id,
                "vote_id": vote_request_id,
                "votes": votes,
                "consensus_reached": consensus_reached,
                "threshold": consensus_threshold
            }
        )
        
        return {
            "pattern": "consensus",
            "consensus_reached": consensus_reached,
            "votes": votes,
            "final_decision": "approved" if consensus_reached else "rejected"
        }
    
    async def _execute_swarm_orchestration(
        self,
        session_id: str,
        agents: List[str],
        task: Dict[str, Any],
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """군집 지능 오케스트레이션"""
        # 페로몬 트레일 초기화
        pheromone_trails = {agent: 1.0 for agent in agents}
        convergence_history = []
        
        for iteration in range(task.get("max_iterations", 5)):
            # 각 Agent의 적합도 평가
            fitness_scores = {}
            for agent_type in agents:
                if agent_type in self._agent_plugins:
                    result = await self.execute_agent_with_communication(
                        agent_type,
                        {"task": task, "iteration": iteration},
                        context,
                        "event_driven"
                    )
                    fitness_scores[agent_type] = result.get("fitness", 0.5)
            
            # 페로몬 업데이트
            for agent_type, fitness in fitness_scores.items():
                pheromone_trails[agent_type] = pheromone_trails[agent_type] * 0.9 + fitness * 0.1
            
            # 페로몬 증착 이벤트 발행
            await self.event_bus.publish(
                "pheromone_deposit",
                {
                    "session_id": session_id,
                    "iteration": iteration,
                    "pheromone_trails": pheromone_trails,
                    "fitness_scores": fitness_scores
                }
            )
            
            convergence_history.append({
                "iteration": iteration,
                "fitness_scores": fitness_scores,
                "pheromone_trails": pheromone_trails.copy()
            })
            
            # 수렴 확인
            if self._check_swarm_convergence(fitness_scores):
                break
        
        # 최적 솔루션 선택
        best_agent = max(fitness_scores.keys(), key=lambda k: fitness_scores[k])
        
        await self.event_bus.publish(
            "swarm_convergence",
            {
                "session_id": session_id,
                "best_agent": best_agent,
                "convergence_history": convergence_history
            }
        )
        
        return {
            "pattern": "swarm",
            "best_agent": best_agent,
            "convergence_history": convergence_history,
            "pheromone_trails": pheromone_trails
        }
    
    async def _execute_dynamic_routing_orchestration(
        self,
        session_id: str,
        agents: List[str],
        task: Dict[str, Any],
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """동적 라우팅 오케스트레이션"""
        # Agent 성능 메트릭 수집
        agent_metrics = {}
        for agent_type in agents:
            if agent_type in self._agent_plugins:
                plugin = self._agent_plugins[agent_type]
                health_status = plugin.get_health_status()
                agent_metrics[agent_type] = {
                    "performance": 0.8,  # 실제로는 성능 메트릭 계산
                    "load": 0.3,         # 현재 부하
                    "accuracy": 0.9,     # 정확도
                    "availability": health_status.get("status") == "healthy"
                }
        
        # 라우팅 결정
        routing_weights = task.get("routing_weights", {"performance": 0.4, "load": 0.3, "accuracy": 0.3})
        
        # 가중 점수 계산
        weighted_scores = {}
        for agent_type, metrics in agent_metrics.items():
            if metrics["availability"]:
                score = (
                    metrics["performance"] * routing_weights["performance"] +
                    (1 - metrics["load"]) * routing_weights["load"] +  # 낮은 부하가 좋음
                    metrics["accuracy"] * routing_weights["accuracy"]
                )
                weighted_scores[agent_type] = score
        
        # 최적 Agent 선택
        if weighted_scores:
            selected_agent = max(weighted_scores.keys(), key=lambda k: weighted_scores[k])
            
            # 라우팅 결정 이벤트 발행
            await self.event_bus.publish(
                "routing_decision",
                {
                    "session_id": session_id,
                    "selected_agent": selected_agent,
                    "agent_metrics": agent_metrics,
                    "weighted_scores": weighted_scores,
                    "routing_weights": routing_weights
                }
            )
            
            # 선택된 Agent 실행
            result = await self.execute_agent_with_communication(
                selected_agent,
                task,
                context,
                "event_driven"
            )
            
            return {
                "pattern": "dynamic_routing",
                "selected_agent": selected_agent,
                "routing_decision": weighted_scores,
                "result": result
            }
        else:
            raise RuntimeError("No available agents for routing")
    
    async def _execute_parallel_orchestration(
        self,
        session_id: str,
        agents: List[str],
        task: Dict[str, Any],
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """병렬 오케스트레이션"""
        # 모든 Agent를 병렬로 실행
        tasks_list = []
        for agent_type in agents:
            if agent_type in self._agent_plugins:
                task_coroutine = self.execute_agent_with_communication(
                    agent_type,
                    task,
                    context,
                    "event_driven"
                )
                tasks_list.append(task_coroutine)
        
        # 병렬 실행 및 결과 수집
        results = await asyncio.gather(*tasks_list, return_exceptions=True)
        
        # 결과 정리
        agent_results = {}
        for i, agent_type in enumerate(agents):
            if i < len(results):
                if isinstance(results[i], Exception):
                    agent_results[agent_type] = {"error": str(results[i])}
                else:
                    agent_results[agent_type] = results[i]
        
        return {
            "pattern": "parallel",
            "agent_results": agent_results,
            "execution_mode": "concurrent"
        }
    
    async def _execute_sequential_orchestration(
        self,
        session_id: str,
        agents: List[str],
        task: Dict[str, Any],
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """순차 오케스트레이션"""
        agent_results = {}
        accumulated_result = task.copy()
        
        for agent_type in agents:
            if agent_type in self._agent_plugins:
                result = await self.execute_agent_with_communication(
                    agent_type,
                    accumulated_result,
                    context,
                    "event_driven"
                )
                agent_results[agent_type] = result
                
                # 다음 Agent를 위해 결과 누적
                if result.get("success"):
                    accumulated_result.update(result.get("result", {}))
        
        return {
            "pattern": "sequential",
            "agent_results": agent_results,
            "final_result": accumulated_result
        }
    
    def _check_swarm_convergence(self, fitness_scores: Dict[str, float]) -> bool:
        """군집 수렴 확인"""
        if not fitness_scores:
            return False
        
        scores = list(fitness_scores.values())
        avg_score = sum(scores) / len(scores)
        variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
        
        # 분산이 작으면 수렴으로 판단
        return variance < 0.01
    
    async def _execute_with_event_communication(
        self,
        plugin: IAgentPlugin,
        input_data: Dict[str, Any],
        context: AgentExecutionContext,
        execution_id: str
    ) -> Dict[str, Any]:
        """이벤트 기반 통신을 사용한 Agent 실행"""
        # 실행 중 이벤트 발행
        await self.event_bus.publish(
            "agent_processing",
            {
                "execution_id": execution_id,
                "agent_type": plugin.get_agent_type(),
                "status": "processing"
            }
        )
        
        # Agent 실행
        result = plugin.execute_agent(input_data, context)
        
        # 중간 결과 이벤트 발행 (필요시)
        if result.get("intermediate_results"):
            await self.event_bus.publish(
                "intermediate_result",
                {
                    "execution_id": execution_id,
                    "agent_type": plugin.get_agent_type(),
                    "intermediate_results": result["intermediate_results"]
                }
            )
        
        return result
    
    # 이벤트 핸들러들
    async def _handle_agent_communication(self, event_data: Dict[str, Any]):
        """Agent 간 통신 이벤트 처리"""
        pass
    
    async def _handle_orchestration_request(self, event_data: Dict[str, Any]):
        """오케스트레이션 요청 이벤트 처리"""
        pass
    
    async def _handle_agent_status_update(self, event_data: Dict[str, Any]):
        """Agent 상태 업데이트 이벤트 처리"""
        pass
    
    async def _handle_vote_request(self, event_data: Dict[str, Any]):
        """투표 요청 이벤트 처리"""
        pass
    
    async def _handle_vote_response(self, event_data: Dict[str, Any]):
        """투표 응답 이벤트 처리"""
        pass
    
    async def _handle_consensus_reached(self, event_data: Dict[str, Any]):
        """합의 도달 이벤트 처리"""
        pass
    
    async def _handle_pheromone_deposit(self, event_data: Dict[str, Any]):
        """페로몬 증착 이벤트 처리"""
        pass
    
    async def _handle_swarm_convergence(self, event_data: Dict[str, Any]):
        """군집 수렴 이벤트 처리"""
        pass
    
    async def _handle_performance_metrics(self, event_data: Dict[str, Any]):
        """성능 메트릭 이벤트 처리"""
        pass
    
    async def _handle_routing_decision(self, event_data: Dict[str, Any]):
        """라우팅 결정 이벤트 처리"""
        pass
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """사용 가능한 Agent 목록 반환"""
        agents = []
        for agent_type, plugin in self._agent_plugins.items():
            agents.append({
                "agent_type": agent_type,
                "agent_id": plugin.get_manifest().name,
                "capabilities": [cap.name for cap in plugin.get_capabilities()],
                "health_status": plugin.get_health_status(),
                "communication_channel": self._agent_communication_channels.get(agent_type)
            })
        return agents
    
    def get_orchestration_patterns(self) -> List[str]:
        """지원하는 오케스트레이션 패턴 목록"""
        return [
            "sequential",
            "parallel", 
            "hierarchical",
            "adaptive",
            "consensus",
            "swarm",
            "dynamic_routing",
            "event_driven",
            "reflection"
        ]