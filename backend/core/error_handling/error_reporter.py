"""
Error Reporting and Analytics System
에러 리포팅 및 분석 시스템
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
from enum import Enum
import hashlib

from backend.core.error_handling.orchestration_errors import (
    ErrorDetail, ErrorSeverity, ErrorCategory, ErrorCode, get_error_handler
)
from backend.core.structured_logging import get_logger
from backend.core.monitoring.performance_monitor import get_performance_monitor

logger = get_logger(__name__)


class ErrorTrend(Enum):
    """에러 트렌드"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    SPIKE = "spike"


@dataclass
class ErrorPattern:
    """에러 패턴"""
    pattern_id: str
    error_code: str
    frequency: int
    first_seen: datetime
    last_seen: datetime
    affected_users: List[str]
    common_contexts: Dict[str, Any]
    trend: ErrorTrend
    severity_distribution: Dict[str, int]


@dataclass
class ErrorReport:
    """에러 리포트"""
    report_id: str
    period_start: datetime
    period_end: datetime
    total_errors: int
    error_rate: float
    top_errors: List[Dict[str, Any]]
    error_patterns: List[ErrorPattern]
    severity_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    user_impact: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime


class ErrorAnalyzer:
    """에러 분석기"""
    
    def __init__(self):
        self.error_history: List[ErrorDetail] = []
        self.pattern_cache: Dict[str, ErrorPattern] = {}
        self.analysis_callbacks: List[Callable[[ErrorReport], None]] = []
    
    def add_error(self, error_detail: ErrorDetail):
        """에러 추가"""
        self.error_history.append(error_detail)
        
        # 오래된 에러 정리 (7일 이상)
        cutoff_time = datetime.now() - timedelta(days=7)
        self.error_history = [
            error for error in self.error_history 
            if datetime.fromisoformat(error.timestamp) > cutoff_time
        ]
        
        # 패턴 업데이트
        self._update_patterns()
    
    def _update_patterns(self):
        """에러 패턴 업데이트"""
        # 에러 코드별 그룹화
        error_groups = defaultdict(list)
        for error in self.error_history:
            error_groups[error.code.value].append(error)
        
        # 패턴 분석
        for error_code, errors in error_groups.items():
            if len(errors) < 3:  # 최소 3개 이상의 에러가 있어야 패턴으로 인식
                continue
            
            pattern_id = self._generate_pattern_id(error_code, errors)
            
            # 시간순 정렬
            errors.sort(key=lambda x: x.timestamp)
            
            # 사용자 추출
            affected_users = list(set([
                error.context.user_id for error in errors 
                if error.context.user_id
            ]))
            
            # 공통 컨텍스트 추출
            common_contexts = self._extract_common_contexts(errors)
            
            # 트렌드 분석
            trend = self._analyze_trend(errors)
            
            # 심각도 분포
            severity_dist = Counter([error.severity.value for error in errors])
            
            pattern = ErrorPattern(
                pattern_id=pattern_id,
                error_code=error_code,
                frequency=len(errors),
                first_seen=datetime.fromisoformat(errors[0].timestamp),
                last_seen=datetime.fromisoformat(errors[-1].timestamp),
                affected_users=affected_users,
                common_contexts=common_contexts,
                trend=trend,
                severity_distribution=dict(severity_dist)
            )
            
            self.pattern_cache[pattern_id] = pattern
    
    def _generate_pattern_id(self, error_code: str, errors: List[ErrorDetail]) -> str:
        """패턴 ID 생성"""
        # 에러 코드와 공통 컨텍스트를 기반으로 해시 생성
        context_keys = set()
        for error in errors:
            if error.context.pattern_type:
                context_keys.add(f"pattern:{error.context.pattern_type}")
            if error.context.step:
                context_keys.add(f"step:{error.context.step}")
        
        pattern_string = f"{error_code}:{':'.join(sorted(context_keys))}"
        return hashlib.md5(pattern_string.encode()).hexdigest()[:8]
    
    def _extract_common_contexts(self, errors: List[ErrorDetail]) -> Dict[str, Any]:
        """공통 컨텍스트 추출"""
        contexts = {}
        
        # 패턴 타입
        pattern_types = [e.context.pattern_type for e in errors if e.context.pattern_type]
        if pattern_types:
            most_common_pattern = Counter(pattern_types).most_common(1)[0]
            if most_common_pattern[1] / len(errors) > 0.5:  # 50% 이상
                contexts['pattern_type'] = most_common_pattern[0]
        
        # 실행 단계
        steps = [e.context.step for e in errors if e.context.step]
        if steps:
            most_common_step = Counter(steps).most_common(1)[0]
            if most_common_step[1] / len(errors) > 0.5:
                contexts['step'] = most_common_step[0]
        
        return contexts
    
    def _analyze_trend(self, errors: List[ErrorDetail]) -> ErrorTrend:
        """트렌드 분석"""
        if len(errors) < 5:
            return ErrorTrend.STABLE
        
        # 최근 24시간과 이전 24시간 비교
        now = datetime.now()
        recent_cutoff = now - timedelta(hours=24)
        previous_cutoff = now - timedelta(hours=48)
        
        recent_errors = [
            e for e in errors 
            if datetime.fromisoformat(e.timestamp) > recent_cutoff
        ]
        previous_errors = [
            e for e in errors 
            if previous_cutoff < datetime.fromisoformat(e.timestamp) <= recent_cutoff
        ]
        
        recent_count = len(recent_errors)
        previous_count = len(previous_errors)
        
        if previous_count == 0:
            return ErrorTrend.SPIKE if recent_count > 5 else ErrorTrend.STABLE
        
        ratio = recent_count / previous_count
        
        if ratio > 2.0:
            return ErrorTrend.SPIKE
        elif ratio > 1.2:
            return ErrorTrend.INCREASING
        elif ratio < 0.8:
            return ErrorTrend.DECREASING
        else:
            return ErrorTrend.STABLE
    
    def generate_report(self, period_hours: int = 24) -> ErrorReport:
        """에러 리포트 생성"""
        now = datetime.now()
        period_start = now - timedelta(hours=period_hours)
        
        # 기간 내 에러 필터링
        period_errors = [
            error for error in self.error_history
            if datetime.fromisoformat(error.timestamp) > period_start
        ]
        
        total_errors = len(period_errors)
        
        # 에러율 계산 (전체 실행 대비)
        monitor = get_performance_monitor()
        total_executions = monitor.orchestration_monitor.execution_count
        error_rate = total_errors / max(total_executions, 1)
        
        # 상위 에러 분석
        error_counter = Counter([error.code.value for error in period_errors])
        top_errors = [
            {
                "error_code": code,
                "count": count,
                "percentage": (count / total_errors) * 100 if total_errors > 0 else 0
            }
            for code, count in error_counter.most_common(10)
        ]
        
        # 심각도별 분류
        severity_breakdown = dict(Counter([error.severity.value for error in period_errors]))
        
        # 카테고리별 분류
        category_breakdown = dict(Counter([error.category.value for error in period_errors]))
        
        # 사용자 영향 분석
        affected_users = set([
            error.context.user_id for error in period_errors 
            if error.context.user_id
        ])
        
        user_impact = {
            "affected_users_count": len(affected_users),
            "errors_per_user": total_errors / len(affected_users) if affected_users else 0,
            "most_affected_patterns": dict(Counter([
                error.context.pattern_type for error in period_errors 
                if error.context.pattern_type
            ]).most_common(5))
        }
        
        # 현재 패턴 필터링 (기간 내)
        current_patterns = [
            pattern for pattern in self.pattern_cache.values()
            if pattern.last_seen > period_start
        ]
        
        # 권장사항 생성
        recommendations = self._generate_recommendations(
            period_errors, current_patterns, error_rate
        )
        
        report = ErrorReport(
            report_id=f"error_report_{now.strftime('%Y%m%d_%H%M%S')}",
            period_start=period_start,
            period_end=now,
            total_errors=total_errors,
            error_rate=error_rate,
            top_errors=top_errors,
            error_patterns=current_patterns,
            severity_breakdown=severity_breakdown,
            category_breakdown=category_breakdown,
            user_impact=user_impact,
            recommendations=recommendations,
            generated_at=now
        )
        
        # 콜백 실행
        for callback in self.analysis_callbacks:
            try:
                callback(report)
            except Exception as e:
                logger.error(f"Error in analysis callback: {e}")
        
        return report
    
    def _generate_recommendations(
        self, 
        errors: List[ErrorDetail], 
        patterns: List[ErrorPattern], 
        error_rate: float
    ) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        # 에러율 기반 권장사항
        if error_rate > 0.1:  # 10% 이상
            recommendations.append("에러율이 높습니다. 시스템 안정성을 점검하세요.")
        
        # 패턴 기반 권장사항
        for pattern in patterns:
            if pattern.trend == ErrorTrend.INCREASING:
                recommendations.append(
                    f"'{pattern.error_code}' 에러가 증가하고 있습니다. 원인을 조사하세요."
                )
            elif pattern.trend == ErrorTrend.SPIKE:
                recommendations.append(
                    f"'{pattern.error_code}' 에러가 급증했습니다. 즉시 대응이 필요합니다."
                )
        
        # 심각도 기반 권장사항
        critical_errors = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
        if critical_errors:
            recommendations.append(
                f"{len(critical_errors)}개의 치명적 에러가 발생했습니다. 우선적으로 해결하세요."
            )
        
        # 사용자 영향 기반 권장사항
        if len(set([e.context.user_id for e in errors if e.context.user_id])) > 10:
            recommendations.append("다수의 사용자가 영향을 받고 있습니다. 공지사항을 고려하세요.")
        
        # 기본 권장사항
        if not recommendations:
            recommendations.append("시스템이 안정적으로 운영되고 있습니다.")
        
        return recommendations
    
    def add_analysis_callback(self, callback: Callable[[ErrorReport], None]):
        """분석 콜백 추가"""
        self.analysis_callbacks.append(callback)
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[ErrorPattern]:
        """패턴 ID로 패턴 조회"""
        return self.pattern_cache.get(pattern_id)
    
    def get_patterns_by_trend(self, trend: ErrorTrend) -> List[ErrorPattern]:
        """트렌드별 패턴 조회"""
        return [p for p in self.pattern_cache.values() if p.trend == trend]


