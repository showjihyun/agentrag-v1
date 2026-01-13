"""
Plugin Monitoring API Endpoints
플러그인 모니터링 및 로그 관리를 위한 API 엔드포인트
"""
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging
import json
import csv
import io
from datetime import datetime, timedelta

from backend.core.dependencies import get_current_user
from backend.models.user import User
from backend.services.plugins.plugin_integration_service import get_plugin_integration_service
from backend.core.monitoring.enhanced_plugin_monitor import enhanced_plugin_monitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/plugins", tags=["Plugin Monitoring"])


# Response Models
class PluginMetric(BaseModel):
    """플러그인 메트릭"""
    name: str
    value: float
    unit: str
    trend: str = Field(..., regex=r'^(up|down|stable)$')
    trend_value: float
    status: str = Field(..., regex=r'^(good|warning|critical)$')
    timestamp: str


class PluginExecution(BaseModel):
    """플러그인 실행 기록"""
    id: str
    timestamp: str
    duration: float
    status: str = Field(..., regex=r'^(success|error|timeout)$')
    input_size: int
    output_size: int
    memory_usage: float
    cpu_usage: float
    error_message: Optional[str] = None
    trace_id: Optional[str] = None


class PluginAlert(BaseModel):
    """플러그인 알림"""
    id: str
    severity: str = Field(..., regex=r'^(info|warning|error|critical)$')
    title: str
    message: str
    timestamp: str
    acknowledged: bool
    rule_id: str


class PluginLogEntry(BaseModel):
    """플러그인 로그 엔트리"""
    id: str
    timestamp: str
    level: str = Field(..., regex=r'^(debug|info|warning|error|trace)$')
    message: str
    context: Optional[Dict[str, Any]] = None
    execution_id: Optional[str] = None
    source: Optional[str] = None
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


# API Endpoints

@router.get("/{plugin_id}/metrics")
async def get_plugin_metrics(
    plugin_id: str,
    time_range: str = Query("24h", regex=r'^(1h|6h|24h|7d|30d)$'),
    current_user: User = Depends(get_current_user)
) -> List[PluginMetric]:
    """플러그인 메트릭 조회"""
    try:
        integration_service = await get_plugin_integration_service()
        
        # 시간 범위 계산
        end_time = datetime.utcnow()
        if time_range == "1h":
            start_time = end_time - timedelta(hours=1)
        elif time_range == "6h":
            start_time = end_time - timedelta(hours=6)
        elif time_range == "24h":
            start_time = end_time - timedelta(days=1)
        elif time_range == "7d":
            start_time = end_time - timedelta(days=7)
        elif time_range == "30d":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=1)
        
        # 메트릭 조회
        metrics_data = await enhanced_plugin_monitor.get_plugin_metrics(
            plugin_id=plugin_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return [
            PluginMetric(
                name=metric["name"],
                value=metric["value"],
                unit=metric["unit"],
                trend=metric["trend"],
                trend_value=metric["trend_value"],
                status=metric["status"],
                timestamp=metric["timestamp"]
            )
            for metric in metrics_data
        ]
        
    except Exception as e:
        logger.error(f"Failed to get metrics for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get plugin metrics")


@router.get("/{plugin_id}/executions")
async def get_plugin_executions(
    plugin_id: str,
    time_range: str = Query("24h", regex=r'^(1h|6h|24h|7d|30d)$'),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
) -> List[PluginExecution]:
    """플러그인 실행 기록 조회"""
    try:
        integration_service = await get_plugin_integration_service()
        
        # 시간 범위 계산
        end_time = datetime.utcnow()
        if time_range == "1h":
            start_time = end_time - timedelta(hours=1)
        elif time_range == "6h":
            start_time = end_time - timedelta(hours=6)
        elif time_range == "24h":
            start_time = end_time - timedelta(days=1)
        elif time_range == "7d":
            start_time = end_time - timedelta(days=7)
        elif time_range == "30d":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=1)
        
        # 실행 기록 조회
        executions_data = await enhanced_plugin_monitor.get_plugin_executions(
            plugin_id=plugin_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return [
            PluginExecution(
                id=execution["id"],
                timestamp=execution["timestamp"],
                duration=execution["duration"],
                status=execution["status"],
                input_size=execution["input_size"],
                output_size=execution["output_size"],
                memory_usage=execution["memory_usage"],
                cpu_usage=execution["cpu_usage"],
                error_message=execution.get("error_message"),
                trace_id=execution.get("trace_id")
            )
            for execution in executions_data
        ]
        
    except Exception as e:
        logger.error(f"Failed to get executions for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get plugin executions")


@router.get("/{plugin_id}/alerts")
async def get_plugin_alerts(
    plugin_id: str,
    time_range: str = Query("24h", regex=r'^(1h|6h|24h|7d|30d)$'),
    acknowledged: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user)
) -> List[PluginAlert]:
    """플러그인 알림 조회"""
    try:
        integration_service = await get_plugin_integration_service()
        
        # 시간 범위 계산
        end_time = datetime.utcnow()
        if time_range == "1h":
            start_time = end_time - timedelta(hours=1)
        elif time_range == "6h":
            start_time = end_time - timedelta(hours=6)
        elif time_range == "24h":
            start_time = end_time - timedelta(days=1)
        elif time_range == "7d":
            start_time = end_time - timedelta(days=7)
        elif time_range == "30d":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=1)
        
        # 알림 조회
        alerts_data = await enhanced_plugin_monitor.get_plugin_alerts(
            plugin_id=plugin_id,
            start_time=start_time,
            end_time=end_time,
            acknowledged=acknowledged
        )
        
        return [
            PluginAlert(
                id=alert["id"],
                severity=alert["severity"],
                title=alert["title"],
                message=alert["message"],
                timestamp=alert["timestamp"],
                acknowledged=alert["acknowledged"],
                rule_id=alert["rule_id"]
            )
            for alert in alerts_data
        ]
        
    except Exception as e:
        logger.error(f"Failed to get alerts for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get plugin alerts")


