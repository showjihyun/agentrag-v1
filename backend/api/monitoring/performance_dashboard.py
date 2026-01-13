"""
Performance Dashboard API
성능 대시보드 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.core.auth_dependencies import get_current_user
from backend.core.monitoring.performance_monitor import get_performance_monitor, PerformanceMonitor
from backend.db.models.user import User
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/dashboard")
async def get_dashboard_data(
    duration_minutes: int = Query(60, ge=1, le=1440, description="데이터 조회 기간 (분)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    대시보드 데이터 조회
    
    Args:
        duration_minutes: 조회할 데이터의 기간 (분 단위, 1분~24시간)
        current_user: 현재 사용자
    
    Returns:
        대시보드 데이터 (시스템 메트릭, 오케스트레이션 메트릭, 알림 등)
    """
    try:
        monitor = get_performance_monitor()
        dashboard_data = monitor.get_dashboard_data(duration_minutes)
        
        logger.info(f"Dashboard data requested by user {current_user.id} for {duration_minutes} minutes")
        
        return {
            "success": True,
            "data": dashboard_data,
            "metadata": {
                "duration_minutes": duration_minutes,
                "generated_at": datetime.now().isoformat(),
                "user_id": current_user.id
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


@router.get("/system/current")
async def get_current_system_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    현재 시스템 상태 조회
    
    Returns:
        현재 시스템 상태 (CPU, 메모리, 디스크 사용률 등)
    """
    try:
        monitor = get_performance_monitor()
        collector = monitor.collector
        
        # 최신 시스템 메트릭 조회
        current_status = {
            "cpu_percent": collector.get_latest("system.cpu_percent"),
            "memory_percent": collector.get_latest("system.memory_percent"),
            "memory_used_mb": collector.get_latest("system.memory_used_mb"),
            "disk_usage_percent": collector.get_latest("system.disk_usage_percent"),
            "process_count": collector.get_latest("system.process_count"),
            "load_1m": collector.get_latest("system.load_1m"),
            "load_5m": collector.get_latest("system.load_5m"),
            "load_15m": collector.get_latest("system.load_15m"),
        }
        
        # None 값을 0으로 변환
        for key, value in current_status.items():
            if value is None:
                current_status[key] = {"timestamp": datetime.now().timestamp(), "value": 0}
            else:
                current_status[key] = {"timestamp": value.timestamp, "value": value.value}
        
        return {
            "success": True,
            "data": current_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting current system status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.get("/orchestration/current")
async def get_current_orchestration_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    현재 오케스트레이션 상태 조회
    
    Returns:
        현재 오케스트레이션 상태 (실행 중인 작업, 성공률, 캐시 히트율 등)
    """
    try:
        monitor = get_performance_monitor()
        current_metrics = monitor.orchestration_monitor.get_current_metrics()
        
        return {
            "success": True,
            "data": {
                "total_executions": current_metrics.total_executions,
                "successful_executions": current_metrics.successful_executions,
                "failed_executions": current_metrics.failed_executions,
                "success_rate": current_metrics.successful_executions / current_metrics.total_executions if current_metrics.total_executions > 0 else 0,
                "average_execution_time": current_metrics.average_execution_time,
                "current_active_executions": current_metrics.current_active_executions,
                "cache_hit_rate": current_metrics.cache_hit_rate,
                "security_validations": current_metrics.security_validations,
                "pattern_usage": current_metrics.pattern_usage,
                "timestamp": current_metrics.timestamp
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting current orchestration status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get orchestration status: {str(e)}")


@router.get("/alerts")
async def get_alerts(
    active_only: bool = Query(False, description="활성 알림만 조회"),
    since_hours: Optional[int] = Query(None, ge=1, le=168, description="지정된 시간 이후의 알림만 조회 (시간)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    알림 목록 조회
    
    Args:
        active_only: True면 활성 알림만, False면 모든 알림
        since_hours: 지정된 시간 이후의 알림만 조회 (시간 단위)
        current_user: 현재 사용자
    
    Returns:
        알림 목록
    """
    try:
        monitor = get_performance_monitor()
        alert_manager = monitor.alert_manager
        
        if active_only:
            alerts = alert_manager.get_active_alerts()
        else:
            since_timestamp = None
            if since_hours:
                since_timestamp = (datetime.now() - timedelta(hours=since_hours)).timestamp()
            alerts = alert_manager.get_all_alerts(since_timestamp)
        
        # Alert 객체를 딕셔너리로 변환
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                "id": alert.id,
                "level": alert.level.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at,
                "duration": (alert.resolved_at - alert.timestamp) if alert.resolved_at else None
            })
        
        return {
            "success": True,
            "data": {
                "alerts": alerts_data,
                "total_count": len(alerts_data),
                "active_count": len([a for a in alerts_data if not a["resolved"]])
            },
            "filters": {
                "active_only": active_only,
                "since_hours": since_hours
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/metrics/{metric_name}")
async def get_metric_history(
    metric_name: str,
    duration_minutes: int = Query(60, ge=1, le=1440, description="데이터 조회 기간 (분)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    특정 메트릭의 히스토리 조회
    
    Args:
        metric_name: 메트릭 이름
        duration_minutes: 조회할 데이터의 기간 (분 단위)
        current_user: 현재 사용자
    
    Returns:
        메트릭 히스토리 데이터
    """
    try:
        monitor = get_performance_monitor()
        collector = monitor.collector
        
        since = datetime.now().timestamp() - (duration_minutes * 60)
        metric_points = collector.get_metric(metric_name, since)
        
        if not metric_points:
            return {
                "success": True,
                "data": {
                    "metric_name": metric_name,
                    "points": [],
                    "count": 0,
                    "average": None,
                    "min": None,
                    "max": None
                },
                "message": f"No data found for metric: {metric_name}"
            }
        
        # 통계 계산
        values = [p.value for p in metric_points]
        average = sum(values) / len(values)
        min_value = min(values)
        max_value = max(values)
        
        # 데이터 포인트 변환
        points_data = [
            {
                "timestamp": p.timestamp,
                "value": p.value,
                "labels": p.labels
            }
            for p in metric_points
        ]
        
        return {
            "success": True,
            "data": {
                "metric_name": metric_name,
                "points": points_data,
                "count": len(points_data),
                "statistics": {
                    "average": average,
                    "min": min_value,
                    "max": max_value,
                    "latest": values[-1] if values else None
                },
                "duration_minutes": duration_minutes
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting metric history for {metric_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metric history: {str(e)}")


@router.get("/health")
async def get_health_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    시스템 헬스 체크
    
    Returns:
        시스템 전반적인 건강 상태
    """
    try:
        monitor = get_performance_monitor()
        collector = monitor.collector
        
        # 주요 메트릭 확인
        cpu_usage = collector.get_latest("system.cpu_percent")
        memory_usage = collector.get_latest("system.memory_percent")
        active_executions = collector.get_latest("orchestration.active_executions")
        success_rate = collector.get_latest("orchestration.success_rate")
        
        # 헬스 상태 계산
        health_issues = []
        overall_status = "healthy"
        
        if cpu_usage and cpu_usage.value > 80:
            health_issues.append(f"High CPU usage: {cpu_usage.value:.1f}%")
            overall_status = "warning"
        
        if memory_usage and memory_usage.value > 85:
            health_issues.append(f"High memory usage: {memory_usage.value:.1f}%")
            overall_status = "warning"
        
        if success_rate and success_rate.value < 0.8:
            health_issues.append(f"Low success rate: {success_rate.value:.2%}")
            overall_status = "critical"
        
        if active_executions and active_executions.value > 50:
            health_issues.append(f"High number of active executions: {int(active_executions.value)}")
            if overall_status == "healthy":
                overall_status = "warning"
        
        # 활성 알림 확인
        active_alerts = monitor.alert_manager.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.level.value == "critical"]
        
        if critical_alerts:
            overall_status = "critical"
            health_issues.extend([f"Critical alert: {a.title}" for a in critical_alerts])
        
        return {
            "success": True,
            "data": {
                "overall_status": overall_status,
                "health_issues": health_issues,
                "active_alerts_count": len(active_alerts),
                "critical_alerts_count": len(critical_alerts),
                "current_metrics": {
                    "cpu_percent": cpu_usage.value if cpu_usage else 0,
                    "memory_percent": memory_usage.value if memory_usage else 0,
                    "active_executions": int(active_executions.value) if active_executions else 0,
                    "success_rate": success_rate.value if success_rate else 0
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        return {
            "success": False,
            "data": {
                "overall_status": "unknown",
                "health_issues": [f"Health check failed: {str(e)}"],
                "error": str(e)
            },
            "timestamp": datetime.now().isoformat()
        }


@router.post("/alerts/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    알림 확인 처리
    
    Args:
        alert_id: 알림 ID
        current_user: 현재 사용자
    
    Returns:
        처리 결과
    """
    try:
        monitor = get_performance_monitor()
        alert_manager = monitor.alert_manager
        
        if alert_id in alert_manager.alerts:
            alert = alert_manager.alerts[alert_id]
            if not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now().timestamp()
                
                logger.info(f"Alert {alert_id} acknowledged by user {current_user.id}")
                
                return {
                    "success": True,
                    "message": f"Alert {alert_id} has been acknowledged",
                    "alert": {
                        "id": alert.id,
                        "title": alert.title,
                        "resolved_at": alert.resolved_at
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Alert {alert_id} is already resolved"
                }
        else:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@router.get("/performance/summary")
async def get_performance_summary(
    duration_hours: int = Query(24, ge=1, le=168, description="요약 기간 (시간)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    성능 요약 정보 조회
    
    Args:
        duration_hours: 요약할 기간 (시간 단위)
        current_user: 현재 사용자
    
    Returns:
        성능 요약 정보
    """
    try:
        monitor = get_performance_monitor()
        collector = monitor.collector
        
        duration_seconds = duration_hours * 3600
        
        # 주요 메트릭의 평균값 계산
        avg_cpu = collector.get_average("system.cpu_percent", duration_seconds)
        avg_memory = collector.get_average("system.memory_percent", duration_seconds)
        avg_execution_time = collector.get_average("orchestration.average_execution_time", duration_seconds)
        avg_cache_hit_rate = collector.get_average("orchestration.cache_hit_rate", duration_seconds)
        
        # 현재 오케스트레이션 메트릭
        current_orchestration = monitor.orchestration_monitor.get_current_metrics()
        
        # 성능 등급 계산
        performance_grade = "A"
        if avg_cpu and avg_cpu > 70:
            performance_grade = "B"
        if avg_memory and avg_memory > 80:
            performance_grade = "C"
        if avg_execution_time and avg_execution_time > 5:
            performance_grade = "C"
        if current_orchestration.successful_executions / max(current_orchestration.total_executions, 1) < 0.9:
            performance_grade = "D"
        
        return {
            "success": True,
            "data": {
                "performance_grade": performance_grade,
                "duration_hours": duration_hours,
                "averages": {
                    "cpu_percent": avg_cpu,
                    "memory_percent": avg_memory,
                    "execution_time_seconds": avg_execution_time,
                    "cache_hit_rate": avg_cache_hit_rate
                },
                "totals": {
                    "executions": current_orchestration.total_executions,
                    "successful_executions": current_orchestration.successful_executions,
                    "failed_executions": current_orchestration.failed_executions,
                    "security_validations": current_orchestration.security_validations
                },
                "recommendations": [
                    "시스템 성능이 양호합니다" if performance_grade == "A" else
                    "CPU 사용률을 모니터링하세요" if avg_cpu and avg_cpu > 70 else
                    "메모리 사용률을 확인하세요" if avg_memory and avg_memory > 80 else
                    "실행 시간 최적화를 고려하세요"
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")