class ErrorReporter:
    """에러 리포터"""
    
    def __init__(self):
        self.analyzer = ErrorAnalyzer()
        self.report_history: List[ErrorReport] = []
        self.auto_report_enabled = False
        self.report_interval_hours = 24
        self._report_task: Optional[asyncio.Task] = None
        
        # 에러 핸들러와 연동
        error_handler = get_error_handler()
        self._setup_error_monitoring(error_handler)
    
    def _setup_error_monitoring(self, error_handler):
        """에러 모니터링 설정"""
        # 에러 핸들러의 에러 히스토리를 주기적으로 동기화
        original_handle_error = error_handler.handle_error
        
        def enhanced_handle_error(error, context=None, auto_recover=True):
            result = original_handle_error(error, context, auto_recover)
            # 분석기에 에러 추가
            self.analyzer.add_error(result)
            return result
        
        error_handler.handle_error = enhanced_handle_error
    
    async def start_auto_reporting(self, interval_hours: int = 24):
        """자동 리포팅 시작"""
        self.auto_report_enabled = True
        self.report_interval_hours = interval_hours
        
        if self._report_task is None or self._report_task.done():
            self._report_task = asyncio.create_task(self._auto_report_loop())
        
        logger.info(f"Auto error reporting started with {interval_hours}h interval")
    
    async def stop_auto_reporting(self):
        """자동 리포팅 중지"""
        self.auto_report_enabled = False
        
        if self._report_task and not self._report_task.done():
            self._report_task.cancel()
            try:
                await self._report_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Auto error reporting stopped")
    
    async def _auto_report_loop(self):
        """자동 리포팅 루프"""
        while self.auto_report_enabled:
            try:
                # 리포트 생성
                report = self.analyzer.generate_report(self.report_interval_hours)
                self.report_history.append(report)
                
                # 오래된 리포트 정리 (30일)
                cutoff_date = datetime.now() - timedelta(days=30)
                self.report_history = [
                    r for r in self.report_history 
                    if r.generated_at > cutoff_date
                ]
                
                logger.info(f"Auto error report generated: {report.report_id}")
                
                # 다음 리포트까지 대기
                await asyncio.sleep(self.report_interval_hours * 3600)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto report loop: {e}")
                await asyncio.sleep(3600)  # 1시간 후 재시도
    
    def generate_manual_report(self, period_hours: int = 24) -> ErrorReport:
        """수동 리포트 생성"""
        report = self.analyzer.generate_report(period_hours)
        self.report_history.append(report)
        
        logger.info(f"Manual error report generated: {report.report_id}")
        return report
    
    def get_latest_report(self) -> Optional[ErrorReport]:
        """최신 리포트 조회"""
        return self.report_history[-1] if self.report_history else None
    
    def get_reports(self, limit: int = 10) -> List[ErrorReport]:
        """리포트 목록 조회"""
        return sorted(self.report_history, key=lambda x: x.generated_at, reverse=True)[:limit]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """에러 통계 조회"""
        if not self.analyzer.error_history:
            return {"message": "No error data available"}
        
        total_errors = len(self.analyzer.error_history)
        
        # 최근 24시간 에러
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_errors = [
            e for e in self.analyzer.error_history
            if datetime.fromisoformat(e.timestamp) > recent_cutoff
        ]
        
        # 트렌드별 패턴 수
        trend_counts = Counter([p.trend.value for p in self.analyzer.pattern_cache.values()])
        
        return {
            "total_errors": total_errors,
            "recent_24h_errors": len(recent_errors),
            "total_patterns": len(self.analyzer.pattern_cache),
            "trend_distribution": dict(trend_counts),
            "most_common_errors": dict(Counter([
                e.code.value for e in self.analyzer.error_history
            ]).most_common(5)),
            "severity_distribution": dict(Counter([
                e.severity.value for e in self.analyzer.error_history
            ])),
            "category_distribution": dict(Counter([
                e.category.value for e in self.analyzer.error_history
            ]))
        }


# 전역 에러 리포터 인스턴스
_error_reporter_instance: Optional[ErrorReporter] = None


def get_error_reporter() -> ErrorReporter:
    """에러 리포터 인스턴스 조회"""
    global _error_reporter_instance
    
    if _error_reporter_instance is None:
        _error_reporter_instance = ErrorReporter()
    
    return _error_reporter_instance


# 편의 함수들
def generate_error_report(period_hours: int = 24) -> ErrorReport:
    """에러 리포트 생성"""
    reporter = get_error_reporter()
    return reporter.generate_manual_report(period_hours)


def get_error_patterns(trend: Optional[ErrorTrend] = None) -> List[ErrorPattern]:
    """에러 패턴 조회"""
    reporter = get_error_reporter()
    if trend:
        return reporter.analyzer.get_patterns_by_trend(trend)
    return list(reporter.analyzer.pattern_cache.values())


async def start_error_monitoring():
    """에러 모니터링 시작"""
    reporter = get_error_reporter()
    await reporter.start_auto_reporting()


async def stop_error_monitoring():
    """에러 모니터링 중지"""
    reporter = get_error_reporter()
    await reporter.stop_auto_reporting()