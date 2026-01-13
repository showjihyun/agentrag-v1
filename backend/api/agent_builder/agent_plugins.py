"""
Agent Plugin API Endpoints

워크플로우 플랫폼에서 Agent Plugin 시스템을 사용하기 위한 REST API
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import asyncio

from backend.services.plugins.agents.agent_plugin_manager import get_agent_plugin_manager, AgentPluginManager
from backend.models.plugin import PluginManifest
from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.core.security.plugin_security import plugin_security_manager, PluginPermission
from backend.core.error_handling.plugin_errors import plugin_error_handler, PluginException, PluginErrorCode


router = APIRouter(prefix="/api/v1/agent-plugins", tags=["Agent Plugins"])


# Request/Response Models
class AgentExecutionRequest(BaseModel):
    """단일 Agent 실행 요청"""
    agent_type: str = Field(..., description="Agent 타입 (vector_search, web_search, local_data, aggregator)")
    input_data: Dict[str, Any] = Field(..., description="Agent 입력 데이터")
    session_id: Optional[str] = Field(None, description="세션 ID")
    workflow_id: Optional[str] = Field(None, description="워크플로우 ID")


class OrchestrationRequest(BaseModel):
    """다중 Agent 오케스트레이션 요청"""
    pattern: str = Field(..., description="오케스트레이션 패턴")
    agents: List[str] = Field(..., description="참여할 Agent 목록")
    task: Dict[str, Any] = Field(..., description="실행할 작업")
    session_id: Optional[str] = Field(None, description="세션 ID")
    workflow_id: Optional[str] = Field(None, description="워크플로우 ID")


class WorkflowExecutionRequest(BaseModel):
    """워크플로우 실행 요청"""
    workflow_definition: Dict[str, Any] = Field(..., description="워크플로우 정의")
    session_id: Optional[str] = Field(None, description="세션 ID")


class PluginInstallRequest(BaseModel):
    """Plugin 설치 요청"""
    plugin_source: str = Field(..., description="Plugin 소스 (URL, 파일 경로 등)")
    config: Optional[Dict[str, Any]] = Field(None, description="Plugin 설정")


class AgentCapabilityResponse(BaseModel):
    """Agent 능력 응답"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_permissions: List[str]


class AgentInfoResponse(BaseModel):
    """Agent 정보 응답"""
    agent_type: str
    agent_id: str
    capabilities: List[AgentCapabilityResponse]
    health_status: Dict[str, Any]
    communication_channel: Optional[str]


class OrchestrationPatternResponse(BaseModel):
    """오케스트레이션 패턴 응답"""
    patterns: List[str]
    descriptions: Dict[str, str]


# API Endpoints

