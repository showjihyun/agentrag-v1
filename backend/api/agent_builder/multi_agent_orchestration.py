"""
Multi-Agent Orchestration API
다중 AI 에이전트 오케스트레이션 REST API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid

from backend.services.multimodal.multi_agent_orchestrator import (
    get_multi_agent_orchestrator,
    Task,
    TaskPriority,
    OrchestrationStrategy,
    AgentType,
    AgentCapability
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/multi-agent", tags=["Multi-Agent Orchestration"])

@router.post("/orchestrate")
async def orchestrate_workflow(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    워크플로우 오케스트레이션 실행
    
    Request Body:
    {
        "tasks": [
            {
                "task_id": "task_1",
                "task_type": "image_analysis",
                "priority": "high",
                "requirements": {"format": "jpg", "max_size": "10MB"},
                "input_data": {"image_url": "https://..."},
                "deadline": "2024-12-31T23:59:59",
                "estimated_duration": 30.0,
                "dependencies": []
            }
        ],
        "strategy": "performance_optimized",
        "constraints": {"max_cost": 1.0, "max_duration": 300}
    }
    """
    try:
        orchestrator = get_multi_agent_orchestrator()
        
        # 요청 데이터 파싱
        tasks_data = request.get("tasks", [])
        strategy_str = request.get("strategy", "performance_optimized")
        constraints = request.get("constraints", {})
        
        # 작업 객체 생성
        tasks = []
        for task_data in tasks_data:
            deadline = None
            if task_data.get("deadline"):
                deadline = datetime.fromisoformat(task_data["deadline"].replace("Z", "+00:00"))
            
            task = Task(
                task_id=task_data.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                task_type=task_data["task_type"],
                priority=TaskPriority(task_data.get("priority", "medium")),
                requirements=task_data.get("requirements", {}),
                input_data=task_data.get("input_data", {}),
                deadline=deadline,
                estimated_duration=task_data.get("estimated_duration", 30.0),
                dependencies=task_data.get("dependencies", [])
            )
            tasks.append(task)
        
        # 전략 설정
        strategy = OrchestrationStrategy(strategy_str)
        
        # 오케스트레이션 계획 생성
        plan = await orchestrator.orchestrate_workflow(tasks, strategy, constraints)
        
        # 계획 실행
        execution_result = await orchestrator.execute_orchestration_plan(plan)
        
        return {
            "success": True,
            "plan": {
                "plan_id": plan.plan_id,
                "strategy": plan.strategy.value,
                "task_assignments": plan.task_assignments,
                "execution_order": plan.execution_order,
                "estimated_completion_time": plan.estimated_completion_time,
                "monitoring_checkpoints": plan.monitoring_checkpoints
            },
            "execution": {
                "execution_id": execution_result["execution_id"],
                "status": execution_result["status"],
                "completed_tasks": len(execution_result["completed_tasks"]),
                "failed_tasks": len(execution_result["failed_tasks"]),
                "total_duration": execution_result.get("total_duration", 0),
                "results": execution_result["results"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Orchestration failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")

@router.post("/plan")
async def create_orchestration_plan(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    오케스트레이션 계획만 생성 (실행하지 않음)
    """
    try:
        orchestrator = get_multi_agent_orchestrator()
        
        # 요청 데이터 파싱
        tasks_data = request.get("tasks", [])
        strategy_str = request.get("strategy", "performance_optimized")
        constraints = request.get("constraints", {})
        
        # 작업 객체 생성
        tasks = []
        for task_data in tasks_data:
            deadline = None
            if task_data.get("deadline"):
                deadline = datetime.fromisoformat(task_data["deadline"].replace("Z", "+00:00"))
            
            task = Task(
                task_id=task_data.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                task_type=task_data["task_type"],
                priority=TaskPriority(task_data.get("priority", "medium")),
                requirements=task_data.get("requirements", {}),
                input_data=task_data.get("input_data", {}),
                deadline=deadline,
                estimated_duration=task_data.get("estimated_duration", 30.0),
                dependencies=task_data.get("dependencies", [])
            )
            tasks.append(task)
        
        # 전략 설정
        strategy = OrchestrationStrategy(strategy_str)
        
        # 오케스트레이션 계획 생성
        plan = await orchestrator.orchestrate_workflow(tasks, strategy, constraints)
        
        return {
            "success": True,
            "plan": {
                "plan_id": plan.plan_id,
                "strategy": plan.strategy.value,
                "task_assignments": plan.task_assignments,
                "execution_order": plan.execution_order,
                "estimated_completion_time": plan.estimated_completion_time,
                "resource_allocation": plan.resource_allocation,
                "fallback_plans": plan.fallback_plans,
                "monitoring_checkpoints": plan.monitoring_checkpoints
            },
            "analysis": {
                "total_tasks": len(tasks),
                "parallel_groups": len(plan.execution_order),
                "agents_involved": len(set(plan.task_assignments.values())),
                "estimated_cost": sum(
                    alloc.get("estimated_cost", 0) 
                    for alloc in plan.resource_allocation.values()
                )
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Plan creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Plan creation failed: {str(e)}")

@router.get("/execution/{execution_id}")
async def get_execution_status(execution_id: str) -> Dict[str, Any]:
    """오케스트레이션 실행 상태 조회"""
    try:
        orchestrator = get_multi_agent_orchestrator()
        status = orchestrator.get_orchestration_status(execution_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        # 시간 정보 직렬화
        serialized_status = status.copy()
        if "start_time" in serialized_status:
            serialized_status["start_time"] = serialized_status["start_time"].isoformat()
        if "end_time" in serialized_status:
            serialized_status["end_time"] = serialized_status["end_time"].isoformat()
        
        # 실패한 작업의 타임스탬프 직렬화
        for failed_task in serialized_status.get("failed_tasks", []):
            if "timestamp" in failed_task:
                failed_task["timestamp"] = failed_task["timestamp"].isoformat()
        
        # 결과의 타임스탬프 직렬화
        for task_id, result in serialized_status.get("results", {}).items():
            if isinstance(result, dict) and "timestamp" in result:
                result["timestamp"] = result["timestamp"].isoformat()
        
        return {
            "success": True,
            "execution": serialized_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@router.get("/agents/status")
async def get_agents_status() -> Dict[str, Any]:
    """모든 에이전트 상태 조회"""
    try:
        orchestrator = get_multi_agent_orchestrator()
        agents_status = orchestrator.get_agent_status()
        
        return {
            "success": True,
            "agents": agents_status,
            "summary": {
                "total_agents": len(agents_status),
                "idle_agents": sum(1 for agent in agents_status.values() if agent["status"] == "idle"),
                "busy_agents": sum(1 for agent in agents_status.values() if agent["status"] == "busy"),
                "error_agents": sum(1 for agent in agents_status.values() if agent["status"] == "error"),
                "total_active_tasks": sum(agent["active_tasks"] for agent in agents_status.values()),
                "average_load": sum(agent["current_load"] for agent in agents_status.values()) / len(agents_status) if agents_status else 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Agent status retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent status retrieval failed: {str(e)}")

@router.post("/agents")
async def add_agent(request: Dict[str, Any]) -> Dict[str, Any]:
    """새 에이전트 추가"""
    try:
        orchestrator = get_multi_agent_orchestrator()
        
        # 에이전트 설정 검증
        required_fields = ["agent_type", "capabilities"]
        for field in required_fields:
            if field not in request:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        agent_id = await orchestrator.add_agent(request)
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent {agent_id} added successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent addition failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent addition failed: {str(e)}")

@router.delete("/agents/{agent_id}")
async def remove_agent(agent_id: str) -> Dict[str, Any]:
    """에이전트 제거"""
    try:
        orchestrator = get_multi_agent_orchestrator()
        success = await orchestrator.remove_agent(agent_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "success": True,
            "message": f"Agent {agent_id} removed successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent removal failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent removal failed: {str(e)}")

@router.get("/strategies")
async def get_orchestration_strategies() -> Dict[str, Any]:
    """사용 가능한 오케스트레이션 전략 목록"""
    strategies = {
        "load_balanced": {
            "name": "Load Balanced",
            "description": "부하를 균등하게 분산하여 에이전트 간 작업량 균형 유지",
            "best_for": ["높은 처리량", "안정적인 성능", "리소스 효율성"],
            "characteristics": {
                "performance": "medium",
                "cost": "medium", 
                "reliability": "high",
                "scalability": "high"
            }
        },
        "capability_matched": {
            "name": "Capability Matched",
            "description": "각 작업을 가장 적합한 전문 에이전트에 할당",
            "best_for": ["높은 정확도", "전문 작업", "품질 우선"],
            "characteristics": {
                "performance": "high",
                "cost": "medium",
                "reliability": "high", 
                "scalability": "medium"
            }
        },
        "performance_optimized": {
            "name": "Performance Optimized",
            "description": "최고 성능을 위해 최적의 에이전트와 실행 순서 선택",
            "best_for": ["빠른 처리", "실시간 응답", "성능 중시"],
            "characteristics": {
                "performance": "very_high",
                "cost": "high",
                "reliability": "medium",
                "scalability": "medium"
            }
        },
        "cost_minimized": {
            "name": "Cost Minimized", 
            "description": "비용을 최소화하면서 요구사항을 충족하는 에이전트 선택",
            "best_for": ["예산 제약", "대량 처리", "비용 효율성"],
            "characteristics": {
                "performance": "medium",
                "cost": "low",
                "reliability": "medium",
                "scalability": "high"
            }
        },
        "deadline_aware": {
            "name": "Deadline Aware",
            "description": "데드라인을 고려하여 우선순위 기반 스케줄링",
            "best_for": ["시간 제약", "우선순위 작업", "SLA 준수"],
            "characteristics": {
                "performance": "high",
                "cost": "medium",
                "reliability": "high",
                "scalability": "medium"
            }
        },
        "collaborative": {
            "name": "Collaborative",
            "description": "여러 에이전트가 협업하여 복잡한 작업 수행",
            "best_for": ["복잡한 분석", "다단계 처리", "종합적 결과"],
            "characteristics": {
                "performance": "very_high",
                "cost": "high",
                "reliability": "high",
                "scalability": "low"
            }
        }
    }
    
    return {
        "success": True,
        "strategies": strategies,
        "default_strategy": "performance_optimized",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/agent-types")
async def get_agent_types() -> Dict[str, Any]:
    """사용 가능한 에이전트 타입 목록"""
    agent_types = {
        "vision_specialist": {
            "name": "Vision Specialist",
            "description": "이미지 및 비디오 분석 전문 에이전트",
            "specializations": ["이미지 분석", "객체 감지", "장면 이해", "OCR"],
            "typical_tasks": ["image_analysis", "object_detection", "scene_understanding", "ocr"],
            "performance_profile": {
                "accuracy": "very_high",
                "speed": "high",
                "cost": "medium"
            }
        },
        "audio_specialist": {
            "name": "Audio Specialist", 
            "description": "음성 및 오디오 처리 전문 에이전트",
            "specializations": ["음성 인식", "오디오 분석", "음악 이해", "소리 분류"],
            "typical_tasks": ["speech_to_text", "audio_analysis", "music_understanding", "sound_classification"],
            "performance_profile": {
                "accuracy": "high",
                "speed": "very_high",
                "cost": "low"
            }
        },
        "text_specialist": {
            "name": "Text Specialist",
            "description": "텍스트 및 언어 처리 전문 에이전트", 
            "specializations": ["텍스트 분석", "요약", "번역", "감정 분석"],
            "typical_tasks": ["text_analysis", "summarization", "translation", "sentiment_analysis"],
            "performance_profile": {
                "accuracy": "very_high",
                "speed": "very_high",
                "cost": "very_low"
            }
        },
        "code_specialist": {
            "name": "Code Specialist",
            "description": "코드 분석 및 생성 전문 에이전트",
            "specializations": ["코드 분석", "버그 탐지", "코드 생성", "리팩토링"],
            "typical_tasks": ["code_analysis", "bug_detection", "code_generation", "refactoring"],
            "performance_profile": {
                "accuracy": "high",
                "speed": "medium",
                "cost": "medium"
            }
        },
        "multimodal_generalist": {
            "name": "Multimodal Generalist",
            "description": "다양한 모달리티를 처리하는 범용 에이전트",
            "specializations": ["멀티모달 융합", "교차 모달 추론", "복합 분석"],
            "typical_tasks": ["multimodal_fusion", "cross_modal_reasoning", "complex_analysis"],
            "performance_profile": {
                "accuracy": "high",
                "speed": "medium",
                "cost": "high"
            }
        },
        "reasoning_specialist": {
            "name": "Reasoning Specialist",
            "description": "논리적 추론 및 문제 해결 전문 에이전트",
            "specializations": ["논리적 추론", "문제 해결", "의사 결정", "분석"],
            "typical_tasks": ["logical_reasoning", "problem_solving", "decision_making", "analysis"],
            "performance_profile": {
                "accuracy": "very_high",
                "speed": "low",
                "cost": "high"
            }
        },
        "creative_specialist": {
            "name": "Creative Specialist",
            "description": "창작 및 생성 작업 전문 에이전트",
            "specializations": ["콘텐츠 생성", "창작", "디자인", "아이디어 발굴"],
            "typical_tasks": ["content_generation", "creative_writing", "design", "ideation"],
            "performance_profile": {
                "accuracy": "medium",
                "speed": "medium",
                "cost": "medium"
            }
        },
        "research_specialist": {
            "name": "Research Specialist",
            "description": "연구 및 조사 작업 전문 에이전트",
            "specializations": ["정보 수집", "연구", "분석", "보고서 작성"],
            "typical_tasks": ["information_gathering", "research", "analysis", "report_writing"],
            "performance_profile": {
                "accuracy": "high",
                "speed": "low",
                "cost": "medium"
            }
        }
    }
    
    return {
        "success": True,
        "agent_types": agent_types,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/simulate")
async def simulate_orchestration(request: Dict[str, Any]) -> Dict[str, Any]:
    """오케스트레이션 시뮬레이션 (실제 실행 없이 계획만 분석)"""
    try:
        orchestrator = get_multi_agent_orchestrator()
        
        # 요청 데이터 파싱
        tasks_data = request.get("tasks", [])
        strategies = request.get("strategies", ["performance_optimized"])
        constraints = request.get("constraints", {})
        
        # 작업 객체 생성
        tasks = []
        for task_data in tasks_data:
            deadline = None
            if task_data.get("deadline"):
                deadline = datetime.fromisoformat(task_data["deadline"].replace("Z", "+00:00"))
            
            task = Task(
                task_id=task_data.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                task_type=task_data["task_type"],
                priority=TaskPriority(task_data.get("priority", "medium")),
                requirements=task_data.get("requirements", {}),
                input_data=task_data.get("input_data", {}),
                deadline=deadline,
                estimated_duration=task_data.get("estimated_duration", 30.0),
                dependencies=task_data.get("dependencies", [])
            )
            tasks.append(task)
        
        # 각 전략별로 계획 생성
        simulation_results = {}
        
        for strategy_str in strategies:
            try:
                strategy = OrchestrationStrategy(strategy_str)
                plan = await orchestrator.orchestrate_workflow(tasks, strategy, constraints)
                
                simulation_results[strategy_str] = {
                    "plan_id": plan.plan_id,
                    "strategy": plan.strategy.value,
                    "estimated_completion_time": plan.estimated_completion_time,
                    "parallel_groups": len(plan.execution_order),
                    "agents_involved": len(set(plan.task_assignments.values())),
                    "estimated_cost": sum(
                        alloc.get("estimated_cost", 0) 
                        for alloc in plan.resource_allocation.values()
                    ),
                    "task_distribution": {},
                    "resource_utilization": {}
                }
                
                # 에이전트별 작업 분배 분석
                for task_id, agent_id in plan.task_assignments.items():
                    if agent_id not in simulation_results[strategy_str]["task_distribution"]:
                        simulation_results[strategy_str]["task_distribution"][agent_id] = 0
                    simulation_results[strategy_str]["task_distribution"][agent_id] += 1
                
                # 리소스 활용도 분석
                for task_id, allocation in plan.resource_allocation.items():
                    agent_id = allocation["agent_id"]
                    if agent_id not in simulation_results[strategy_str]["resource_utilization"]:
                        simulation_results[strategy_str]["resource_utilization"][agent_id] = {
                            "total_duration": 0,
                            "total_cost": 0,
                            "task_count": 0
                        }
                    
                    simulation_results[strategy_str]["resource_utilization"][agent_id]["total_duration"] += allocation["estimated_duration"]
                    simulation_results[strategy_str]["resource_utilization"][agent_id]["total_cost"] += allocation["estimated_cost"]
                    simulation_results[strategy_str]["resource_utilization"][agent_id]["task_count"] += 1
                
            except Exception as e:
                simulation_results[strategy_str] = {
                    "error": str(e),
                    "status": "failed"
                }
        
        # 최적 전략 추천
        best_strategy = None
        best_score = 0
        
        for strategy_str, result in simulation_results.items():
            if "error" in result:
                continue
            
            # 점수 계산 (시간, 비용, 리소스 활용도 고려)
            time_score = max(0, 100 - result["estimated_completion_time"])
            cost_score = max(0, 100 - result["estimated_cost"] * 10)
            balance_score = 100 - (len(result["task_distribution"]) * 5)  # 적은 에이전트 사용 시 높은 점수
            
            total_score = (time_score + cost_score + balance_score) / 3
            
            if total_score > best_score:
                best_score = total_score
                best_strategy = strategy_str
        
        return {
            "success": True,
            "simulation_results": simulation_results,
            "recommendation": {
                "best_strategy": best_strategy,
                "score": best_score,
                "reasoning": f"최적 전략: {best_strategy} (점수: {best_score:.1f})"
            },
            "analysis": {
                "total_tasks": len(tasks),
                "strategies_compared": len(strategies),
                "successful_simulations": len([r for r in simulation_results.values() if "error" not in r])
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")