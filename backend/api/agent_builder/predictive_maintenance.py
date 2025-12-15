"""
Predictive Maintenance & Self-Healing API
예측 유지보수 및 자가 치유 API - Phase 5-4 구현
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from backend.services.multimodal.predictive_maintenance import (
    get_predictive_maintenance_system,
    PredictiveMaintenanceSystem,
    HealthReport,
    AnomalyAlert,
    MaintenanceTask,
    SystemMetrics,
    HealthStatus,
    AnomalyType,
    MaintenanceAction
)
from backend.core.structured_logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/predictive-maintenance",
    tags=["predictive-maintenance"]
)

# Request/Response Models
class SystemHealthRequest(BaseModel):
    """시스템 건강 상태 요청"""
    include_trends: bool = Field(default=True, description="성능 트렌드 포함 여부")
    include_forecast: bool = Field(default=True, description="용량 예측 포함 여부")
    include_recommendations: bool = Field(default=True, description="권장사항 포함 여부")

class AnomalyDetectionRequest(BaseModel):
    """이상 징후 탐지 요청"""
    time_window_hours: int = Field(default=1, description="분석 시간 윈도우 (시간)")
    severity_filter: Optional[List[str]] = Field(default=None, description="심각도 필터")
    component_filter: Optional[List[str]] = Field(default=None, description="컴포넌트 필터")

class MaintenanceScheduleRequest(BaseModel):
    """유지보수 일정 요청"""
    priority_filter: Optional[List[str]] = Field(default=None, description="우선순위 필터")
    component_filter: Optional[List[str]] = Field(default=None, description="컴포넌트 필터")
    time_horizon_hours: int = Field(default=24, description="일정 조회 시간 (시간)")

class MaintenanceExecutionRequest(BaseModel):
    """유지보수 실행 요청"""
    task_id: str = Field(description="유지보수 작업 ID")
    force_execution: bool = Field(default=False, description="강제 실행 여부")
    override_dependencies: bool = Field(default=False, description="의존성 무시 여부")

class SystemConfigurationRequest(BaseModel):
    """시스템 설정 요청"""
    auto_healing_enabled: bool = Field(default=True, description="자가 치유 활성화")
    collection_interval: int = Field(default=30, description="메트릭 수집 간격 (초)")
    anomaly_threshold: float = Field(default=0.8, description="이상 징후 임계값")
    max_concurrent_maintenance: int = Field(default=3, description="최대 동시 유지보수 작업")

class PerformanceAnalyticsRequest(BaseModel):
    """성능 분석 요청"""
    time_range_hours: int = Field(default=24, description="분석 시간 범위 (시간)")
    metrics_filter: Optional[List[str]] = Field(default=None, description="메트릭 필터")
    aggregation_interval: str = Field(default="1h", description="집계 간격")

# Response Models
class SystemHealthResponse(BaseModel):
    """시스템 건강 상태 응답"""
    health_report: Dict[str, Any]
    system_status: str
    component_status: Dict[str, str]
    active_anomalies_count: int
    maintenance_tasks_count: int
    risk_score: float
    generated_at: datetime

class AnomalyDetectionResponse(BaseModel):
    """이상 징후 탐지 응답"""
    anomalies: List[Dict[str, Any]]
    total_count: int
    severity_distribution: Dict[str, int]
    affected_components: List[str]
    detection_confidence: float
    analyzed_at: datetime

class MaintenanceScheduleResponse(BaseModel):
    """유지보수 일정 응답"""
    scheduled_tasks: List[Dict[str, Any]]
    active_tasks: List[Dict[str, Any]]
    completed_tasks: List[Dict[str, Any]]
    total_tasks: int
    next_maintenance_window: Optional[datetime]
    estimated_total_duration: float

class PerformanceAnalyticsResponse(BaseModel):
    """성능 분석 응답"""
    metrics_summary: Dict[str, Any]
    performance_trends: Dict[str, List[float]]
    bottleneck_analysis: Dict[str, Any]
    capacity_utilization: Dict[str, float]
    recommendations: List[str]
    analysis_period: Dict[str, datetime]

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    request: SystemHealthRequest = Depends(),
    maintenance_system: PredictiveMaintenanceSystem = Depends(get_predictive_maintenance_system)
):
    """
    시스템 건강 상태 조회
    
    전체 시스템의 건강 상태, 컴포넌트별 상태, 활성 이상 징후 등을 반환합니다.
    """
    try:
        logger.info("Generating system health report")
        
        # 건강 보고서 생성
        health_report = await maintenance_system.generate_health_report()
        
        # 위험 점수 계산
        risk_scores = list(health_report.risk_assessment.values())
        average_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        response = SystemHealthResponse(
            health_report=health_report.__dict__,
            system_status=health_report.overall_status.value,
            component_status={k: v.value for k, v in health_report.component_status.items()},
            active_anomalies_count=len(health_report.active_anomalies),
            maintenance_tasks_count=len(health_report.maintenance_recommendations),
            risk_score=average_risk,
            generated_at=health_report.generated_at
        )
        
        logger.info(f"System health report generated: {health_report.overall_status.value}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get system health: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")

@router.post("/anomalies/detect", response_model=AnomalyDetectionResponse)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    maintenance_system: PredictiveMaintenanceSystem = Depends(get_predictive_maintenance_system)
):
    """
    이상 징후 탐지
    
    시스템 메트릭을 분석하여 이상 징후를 탐지하고 분석 결과를 반환합니다.
    """
    try:
        logger.info(f"Detecting anomalies with time window: {request.time_window_hours}h")
        
        # 최근 메트릭 가져오기
        if not maintenance_system.metrics_history:
            raise HTTPException(status_code=404, detail="No metrics data available")
        
        current_metrics = maintenance_system.metrics_history[-1]
        
        # 이상 징후 탐지
        anomalies = await maintenance_system._detect_anomalies(current_metrics)
        
        # 필터 적용
        if request.severity_filter:
            anomalies = [a for a in anomalies if a.severity in request.severity_filter]
        
        if request.component_filter:
            anomalies = [a for a in anomalies if any(comp in request.component_filter for comp in a.affected_components)]
        
        # 심각도 분포 계산
        severity_distribution = {}
        for anomaly in anomalies:
            severity_distribution[anomaly.severity] = severity_distribution.get(anomaly.severity, 0) + 1
        
        # 영향받는 컴포넌트 수집
        affected_components = list(set(
            comp for anomaly in anomalies for comp in anomaly.affected_components
        ))
        
        # 탐지 신뢰도 계산
        confidence_scores = [a.confidence_score for a in anomalies]
        detection_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        response = AnomalyDetectionResponse(
            anomalies=[anomaly.__dict__ for anomaly in anomalies],
            total_count=len(anomalies),
            severity_distribution=severity_distribution,
            affected_components=affected_components,
            detection_confidence=detection_confidence,
            analyzed_at=datetime.now()
        )
        
        logger.info(f"Detected {len(anomalies)} anomalies")
        return response
        
    except Exception as e:
        logger.error(f"Failed to detect anomalies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")

@router.get("/maintenance/schedule", response_model=MaintenanceScheduleResponse)
async def get_maintenance_schedule(
    request: MaintenanceScheduleRequest = Depends(),
    maintenance_system: PredictiveMaintenanceSystem = Depends(get_predictive_maintenance_system)
):
    """
    유지보수 일정 조회
    
    예정된 유지보수 작업, 진행 중인 작업, 완료된 작업 목록을 반환합니다.
    """
    try:
        logger.info("Getting maintenance schedule")
        
        # 건강 보고서에서 권장사항 가져오기
        health_report = await maintenance_system.generate_health_report()
        scheduled_tasks = health_report.maintenance_recommendations
        
        # 활성 유지보수 작업
        active_tasks = list(maintenance_system.active_maintenance.values())
        
        # 완료된 작업 (최근 24시간)
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=request.time_horizon_hours)
        completed_tasks = [
            task for task in maintenance_system.maintenance_history
            if task.status == "completed" and 
            (task.scheduled_time and task.scheduled_time >= cutoff_time)
        ]
        
        # 필터 적용
        if request.priority_filter:
            scheduled_tasks = [t for t in scheduled_tasks if t.priority in request.priority_filter]
            active_tasks = [t for t in active_tasks if t.priority in request.priority_filter]
            completed_tasks = [t for t in completed_tasks if t.priority in request.priority_filter]
        
        if request.component_filter:
            scheduled_tasks = [t for t in scheduled_tasks if t.target_component in request.component_filter]
            active_tasks = [t for t in active_tasks if t.target_component in request.component_filter]
            completed_tasks = [t for t in completed_tasks if t.target_component in request.component_filter]
        
        # 다음 유지보수 윈도우 계산
        next_maintenance = None
        if scheduled_tasks:
            upcoming_tasks = [t for t in scheduled_tasks if t.scheduled_time and t.scheduled_time > datetime.now()]
            if upcoming_tasks:
                next_maintenance = min(t.scheduled_time for t in upcoming_tasks)
        
        # 총 예상 소요 시간
        total_duration = sum(t.estimated_duration for t in scheduled_tasks)
        
        response = MaintenanceScheduleResponse(
            scheduled_tasks=[task.__dict__ for task in scheduled_tasks],
            active_tasks=[task.__dict__ for task in active_tasks],
            completed_tasks=[task.__dict__ for task in completed_tasks],
            total_tasks=len(scheduled_tasks) + len(active_tasks),
            next_maintenance_window=next_maintenance,
            estimated_total_duration=total_duration
        )
        
        logger.info(f"Retrieved maintenance schedule: {len(scheduled_tasks)} scheduled, {len(active_tasks)} active")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get maintenance schedule: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get maintenance schedule: {str(e)}")

@router.post("/maintenance/execute")
async def execute_maintenance_task(
    request: MaintenanceExecutionRequest,
    maintenance_system: PredictiveMaintenanceSystem = Depends(get_predictive_maintenance_system)
):
    """
    유지보수 작업 실행
    
    지정된 유지보수 작업을 실행합니다.
    """
    try:
        logger.info(f"Executing maintenance task: {request.task_id}")
        
        # 작업 찾기
        task = None
        health_report = await maintenance_system.generate_health_report()
        
        for recommended_task in health_report.maintenance_recommendations:
            if recommended_task.task_id == request.task_id:
                task = recommended_task
                break
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Maintenance task not found: {request.task_id}")
        
        # 의존성 확인 (override가 아닌 경우)
        if not request.override_dependencies:
            for dependency in task.dependencies:
                # 의존성 확인 로직 (시뮬레이션)
                logger.info(f"Checking dependency: {dependency}")
        
        # 작업 실행
        await maintenance_system._execute_maintenance_task(task)
        
        return {
            "success": True,
            "message": f"Maintenance task {request.task_id} executed successfully",
            "task_id": request.task_id,
            "status": task.status,
            "executed_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to execute maintenance task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to execute maintenance task: {str(e)}")

@router.post("/configuration")
async def update_system_configuration(
    request: SystemConfigurationRequest,
    maintenance_system: PredictiveMaintenanceSystem = Depends(get_predictive_maintenance_system)
):
    """
    시스템 설정 업데이트
    
    예측 유지보수 시스템의 설정을 업데이트합니다.
    """
    try:
        logger.info("Updating system configuration")
        
        # 설정 업데이트
        maintenance_system.monitoring_config.update({
            "auto_healing_enabled": request.auto_healing_enabled,
            "collection_interval": request.collection_interval,
            "anomaly_threshold": request.anomaly_threshold,
            "max_concurrent_maintenance": request.max_concurrent_maintenance
        })
        
        return {
            "success": True,
            "message": "System configuration updated successfully",
            "configuration": maintenance_system.monitoring_config,
            "updated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")

@router.get("/analytics", response_model=PerformanceAnalyticsResponse)
async def get_performance_analytics(
    request: PerformanceAnalyticsRequest = Depends(),
    maintenance_system: PredictiveMaintenanceSystem = Depends(get_predictive_maintenance_system)
):
    """
    성능 분석 조회
    
    시스템 성능 메트릭, 트렌드, 병목 지점 분석 결과를 반환합니다.
    """
    try:
        logger.info(f"Getting performance analytics for {request.time_range_hours}h")
        
        if not maintenance_system.metrics_history:
            raise HTTPException(status_code=404, detail="No metrics data available")
        
        # 시간 범위에 따른 메트릭 필터링
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=request.time_range_hours)
        
        filtered_metrics = [
            m for m in maintenance_system.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if not filtered_metrics:
            raise HTTPException(status_code=404, detail="No metrics data in specified time range")
        
        # 메트릭 요약 계산
        metrics_summary = {
            "avg_cpu_usage": sum(m.cpu_usage for m in filtered_metrics) / len(filtered_metrics),
            "avg_memory_usage": sum(m.memory_usage for m in filtered_metrics) / len(filtered_metrics),
            "avg_response_time": sum(m.response_time for m in filtered_metrics) / len(filtered_metrics),
            "avg_throughput": sum(m.throughput for m in filtered_metrics) / len(filtered_metrics),
            "avg_error_rate": sum(m.error_rate for m in filtered_metrics) / len(filtered_metrics),
            "total_samples": len(filtered_metrics)
        }
        
        # 성능 트렌드
        performance_trends = {
            "cpu_usage": [m.cpu_usage for m in filtered_metrics],
            "memory_usage": [m.memory_usage for m in filtered_metrics],
            "response_time": [m.response_time for m in filtered_metrics],
            "throughput": [m.throughput for m in filtered_metrics],
            "error_rate": [m.error_rate for m in filtered_metrics]
        }
        
        # 병목 지점 분석
        latest_metrics = filtered_metrics[-1]
        bottleneck_analysis = {
            "cpu_bottleneck": latest_metrics.cpu_usage > 80,
            "memory_bottleneck": latest_metrics.memory_usage > 80,
            "response_time_bottleneck": latest_metrics.response_time > 1000,
            "throughput_bottleneck": latest_metrics.throughput < 200,
            "primary_bottleneck": "cpu" if latest_metrics.cpu_usage > 80 else 
                                 "memory" if latest_metrics.memory_usage > 80 else
                                 "response_time" if latest_metrics.response_time > 1000 else "none"
        }
        
        # 용량 사용률
        capacity_utilization = {
            "cpu": latest_metrics.cpu_usage,
            "memory": latest_metrics.memory_usage,
            "disk": latest_metrics.disk_usage,
            "network": min(100.0, latest_metrics.network_io / 100 * 100)  # 정규화
        }
        
        # 권장사항
        recommendations = []
        if latest_metrics.cpu_usage > 80:
            recommendations.append("CPU 사용률이 높습니다. 스케일 업을 고려하세요.")
        if latest_metrics.memory_usage > 80:
            recommendations.append("메모리 사용률이 높습니다. 메모리 최적화가 필요합니다.")
        if latest_metrics.response_time > 1000:
            recommendations.append("응답 시간이 느립니다. 부하 분산을 확인하세요.")
        if latest_metrics.error_rate > 0.05:
            recommendations.append("오류율이 높습니다. 시스템 안정성을 점검하세요.")
        
        if not recommendations:
            recommendations.append("시스템이 정상적으로 작동하고 있습니다.")
        
        response = PerformanceAnalyticsResponse(
            metrics_summary=metrics_summary,
            performance_trends=performance_trends,
            bottleneck_analysis=bottleneck_analysis,
            capacity_utilization=capacity_utilization,
            recommendations=recommendations,
            analysis_period={
                "start": cutoff_time,
                "end": datetime.now()
            }
        )
        
        logger.info(f"Performance analytics generated for {len(filtered_metrics)} samples")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get performance analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get performance analytics: {str(e)}")

@router.get("/metrics/current")
async def get_current_metrics(
    maintenance_system: PredictiveMaintenanceSystem = Depends(get_predictive_maintenance_system)
):
    """
    현재 시스템 메트릭 조회
    
    실시간 시스템 메트릭을 반환합니다.
    """
    try:
        if not maintenance_system.metrics_history:
            # 메트릭 수집
            current_metrics = await maintenance_system._collect_system_metrics()
        else:
            current_metrics = maintenance_system.metrics_history[-1]
        
        return {
            "metrics": current_metrics.__dict__,
            "collected_at": current_metrics.timestamp,
            "system_status": "healthy" if current_metrics.cpu_usage < 80 and current_metrics.memory_usage < 80 else "warning"
        }
        
    except Exception as e:
        logger.error(f"Failed to get current metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get current metrics: {str(e)}")

@router.get("/status")
async def get_system_status(
    maintenance_system: PredictiveMaintenanceSystem = Depends(get_predictive_maintenance_system)
):
    """
    시스템 상태 요약 조회
    
    시스템의 전반적인 상태를 간단히 요약하여 반환합니다.
    """
    try:
        health_report = await maintenance_system.generate_health_report()
        
        return {
            "overall_status": health_report.overall_status.value,
            "component_count": len(health_report.component_status),
            "healthy_components": sum(1 for status in health_report.component_status.values() if status == HealthStatus.HEALTHY),
            "active_anomalies": len(health_report.active_anomalies),
            "pending_maintenance": len(health_report.maintenance_recommendations),
            "active_maintenance": len(maintenance_system.active_maintenance),
            "auto_healing_enabled": maintenance_system.monitoring_config["auto_healing_enabled"],
            "last_updated": health_report.generated_at
        }
        
    except Exception as e:
        logger.error(f"Failed to get system status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")