@router.post("/{plugin_id}/alerts/{alert_id}/acknowledge")
async def acknowledge_plugin_alert(
    plugin_id: str,
    alert_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """플러그인 알림 확인"""
    try:
        integration_service = await get_plugin_integration_service()
        
        success = await enhanced_plugin_monitor.acknowledge_alert(
            alert_id=alert_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"message": "Alert acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to acknowledge alert")


@router.get("/{plugin_id}/logs")
async def get_plugin_logs(
    plugin_id: str,
    time_range: str = Query("1h", regex=r'^(15m|1h|6h|24h|7d)$'),
    level: Optional[str] = Query(None, regex=r'^(debug|info|warning|error|trace)$'),
    execution_id: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=10000),
    current_user: User = Depends(get_current_user)
) -> List[PluginLogEntry]:
    """플러그인 로그 조회"""
    try:
        integration_service = await get_plugin_integration_service()
        
        # 시간 범위 계산
        if start_time and end_time:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end_dt = datetime.utcnow()
            if time_range == "15m":
                start_dt = end_dt - timedelta(minutes=15)
            elif time_range == "1h":
                start_dt = end_dt - timedelta(hours=1)
            elif time_range == "6h":
                start_dt = end_dt - timedelta(hours=6)
            elif time_range == "24h":
                start_dt = end_dt - timedelta(days=1)
            elif time_range == "7d":
                start_dt = end_dt - timedelta(days=7)
            else:
                start_dt = end_dt - timedelta(hours=1)
        
        # 로그 조회
        logs_data = await enhanced_plugin_monitor.get_plugin_logs(
            plugin_id=plugin_id,
            start_time=start_dt,
            end_time=end_dt,
            level=level,
            execution_id=execution_id,
            source=source,
            user_id=user_id,
            limit=limit
        )
        
        return [
            PluginLogEntry(
                id=log["id"],
                timestamp=log["timestamp"],
                level=log["level"],
                message=log["message"],
                context=log.get("context"),
                execution_id=log.get("execution_id"),
                source=log.get("source"),
                stack_trace=log.get("stack_trace"),
                user_id=log.get("user_id"),
                session_id=log.get("session_id")
            )
            for log in logs_data
        ]
        
    except Exception as e:
        logger.error(f"Failed to get logs for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get plugin logs")


@router.get("/{plugin_id}/logs/export")
async def export_plugin_logs(
    plugin_id: str,
    format: str = Query("csv", regex=r'^(csv|json|txt)$'),
    time_range: str = Query("24h", regex=r'^(1h|6h|24h|7d|30d)$'),
    level: Optional[str] = Query(None, regex=r'^(debug|info|warning|error|trace)$'),
    execution_id: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """플러그인 로그 내보내기"""
    try:
        integration_service = await get_plugin_integration_service()
        
        # 시간 범위 계산
        end_time = datetime.utcnow()
        if time_range == "1h":
            start_time = end_time - timedelta(hours=1)
        elif time_range == "6h":
            start_time = end_time - timedelta(hours=6)
        elif time_range == "24h":
            start_time = end_time - timedelta(days=1)
        elif time_range == "7d":
            start_time = end_time - timedelta(days=7)
        elif time_range == "30d":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=1)
        
        # 로그 조회 (제한 없음)
        logs_data = await enhanced_plugin_monitor.get_plugin_logs(
            plugin_id=plugin_id,
            start_time=start_time,
            end_time=end_time,
            level=level,
            execution_id=execution_id,
            source=source,
            user_id=user_id,
            limit=None  # 모든 로그
        )
        
        # 형식에 따른 내보내기
        if format == "csv":
            return export_logs_as_csv(logs_data, plugin_id)
        elif format == "json":
            return export_logs_as_json(logs_data, plugin_id)
        elif format == "txt":
            return export_logs_as_txt(logs_data, plugin_id)
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export logs for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export plugin logs")


