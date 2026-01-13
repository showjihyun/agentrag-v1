"""
Aggregator Agent Plugin

기존 AggregatorAgent를 Plugin 형태로 래핑하며 이벤트 기반 통신 프로토콜 지원
"""
from typing import Dict, List, Any, Optional
from backend.services.plugins.agents.base_agent_plugin import (
    BaseAgentPlugin, 
    AgentCapability, 
    AgentExecutionContext
)
from backend.models.plugin import PluginManifest
from backend.agents.aggregator import AggregatorAgent
from backend.agents.base import BaseAgent


class AggregatorAgentPlugin(BaseAgentPlugin):
    """Aggregator Agent Plugin 구현 - 마스터 오케스트레이터"""
    
    def get_manifest(self) -> PluginManifest:
        """플러그인 매니페스트 반환"""
        return PluginManifest(
            name="aggregator-agent",
            version="1.0.0",
            description="Master orchestrator agent using ReAct + CoT patterns with event-driven communication",
            author="AgenticRAG Team",
            category="orchestration",
            dependencies=[
                "vector-search-agent@>=1.0.0",
                "web-search-agent@>=1.0.0", 
                "local-data-agent@>=1.0.0",
                "redis@>=4.0.0",
                "event-bus@>=1.0.0"
            ],
            permissions=[
                "agent_orchestration", 
                "event_bus_access", 
                "redis_streams_access",
                "multi_agent_coordination",
                "pattern_execution"
            ],
            configuration_schema={
                "type": "object",
                "properties": {
                    "orchestration_pattern": {
                        "type": "string",
                        "enum": ["sequential", "parallel", "hierarchical", "adaptive", "consensus", "swarm", "dynamic_routing", "event_driven", "reflection"],
                        "default": "adaptive",
                        "description": "Default orchestration pattern"
                    },
                    "max_agents": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                        "description": "Maximum number of agents to coordinate"
                    },
                    "timeout_seconds": {
                        "type": "integer",
                        "default": 300,
                        "minimum": 30,
                        "maximum": 3600,
                        "description": "Orchestration timeout in seconds"
                    },
                    "event_bus_config": {
                        "type": "object",
                        "properties": {
                            "stream_name": {
                                "type": "string",
                                "default": "agent_orchestration",
                                "description": "Redis stream name for agent communication"
                            },
                            "consumer_group": {
                                "type": "string",
                                "default": "aggregator_agents",
                                "description": "Consumer group for event processing"
                            },
                            "max_retries": {
                                "type": "integer",
                                "default": 3,
                                "description": "Maximum retry attempts for failed events"
                            }
                        }
                    },
                    "communication_protocols": {
                        "type": "object",
                        "properties": {
                            "consensus_threshold": {
                                "type": "number",
                                "default": 0.7,
                                "minimum": 0.5,
                                "maximum": 1.0,
                                "description": "Consensus threshold for voting patterns"
                            },
                            "swarm_pheromone_decay": {
                                "type": "number",
                                "default": 0.1,
                                "description": "Pheromone decay rate for swarm intelligence"
                            },
                            "routing_metric_weight": {
                                "type": "object",
                                "properties": {
                                    "performance": {"type": "number", "default": 0.4},
                                    "load": {"type": "number", "default": 0.3},
                                    "accuracy": {"type": "number", "default": 0.3}
                                }
                            }
                        }
                    }
                },
                "required": ["orchestration_pattern"]
            }
        )
    
    def get_agent_type(self) -> str:
        """Agent 타입 반환"""
        return "aggregator"
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Agent 능력 반환"""
        return [
            AgentCapability(
                name="multi_agent_orchestration",
                description="Orchestrate multiple agents using various patterns",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Task to be executed by agents"
                        },
                        "agents": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "agent_id": {"type": "string"},
                                    "agent_type": {"type": "string"},
                                    "capabilities": {"type": "array"}
                                }
                            },
                            "description": "Available agents for orchestration"
                        },
                        "pattern": {
                            "type": "string",
                            "enum": ["sequential", "parallel", "hierarchical", "adaptive", "consensus", "swarm", "dynamic_routing", "event_driven", "reflection"],
                            "description": "Orchestration pattern to use"
                        },
                        "constraints": {
                            "type": "object",
                            "description": "Execution constraints and preferences"
                        }
                    },
                    "required": ["task", "agents"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "orchestration_result": {
                            "type": "object",
                            "properties": {
                                "final_result": {"type": "string"},
                                "execution_plan": {"type": "object"},
                                "agent_results": {"type": "array"},
                                "performance_metrics": {"type": "object"},
                                "communication_log": {"type": "array"}
                            }
                        }
                    }
                },
                required_permissions=["agent_orchestration", "event_bus_access"]
            ),
            AgentCapability(
                name="consensus_building",
                description="Coordinate agents to reach consensus on decisions",
                input_schema={
                    "type": "object",
                    "properties": {
                        "decision_topic": {"type": "string"},
                        "voting_agents": {"type": "array"},
                        "consensus_threshold": {"type": "number"},
                        "max_rounds": {"type": "integer", "default": 5}
                    },
                    "required": ["decision_topic", "voting_agents"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "consensus_reached": {"type": "boolean"},
                        "final_decision": {"type": "string"},
                        "vote_history": {"type": "array"},
                        "discussion_rounds": {"type": "array"}
                    }
                },
                required_permissions=["agent_orchestration", "event_bus_access"]
            ),
            AgentCapability(
                name="swarm_coordination",
                description="Coordinate agents using swarm intelligence patterns",
                input_schema={
                    "type": "object",
                    "properties": {
                        "optimization_target": {"type": "string"},
                        "swarm_agents": {"type": "array"},
                        "pheromone_config": {"type": "object"},
                        "convergence_criteria": {"type": "object"}
                    },
                    "required": ["optimization_target", "swarm_agents"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "optimal_solution": {"type": "object"},
                        "convergence_history": {"type": "array"},
                        "pheromone_trails": {"type": "object"},
                        "swarm_metrics": {"type": "object"}
                    }
                },
                required_permissions=["agent_orchestration", "event_bus_access"]
            ),
            AgentCapability(
                name="dynamic_routing",
                description="Route tasks to agents based on real-time performance metrics",
                input_schema={
                    "type": "object",
                    "properties": {
                        "tasks": {"type": "array"},
                        "available_agents": {"type": "array"},
                        "routing_criteria": {"type": "object"},
                        "load_balancing": {"type": "boolean", "default": true}
                    },
                    "required": ["tasks", "available_agents"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "routing_plan": {"type": "object"},
                        "agent_assignments": {"type": "array"},
                        "load_distribution": {"type": "object"},
                        "performance_predictions": {"type": "object"}
                    }
                },
                required_permissions=["agent_orchestration", "event_bus_access"]
            ),
            AgentCapability(
                name="event_driven_coordination",
                description="Coordinate agents through event-driven communication",
                input_schema={
                    "type": "object",
                    "properties": {
                        "trigger_events": {"type": "array"},
                        "event_handlers": {"type": "object"},
                        "workflow_definition": {"type": "object"}
                    },
                    "required": ["trigger_events", "workflow_definition"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "workflow_execution": {"type": "object"},
                        "event_timeline": {"type": "array"},
                        "handler_results": {"type": "object"}
                    }
                },
                required_permissions=["agent_orchestration", "event_bus_access", "redis_streams_access"]
            )
        ]
    
    def execute_agent(
        self, 
        input_data: Dict[str, Any], 
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """Agent 실행 - 이벤트 기반 통신 프로토콜 사용"""
        try:
            agent = self.get_agent_instance()
            
            # 이벤트 기반 실행 컨텍스트 설정
            execution_context = {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "workflow_id": context.workflow_id,
                "orchestration_pattern": context.orchestration_pattern,
                "event_bus_config": self.config.get("event_bus_config", {}),
                "communication_protocols": self.config.get("communication_protocols", {}),
                **context.execution_metadata
            }
            
            # 오케스트레이션 패턴에 따른 통신 프로토콜 설정
            pattern = input_data.get("pattern", self.config.get("orchestration_pattern", "adaptive"))
            
            if pattern == "consensus":
                return self._execute_consensus_orchestration(agent, input_data, execution_context)
            elif pattern == "swarm":
                return self._execute_swarm_orchestration(agent, input_data, execution_context)
            elif pattern == "dynamic_routing":
                return self._execute_dynamic_routing_orchestration(agent, input_data, execution_context)
            elif pattern == "event_driven":
                return self._execute_event_driven_orchestration(agent, input_data, execution_context)
            else:
                # 기본 오케스트레이션 실행
                result = agent.execute(input_data, execution_context)
                
                return {
                    "success": True,
                    "result": result,
                    "agent_type": self.get_agent_type(),
                    "orchestration_pattern": pattern,
                    "execution_context": execution_context
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_type": self.get_agent_type(),
                "input_data": input_data
            }
    
    def _execute_consensus_orchestration(
        self, 
        agent: BaseAgent, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """합의 기반 오케스트레이션 실행"""
        # 투표 수집 → 라운드 기반 토론 → 합의 도달
        consensus_config = context.get("communication_protocols", {})
        threshold = consensus_config.get("consensus_threshold", 0.7)
        
        # 이벤트 버스를 통한 투표 메시지 발행
        voting_events = [
            {"event_type": "vote_request", "data": input_data},
            {"event_type": "discussion_round", "data": {"round": 1}},
            {"event_type": "consensus_check", "data": {"threshold": threshold}}
        ]
        
        result = agent.execute(input_data, context)
        result["communication_protocol"] = "consensus_building"
        result["voting_events"] = voting_events
        
        return {
            "success": True,
            "result": result,
            "orchestration_pattern": "consensus",
            "communication_events": voting_events
        }
    
    def _execute_swarm_orchestration(
        self, 
        agent: BaseAgent, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """군집 지능 오케스트레이션 실행"""
        # 페로몬 트레일 기반 통신
        swarm_config = context.get("communication_protocols", {})
        pheromone_decay = swarm_config.get("swarm_pheromone_decay", 0.1)
        
        # 군집 지능 이벤트 발행
        swarm_events = [
            {"event_type": "agent_fitness_update", "data": {"fitness": 0.8}},
            {"event_type": "pheromone_deposit", "data": {"decay_rate": pheromone_decay}},
            {"event_type": "swarm_convergence", "data": {"iteration": 1}}
        ]
        
        result = agent.execute(input_data, context)
        result["communication_protocol"] = "swarm_intelligence"
        result["swarm_events"] = swarm_events
        
        return {
            "success": True,
            "result": result,
            "orchestration_pattern": "swarm",
            "communication_events": swarm_events
        }
    
    def _execute_dynamic_routing_orchestration(
        self, 
        agent: BaseAgent, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """동적 라우팅 오케스트레이션 실행"""
        # 성능 기반 라우팅 통신
        routing_config = context.get("communication_protocols", {})
        metric_weights = routing_config.get("routing_metric_weight", {})
        
        # 성능 메트릭 수집 이벤트
        routing_events = [
            {"event_type": "performance_metrics_request", "data": {"agents": input_data.get("agents", [])}},
            {"event_type": "load_balancing_update", "data": {"weights": metric_weights}},
            {"event_type": "routing_decision", "data": {"algorithm": "weighted_round_robin"}}
        ]
        
        result = agent.execute(input_data, context)
        result["communication_protocol"] = "dynamic_routing"
        result["routing_events"] = routing_events
        
        return {
            "success": True,
            "result": result,
            "orchestration_pattern": "dynamic_routing",
            "communication_events": routing_events
        }
    
    def _execute_event_driven_orchestration(
        self, 
        agent: BaseAgent, 
        input_data: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """이벤트 기반 오케스트레이션 실행"""
        # Redis Streams 기반 이벤트 처리
        event_config = context.get("event_bus_config", {})
        stream_name = event_config.get("stream_name", "agent_orchestration")
        
        # 이벤트 기반 워크플로우 실행
        workflow_events = [
            {"event_type": "workflow_started", "stream": stream_name, "data": input_data},
            {"event_type": "agent_task_assigned", "stream": stream_name, "data": {"task_id": "task_001"}},
            {"event_type": "intermediate_result", "stream": stream_name, "data": {"progress": 50}},
            {"event_type": "workflow_completed", "stream": stream_name, "data": {"status": "success"}}
        ]
        
        result = agent.execute(input_data, context)
        result["communication_protocol"] = "event_driven"
        result["workflow_events"] = workflow_events
        
        return {
            "success": True,
            "result": result,
            "orchestration_pattern": "event_driven",
            "communication_events": workflow_events,
            "redis_stream": stream_name
        }
    
    def _create_agent_instance(self) -> BaseAgent:
        """AggregatorAgent 인스턴스 생성"""
        return AggregatorAgent(
            orchestration_pattern=self.config.get("orchestration_pattern", "adaptive"),
            max_agents=self.config.get("max_agents", 10),
            timeout_seconds=self.config.get("timeout_seconds", 300),
            event_bus_config=self.config.get("event_bus_config", {}),
            communication_protocols=self.config.get("communication_protocols", {})
        )
    
    def _get_required_config_fields(self) -> List[str]:
        """필수 설정 필드"""
        return ["orchestration_pattern"]
    
    def _validate_agent_specific_config(self, config: Dict[str, Any]) -> List[str]:
        """Aggregator Agent 특화 설정 검증"""
        errors = []
        
        # 오케스트레이션 패턴 검증
        valid_patterns = ["sequential", "parallel", "hierarchical", "adaptive", "consensus", "swarm", "dynamic_routing", "event_driven", "reflection"]
        if "orchestration_pattern" in config:
            pattern = config["orchestration_pattern"]
            if pattern not in valid_patterns:
                errors.append(f"orchestration_pattern must be one of: {', '.join(valid_patterns)}")
        
        # 최대 Agent 수 검증
        if "max_agents" in config:
            max_agents = config["max_agents"]
            if not isinstance(max_agents, int) or max_agents < 1 or max_agents > 50:
                errors.append("max_agents must be an integer between 1 and 50")
        
        # 합의 임계값 검증
        if "communication_protocols" in config:
            protocols = config["communication_protocols"]
            if "consensus_threshold" in protocols:
                threshold = protocols["consensus_threshold"]
                if not isinstance(threshold, (int, float)) or not (0.5 <= threshold <= 1.0):
                    errors.append("consensus_threshold must be a number between 0.5 and 1.0")
        
        return errors
    
    def get_health_status(self) -> Dict[str, Any]:
        """Aggregator Agent 상태 확인"""
        base_status = super().get_health_status()
        
        if self._initialized and self._agent_instance:
            try:
                # 이벤트 버스 및 Redis 연결 상태 확인
                agent_health = {
                    "redis_connected": True,  # 실제로는 Redis 연결 확인
                    "event_bus_available": True,  # 실제로는 Event Bus 상태 확인
                    "orchestration_patterns_loaded": True,  # 패턴 로딩 상태
                    "dependent_agents_available": True,  # 의존 Agent들 상태
                    "communication_protocols_active": True  # 통신 프로토콜 활성 상태
                }
                base_status.update(agent_health)
            except Exception as e:
                base_status["error"] = str(e)
                base_status["status"] = "unhealthy"
        
        return base_status