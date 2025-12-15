"""
Intelligent Workflow Optimization API
지능형 워크플로우 최적화 REST API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid

from backend.services.multimodal.workflow_optimizer import (
    get_workflow_optimizer,
    OptimizationObjective,
    OptimizationStrategy,
    PredictionModel,
    WorkflowMetrics
)
from backend.services.multimodal.multi_agent_orchestrator import (
    Task,
    TaskPriority
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/workflow-optimization", tags=["Workflow Optimization"])

@router.post("/predict-performance")
async def predict_workflow_performance(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    워크플로우 성능 예측
    
    Request Body:
    {
        "tasks": [
            {
                "task_id": "task_1",
                "task_type": "image_analysis",
                "priority": "high",
                "requirements": {"accuracy": 0.9},
                "input_data": {"image_url": "..."},
                "estimated_duration": 30.0,
                "dependencies": []
            }
        ],
        "agent_assignments": {"task_1": "vision_agent_01"},
        "collaboration_pattern": "ensemble"
    }
    """
    try:
        optimizer = get_workflow_optimizer()
        
        # 요청 데이터 파싱
        tasks_data = request.get("tasks", [])
        agent_assignments = request.get("agent_assignments")
        collaboration_pattern = request.get("collaboration_pattern")
        
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
        
        # 성능 예측 실행
        prediction = await optimizer.predict_workflow_performance(
            tasks, agent_assignments, collaboration_pattern
        )
        
        return {
            "success": True,
            "prediction": {
                "execution_time": prediction.execution_time,
                "cost_estimate": prediction.cost_estimate,
                "quality_score": prediction.quality_score,
                "resource_usage": prediction.resource_usage,
                "confidence_interval": {
                    "lower": prediction.confidence_interval[0],
                    "upper": prediction.confidence_interval[1]
                },
                "prediction_accuracy": prediction.prediction_accuracy,
                "bottlenecks": prediction.bottlenecks,
                "optimization_suggestions": prediction.optimization_suggestions
            },
            "analysis": {
                "total_tasks": len(tasks),
                "predicted_bottlenecks": len(prediction.bottlenecks),
                "optimization_opportunities": len(prediction.optimization_suggestions),
                "confidence_level": "high" if prediction.prediction_accuracy > 0.8 else "medium" if prediction.prediction_accuracy > 0.6 else "low"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance prediction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/optimize-configuration")
async def optimize_workflow_configuration(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    워크플로우 설정 최적화
    
    Request Body:
    {
        "tasks": [...],
        "objective": "balance_all",
        "strategy": "greedy",
        "constraints": {
            "max_cost": 1.0,
            "max_execution_time": 300,
            "required_quality": 0.85
        }
    }
    """
    try:
        optimizer = get_workflow_optimizer()
        
        # 요청 데이터 파싱
        tasks_data = request.get("tasks", [])
        objective_str = request.get("objective", "balance_all")
        strategy_str = request.get("strategy", "greedy")
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
        
        # 최적화 목표 및 전략 설정
        objective = OptimizationObjective(objective_str)
        strategy = OptimizationStrategy(strategy_str)
        
        # 최적화 실행
        optimization_result = await optimizer.optimize_workflow_configuration(
            tasks, objective, strategy, constraints
        )
        
        return {
            "success": True,
            "optimization": {
                "original_config": optimization_result.original_config,
                "optimized_config": optimization_result.optimized_config,
                "predicted_improvement": optimization_result.predicted_improvement,
                "optimization_strategy": optimization_result.optimization_strategy.value,
                "confidence_score": optimization_result.confidence_score,
                "estimated_savings": optimization_result.estimated_savings,
                "risk_assessment": optimization_result.risk_assessment
            },
            "summary": {
                "time_improvement": f"{optimization_result.predicted_improvement.get('execution_time', 0):.1f}%",
                "cost_improvement": f"{optimization_result.predicted_improvement.get('cost', 0):.1f}%",
                "quality_improvement": f"{optimization_result.predicted_improvement.get('quality', 0):.1f}%",
                "overall_risk": sum(optimization_result.risk_assessment.values()) / len(optimization_result.risk_assessment),
                "recommendation": "apply" if optimization_result.confidence_score > 0.7 else "review"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Workflow optimization failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.post("/analyze-bottlenecks")
async def analyze_workflow_bottlenecks(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    워크플로우 병목 지점 분석
    """
    try:
        optimizer = get_workflow_optimizer()
        
        # 요청 데이터 파싱
        tasks_data = request.get("tasks", [])
        agent_assignments = request.get("agent_assignments")
        collaboration_pattern = request.get("collaboration_pattern")
        
        # 작업 객체 생성
        tasks = []
        for task_data in tasks_data:
            task = Task(
                task_id=task_data.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                task_type=task_data["task_type"],
                priority=TaskPriority(task_data.get("priority", "medium")),
                requirements=task_data.get("requirements", {}),
                input_data=task_data.get("input_data", {}),
                deadline=None,
                estimated_duration=task_data.get("estimated_duration", 30.0),
                dependencies=task_data.get("dependencies", [])
            )
            tasks.append(task)
        
        # 성능 예측으로 병목 분석
        prediction = await optimizer.predict_workflow_performance(
            tasks, agent_assignments, collaboration_pattern
        )
        
        # 상세 병목 분석
        bottleneck_analysis = {
            "identified_bottlenecks": prediction.bottlenecks,
            "bottleneck_details": {},
            "impact_assessment": {},
            "resolution_strategies": {}
        }
        
        # 각 병목에 대한 상세 분석
        for bottleneck in prediction.bottlenecks:
            if bottleneck == "high_complexity_tasks":
                bottleneck_analysis["bottleneck_details"][bottleneck] = {
                    "description": "복잡한 작업들이 전체 실행 시간을 지연시킴",
                    "affected_tasks": [task.task_id for task in tasks if task.estimated_duration > 60.0],
                    "severity": "high"
                }
                bottleneck_analysis["impact_assessment"][bottleneck] = {
                    "time_impact": "30-50% 실행 시간 증가",
                    "cost_impact": "20-30% 비용 증가",
                    "quality_impact": "품질에는 긍정적 영향"
                }
                bottleneck_analysis["resolution_strategies"][bottleneck] = [
                    "작업 분해를 통한 병렬화",
                    "더 강력한 에이전트 할당",
                    "사전 처리 최적화"
                ]
            
            elif bottleneck == "unbalanced_agent_load":
                bottleneck_analysis["bottleneck_details"][bottleneck] = {
                    "description": "에이전트 간 작업 부하 불균형",
                    "load_distribution": agent_assignments,
                    "severity": "medium"
                }
                bottleneck_analysis["impact_assessment"][bottleneck] = {
                    "time_impact": "20-40% 실행 시간 증가",
                    "cost_impact": "리소스 낭비",
                    "quality_impact": "일부 에이전트 과부하로 품질 저하 가능"
                }
                bottleneck_analysis["resolution_strategies"][bottleneck] = [
                    "작업 재분배",
                    "추가 에이전트 투입",
                    "동적 로드 밸런싱"
                ]
        
        return {
            "success": True,
            "bottleneck_analysis": bottleneck_analysis,
            "optimization_suggestions": prediction.optimization_suggestions,
            "priority_actions": [
                {
                    "action": suggestion,
                    "priority": "high" if i < 2 else "medium",
                    "estimated_impact": "20-30% improvement"
                }
                for i, suggestion in enumerate(prediction.optimization_suggestions[:5])
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Bottleneck analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/record-execution")
async def record_workflow_execution(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """워크플로우 실행 결과 기록"""
    try:
        optimizer = get_workflow_optimizer()
        
        # 실행 메트릭 생성
        metrics = WorkflowMetrics(
            workflow_id=request.get("workflow_id", f"workflow_{uuid.uuid4().hex[:8]}"),
            execution_time=request.get("execution_time", 0.0),
            cost=request.get("cost", 0.0),
            quality_score=request.get("quality_score", 0.0),
            resource_usage=request.get("resource_usage", {}),
            agent_assignments=request.get("agent_assignments", {}),
            collaboration_pattern=request.get("collaboration_pattern", ""),
            input_characteristics=request.get("input_characteristics", {})
        )
        
        # 실행 결과 기록
        optimizer.record_workflow_execution(metrics)
        
        return {
            "success": True,
            "message": "Execution metrics recorded successfully",
            "metrics_id": metrics.workflow_id,
            "total_recorded_executions": len(optimizer.performance_history),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Recording execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Recording failed: {str(e)}")

@router.get("/optimization-objectives")
async def get_optimization_objectives() -> Dict[str, Any]:
    """사용 가능한 최적화 목표 목록"""
    objectives = {
        "minimize_time": {
            "name": "실행 시간 최소화",
            "description": "워크플로우 실행 시간을 최대한 단축",
            "best_for": ["실시간 처리", "빠른 응답 필요", "시간 제약 있는 작업"],
            "trade_offs": {
                "pros": ["빠른 실행", "높은 처리량"],
                "cons": ["높은 비용 가능성", "품질 타협 가능성"]
            }
        },
        "minimize_cost": {
            "name": "비용 최소화",
            "description": "실행 비용을 최대한 절약",
            "best_for": ["예산 제약", "대량 처리", "비용 효율성 중시"],
            "trade_offs": {
                "pros": ["낮은 운영 비용", "높은 ROI"],
                "cons": ["느린 실행 가능성", "리소스 제약"]
            }
        },
        "maximize_quality": {
            "name": "품질 최대화",
            "description": "출력 품질을 최대한 향상",
            "best_for": ["정확도 중시", "중요한 결정", "품질 보증 필요"],
            "trade_offs": {
                "pros": ["높은 정확도", "신뢰할 수 있는 결과"],
                "cons": ["높은 비용", "긴 실행 시간"]
            }
        },
        "balance_all": {
            "name": "균형 최적화",
            "description": "시간, 비용, 품질의 균형점 찾기",
            "best_for": ["일반적인 용도", "다목적 최적화", "안정적인 성능"],
            "trade_offs": {
                "pros": ["균형잡힌 성능", "예측 가능한 결과"],
                "cons": ["특정 영역에서 최적이 아닐 수 있음"]
            }
        },
        "minimize_resource": {
            "name": "리소스 사용량 최소화",
            "description": "CPU, 메모리, GPU 사용량 최소화",
            "best_for": ["리소스 제약 환경", "에너지 효율성", "동시 실행"],
            "trade_offs": {
                "pros": ["낮은 리소스 사용", "높은 동시성"],
                "cons": ["느린 실행", "품질 제한"]
            }
        },
        "maximize_throughput": {
            "name": "처리량 최대화",
            "description": "단위 시간당 처리 작업 수 최대화",
            "best_for": ["대량 처리", "배치 작업", "높은 처리량 필요"],
            "trade_offs": {
                "pros": ["높은 처리량", "효율적인 배치 처리"],
                "cons": ["개별 작업 지연", "리소스 집약적"]
            }
        }
    }
    
    return {
        "success": True,
        "objectives": objectives,
        "default_objective": "balance_all",
        "recommendations": {
            "real_time_applications": "minimize_time",
            "batch_processing": "maximize_throughput",
            "cost_sensitive": "minimize_cost",
            "quality_critical": "maximize_quality",
            "general_purpose": "balance_all"
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/optimization-strategies")
async def get_optimization_strategies() -> Dict[str, Any]:
    """사용 가능한 최적화 전략 목록"""
    strategies = {
        "greedy": {
            "name": "탐욕적 최적화",
            "description": "각 단계에서 가장 좋은 선택을 하는 빠른 최적화",
            "complexity": "low",
            "execution_time": "fast",
            "quality": "good",
            "best_for": ["빠른 최적화", "실시간 적용", "간단한 문제"],
            "limitations": ["지역 최적해", "복잡한 문제에서 제한적"]
        },
        "genetic": {
            "name": "유전 알고리즘",
            "description": "진화 원리를 모방한 전역 최적화 알고리즘",
            "complexity": "high",
            "execution_time": "slow",
            "quality": "excellent",
            "best_for": ["복잡한 최적화", "전역 최적해", "다목적 최적화"],
            "limitations": ["긴 실행 시간", "매개변수 조정 필요"]
        },
        "annealing": {
            "name": "시뮬레이티드 어닐링",
            "description": "금속 어닐링 과정을 모방한 확률적 최적화",
            "complexity": "medium",
            "execution_time": "medium",
            "quality": "very_good",
            "best_for": ["지역 최적해 탈출", "연속 최적화", "중간 복잡도"],
            "limitations": ["매개변수 민감", "수렴 보장 없음"]
        },
        "particle_swarm": {
            "name": "입자 군집 최적화",
            "description": "새 떼의 행동을 모방한 집단 지능 최적화",
            "complexity": "medium",
            "execution_time": "medium",
            "quality": "good",
            "best_for": ["연속 공간 최적화", "다차원 문제", "병렬 처리"],
            "limitations": ["이산 문제에 제한", "조기 수렴 가능"]
        },
        "bayesian": {
            "name": "베이지안 최적화",
            "description": "베이지안 추론을 활용한 효율적인 최적화",
            "complexity": "high",
            "execution_time": "medium",
            "quality": "excellent",
            "best_for": ["비싼 함수 최적화", "적은 평가 횟수", "불확실성 고려"],
            "limitations": ["복잡한 구현", "고차원에서 제한적"]
        }
    }
    
    return {
        "success": True,
        "strategies": strategies,
        "default_strategy": "greedy",
        "recommendations": {
            "quick_optimization": "greedy",
            "best_quality": "genetic",
            "balanced_approach": "annealing",
            "parallel_processing": "particle_swarm",
            "expensive_evaluation": "bayesian"
        },
        "performance_comparison": {
            "speed": ["greedy", "particle_swarm", "annealing", "bayesian", "genetic"],
            "quality": ["genetic", "bayesian", "annealing", "particle_swarm", "greedy"],
            "complexity": ["greedy", "particle_swarm", "annealing", "bayesian", "genetic"]
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/performance-history")
async def get_performance_history(
    limit: Optional[int] = 100,
    workflow_type: Optional[str] = None
) -> Dict[str, Any]:
    """성능 히스토리 조회"""
    try:
        optimizer = get_workflow_optimizer()
        
        # 히스토리 필터링
        history = optimizer.performance_history[-limit:] if limit else optimizer.performance_history
        
        if workflow_type:
            history = [h for h in history if workflow_type in h.workflow_id]
        
        # 통계 계산
        if history:
            execution_times = [h.execution_time for h in history]
            costs = [h.cost for h in history]
            quality_scores = [h.quality_score for h in history]
            
            statistics = {
                "execution_time": {
                    "mean": sum(execution_times) / len(execution_times),
                    "min": min(execution_times),
                    "max": max(execution_times),
                    "std": (sum((x - sum(execution_times)/len(execution_times))**2 for x in execution_times) / len(execution_times))**0.5
                },
                "cost": {
                    "mean": sum(costs) / len(costs),
                    "min": min(costs),
                    "max": max(costs),
                    "std": (sum((x - sum(costs)/len(costs))**2 for x in costs) / len(costs))**0.5
                },
                "quality": {
                    "mean": sum(quality_scores) / len(quality_scores),
                    "min": min(quality_scores),
                    "max": max(quality_scores),
                    "std": (sum((x - sum(quality_scores)/len(quality_scores))**2 for x in quality_scores) / len(quality_scores))**0.5
                }
            }
        else:
            statistics = {}
        
        # 히스토리 직렬화
        serialized_history = []
        for h in history:
            serialized_history.append({
                "workflow_id": h.workflow_id,
                "execution_time": h.execution_time,
                "cost": h.cost,
                "quality_score": h.quality_score,
                "resource_usage": h.resource_usage,
                "agent_assignments": h.agent_assignments,
                "collaboration_pattern": h.collaboration_pattern,
                "timestamp": h.timestamp.isoformat()
            })
        
        return {
            "success": True,
            "history": serialized_history,
            "statistics": statistics,
            "summary": {
                "total_executions": len(optimizer.performance_history),
                "returned_executions": len(history),
                "date_range": {
                    "earliest": history[0].timestamp.isoformat() if history else None,
                    "latest": history[-1].timestamp.isoformat() if history else None
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Performance history retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

@router.post("/compare-configurations")
async def compare_workflow_configurations(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """워크플로우 설정 비교"""
    try:
        optimizer = get_workflow_optimizer()
        
        # 요청 데이터 파싱
        tasks_data = request.get("tasks", [])
        configurations = request.get("configurations", [])
        
        if len(configurations) < 2:
            raise HTTPException(status_code=400, detail="At least 2 configurations required for comparison")
        
        # 작업 객체 생성
        tasks = []
        for task_data in tasks_data:
            task = Task(
                task_id=task_data.get("task_id", f"task_{uuid.uuid4().hex[:8]}"),
                task_type=task_data["task_type"],
                priority=TaskPriority(task_data.get("priority", "medium")),
                requirements=task_data.get("requirements", {}),
                input_data=task_data.get("input_data", {}),
                deadline=None,
                estimated_duration=task_data.get("estimated_duration", 30.0),
                dependencies=task_data.get("dependencies", [])
            )
            tasks.append(task)
        
        # 각 설정에 대한 예측
        comparison_results = []
        
        for i, config in enumerate(configurations):
            prediction = await optimizer.predict_workflow_performance(
                tasks,
                config.get("agent_assignments"),
                config.get("collaboration_pattern")
            )
            
            comparison_results.append({
                "configuration_id": config.get("name", f"Config_{i+1}"),
                "configuration": config,
                "prediction": {
                    "execution_time": prediction.execution_time,
                    "cost_estimate": prediction.cost_estimate,
                    "quality_score": prediction.quality_score,
                    "resource_usage": prediction.resource_usage,
                    "bottlenecks": prediction.bottlenecks,
                    "optimization_suggestions": prediction.optimization_suggestions
                },
                "scores": {
                    "time_score": 1000.0 / (prediction.execution_time + 1),
                    "cost_score": 10.0 / (prediction.cost_estimate + 0.1),
                    "quality_score": prediction.quality_score * 100,
                    "overall_score": (
                        (1000.0 / (prediction.execution_time + 1)) * 0.3 +
                        (10.0 / (prediction.cost_estimate + 0.1)) * 0.3 +
                        (prediction.quality_score * 100) * 0.4
                    )
                }
            })
        
        # 순위 매기기
        comparison_results.sort(key=lambda x: x["scores"]["overall_score"], reverse=True)
        
        # 상대적 비교
        best_config = comparison_results[0]
        relative_comparisons = []
        
        for result in comparison_results[1:]:
            relative_comparisons.append({
                "configuration_id": result["configuration_id"],
                "relative_performance": {
                    "time_difference": ((result["prediction"]["execution_time"] - best_config["prediction"]["execution_time"]) / best_config["prediction"]["execution_time"]) * 100,
                    "cost_difference": ((result["prediction"]["cost_estimate"] - best_config["prediction"]["cost_estimate"]) / best_config["prediction"]["cost_estimate"]) * 100,
                    "quality_difference": ((result["prediction"]["quality_score"] - best_config["prediction"]["quality_score"]) / best_config["prediction"]["quality_score"]) * 100
                }
            })
        
        return {
            "success": True,
            "comparison": {
                "configurations": comparison_results,
                "best_configuration": best_config["configuration_id"],
                "relative_comparisons": relative_comparisons,
                "summary": {
                    "fastest": min(comparison_results, key=lambda x: x["prediction"]["execution_time"])["configuration_id"],
                    "cheapest": min(comparison_results, key=lambda x: x["prediction"]["cost_estimate"])["configuration_id"],
                    "highest_quality": max(comparison_results, key=lambda x: x["prediction"]["quality_score"])["configuration_id"],
                    "most_balanced": comparison_results[0]["configuration_id"]
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Configuration comparison failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")