@router.get("/{plugin_id}/export/{data_type}")
async def export_plugin_data(
    plugin_id: str,
    data_type: str = Field(..., regex=r'^(metrics|executions|logs)$'),
    time_range: str = Query("24h", regex=r'^(1h|6h|24h|7d|30d)$'),
    current_user: User = Depends(get_current_user)
):
    """플러그인 데이터 내보내기 (CSV 형식)"""
    try:
        integration_service = await get_plugin_integration_service()
        
        # 시간 범위 계산
        end_time = datetime.utcnow()
        if time_range == "1h":
            start_time = end_time - timedelta(hours=1)
        elif time_range == "6h":
            start_time = end_time - timedelta(hours=6)
        elif time_range == "24h":
            start_time = end_time - timedelta(days=1)
        elif time_range == "7d":
            start_time = end_time - timedelta(days=7)
        elif time_range == "30d":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=1)
        
        if data_type == "metrics":
            data = await enhanced_plugin_monitor.get_plugin_metrics(
                plugin_id=plugin_id,
                start_time=start_time,
                end_time=end_time
            )
            return export_metrics_as_csv(data, plugin_id)
        
        elif data_type == "executions":
            data = await enhanced_plugin_monitor.get_plugin_executions(
                plugin_id=plugin_id,
                start_time=start_time,
                end_time=end_time,
                limit=None
            )
            return export_executions_as_csv(data, plugin_id)
        
        elif data_type == "logs":
            data = await enhanced_plugin_monitor.get_plugin_logs(
                plugin_id=plugin_id,
                start_time=start_time,
                end_time=end_time,
                limit=None
            )
            return export_logs_as_csv(data, plugin_id)
        
        else:
            raise HTTPException(status_code=400, detail="Invalid data type")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export {data_type} for plugin {plugin_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export plugin {data_type}")


# Helper Functions

def export_logs_as_csv(logs_data: List[Dict[str, Any]], plugin_id: str) -> StreamingResponse:
    """로그를 CSV 형식으로 내보내기"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 헤더
    writer.writerow([
        'timestamp', 'level', 'message', 'execution_id', 'source', 'user_id'
    ])
    
    # 데이터
    for log in logs_data:
        writer.writerow([
            log.get('timestamp', ''),
            log.get('level', ''),
            log.get('message', ''),
            log.get('execution_id', ''),
            log.get('source', ''),
            log.get('user_id', '')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename=plugin-{plugin_id}-logs.csv'}
    )


def export_logs_as_json(logs_data: List[Dict[str, Any]], plugin_id: str) -> StreamingResponse:
    """로그를 JSON 형식으로 내보내기"""
    json_data = json.dumps(logs_data, indent=2, ensure_ascii=False)
    
    return StreamingResponse(
        io.BytesIO(json_data.encode('utf-8')),
        media_type='application/json',
        headers={'Content-Disposition': f'attachment; filename=plugin-{plugin_id}-logs.json'}
    )


def export_logs_as_txt(logs_data: List[Dict[str, Any]], plugin_id: str) -> StreamingResponse:
    """로그를 텍스트 형식으로 내보내기"""
    output = io.StringIO()
    
    for log in logs_data:
        timestamp = log.get('timestamp', '')
        level = log.get('level', '').upper()
        message = log.get('message', '')
        execution_id = log.get('execution_id', '')
        
        line = f"[{timestamp}] {level}: {message}"
        if execution_id:
            line += f" (execution: {execution_id})"
        
        output.write(line + '\n')
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/plain',
        headers={'Content-Disposition': f'attachment; filename=plugin-{plugin_id}-logs.txt'}
    )


def export_metrics_as_csv(metrics_data: List[Dict[str, Any]], plugin_id: str) -> StreamingResponse:
    """메트릭을 CSV 형식으로 내보내기"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 헤더
    writer.writerow([
        'timestamp', 'name', 'value', 'unit', 'trend', 'trend_value', 'status'
    ])
    
    # 데이터
    for metric in metrics_data:
        writer.writerow([
            metric.get('timestamp', ''),
            metric.get('name', ''),
            metric.get('value', ''),
            metric.get('unit', ''),
            metric.get('trend', ''),
            metric.get('trend_value', ''),
            metric.get('status', '')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename=plugin-{plugin_id}-metrics.csv'}
    )


def export_executions_as_csv(executions_data: List[Dict[str, Any]], plugin_id: str) -> StreamingResponse:
    """실행 기록을 CSV 형식으로 내보내기"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 헤더
    writer.writerow([
        'timestamp', 'duration', 'status', 'input_size', 'output_size', 
        'memory_usage', 'cpu_usage', 'error_message', 'trace_id'
    ])
    
    # 데이터
    for execution in executions_data:
        writer.writerow([
            execution.get('timestamp', ''),
            execution.get('duration', ''),
            execution.get('status', ''),
            execution.get('input_size', ''),
            execution.get('output_size', ''),
            execution.get('memory_usage', ''),
            execution.get('cpu_usage', ''),
            execution.get('error_message', ''),
            execution.get('trace_id', '')
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename=plugin-{plugin_id}-executions.csv'}
    )