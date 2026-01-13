"""
Error Reporting API
에러 리포팅 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.core.auth_dependencies import get_current_user
from backend.core.error_handling.error_reporter import (
    get_error_reporter, ErrorReporter, ErrorTrend, generate_error_report
)
from backend.db.models.user import User
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/monitoring/errors", tags=["error-monitoring"])


@router.get("/statistics")
async def get_error_statistics(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    에러 통계 조회
    
    Returns:
        전체 에러 통계 정보
    """
    try:
        reporter = get_error_reporter()
        statistics = reporter.get_error_statistics()
        
        return {
            "success": True,
            "data": statistics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting error statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error statistics: {str(e)}")


@router.get("/patterns")
async def get_error_patterns(
    trend: Optional[str] = Query(None, description="트렌드 필터 (increasing, decreasing, stable, spike)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    에러 패턴 조회
    
    Args:
        trend: 트렌드별 필터링
        current_user: 현재 사용자
    
    Returns:
        에러 패턴 목록
    """
    try:
        reporter = get_error_reporter()
        
        # 트렌드 필터링
        if trend:
            try:
                trend_enum = ErrorTrend(trend)
                patterns = reporter.analyzer.get_patterns_by_trend(trend_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid trend value: {trend}")
        else:
            patterns = list(reporter.analyzer.pattern_cache.values())
        
        # 패턴 데이터 변환
        patterns_data = []
        for pattern in patterns:
            patterns_data.append({
                "pattern_id": pattern.pattern_id,
                "error_code": pattern.error_code,
                "frequency": pattern.frequency,
                "first_seen": pattern.first_seen.isoformat(),
                "last_seen": pattern.last_seen.isoformat(),
                "affected_users_count": len(pattern.affected_users),
                "common_contexts": pattern.common_contexts,
                "trend": pattern.trend.value,
                "severity_distribution": pattern.severity_distribution,
                "duration_hours": (pattern.last_seen - pattern.first_seen).total_seconds() / 3600
            })
        
        return {
            "success": True,
            "data": {
                "patterns": patterns_data,
                "total_count": len(patterns_data),
                "trend_filter": trend
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting error patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error patterns: {str(e)}")


@router.get("/patterns/{pattern_id}")
async def get_error_pattern_details(
    pattern_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    특정 에러 패턴 상세 정보 조회
    
    Args:
        pattern_id: 패턴 ID
        current_user: 현재 사용자
    
    Returns:
        에러 패턴 상세 정보
    """
    try:
        reporter = get_error_reporter()
        pattern = reporter.analyzer.get_pattern_by_id(pattern_id)
        
        if not pattern:
            raise HTTPException(status_code=404, detail=f"Pattern {pattern_id} not found")
        
        # 관련 에러들 조회
        related_errors = [
            error for error in reporter.analyzer.error_history
            if error.code.value == pattern.error_code
        ]
        
        # 최근 에러들만 (최대 50개)
        recent_errors = sorted(related_errors, key=lambda x: x.timestamp, reverse=True)[:50]
        
        errors_data = []
        for error in recent_errors:
            errors_data.append({
                "timestamp": error.timestamp,
                "message": error.message,
                "severity": error.severity.value,
                "category": error.category.value,
                "context": {
                    "user_id": error.context.user_id,
                    "execution_id": error.context.execution_id,
                    "pattern_type": error.context.pattern_type,
                    "step": error.context.step
                },
                "suggestions": error.suggestions,
                "recovery_actions": error.recovery_actions
            })
        
        return {
            "success": True,
            "data": {
                "pattern": {
                    "pattern_id": pattern.pattern_id,
                    "error_code": pattern.error_code,
                    "frequency": pattern.frequency,
                    "first_seen": pattern.first_seen.isoformat(),
                    "last_seen": pattern.last_seen.isoformat(),
                    "affected_users": pattern.affected_users,
                    "common_contexts": pattern.common_contexts,
                    "trend": pattern.trend.value,
                    "severity_distribution": pattern.severity_distribution
                },
                "recent_errors": errors_data,
                "total_related_errors": len(related_errors)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pattern details for {pattern_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pattern details: {str(e)}")


@router.post("/reports/generate")
async def generate_manual_error_report(
    period_hours: int = Query(24, ge=1, le=168, description="리포트 기간 (시간)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    수동 에러 리포트 생성
    
    Args:
        period_hours: 리포트 생성 기간 (시간 단위)
        current_user: 현재 사용자
    
    Returns:
        생성된 에러 리포트
    """
    try:
        report = generate_error_report(period_hours)
        
        # 리포트 데이터 변환
        report_data = {
            "report_id": report.report_id,
            "period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat(),
                "hours": period_hours
            },
            "summary": {
                "total_errors": report.total_errors,
                "error_rate": report.error_rate,
                "severity_breakdown": report.severity_breakdown,
                "category_breakdown": report.category_breakdown
            },
            "top_errors": report.top_errors,
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "error_code": p.error_code,
                    "frequency": p.frequency,
                    "trend": p.trend.value,
                    "affected_users_count": len(p.affected_users)
                }
                for p in report.error_patterns
            ],
            "user_impact": report.user_impact,
            "recommendations": report.recommendations,
            "generated_at": report.generated_at.isoformat()
        }
        
        logger.info(f"Manual error report generated by user {current_user.id}: {report.report_id}")
        
        return {
            "success": True,
            "data": report_data,
            "message": f"Error report generated successfully for {period_hours} hours period"
        }
        
    except Exception as e:
        logger.error(f"Error generating manual report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate error report: {str(e)}")


@router.get("/reports")
async def get_error_reports(
    limit: int = Query(10, ge=1, le=50, description="조회할 리포트 수"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    에러 리포트 목록 조회
    
    Args:
        limit: 조회할 리포트 수
        current_user: 현재 사용자
    
    Returns:
        에러 리포트 목록
    """
    try:
        reporter = get_error_reporter()
        reports = reporter.get_reports(limit)
        
        reports_data = []
        for report in reports:
            reports_data.append({
                "report_id": report.report_id,
                "period_start": report.period_start.isoformat(),
                "period_end": report.period_end.isoformat(),
                "total_errors": report.total_errors,
                "error_rate": report.error_rate,
                "patterns_count": len(report.error_patterns),
                "critical_errors": report.severity_breakdown.get("critical", 0),
                "generated_at": report.generated_at.isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "reports": reports_data,
                "total_count": len(reports_data)
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting error reports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error reports: {str(e)}")


@router.get("/reports/{report_id}")
async def get_error_report_details(
    report_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    특정 에러 리포트 상세 정보 조회
    
    Args:
        report_id: 리포트 ID
        current_user: 현재 사용자
    
    Returns:
        에러 리포트 상세 정보
    """
    try:
        reporter = get_error_reporter()
        
        # 리포트 찾기
        report = None
        for r in reporter.report_history:
            if r.report_id == report_id:
                report = r
                break
        
        if not report:
            raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
        
        # 상세 리포트 데이터
        report_data = {
            "report_id": report.report_id,
            "period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat(),
                "duration_hours": (report.period_end - report.period_start).total_seconds() / 3600
            },
            "summary": {
                "total_errors": report.total_errors,
                "error_rate": report.error_rate,
                "severity_breakdown": report.severity_breakdown,
                "category_breakdown": report.category_breakdown
            },
            "top_errors": report.top_errors,
            "error_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "error_code": p.error_code,
                    "frequency": p.frequency,
                    "first_seen": p.first_seen.isoformat(),
                    "last_seen": p.last_seen.isoformat(),
                    "affected_users_count": len(p.affected_users),
                    "common_contexts": p.common_contexts,
                    "trend": p.trend.value,
                    "severity_distribution": p.severity_distribution
                }
                for p in report.error_patterns
            ],
            "user_impact": report.user_impact,
            "recommendations": report.recommendations,
            "generated_at": report.generated_at.isoformat()
        }
        
        return {
            "success": True,
            "data": report_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report details for {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get report details: {str(e)}")


@router.get("/trends")
async def get_error_trends(
    period_hours: int = Query(168, ge=24, le=720, description="분석 기간 (시간)"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    에러 트렌드 분석
    
    Args:
        period_hours: 분석 기간 (시간 단위)
        current_user: 현재 사용자
    
    Returns:
        에러 트렌드 분석 결과
    """
    try:
        reporter = get_error_reporter()
        
        # 기간 내 에러 필터링
        cutoff_time = datetime.now() - timedelta(hours=period_hours)
        period_errors = [
            error for error in reporter.analyzer.error_history
            if datetime.fromisoformat(error.timestamp) > cutoff_time
        ]
        
        # 시간대별 에러 수 계산 (1시간 단위)
        hourly_errors = {}
        for error in period_errors:
            error_time = datetime.fromisoformat(error.timestamp)
            hour_key = error_time.replace(minute=0, second=0, microsecond=0)
            hourly_errors[hour_key] = hourly_errors.get(hour_key, 0) + 1
        
        # 시계열 데이터 생성
        timeline_data = []
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        for i in range(period_hours):
            hour = current_hour - timedelta(hours=i)
            timeline_data.append({
                "timestamp": hour.isoformat(),
                "error_count": hourly_errors.get(hour, 0)
            })
        
        timeline_data.reverse()  # 시간순 정렬
        
        # 트렌드별 패턴 수
        trend_summary = {}
        for trend in ErrorTrend:
            patterns = reporter.analyzer.get_patterns_by_trend(trend)
            trend_summary[trend.value] = {
                "count": len(patterns),
                "patterns": [
                    {
                        "pattern_id": p.pattern_id,
                        "error_code": p.error_code,
                        "frequency": p.frequency
                    }
                    for p in patterns[:5]  # 상위 5개만
                ]
            }
        
        # 에러 코드별 트렌드
        error_code_trends = {}
        for error in period_errors:
            code = error.code.value
            if code not in error_code_trends:
                error_code_trends[code] = []
            
            error_time = datetime.fromisoformat(error.timestamp)
            error_code_trends[code].append(error_time)
        
        # 각 에러 코드의 트렌드 계산
        code_trend_analysis = {}
        for code, timestamps in error_code_trends.items():
            if len(timestamps) < 2:
                continue
            
            # 최근 절반과 이전 절반 비교
            mid_point = len(timestamps) // 2
            recent_count = len(timestamps[mid_point:])
            previous_count = len(timestamps[:mid_point])
            
            if previous_count > 0:
                trend_ratio = recent_count / previous_count
                if trend_ratio > 1.5:
                    trend_direction = "increasing"
                elif trend_ratio < 0.5:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "new"
            
            code_trend_analysis[code] = {
                "total_count": len(timestamps),
                "recent_count": recent_count,
                "previous_count": previous_count,
                "trend_direction": trend_direction,
                "trend_ratio": trend_ratio if previous_count > 0 else None
            }
        
        return {
            "success": True,
            "data": {
                "period_hours": period_hours,
                "total_errors": len(period_errors),
                "timeline": timeline_data,
                "trend_summary": trend_summary,
                "error_code_trends": code_trend_analysis,
                "analysis_timestamp": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting error trends: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error trends: {str(e)}")


@router.get("/health")
async def get_error_health_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    에러 기반 시스템 건강 상태 조회
    
    Returns:
        에러 기반 시스템 건강 상태
    """
    try:
        reporter = get_error_reporter()
        
        # 최근 24시간 에러 분석
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_errors = [
            error for error in reporter.analyzer.error_history
            if datetime.fromisoformat(error.timestamp) > recent_cutoff
        ]
        
        # 건강 상태 계산
        health_score = 100  # 시작점
        health_issues = []
        
        # 에러 수 기반 점수 차감
        if len(recent_errors) > 100:
            health_score -= 30
            health_issues.append(f"High error count: {len(recent_errors)} errors in 24h")
        elif len(recent_errors) > 50:
            health_score -= 15
            health_issues.append(f"Moderate error count: {len(recent_errors)} errors in 24h")
        
        # 치명적 에러 확인
        critical_errors = [e for e in recent_errors if e.severity.value == "critical"]
        if critical_errors:
            health_score -= 40
            health_issues.append(f"Critical errors detected: {len(critical_errors)}")
        
        # 증가 트렌드 패턴 확인
        increasing_patterns = reporter.analyzer.get_patterns_by_trend(ErrorTrend.INCREASING)
        spike_patterns = reporter.analyzer.get_patterns_by_trend(ErrorTrend.SPIKE)
        
        if spike_patterns:
            health_score -= 25
            health_issues.append(f"Error spikes detected: {len(spike_patterns)} patterns")
        elif increasing_patterns:
            health_score -= 10
            health_issues.append(f"Increasing error trends: {len(increasing_patterns)} patterns")
        
        # 건강 상태 등급
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 75:
            health_status = "good"
        elif health_score >= 60:
            health_status = "fair"
        elif health_score >= 40:
            health_status = "poor"
        else:
            health_status = "critical"
        
        return {
            "success": True,
            "data": {
                "health_status": health_status,
                "health_score": max(0, health_score),
                "health_issues": health_issues,
                "recent_24h_summary": {
                    "total_errors": len(recent_errors),
                    "critical_errors": len(critical_errors),
                    "error_rate": len(recent_errors) / 24,  # errors per hour
                    "unique_error_codes": len(set([e.code.value for e in recent_errors]))
                },
                "pattern_summary": {
                    "increasing_trends": len(increasing_patterns),
                    "spike_patterns": len(spike_patterns),
                    "stable_patterns": len(reporter.analyzer.get_patterns_by_trend(ErrorTrend.STABLE)),
                    "decreasing_patterns": len(reporter.analyzer.get_patterns_by_trend(ErrorTrend.DECREASING))
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting error health status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get error health status: {str(e)}")