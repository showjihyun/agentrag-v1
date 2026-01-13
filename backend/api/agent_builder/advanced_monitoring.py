"""
Advanced Monitoring API

고급 모니터링 및 관찰가능성 API 엔드포인트
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.core.monitoring.advanced_metrics_collector import AdvancedMetricsCollector
from backend.core.monitoring.plugin_performance_monitor import PluginPerformanceMonitor
from backend.core.security.runtime_security_monitor import RuntimeSecurityMonitor
from backend.core.scaling.auto_scaling_manager import AutoScalingManager, ScalingPolicy
from backend.services.plugins.enhanced_security_manager import ThreatLevel
from backend.core.event_bus.validated_event_bus import ValidatedEventBus

router = APIRouter(prefix="/api/v1/advanced-monitoring", tags=["Advanced Monitoring"])


class UserSatisfactionRequest(BaseModel):
    """사용자 만족도 요청"""
    user_id: str
    workflow_id: str
    satisfaction_score: float = Field(..., ge=0, le=10)
    feedback: Optional[str] = None


class BusinessValueRequest(BaseModel):
    """비즈니스 가치 요청"""
    workflow_id: str
    outcomes: List[Dict[str, Any]]


class ScalingPolicyRequest(BaseModel):
    """스케일링 정책 요청"""
    plugin_type: str
    min_instances: int = Field(default=1, ge=1)
    max_instances: int = Field(default=10, ge=1)
    target_cpu_utilization: float = Field(default=70.0, ge=0, le=100)
    target_memory_utilization: float = Field(default=80.0, ge=0, le=100)
    target_response_time: float = Field(default=2.0, ge=0)
    scale_up_cooldown: int = Field(default=300, ge=60)
    scale_down_cooldown: int = Field(default=600, ge=60)


class ManualScalingRequest(BaseModel):
    """수동 스케일링 요청"""
    plugin_type: str
    target_instances: int = Field(..., ge=1)
    reason: str = "Manual scaling"


# 의존성 주입을 위한 전역 변수들 (실제로는 DI 컨테이너 사용)
advanced_metrics_collector: Optional[AdvancedMetricsCollector] = None
runtime_security_monitor: Optional[RuntimeSecurityMonitor] = None
auto_scaling_manager: Optional[AutoScalingManager] = None


def initialize_monitoring_dependencies(
    metrics_collector: AdvancedMetricsCollector,
    security_monitor: RuntimeSecurityMonitor,
    scaling_manager: AutoScalingManager
):
    """모니터링 의존성 초기화"""
    global advanced_metrics_collector, runtime_security_monitor, auto_scaling_manager
    advanced_metrics_collector = metrics_collector
    runtime_security_monitor = security_monitor
    auto_scaling_manager = scaling_manager


def get_advanced_metrics_collector() -> AdvancedMetricsCollector:
    """고급 메트릭 수집기 의존성"""
    if advanced_metrics_collector is None:
        raise HTTPException(status_code=503, detail="Advanced metrics collector not available")
    return advanced_metrics_collector


def get_runtime_security_monitor() -> RuntimeSecurityMonitor:
    """런타임 보안 모니터 의존성"""
    if runtime_security_monitor is None:
        raise HTTPException(status_code=503, detail="Runtime security monitor not available")
    return runtime_security_monitor


def get_auto_scaling_manager() -> AutoScalingManager:
    """자동 스케일링 매니저 의존성"""
    if auto_scaling_manager is None:
        raise HTTPException(status_code=503, detail="Auto scaling manager not available")
    return auto_scaling_manager


@router.get("/dashboard")
async def get_comprehensive_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user),
    metrics_collector: AdvancedMetricsCollector = Depends(get_advanced_metrics_collector)
):
    """종합 대시보드 데이터 조회"""
    try:
        dashboard_data = await metrics_collector.get_comprehensive_dashboard_data()
        return {
            "success": True,
            "data": dashboard_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.post("/business-metrics/user-satisfaction")
async def record_user_satisfaction(
    request: UserSatisfactionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    metrics_collector: AdvancedMetricsCollector = Depends(get_advanced_metrics_collector)
):
    """사용자 만족도 기록"""
    try:
        execution_result = {
            'success': True,
            'execution_time': 2.0,  # 실제로는 워크플로우 실행 결과에서 가져옴
            'error': None
        }
        
        satisfaction_score = await metrics_collector.business_metrics.collect_user_satisfaction(
            request.user_id,
            request.workflow_id,
            execution_result
        )
        
        return {
            "success": True,
            "satisfaction_score": satisfaction_score,
            "message": "User satisfaction recorded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record satisfaction: {str(e)}")


@router.post("/business-metrics/business-value")
async def calculate_business_value(
    request: BusinessValueRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    metrics_collector: AdvancedMetricsCollector = Depends(get_advanced_metrics_collector)
):
    """비즈니스 가치 계산"""
    try:
        roi_metric = await metrics_collector.business_metrics.calculate_business_value(
            request.workflow_id,
            request.outcomes
        )
        
        return {
            "success": True,
            "roi_metric": {
                "workflow_id": roi_metric.workflow_id,
                "cost_saved": roi_metric.cost_saved,
                "time_saved": roi_metric.time_saved,
                "revenue_generated": roi_metric.revenue_generated,
                "efficiency_gain": roi_metric.efficiency_gain,
                "timestamp": roi_metric.timestamp.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate business value: {str(e)}")


@router.get("/business-metrics/summary")
async def get_business_metrics_summary(
    hours: int = Query(default=24, ge=1, le=168),  # 1시간 ~ 1주일
    current_user: Dict[str, Any] = Depends(get_current_user),
    metrics_collector: AdvancedMetricsCollector = Depends(get_advanced_metrics_collector)
):
    """비즈니스 메트릭 요약"""
    try:
        user_satisfaction = metrics_collector.business_metrics.get_user_satisfaction_summary(hours)
        roi_summary = metrics_collector.business_metrics.get_roi_summary(hours // 24)
        sla_summary = metrics_collector.business_metrics.get_sla_summary()
        
        return {
            "success": True,
            "data": {
                "user_satisfaction": user_satisfaction,
                "roi_summary": roi_summary,
                "sla_summary": sla_summary,
                "period_hours": hours
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get business metrics: {str(e)}")


@router.get("/predictive-analytics/load-prediction")
async def get_load_prediction(
    time_horizon_hours: int = Query(default=24, ge=1, le=168),
    current_user: Dict[str, Any] = Depends(get_current_user),
    metrics_collector: AdvancedMetricsCollector = Depends(get_advanced_metrics_collector)
):
    """시스템 부하 예측"""
    try:
        prediction = await metrics_collector.predictive_analytics.predict_system_load(
            time_horizon_hours
        )
        
        return {
            "success": True,
            "prediction": prediction
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to predict load: {str(e)}")


@router.get("/predictive-analytics/anomalies")
async def get_performance_anomalies(
    current_user: Dict[str, Any] = Depends(get_current_user),
    metrics_collector: AdvancedMetricsCollector = Depends(get_advanced_metrics_collector)
):
    """성능 이상 탐지"""
    try:
        anomalies = await metrics_collector.predictive_analytics.detect_performance_anomalies()
        
        return {
            "success": True,
            "anomalies": anomalies
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")


@router.get("/predictive-analytics/scaling-recommendations")
async def get_scaling_recommendations(
    current_user: Dict[str, Any] = Depends(get_current_user),
    metrics_collector: AdvancedMetricsCollector = Depends(get_advanced_metrics_collector)
):
    """스케일링 권장사항"""
    try:
        recommendations = await metrics_collector.predictive_analytics.recommend_scaling_actions()
        
        return {
            "success": True,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/security/incidents")
async def get_security_incidents(
    status: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user),
    security_monitor: RuntimeSecurityMonitor = Depends(get_runtime_security_monitor)
):
    """보안 사고 조회"""
    try:
        severity_enum = None
        if severity:
            try:
                severity_enum = ThreatLevel(severity)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        
        incidents = security_monitor.get_security_incidents(
            status=status,
            severity=severity_enum,
            limit=limit
        )
        
        return {
            "success": True,
            "incidents": incidents,
            "total_count": len(incidents)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security incidents: {str(e)}")


@router.get("/security/statistics")
async def get_security_statistics(
    current_user: Dict[str, Any] = Depends(get_current_user),
    security_monitor: RuntimeSecurityMonitor = Depends(get_runtime_security_monitor)
):
    """보안 통계"""
    try:
        statistics = security_monitor.get_monitoring_statistics()
        
        return {
            "success": True,
            "statistics": statistics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security statistics: {str(e)}")


@router.post("/security/monitoring/{execution_id}/start")
async def start_security_monitoring(
    execution_id: str,
    plugin_id: str = Query(...),
    user_id: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    security_monitor: RuntimeSecurityMonitor = Depends(get_runtime_security_monitor)
):
    """보안 모니터링 시작"""
    try:
        context = await security_monitor.start_monitoring_session(
            plugin_id, user_id, execution_id
        )
        
        return {
            "success": True,
            "execution_id": execution_id,
            "monitoring_started": True,
            "start_time": context.start_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/security/monitoring/{execution_id}/analyze")
async def analyze_runtime_security(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    security_monitor: RuntimeSecurityMonitor = Depends(get_runtime_security_monitor)
):
    """런타임 보안 분석"""
    try:
        analysis = await security_monitor.analyze_runtime_security(execution_id)
        
        return {
            "success": True,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze security: {str(e)}")


@router.post("/security/monitoring/{execution_id}/end")
async def end_security_monitoring(
    execution_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    security_monitor: RuntimeSecurityMonitor = Depends(get_runtime_security_monitor)
):
    """보안 모니터링 종료"""
    try:
        final_analysis = await security_monitor.end_monitoring_session(execution_id)
        
        return {
            "success": True,
            "execution_id": execution_id,
            "monitoring_ended": True,
            "final_analysis": final_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to end monitoring: {str(e)}")


@router.get("/scaling/status")
async def get_scaling_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    scaling_manager: AutoScalingManager = Depends(get_auto_scaling_manager)
):
    """스케일링 상태 조회"""
    try:
        status = scaling_manager.get_scaling_status()
        
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scaling status: {str(e)}")


@router.post("/scaling/policies")
async def set_scaling_policy(
    request: ScalingPolicyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    scaling_manager: AutoScalingManager = Depends(get_auto_scaling_manager)
):
    """스케일링 정책 설정"""
    try:
        policy = ScalingPolicy(
            plugin_type=request.plugin_type,
            min_instances=request.min_instances,
            max_instances=request.max_instances,
            target_cpu_utilization=request.target_cpu_utilization,
            target_memory_utilization=request.target_memory_utilization,
            target_response_time=request.target_response_time,
            scale_up_cooldown=request.scale_up_cooldown,
            scale_down_cooldown=request.scale_down_cooldown
        )
        
        scaling_manager.set_scaling_policy(request.plugin_type, policy)
        
        return {
            "success": True,
            "message": f"Scaling policy set for {request.plugin_type}",
            "policy": {
                "plugin_type": policy.plugin_type,
                "min_instances": policy.min_instances,
                "max_instances": policy.max_instances,
                "target_cpu_utilization": policy.target_cpu_utilization,
                "target_memory_utilization": policy.target_memory_utilization
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set scaling policy: {str(e)}")


@router.post("/scaling/manual")
async def manual_scale(
    request: ManualScalingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    scaling_manager: AutoScalingManager = Depends(get_auto_scaling_manager)
):
    """수동 스케일링"""
    try:
        result = await scaling_manager.manual_scale(
            request.plugin_type,
            request.target_instances,
            request.reason
        )
        
        return {
            "success": result["success"],
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform manual scaling: {str(e)}")


@router.post("/scaling/start")
async def start_auto_scaling(
    current_user: Dict[str, Any] = Depends(get_current_user),
    scaling_manager: AutoScalingManager = Depends(get_auto_scaling_manager)
):
    """자동 스케일링 시작"""
    try:
        await scaling_manager.start_auto_scaling()
        
        return {
            "success": True,
            "message": "Auto scaling started successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start auto scaling: {str(e)}")


@router.post("/scaling/stop")
async def stop_auto_scaling(
    current_user: Dict[str, Any] = Depends(get_current_user),
    scaling_manager: AutoScalingManager = Depends(get_auto_scaling_manager)
):
    """자동 스케일링 중지"""
    try:
        await scaling_manager.stop_auto_scaling()
        
        return {
            "success": True,
            "message": "Auto scaling stopped successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop auto scaling: {str(e)}")


@router.get("/scaling/recommendations")
async def get_scaling_recommendations_api(
    current_user: Dict[str, Any] = Depends(get_current_user),
    scaling_manager: AutoScalingManager = Depends(get_auto_scaling_manager)
):
    """스케일링 권장사항 조회"""
    try:
        recommendations = scaling_manager.get_scaling_recommendations()
        
        return {
            "success": True,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scaling recommendations: {str(e)}")


@router.post("/metrics/start-collection")
async def start_metrics_collection(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    metrics_collector: AdvancedMetricsCollector = Depends(get_advanced_metrics_collector)
):
    """메트릭 수집 시작"""
    try:
        background_tasks.add_task(metrics_collector.start_collection)
        
        return {
            "success": True,
            "message": "Metrics collection started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start metrics collection: {str(e)}")


@router.post("/metrics/stop-collection")
async def stop_metrics_collection(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    metrics_collector: AdvancedMetricsCollector = Depends(get_advanced_metrics_collector)
):
    """메트릭 수집 중지"""
    try:
        background_tasks.add_task(metrics_collector.stop_collection)
        
        return {
            "success": True,
            "message": "Metrics collection stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop metrics collection: {str(e)}")


@router.get("/health")
async def get_monitoring_health():
    """모니터링 시스템 상태 확인"""
    try:
        health_status = {
            "advanced_metrics_collector": advanced_metrics_collector is not None,
            "runtime_security_monitor": runtime_security_monitor is not None,
            "auto_scaling_manager": auto_scaling_manager is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        all_healthy = all(health_status.values())
        
        return {
            "success": True,
            "healthy": all_healthy,
            "components": health_status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check health: {str(e)}")