@router.get("/agents", response_model=List[AgentInfoResponse])
async def get_available_agents(
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """사용 가능한 Agent 목록 조회"""
    try:
        status = await manager.get_agent_status()
        agents = status.get("agents", [])
        
        return [
            AgentInfoResponse(
                agent_type=agent["agent_type"],
                agent_id=agent["agent_id"],
                capabilities=[
                    AgentCapabilityResponse(**cap) for cap in agent["capabilities"]
                ],
                health_status=agent["health_status"],
                communication_channel=agent.get("communication_channel")
            )
            for agent in agents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")


@router.get("/agents/{agent_type}")
async def get_agent_info(
    agent_type: str,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """특정 Agent 정보 조회"""
    try:
        status = await manager.get_agent_status(agent_type)
        
        if "error" in status:
            raise HTTPException(status_code=404, detail=status["error"])
        
        return AgentInfoResponse(
            agent_type=status["agent_type"],
            agent_id=status["agent_id"],
            capabilities=[
                AgentCapabilityResponse(**cap) for cap in status["capabilities"]
            ],
            health_status=status["health_status"],
            communication_channel=status.get("communication_channel")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent info: {str(e)}")


@router.post("/agents/{agent_type}/execute")
async def execute_agent(
    agent_type: str,
    request: AgentExecutionRequest,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """단일 Agent 실행 (보안 및 에러 처리 강화)"""
    try:
        # 권한 검증
        plugin_security_manager.validate_user_permissions(
            current_user.id, PluginPermission.EXECUTE, agent_type
        )
        
        # 레이트 리미팅 검증
        plugin_security_manager.check_rate_limit(current_user.id)
        
        # Agent 타입 검증
        if request.agent_type != agent_type:
            raise PluginException(
                code=PluginErrorCode.VALIDATION_ERROR,
                message="Agent type in path and request body must match",
                plugin_id=agent_type,
                user_id=current_user.id
            )
        
        # Agent 실행
        result = await manager.execute_single_agent(
            agent_type=request.agent_type,
            input_data=request.input_data,
            user_id=current_user.id,
            session_id=request.session_id,
            workflow_id=request.workflow_id
        )
        
        return {
            "success": True,
            "result": result,
            "agent_type": agent_type,
            "execution_id": result.get("execution_id"),
            "timestamp": result.get("timestamp")
        }
        
    except PluginException as e:
        raise e.to_http_exception()
    except HTTPException:
        raise
    except Exception as e:
        plugin_exception = plugin_error_handler.handle_exception(
            e, agent_type, current_user.id, context={"request": request.dict()}
        )
        raise plugin_exception.to_http_exception()
            input_data=request.input_data,
            user_id=current_user.id,
            session_id=request.session_id,
            workflow_id=request.workflow_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.get("/orchestration/patterns", response_model=OrchestrationPatternResponse)
async def get_orchestration_patterns(
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """지원하는 오케스트레이션 패턴 목록"""
    try:
        status = await manager.get_agent_status()
        patterns = status.get("orchestration_patterns", [])
        
        # 패턴 설명 추가
        pattern_descriptions = {
            "sequential": "순차적으로 Agent들을 실행",
            "parallel": "모든 Agent를 동시에 병렬 실행",
            "hierarchical": "계층적 구조로 Agent 실행",
            "adaptive": "상황에 따라 적응적으로 패턴 선택",
            "consensus": "Agent들 간의 합의를 통한 의사결정",
            "swarm": "군집 지능을 활용한 최적화",
            "dynamic_routing": "실시간 성능 기반 동적 라우팅",
            "event_driven": "이벤트 기반 반응형 실행",
            "reflection": "자기 성찰 및 개선 기반 실행"
        }
        
        return OrchestrationPatternResponse(
            patterns=patterns,
            descriptions={p: pattern_descriptions.get(p, "설명 없음") for p in patterns}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")


@router.post("/orchestration/execute")
async def execute_orchestration(
    request: OrchestrationRequest,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """다중 Agent 오케스트레이션 실행"""
    try:
        # 패턴 검증
        status = await manager.get_agent_status()
        available_patterns = status.get("orchestration_patterns", [])
        
        if request.pattern not in available_patterns:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported orchestration pattern: {request.pattern}"
            )
        
        # Agent 존재 확인
        available_agents = [agent["agent_type"] for agent in status.get("agents", [])]
        invalid_agents = [agent for agent in request.agents if agent not in available_agents]
        
        if invalid_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agents: {invalid_agents}"
            )
        
        # 오케스트레이션 실행
        result = await manager.execute_orchestration(
            pattern=request.pattern,
            agents=request.agents,
            task=request.task,
            user_id=current_user.id,
            session_id=request.session_id,
            workflow_id=request.workflow_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


@router.post("/workflows/execute")
async def execute_workflow(
    request: WorkflowExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """워크플로우 실행 (비동기)"""
    try:
        # 워크플로우 정의 검증
        if "steps" not in request.workflow_definition:
            raise HTTPException(
                status_code=400,
                detail="Workflow definition must contain 'steps'"
            )
        
        # 백그라운드에서 워크플로우 실행
        background_tasks.add_task(
            _execute_workflow_background,
            manager,
            request.workflow_definition,
            current_user.id,
            request.session_id
        )
        
        return {
            "message": "Workflow execution started",
            "status": "processing",
            "user_id": current_user.id,
            "session_id": request.session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/plugins/install")
async def install_plugin(
    request: PluginInstallRequest,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """새로운 Agent Plugin 설치"""
    try:
        # 관리자 권한 확인 (실제 구현에서는 권한 체크)
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required for plugin installation"
            )
        
        result = await manager.install_agent_plugin(
            plugin_source=request.plugin_source,
            config=request.config
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plugin installation failed: {str(e)}")


@router.get("/health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """Agent Plugin 시스템 상태 확인"""
    try:
        status = await manager.get_agent_status()
        
        # 전체 시스템 상태 계산
        manager_status = status.get("manager_status", {})
        agents = status.get("agents", [])
        
        healthy_agents = sum(1 for agent in agents if agent["health_status"].get("status") == "healthy")
        total_agents = len(agents)
        
        # 성능 모니터링 요약 추가
        performance_summary = manager.performance_monitor.get_all_metrics_summary()
        
        # 생명주기 관리 요약 추가
        lifecycle_summary = manager.lifecycle_manager.get_plugin_status_summary()
        
        system_health = {
            "overall_status": "healthy" if manager_status.get("initialized") and healthy_agents == total_agents else "degraded",
            "manager_initialized": manager_status.get("initialized", False),
            "event_bus_active": manager_status.get("event_bus_active", False),
            "total_agents": total_agents,
            "healthy_agents": healthy_agents,
            "registered_plugins": manager_status.get("registered_plugins", 0),
            "available_patterns": len(status.get("orchestration_patterns", [])),
            "performance_summary": performance_summary,
            "lifecycle_summary": lifecycle_summary,
            "timestamp": datetime.now().isoformat()
        }
        
        return system_health
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/performance/metrics")
async def get_performance_metrics(
    plugin_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """성능 메트릭 조회"""
    try:
        if plugin_type:
            # 특정 Plugin의 상세 메트릭
            metrics = manager.performance_monitor.get_plugin_metrics(plugin_type)
            return metrics
        else:
            # 전체 Plugin 성능 요약
            summary = manager.performance_monitor.get_all_metrics_summary()
            return summary
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.post("/performance/thresholds")
async def update_performance_thresholds(
    thresholds: Dict[str, float],
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """성능 알림 임계값 업데이트"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        manager.performance_monitor.set_alert_thresholds(thresholds)
        
        return {
            "success": True,
            "message": "Performance thresholds updated",
            "thresholds": thresholds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update thresholds: {str(e)}")


@router.get("/optimization/recommendations")
async def get_optimization_recommendations(
    workflow_id: Optional[str] = None,
    strategy: str = "balanced",
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """AI 기반 최적화 추천 조회"""
    try:
        from backend.core.ml.orchestration_optimizer import OptimizationObjective
        from backend.services.optimization.auto_tuning_service import AutoTuningService, TuningStrategy
        
        # 자동 튜닝 서비스 초기화 (실제로는 의존성 주입)
        auto_tuning = AutoTuningService(
            manager.optimizer if hasattr(manager, 'optimizer') else None,
            manager.performance_monitor,
            manager.event_bus
        )
        
        if workflow_id:
            # 특정 워크플로우 추천
            insights = await auto_tuning.get_tuning_insights(workflow_id)
            return insights
        else:
            # 전체 추천 요약
            insights = await auto_tuning.get_tuning_insights()
            return insights
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get optimization recommendations: {str(e)}")


@router.post("/optimization/analyze")
async def analyze_workflow_optimization(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """워크플로우 최적화 분석"""
    try:
        workflow_id = request.get('workflow_id')
        pattern = request.get('pattern')
        agents = request.get('agents', [])
        task = request.get('task', {})
        
        if not all([workflow_id, pattern, agents]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # ML 최적화기 사용 (실제로는 의존성 주입)
        if not hasattr(manager, 'optimizer'):
            raise HTTPException(status_code=503, detail="Optimization service not available")
        
        # 성능 예측
        prediction = await manager.optimizer.predict_performance(pattern, agents, task)
        
        # 최적화 제안
        optimization = await manager.optimizer.optimize_orchestration(
            pattern, agents, task
        )
        
        return {
            'workflow_id': workflow_id,
            'current_prediction': {
                'execution_time': prediction.predicted_execution_time,
                'success_rate': prediction.predicted_success_rate,
                'cost': prediction.predicted_cost,
                'confidence': prediction.confidence
            },
            'optimization_recommendation': {
                'optimized_pattern': optimization.optimized_pattern,
                'optimized_agents': optimization.optimized_agents,
                'performance_improvement': optimization.performance_improvement,
                'cost_reduction': optimization.cost_reduction,
                'reliability_improvement': optimization.reliability_improvement,
                'reasoning': optimization.reasoning,
                'estimated_savings': optimization.estimated_savings
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization analysis failed: {str(e)}")


@router.post("/optimization/auto-tune")
async def start_auto_tuning(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """자동 성능 튜닝 시작"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        from backend.services.optimization.auto_tuning_service import AutoTuningService, TuningConfiguration, TuningStrategy
        
        # 튜닝 설정
        config = TuningConfiguration(
            strategy=TuningStrategy(request.get('strategy', 'balanced')),
            auto_apply=request.get('auto_apply', False),
            tuning_interval_hours=request.get('interval_hours', 24),
            min_improvement_threshold=request.get('min_improvement', 5.0)
        )
        
        # 자동 튜닝 서비스 시작
        auto_tuning = AutoTuningService(
            manager.optimizer if hasattr(manager, 'optimizer') else None,
            manager.performance_monitor,
            manager.event_bus
        )
        
        await auto_tuning.start_auto_tuning(config)
        
        return {
            'success': True,
            'message': 'Auto tuning started successfully',
            'config': {
                'strategy': config.strategy,
                'auto_apply': config.auto_apply,
                'interval_hours': config.tuning_interval_hours
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start auto tuning: {str(e)}")


@router.post("/optimization/cost-analysis")
async def analyze_workflow_costs(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """워크플로우 비용 분석"""
    try:
        from backend.services.optimization.cost_optimization_engine import CostOptimizationEngine
        
        workflow_id = request.get('workflow_id')
        pattern = request.get('pattern')
        agents = request.get('agents', [])
        
        if not all([workflow_id, pattern, agents]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # 비용 최적화 엔진 초기화
        cost_engine = CostOptimizationEngine(manager.event_bus)
        
        # 최근 실행 데이터 (실제로는 DB에서 조회)
        recent_executions = request.get('recent_executions', [])
        
        # 비용 분석
        cost_analysis = await cost_engine.analyze_workflow_costs(
            workflow_id, pattern, agents, recent_executions
        )
        
        return cost_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost analysis failed: {str(e)}")


@router.post("/optimization/cost-optimize")
async def optimize_workflow_costs(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """워크플로우 비용 최적화"""
    try:
        from backend.services.optimization.cost_optimization_engine import (
            CostOptimizationEngine, CostOptimizationStrategy
        )
        
        workflow_id = request.get('workflow_id')
        pattern = request.get('pattern')
        agents = request.get('agents', [])
        cost_analysis = request.get('cost_analysis', {})
        strategy = request.get('strategy', 'balanced')
        
        if not all([workflow_id, pattern, agents, cost_analysis]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # 비용 최적화 엔진
        cost_engine = CostOptimizationEngine(manager.event_bus)
        
        # 최적화 계획 생성
        optimization_plan = await cost_engine.generate_cost_optimization_plan(
            workflow_id, pattern, agents, cost_analysis, 
            CostOptimizationStrategy(strategy)
        )
        
        return {
            'workflow_id': optimization_plan.workflow_id,
            'current_cost': {
                'total': optimization_plan.current_cost.total_cost,
                'breakdown': {
                    'compute': optimization_plan.current_cost.compute_cost,
                    'llm_api': optimization_plan.current_cost.llm_api_cost,
                    'storage': optimization_plan.current_cost.storage_cost,
                    'network': optimization_plan.current_cost.network_cost,
                    'overhead': optimization_plan.current_cost.overhead_cost
                }
            },
            'optimized_cost': {
                'total': optimization_plan.optimized_cost.total_cost,
                'breakdown': {
                    'compute': optimization_plan.optimized_cost.compute_cost,
                    'llm_api': optimization_plan.optimized_cost.llm_api_cost,
                    'storage': optimization_plan.optimized_cost.storage_cost,
                    'network': optimization_plan.optimized_cost.network_cost,
                    'overhead': optimization_plan.optimized_cost.overhead_cost
                }
            },
            'optimization_actions': optimization_plan.optimization_actions,
            'estimated_savings': optimization_plan.estimated_savings,
            'confidence': optimization_plan.confidence,
            'risk_level': optimization_plan.risk_level,
            'implementation_effort': optimization_plan.implementation_effort
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cost optimization failed: {str(e)}")


@router.get("/optimization/analytics")
async def get_optimization_analytics(
    start_date: str,
    end_date: str,
    workflow_ids: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """최적화 분석 데이터 조회"""
    try:
        from datetime import datetime
        
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        workflow_list = workflow_ids.split(',') if workflow_ids else None
        
        if not hasattr(manager, 'optimization_manager') or not manager.optimization_manager:
            raise HTTPException(status_code=503, detail="Optimization services not available")
        
        analytics = await manager.optimization_manager.get_optimization_analytics(
            start_dt, end_dt, workflow_list
        )
        
        return analytics
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")


@router.get("/optimization/real-time-metrics")
async def get_real_time_optimization_metrics(
    workflow_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """실시간 최적화 메트릭 조회"""
    try:
        if not hasattr(manager, 'optimization_manager') or not manager.optimization_manager:
            raise HTTPException(status_code=503, detail="Optimization services not available")
        
        metrics = await manager.optimization_manager.get_real_time_optimization_metrics(workflow_id)
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Real-time metrics retrieval failed: {str(e)}")


@router.post("/optimization/notifications/settings")
async def update_notification_settings(
    settings: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """알림 설정 업데이트"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        if not hasattr(manager, 'optimization_manager') or not manager.optimization_manager:
            raise HTTPException(status_code=503, detail="Optimization services not available")
        
        result = await manager.optimization_manager.update_notification_settings(settings)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification settings update failed: {str(e)}")


@router.get("/optimization/notifications/history")
async def get_notification_history(
    limit: int = 50,
    notification_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """알림 이력 조회"""
    try:
        if not hasattr(manager, 'optimization_manager') or not manager.optimization_manager:
            raise HTTPException(status_code=503, detail="Optimization services not available")
        
        history = await manager.optimization_manager.get_notification_history(limit, notification_type)
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification history retrieval failed: {str(e)}")


@router.post("/optimization/reports/weekly")
async def generate_weekly_report(
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """주간 리포트 생성"""
    try:
        # 관리자 권한 확인
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        
        if not hasattr(manager, 'optimization_manager') or not manager.optimization_manager:
            raise HTTPException(status_code=503, detail="Optimization services not available")
        
        result = await manager.optimization_manager.generate_weekly_report()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weekly report generation failed: {str(e)}")


@router.get("/optimization/dashboard-data")
async def get_optimization_dashboard_data(
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """최적화 대시보드 데이터 조회 (통합)"""
    try:
        if not hasattr(manager, 'optimization_manager') or not manager.optimization_manager:
            return {
                'status': 'optimization_services_unavailable',
                'message': '최적화 서비스가 사용할 수 없습니다.'
            }
        
        # 기본 대시보드 데이터
        dashboard_data = await manager.optimization_manager.get_optimization_dashboard_data()
        
        # 실시간 메트릭 추가
        real_time_metrics = await manager.optimization_manager.get_real_time_optimization_metrics()
        
        # 최근 알림 이력 추가
        notification_history = await manager.optimization_manager.get_notification_history(10)
        
        # 통합 데이터 반환
        return {
            **dashboard_data,
            'real_time_metrics': real_time_metrics,
            'recent_notifications': notification_history.get('history', []),
            'notification_stats': notification_history.get('stats', {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")


@router.post("/custom-agents/{agent_id}/register")
async def register_custom_agent_as_plugin(
    agent_id: str,
    config: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """Custom Agent를 Plugin으로 등록"""
    try:
        result = await manager.register_custom_agent_as_plugin(
            agent_id=agent_id,
            user_id=current_user.id,
            config=config or {}
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.delete("/custom-agents/{agent_id}/unregister")
async def unregister_custom_agent_plugin(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """Custom Agent Plugin 등록 해제"""
    try:
        result = await manager.unregister_custom_agent_plugin(
            agent_id=agent_id,
            user_id=current_user.id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unregistration failed: {str(e)}")


@router.post("/custom-agents/{agent_id}/refresh")
async def refresh_custom_agent_plugin(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """Custom Agent Plugin 갱신"""
    try:
        result = await manager.refresh_custom_agent_plugin(
            agent_id=agent_id,
            user_id=current_user.id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.get("/custom-agents")
async def get_user_custom_agents(
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """사용자의 Custom Agent 목록 조회"""
    try:
        result = await manager.get_user_custom_agents(current_user.id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get custom agents: {str(e)}")


@router.post("/custom-agents/{agent_id}/execute")
async def execute_custom_agent(
    agent_id: str,
    request: AgentExecutionRequest,
    current_user: User = Depends(get_current_user),
    manager: AgentPluginManager = Depends(get_agent_plugin_manager)
):
    """Custom Agent 실행"""
    try:
        result = await manager.execute_custom_agent(
            agent_id=agent_id,
            input_data=request.input_data,
            user_id=current_user.id,
            session_id=request.session_id,
            workflow_id=request.workflow_id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Custom agent execution failed: {str(e)}")


@router.get("/blocks/custom-agent-execution")
async def get_custom_agent_execution_block_config():
    """Custom Agent 실행 블록 설정 정보 (워크플로우 디자이너용)"""
    return {
        "block_type": "custom_agent_execution",
        "display_name": "Custom Agent 실행",
        "description": "사용자가 생성한 Custom Agent를 실행합니다",
        "category": "AI Agents",
        "icon": "user-bot",
        "inputs": [
            {
                "name": "agent_id",
                "type": "select",
                "label": "Custom Agent",
                "required": True,
                "dynamic_options": True,
                "options_endpoint": "/api/v1/agent-plugins/custom-agents",
                "option_value_field": "agent_id",
                "option_label_field": "agent_name"
            },
            {
                "name": "input_data",
                "type": "json",
                "label": "입력 데이터",
                "required": True,
                "placeholder": '{"input": "사용자 입력"}',
                "description": "Custom Agent에 전달할 입력 데이터"
            },
            {
                "name": "session_id",
                "type": "string",
                "label": "세션 ID",
                "required": False,
                "description": "세션 추적을 위한 ID (선택사항)"
            }
        ],
        "outputs": [
            {
                "name": "response",
                "type": "string",
                "label": "Agent 응답"
            },
            {
                "name": "success",
                "type": "boolean",
                "label": "성공 여부"
            },
            {
                "name": "agent_name",
                "type": "string",
                "label": "Agent 이름"
            },
            {
                "name": "tool_results",
                "type": "array",
                "label": "도구 실행 결과"
            },
            {
                "name": "kb_results",
                "type": "array",
                "label": "지식베이스 검색 결과"
            }
        ]
    }


# 워크플로우 블록 통합을 위한 엔드포인트
@router.get("/blocks/agent-execution")
async def get_agent_execution_block_config():
    """Agent 실행 블록 설정 정보 (워크플로우 디자이너용)"""
    return {
        "block_type": "agent_execution",
        "display_name": "Agent 실행",
        "description": "단일 AI Agent를 실행합니다",
        "category": "AI Agents",
        "icon": "bot",
        "inputs": [
            {
                "name": "agent_type",
                "type": "select",
                "label": "Agent 타입",
                "required": True,
                "options": [
                    {"value": "vector_search", "label": "Vector Search Agent"},
                    {"value": "web_search", "label": "Web Search Agent"},
                    {"value": "local_data", "label": "Local Data Agent"},
                    {"value": "aggregator", "label": "Aggregator Agent"}
                ]
            },
            {
                "name": "input_data",
                "type": "json",
                "label": "입력 데이터",
                "required": True,
                "placeholder": "{\"query\": \"검색할 내용\"}"
            }
        ],
        "outputs": [
            {
                "name": "result",
                "type": "json",
                "label": "실행 결과"
            },
            {
                "name": "success",
                "type": "boolean",
                "label": "성공 여부"
            }
        ]
    }


@router.get("/blocks/orchestration")
async def get_orchestration_block_config():
    """오케스트레이션 블록 설정 정보 (워크플로우 디자이너용)"""
    return {
        "block_type": "agent_orchestration",
        "display_name": "Agent 오케스트레이션",
        "description": "여러 AI Agent를 조정하여 복합 작업을 수행합니다",
        "category": "AI Agents",
        "icon": "network",
        "inputs": [
            {
                "name": "pattern",
                "type": "select",
                "label": "오케스트레이션 패턴",
                "required": True,
                "options": [
                    {"value": "sequential", "label": "순차 실행"},
                    {"value": "parallel", "label": "병렬 실행"},
                    {"value": "consensus", "label": "합의 기반"},
                    {"value": "swarm", "label": "군집 지능"},
                    {"value": "dynamic_routing", "label": "동적 라우팅"}
                ]
            },
            {
                "name": "agents",
                "type": "multi-select",
                "label": "참여 Agent",
                "required": True,
                "options": [
                    {"value": "vector_search", "label": "Vector Search"},
                    {"value": "web_search", "label": "Web Search"},
                    {"value": "local_data", "label": "Local Data"}
                ]
            },
            {
                "name": "task",
                "type": "json",
                "label": "작업 정의",
                "required": True,
                "placeholder": "{\"objective\": \"작업 목표\"}"
            }
        ],
        "outputs": [
            {
                "name": "orchestration_result",
                "type": "json",
                "label": "오케스트레이션 결과"
            },
            {
                "name": "agent_results",
                "type": "array",
                "label": "개별 Agent 결과"
            }
        ]
    }


# 백그라운드 작업 함수
async def _execute_workflow_background(
    manager: AgentPluginManager,
    workflow_definition: Dict[str, Any],
    user_id: str,
    session_id: Optional[str]
):
    """백그라운드에서 워크플로우 실행"""
    try:
        result = await manager.execute_workflow(
            workflow_definition=workflow_definition,
            user_id=user_id,
            session_id=session_id
        )
        
        # 결과를 이벤트로 발행하거나 데이터베이스에 저장
        # 실제 구현에서는 WebSocket이나 SSE를 통해 클라이언트에 알림
        
    except Exception as e:
        # 에러 로깅 및 알림
        print(f"Background workflow execution failed: {e}")