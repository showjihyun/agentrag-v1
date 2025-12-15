"""
Advanced Multi-Agent Orchestration API
고급 다중 에이전트 오케스트레이션 REST API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid

from backend.services.multimodal.advanced_orchestrator import (
    get_advanced_orchestrator,
    CollaborationPattern,
    TaskComplexity,
    LearningMode,
    Task,
    TaskPriority
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/advanced-orchestration", tags=["Advanced Multi-Agent Orchestration"])

@router.post("/intelligent-decomposition")
async def intelligent_task_decomposition(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    지능형 작업 분해
    
    Request Body:
    {
        "task": {
            "task_id": "complex_task_1",
            "task_type": "multimodal_fusion",
            "priority": "high",
            "requirements": {"accuracy_threshold": 0.9, "multi_step": true},
            "input_data": {"image": "...", "text": "..."},
            "estimated_duration": 120.0
        },
        "complexity_threshold": "moderate"
    }
    """
    try:
        orchestrator = get_advanced_orchestrator()
        
        # 요청 데이터 파싱
        task_data = request.get("task", {})
        complexity_threshold = TaskComplexity(request.get("complexity_threshold", "moderate"))
        
        # 작업 객체 생성
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
        
        # 지능형 분해 실행
        decomposition = await orchestrator.intelligent_task_decomposition(task, complexity_threshold)
        
        if decomposition is None:
            return {
                "success": True,
                "decomposition_needed": False,
                "message": "Task complexity is below threshold, no decomposition needed",
                "original_task": task_data,
                "timestamp": datetime.now().isoformat()
            }
        
        # 분해 결과 직렬화
        subtasks_data = []
        for subtask in decomposition.subtasks:
            subtask_data = {
                "task_id": subtask.task_id,
                "task_type": subtask.task_type,
                "priority": subtask.priority.value,
                "requirements": subtask.requirements,
                "input_data": subtask.input_data,
                "estimated_duration": subtask.estimated_duration,
                "dependencies": subtask.dependencies
            }
            if subtask.deadline:
                subtask_data["deadline"] = subtask.deadline.isoformat()
            subtasks_data.append(subtask_data)
        
        return {
            "success": True,
            "decomposition_needed": True,
            "decomposition": {
                "original_task_id": decomposition.original_task_id,
                "subtasks": subtasks_data,
                "dependencies": decomposition.dependencies,
                "merge_strategy": decomposition.merge_strategy,
                "quality_requirements": decomposition.quality_requirements,
                "estimated_improvement": decomposition.estimated_improvement
            },
            "analysis": {
                "subtasks_count": len(decomposition.subtasks),
                "dependency_levels": len(set(len(deps) for deps in decomposition.dependencies.values())),
                "estimated_total_duration": sum(st.estimated_duration for st in decomposition.subtasks)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Intelligent decomposition failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Decomposition failed: {str(e)}")

@router.post("/collaboration-pattern")
async def create_collaboration_pattern(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    협업 패턴 생성
    
    Request Body:
    {
        "pattern_type": "ensemble",
        "tasks": [...],
        "participating_agents": ["agent_1", "agent_2"],  // optional
        "coordination_rules": {...}  // optional
    }
    """
    try:
        orchestrator = get_advanced_orchestrator()
        
        # 요청 데이터 파싱
        pattern_type = CollaborationPattern(request.get("pattern_type", "pipeline"))
        participating_agents = request.get("participating_agents")
        
        # 작업 객체 생성
        tasks = []
        for task_data in request.get("tasks", []):
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
        
        # 협업 패턴 생성
        collaboration_spec = await orchestrator.create_collaboration_pattern(
            pattern_type, tasks, participating_agents
        )
        
        return {
            "success": True,
            "collaboration_spec": {
                "pattern": collaboration_spec.pattern.value,
                "participants": collaboration_spec.participants,
                "coordination_rules": collaboration_spec.coordination_rules,
                "data_flow": collaboration_spec.data_flow,
                "synchronization_points": collaboration_spec.synchronization_points,
                "quality_gates": collaboration_spec.quality_gates,
                "timeout_seconds": collaboration_spec.timeout_seconds
            },
            "analysis": {
                "participants_count": len(collaboration_spec.participants),
                "data_flow_connections": len(collaboration_spec.data_flow),
                "synchronization_points": len(collaboration_spec.synchronization_points),
                "quality_gates": len(collaboration_spec.quality_gates)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Collaboration pattern creation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pattern creation failed: {str(e)}")

@router.post("/collaborative-execution")
async def execute_collaborative_workflow(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    협업 워크플로우 실행
    
    Request Body:
    {
        "collaboration_spec": {...},
        "tasks": [...]
    }
    """
    try:
        orchestrator = get_advanced_orchestrator()
        
        # 협업 사양 재구성 (실제로는 더 정교한 직렬화/역직렬화 필요)
        spec_data = request.get("collaboration_spec", {})
        pattern_type = CollaborationPattern(spec_data["pattern"])
        
        # 작업 객체 생성
        tasks = []
        for task_data in request.get("tasks", []):
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
        
        # 새로운 협업 패턴 생성 (간소화된 버전)
        collaboration_spec = await orchestrator.create_collaboration_pattern(
            pattern_type, tasks, spec_data.get("participants")
        )
        
        # 협업 워크플로우 실행
        result = await orchestrator.execute_collaborative_workflow(collaboration_spec, tasks)
        
        # 결과 직렬화
        serialized_result = result.copy()
        
        # datetime 객체 직렬화
        for key, value in serialized_result.items():
            if isinstance(value, datetime):
                serialized_result[key] = value.isoformat()
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, datetime):
                        value[sub_key] = sub_value.isoformat()
        
        return {
            "success": True,
            "execution_result": serialized_result,
            "collaboration_analysis": {
                "pattern_used": collaboration_spec.pattern.value,
                "participants": len(collaboration_spec.participants),
                "execution_status": result.get("status", "unknown"),
                "efficiency_score": result.get("efficiency_score", 0)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Collaborative execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.post("/adaptive-scaling")
async def trigger_adaptive_scaling(
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """적응적 에이전트 스케일링 트리거"""
    try:
        orchestrator = get_advanced_orchestrator()
        
        # 백그라운드에서 스케일링 실행
        scaling_result = await orchestrator.adaptive_agent_scaling()
        
        return {
            "success": True,
            "scaling_result": scaling_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Adaptive scaling failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scaling failed: {str(e)}")

@router.post("/cross-agent-learning")
async def trigger_cross_agent_learning(
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """에이전트 간 교차 학습 트리거"""
    try:
        orchestrator = get_advanced_orchestrator()
        
        # 교차 학습 실행
        learning_result = await orchestrator.cross_agent_learning()
        
        return {
            "success": True,
            "learning_result": learning_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Cross-agent learning failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Learning failed: {str(e)}")

@router.get("/performance-analytics")
async def get_performance_analytics() -> Dict[str, Any]:
    """성능 분석 데이터 조회"""
    try:
        orchestrator = get_advanced_orchestrator()
        
        # 에이전트 성능 메트릭
        performance_metrics = {}
        for agent_id, metrics in orchestrator.agent_performance_metrics.items():
            performance_metrics[agent_id] = {
                "task_completion_rate": metrics.task_completion_rate,
                "average_quality_score": metrics.average_quality_score,
                "average_response_time": metrics.average_response_time,
                "collaboration_effectiveness": metrics.collaboration_effectiveness,
                "learning_rate": metrics.learning_rate,
                "specialization_scores": metrics.specialization_scores,
                "performance_trend": metrics.recent_performance_trend[-10:],  # 최근 10개
                "last_updated": metrics.last_updated.isoformat()
            }
        
        # 협업 분석
        collaboration_analytics = {}
        for exec_id, analytics in orchestrator.collaboration_analytics.items():
            collaboration_analytics[exec_id] = {
                "pattern": analytics["pattern"],
                "success_rate": analytics["success_rate"],
                "efficiency_score": analytics["efficiency_score"],
                "duration": analytics["duration"],
                "participating_agents": len(analytics["participating_agents"]),
                "timestamp": analytics["timestamp"].isoformat()
            }
        
        # 지식 베이스 통계
        knowledge_stats = {
            "total_items": len(orchestrator.knowledge_base),
            "by_type": {},
            "by_source": {},
            "high_confidence_items": 0
        }
        
        for knowledge in orchestrator.knowledge_base.values():
            # 타입별 통계
            k_type = knowledge.knowledge_type
            knowledge_stats["by_type"][k_type] = knowledge_stats["by_type"].get(k_type, 0) + 1
            
            # 소스별 통계
            source = knowledge.source_agent
            knowledge_stats["by_source"][source] = knowledge_stats["by_source"].get(source, 0) + 1
            
            # 고신뢰도 항목
            if knowledge.confidence_score > 0.8:
                knowledge_stats["high_confidence_items"] += 1
        
        return {
            "success": True,
            "analytics": {
                "agent_performance": performance_metrics,
                "collaboration_analytics": collaboration_analytics,
                "knowledge_base_stats": knowledge_stats,
                "system_overview": {
                    "total_agents": len(orchestrator.agents),
                    "active_executions": len(orchestrator.active_executions),
                    "task_queue_length": len(orchestrator.task_queue),
                    "learning_enabled": orchestrator.learning_enabled,
                    "auto_scaling_enabled": orchestrator.auto_scaling_enabled
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance analytics retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")

@router.get("/knowledge-base")
async def get_knowledge_base(
    knowledge_type: Optional[str] = None,
    source_agent: Optional[str] = None,
    min_confidence: Optional[float] = None
) -> Dict[str, Any]:
    """지식 베이스 조회"""
    try:
        orchestrator = get_advanced_orchestrator()
        
        # 필터링
        filtered_knowledge = {}
        
        for knowledge_id, knowledge in orchestrator.knowledge_base.items():
            # 타입 필터
            if knowledge_type and knowledge.knowledge_type != knowledge_type:
                continue
            
            # 소스 에이전트 필터
            if source_agent and knowledge.source_agent != source_agent:
                continue
            
            # 신뢰도 필터
            if min_confidence and knowledge.confidence_score < min_confidence:
                continue
            
            filtered_knowledge[knowledge_id] = {
                "knowledge_id": knowledge.knowledge_id,
                "source_agent": knowledge.source_agent,
                "knowledge_type": knowledge.knowledge_type,
                "content": knowledge.content,
                "confidence_score": knowledge.confidence_score,
                "usage_count": knowledge.usage_count,
                "success_rate": knowledge.success_rate,
                "created_at": knowledge.created_at.isoformat(),
                "last_used": knowledge.last_used.isoformat() if knowledge.last_used else None
            }
        
        return {
            "success": True,
            "knowledge_items": filtered_knowledge,
            "summary": {
                "total_items": len(filtered_knowledge),
                "average_confidence": sum(k["confidence_score"] for k in filtered_knowledge.values()) / len(filtered_knowledge) if filtered_knowledge else 0,
                "most_used_item": max(filtered_knowledge.values(), key=lambda x: x["usage_count"])["knowledge_id"] if filtered_knowledge else None
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Knowledge base retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Knowledge retrieval failed: {str(e)}")

@router.get("/collaboration-patterns")
async def get_collaboration_patterns() -> Dict[str, Any]:
    """사용 가능한 협업 패턴 목록"""
    patterns = {
        "pipeline": {
            "name": "Pipeline Collaboration",
            "description": "순차적 파이프라인 방식으로 에이전트들이 작업을 처리",
            "best_for": ["순차 처리", "데이터 변환", "단계별 정제"],
            "characteristics": {
                "execution_order": "sequential",
                "data_flow": "linear",
                "coordination_complexity": "low",
                "fault_tolerance": "medium"
            },
            "use_cases": [
                "문서 처리 파이프라인",
                "이미지 전처리 → 분석 → 후처리",
                "데이터 수집 → 정제 → 분석"
            ]
        },
        "ensemble": {
            "name": "Ensemble Collaboration",
            "description": "여러 에이전트가 병렬로 작업하고 결과를 결합",
            "best_for": ["높은 정확도", "다양한 관점", "리스크 분산"],
            "characteristics": {
                "execution_order": "parallel",
                "data_flow": "convergent",
                "coordination_complexity": "medium",
                "fault_tolerance": "high"
            },
            "use_cases": [
                "다중 모델 예측",
                "합의 기반 의사결정",
                "품질 검증"
            ]
        },
        "hierarchical": {
            "name": "Hierarchical Collaboration",
            "description": "마스터-워커 구조로 계층적 작업 분배",
            "best_for": ["복잡한 작업 분해", "리소스 관리", "중앙 제어"],
            "characteristics": {
                "execution_order": "coordinated",
                "data_flow": "hierarchical",
                "coordination_complexity": "high",
                "fault_tolerance": "medium"
            },
            "use_cases": [
                "대규모 데이터 처리",
                "분산 계산",
                "프로젝트 관리"
            ]
        },
        "consensus": {
            "name": "Consensus Collaboration",
            "description": "에이전트들이 합의를 통해 최종 결정",
            "best_for": ["중요한 결정", "높은 신뢰성", "민주적 처리"],
            "characteristics": {
                "execution_order": "iterative",
                "data_flow": "multi_directional",
                "coordination_complexity": "very_high",
                "fault_tolerance": "very_high"
            },
            "use_cases": [
                "중요 의사결정",
                "품질 평가",
                "리스크 분석"
            ]
        },
        "peer_to_peer": {
            "name": "Peer-to-Peer Collaboration",
            "description": "에이전트들이 직접 통신하며 협업",
            "best_for": ["유연한 협업", "동적 조정", "분산 처리"],
            "characteristics": {
                "execution_order": "dynamic",
                "data_flow": "mesh",
                "coordination_complexity": "high",
                "fault_tolerance": "high"
            },
            "use_cases": [
                "동적 워크플로우",
                "실시간 협업",
                "적응적 처리"
            ]
        },
        "competitive": {
            "name": "Competitive Collaboration",
            "description": "에이전트들이 경쟁하여 최고 결과 선택",
            "best_for": ["최고 품질", "혁신적 솔루션", "성능 최적화"],
            "characteristics": {
                "execution_order": "parallel",
                "data_flow": "competitive",
                "coordination_complexity": "low",
                "fault_tolerance": "high"
            },
            "use_cases": [
                "창작 작업",
                "최적화 문제",
                "혁신적 솔루션 탐색"
            ]
        },
        "iterative": {
            "name": "Iterative Collaboration",
            "description": "반복적 개선을 통한 협업",
            "best_for": ["점진적 개선", "학습 기반", "품질 향상"],
            "characteristics": {
                "execution_order": "iterative",
                "data_flow": "cyclic",
                "coordination_complexity": "medium",
                "fault_tolerance": "medium"
            },
            "use_cases": [
                "반복적 최적화",
                "학습 기반 개선",
                "품질 향상 프로세스"
            ]
        }
    }
    
    return {
        "success": True,
        "collaboration_patterns": patterns,
        "default_pattern": "pipeline",
        "recommended_combinations": {
            "high_accuracy_tasks": ["ensemble", "consensus"],
            "fast_processing": ["pipeline", "competitive"],
            "complex_analysis": ["hierarchical", "iterative"],
            "creative_tasks": ["competitive", "peer_to_peer"]
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/task-complexity-analysis")
async def analyze_task_complexity(
    task_type: str,
    requirements: Optional[Dict[str, Any]] = None,
    input_data_size: Optional[int] = None
) -> Dict[str, Any]:
    """작업 복잡도 분석"""
    try:
        # 작업 복잡도 분석 로직 (간소화된 버전)
        complexity_score = 0.0
        complexity_factors = []
        
        # 작업 유형별 기본 복잡도
        base_complexity = {
            "text_processing": 0.2,
            "image_analysis": 0.4,
            "video_analysis": 0.6,
            "audio_processing": 0.3,
            "multimodal_fusion": 0.8,
            "complex_reasoning": 0.9,
            "creative_generation": 0.7,
            "research_synthesis": 0.8
        }
        
        complexity_score += base_complexity.get(task_type, 0.5)
        complexity_factors.append(f"Base complexity for {task_type}: {base_complexity.get(task_type, 0.5)}")
        
        # 요구사항 복잡도
        if requirements:
            if requirements.get("accuracy_threshold", 0) > 0.9:
                complexity_score += 0.2
                complexity_factors.append("High accuracy requirement: +0.2")
            
            if requirements.get("real_time", False):
                complexity_score += 0.3
                complexity_factors.append("Real-time requirement: +0.3")
            
            if requirements.get("multi_step", False):
                complexity_score += 0.4
                complexity_factors.append("Multi-step processing: +0.4")
        
        # 입력 데이터 크기
        if input_data_size:
            if input_data_size > 10000000:  # 10MB
                complexity_score += 0.3
                complexity_factors.append("Large input data: +0.3")
            elif input_data_size > 1000000:  # 1MB
                complexity_score += 0.1
                complexity_factors.append("Medium input data: +0.1")
        
        # 복잡도 분류
        if complexity_score < 0.4:
            complexity_level = "simple"
            recommended_approach = "single_agent"
        elif complexity_score < 0.7:
            complexity_level = "moderate"
            recommended_approach = "small_team_collaboration"
        elif complexity_score < 0.9:
            complexity_level = "complex"
            recommended_approach = "multi_agent_orchestration"
        else:
            complexity_level = "expert"
            recommended_approach = "advanced_collaboration_patterns"
        
        # 권장 전략
        strategy_recommendations = {
            "simple": {
                "patterns": ["single_agent"],
                "agent_count": 1,
                "estimated_time": "< 30 seconds"
            },
            "moderate": {
                "patterns": ["pipeline", "ensemble"],
                "agent_count": "2-3",
                "estimated_time": "30 seconds - 2 minutes"
            },
            "complex": {
                "patterns": ["hierarchical", "ensemble", "consensus"],
                "agent_count": "3-5",
                "estimated_time": "2-10 minutes"
            },
            "expert": {
                "patterns": ["consensus", "iterative", "peer_to_peer"],
                "agent_count": "5+",
                "estimated_time": "10+ minutes"
            }
        }
        
        return {
            "success": True,
            "analysis": {
                "task_type": task_type,
                "complexity_score": complexity_score,
                "complexity_level": complexity_level,
                "complexity_factors": complexity_factors,
                "recommended_approach": recommended_approach,
                "strategy_recommendations": strategy_recommendations[complexity_level],
                "decomposition_recommended": complexity_level in ["complex", "expert"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Task complexity analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")