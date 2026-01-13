"""
Optimization Analytics Service

최적화 성과를 추적하고 분석하는 서비스
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json

from backend.core.event_bus.validated_event_bus import ValidatedEventBus


logger = logging.getLogger(__name__)


class AnalyticsMetric(str, Enum):
    """분석 메트릭 유형"""
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    COST_REDUCTION = "cost_reduction"
    RELIABILITY_IMPROVEMENT = "reliability_improvement"
    EXECUTION_TIME = "execution_time"
    SUCCESS_RATE = "success_rate"
    COST_PER_EXECUTION = "cost_per_execution"
    OPTIMIZATION_FREQUENCY = "optimization_frequency"
    USER_SATISFACTION = "user_satisfaction"


class TimeGranularity(str, Enum):
    """시간 단위"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass
class OptimizationEvent:
    """최적화 이벤트"""
    id: str
    workflow_id: str
    timestamp: datetime
    optimization_type: str
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvements: Dict[str, float]
    confidence: float
    applied: bool
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalyticsReport:
    """분석 리포트"""
    period_start: datetime
    period_end: datetime
    total_optimizations: int
    successful_optimizations: int
    avg_performance_improvement: float
    avg_cost_reduction: float
    avg_reliability_improvement: float
    total_cost_savings: float
    total_time_saved: float
    top_performing_workflows: List[Dict[str, Any]]
    optimization_trends: List[Dict[str, Any]]
    roi_analysis: Dict[str, float]
    recommendations: List[str]


class OptimizationAnalyticsService:
    """최적화 분석 서비스"""
    
    def __init__(self, event_bus: ValidatedEventBus):
        self.event_bus = event_bus
        
        # 데이터 저장소
        self.optimization_events: List[OptimizationEvent] = []
        self.workflow_baselines: Dict[str, Dict[str, float]] = {}
        self.user_preferences: Dict[str, Dict[str, Any]] = {}
        
        # 분석 캐시
        self.analytics_cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5분
        
        # 백그라운드 작업
        self._analytics_task: Optional[asyncio.Task] = None
        
    async def start_analytics_service(self):
        """분석 서비스 시작"""
        if self._analytics_task and not self._analytics_task.done():
            return
        
        self._analytics_task = asyncio.create_task(self._analytics_loop())
        
        # 이벤트 구독
        await self._subscribe_to_events()
        
        logger.info("Optimization analytics service started")
    
    async def stop_analytics_service(self):
        """분석 서비스 중지"""
        if self._analytics_task and not self._analytics_task.done():
            self._analytics_task.cancel()
            try:
                await self._analytics_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Optimization analytics service stopped")
    
    async def _subscribe_to_events(self):
        """이벤트 구독"""
        # 최적화 완료 이벤트
        self.event_bus.subscribe(
            'optimization_recommendations_applied',
            self._handle_optimization_applied
        )
        
        # 워크플로우 실행 이벤트
        self.event_bus.subscribe(
            'workflow_execution_completed',
            self._handle_workflow_execution
        )
        
        # 성능 메트릭 업데이트 이벤트
        self.event_bus.subscribe(
            'performance_metrics_updated',
            self._handle_metrics_update
        )
    
    async def _handle_optimization_applied(self, event_data: Dict[str, Any]):
        """최적화 적용 이벤트 처리"""
        workflow_id = event_data.get('workflow_id')
        results = event_data.get('results', [])
        
        for result in results:
            optimization_event = OptimizationEvent(
                id=f"opt_{datetime.now().timestamp()}",
                workflow_id=workflow_id,
                timestamp=datetime.now(),
                optimization_type=result.get('type', 'unknown'),
                before_metrics=result.get('before_metrics', {}),
                after_metrics=result.get('after_metrics', {}),
                improvements=result.get('improvements', {}),
                confidence=result.get('confidence', 0.0),
                applied=True,
                user_id=event_data.get('user_id'),
                metadata=result.get('metadata', {})
            )
            
            self.optimization_events.append(optimization_event)
            
            # 워크플로우 베이스라인 업데이트
            await self._update_workflow_baseline(workflow_id, optimization_event.after_metrics)
        
        # 캐시 무효화
        self._invalidate_cache()
    
    async def _handle_workflow_execution(self, event_data: Dict[str, Any]):
        """워크플로우 실행 이벤트 처리"""
        workflow_id = event_data.get('workflow_id')
        metrics = {
            'execution_time': event_data.get('execution_time', 0),
            'success': event_data.get('success', False),
            'cost': event_data.get('cost', 0),
            'memory_usage': event_data.get('memory_usage', 0)
        }
        
        # 베이스라인이 없으면 생성
        if workflow_id not in self.workflow_baselines:
            self.workflow_baselines[workflow_id] = {
                'avg_execution_time': metrics['execution_time'],
                'success_rate': 1.0 if metrics['success'] else 0.0,
                'avg_cost': metrics['cost'],
                'sample_count': 1
            }
        else:
            # 이동 평균 업데이트
            baseline = self.workflow_baselines[workflow_id]
            count = baseline['sample_count']
            
            baseline['avg_execution_time'] = (
                (baseline['avg_execution_time'] * count + metrics['execution_time']) / (count + 1)
            )
            baseline['avg_cost'] = (
                (baseline['avg_cost'] * count + metrics['cost']) / (count + 1)
            )
            baseline['success_rate'] = (
                (baseline['success_rate'] * count + (1.0 if metrics['success'] else 0.0)) / (count + 1)
            )
            baseline['sample_count'] = min(count + 1, 100)  # 최대 100개 샘플
    
    async def _handle_metrics_update(self, event_data: Dict[str, Any]):
        """메트릭 업데이트 이벤트 처리"""
        # 실시간 메트릭 업데이트 처리
        self._invalidate_cache()
    
    async def _update_workflow_baseline(self, workflow_id: str, metrics: Dict[str, float]):
        """워크플로우 베이스라인 업데이트"""
        if workflow_id not in self.workflow_baselines:
            self.workflow_baselines[workflow_id] = {
                'avg_execution_time': metrics.get('execution_time', 0),
                'success_rate': metrics.get('success_rate', 0),
                'avg_cost': metrics.get('cost', 0),
                'sample_count': 1
            }
        else:
            # 최적화 후 메트릭으로 베이스라인 업데이트
            baseline = self.workflow_baselines[workflow_id]
            baseline.update({
                'avg_execution_time': metrics.get('execution_time', baseline['avg_execution_time']),
                'success_rate': metrics.get('success_rate', baseline['success_rate']),
                'avg_cost': metrics.get('cost', baseline['avg_cost'])
            })
    
    async def generate_analytics_report(
        self,
        start_date: datetime,
        end_date: datetime,
        workflow_ids: Optional[List[str]] = None
    ) -> AnalyticsReport:
        """분석 리포트 생성"""
        # 캐시 확인
        cache_key = f"report_{start_date.isoformat()}_{end_date.isoformat()}_{workflow_ids}"
        if cache_key in self.analytics_cache:
            cache_entry = self.analytics_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(seconds=self.cache_ttl):
                return cache_entry['data']
        
        # 기간 내 최적화 이벤트 필터링
        filtered_events = [
            event for event in self.optimization_events
            if start_date <= event.timestamp <= end_date and
            (workflow_ids is None or event.workflow_id in workflow_ids)
        ]
        
        if not filtered_events:
            return AnalyticsReport(
                period_start=start_date,
                period_end=end_date,
                total_optimizations=0,
                successful_optimizations=0,
                avg_performance_improvement=0.0,
                avg_cost_reduction=0.0,
                avg_reliability_improvement=0.0,
                total_cost_savings=0.0,
                total_time_saved=0.0,
                top_performing_workflows=[],
                optimization_trends=[],
                roi_analysis={},
                recommendations=[]
            )
        
        # 기본 통계 계산
        total_optimizations = len(filtered_events)
        successful_optimizations = len([e for e in filtered_events if e.applied])
        
        # 개선율 계산
        performance_improvements = [
            e.improvements.get('performance_improvement', 0) 
            for e in filtered_events if e.applied
        ]
        cost_reductions = [
            e.improvements.get('cost_reduction', 0) 
            for e in filtered_events if e.applied
        ]
        reliability_improvements = [
            e.improvements.get('reliability_improvement', 0) 
            for e in filtered_events if e.applied
        ]
        
        avg_performance_improvement = statistics.mean(performance_improvements) if performance_improvements else 0.0
        avg_cost_reduction = statistics.mean(cost_reductions) if cost_reductions else 0.0
        avg_reliability_improvement = statistics.mean(reliability_improvements) if reliability_improvements else 0.0
        
        # 총 절약 계산
        total_cost_savings = await self._calculate_total_savings(filtered_events)
        total_time_saved = await self._calculate_total_time_saved(filtered_events)
        
        # 상위 성과 워크플로우
        top_performing_workflows = await self._get_top_performing_workflows(filtered_events)
        
        # 최적화 트렌드
        optimization_trends = await self._calculate_optimization_trends(
            filtered_events, start_date, end_date
        )
        
        # ROI 분석
        roi_analysis = await self._calculate_roi_analysis(filtered_events)
        
        # 추천사항 생성
        recommendations = await self._generate_recommendations(filtered_events)
        
        report = AnalyticsReport(
            period_start=start_date,
            period_end=end_date,
            total_optimizations=total_optimizations,
            successful_optimizations=successful_optimizations,
            avg_performance_improvement=avg_performance_improvement,
            avg_cost_reduction=avg_cost_reduction,
            avg_reliability_improvement=avg_reliability_improvement,
            total_cost_savings=total_cost_savings,
            total_time_saved=total_time_saved,
            top_performing_workflows=top_performing_workflows,
            optimization_trends=optimization_trends,
            roi_analysis=roi_analysis,
            recommendations=recommendations
        )
        
        # 캐시 저장
        self.analytics_cache[cache_key] = {
            'timestamp': datetime.now(),
            'data': report
        }
        
        return report
    
    async def _calculate_total_savings(self, events: List[OptimizationEvent]) -> float:
        """총 비용 절약 계산"""
        total_savings = 0.0
        
        for event in events:
            if not event.applied:
                continue
            
            before_cost = event.before_metrics.get('cost', 0)
            after_cost = event.after_metrics.get('cost', 0)
            cost_reduction = before_cost - after_cost
            
            # 월간 실행 횟수 가정 (실제로는 워크플로우별 통계 사용)
            monthly_executions = 1000
            monthly_savings = cost_reduction * monthly_executions
            
            total_savings += monthly_savings
        
        return total_savings
    
    async def _calculate_total_time_saved(self, events: List[OptimizationEvent]) -> float:
        """총 시간 절약 계산"""
        total_time_saved = 0.0
        
        for event in events:
            if not event.applied:
                continue
            
            before_time = event.before_metrics.get('execution_time', 0)
            after_time = event.after_metrics.get('execution_time', 0)
            time_reduction = before_time - after_time
            
            # 월간 실행 횟수 가정
            monthly_executions = 1000
            monthly_time_saved = time_reduction * monthly_executions / 3600  # 시간 단위
            
            total_time_saved += monthly_time_saved
        
        return total_time_saved
    
    async def _get_top_performing_workflows(
        self, 
        events: List[OptimizationEvent]
    ) -> List[Dict[str, Any]]:
        """상위 성과 워크플로우 조회"""
        workflow_performance = {}
        
        for event in events:
            if not event.applied:
                continue
            
            workflow_id = event.workflow_id
            if workflow_id not in workflow_performance:
                workflow_performance[workflow_id] = {
                    'workflow_id': workflow_id,
                    'optimization_count': 0,
                    'total_performance_improvement': 0.0,
                    'total_cost_reduction': 0.0,
                    'avg_confidence': 0.0
                }
            
            perf = workflow_performance[workflow_id]
            perf['optimization_count'] += 1
            perf['total_performance_improvement'] += event.improvements.get('performance_improvement', 0)
            perf['total_cost_reduction'] += event.improvements.get('cost_reduction', 0)
            perf['avg_confidence'] += event.confidence
        
        # 평균 계산 및 정렬
        for perf in workflow_performance.values():
            count = perf['optimization_count']
            perf['avg_performance_improvement'] = perf['total_performance_improvement'] / count
            perf['avg_cost_reduction'] = perf['total_cost_reduction'] / count
            perf['avg_confidence'] = perf['avg_confidence'] / count
            
            # 종합 점수 계산
            perf['composite_score'] = (
                perf['avg_performance_improvement'] * 0.4 +
                perf['avg_cost_reduction'] * 0.4 +
                perf['avg_confidence'] * 100 * 0.2
            )
        
        # 상위 10개 반환
        top_workflows = sorted(
            workflow_performance.values(),
            key=lambda x: x['composite_score'],
            reverse=True
        )[:10]
        
        return top_workflows
    
    async def _calculate_optimization_trends(
        self,
        events: List[OptimizationEvent],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """최적화 트렌드 계산"""
        # 일별 트렌드 계산
        trends = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            day_events = [
                e for e in events 
                if e.timestamp.date() == current_date and e.applied
            ]
            
            if day_events:
                avg_performance = statistics.mean([
                    e.improvements.get('performance_improvement', 0) for e in day_events
                ])
                avg_cost = statistics.mean([
                    e.improvements.get('cost_reduction', 0) for e in day_events
                ])
                avg_confidence = statistics.mean([e.confidence for e in day_events])
            else:
                avg_performance = 0.0
                avg_cost = 0.0
                avg_confidence = 0.0
            
            trends.append({
                'date': current_date.isoformat(),
                'optimization_count': len(day_events),
                'avg_performance_improvement': avg_performance,
                'avg_cost_reduction': avg_cost,
                'avg_confidence': avg_confidence
            })
            
            current_date += timedelta(days=1)
        
        return trends
    
    async def _calculate_roi_analysis(self, events: List[OptimizationEvent]) -> Dict[str, float]:
        """ROI 분석 계산"""
        # 최적화 투자 비용 (시간, 리소스 등)
        optimization_cost = len([e for e in events if e.applied]) * 10.0  # 최적화당 $10 가정
        
        # 총 절약액
        total_savings = await self._calculate_total_savings(events)
        
        # ROI 계산
        roi = ((total_savings - optimization_cost) / optimization_cost * 100) if optimization_cost > 0 else 0
        
        # 회수 기간 (개월)
        monthly_savings = total_savings / 12 if total_savings > 0 else 0
        payback_period = optimization_cost / monthly_savings if monthly_savings > 0 else float('inf')
        
        return {
            'total_investment': optimization_cost,
            'total_savings': total_savings,
            'net_benefit': total_savings - optimization_cost,
            'roi_percentage': roi,
            'payback_period_months': min(payback_period, 999),  # 최대 999개월
            'monthly_savings': monthly_savings
        }
    
    async def _generate_recommendations(self, events: List[OptimizationEvent]) -> List[str]:
        """추천사항 생성"""
        recommendations = []
        
        # 성공률 분석
        success_rate = len([e for e in events if e.applied]) / len(events) if events else 0
        if success_rate < 0.8:
            recommendations.append(
                "최적화 성공률이 낮습니다. 신뢰도 임계값을 조정하거나 더 많은 학습 데이터를 수집하세요."
            )
        
        # 최적화 빈도 분석
        if len(events) < 5:
            recommendations.append(
                "최적화 빈도가 낮습니다. 자동 튜닝을 활성화하거나 튜닝 주기를 단축하세요."
            )
        
        # 성능 개선 분석
        performance_improvements = [
            e.improvements.get('performance_improvement', 0) 
            for e in events if e.applied
        ]
        if performance_improvements and statistics.mean(performance_improvements) < 10:
            recommendations.append(
                "평균 성능 개선율이 낮습니다. 더 적극적인 최적화 전략을 고려하세요."
            )
        
        # 비용 절감 분석
        cost_reductions = [
            e.improvements.get('cost_reduction', 0) 
            for e in events if e.applied
        ]
        if cost_reductions and statistics.mean(cost_reductions) < 15:
            recommendations.append(
                "비용 절감 효과가 제한적입니다. 비용 최적화 전략을 강화하세요."
            )
        
        # 워크플로우별 분석
        workflow_counts = {}
        for event in events:
            workflow_counts[event.workflow_id] = workflow_counts.get(event.workflow_id, 0) + 1
        
        if len(workflow_counts) > 0:
            max_optimizations = max(workflow_counts.values())
            min_optimizations = min(workflow_counts.values())
            
            if max_optimizations > min_optimizations * 3:
                recommendations.append(
                    "일부 워크플로우에 최적화가 집중되어 있습니다. 다른 워크플로우도 검토하세요."
                )
        
        return recommendations
    
    async def get_real_time_metrics(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """실시간 메트릭 조회"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        # 최근 24시간 이벤트
        recent_events = [
            e for e in self.optimization_events
            if e.timestamp >= last_24h and (workflow_id is None or e.workflow_id == workflow_id)
        ]
        
        if not recent_events:
            return {
                'status': 'no_recent_activity',
                'message': '최근 24시간 동안 최적화 활동이 없습니다.'
            }
        
        # 실시간 통계
        applied_events = [e for e in recent_events if e.applied]
        
        return {
            'period': '24h',
            'total_optimizations': len(recent_events),
            'successful_optimizations': len(applied_events),
            'success_rate': len(applied_events) / len(recent_events) * 100,
            'avg_performance_improvement': statistics.mean([
                e.improvements.get('performance_improvement', 0) for e in applied_events
            ]) if applied_events else 0,
            'avg_cost_reduction': statistics.mean([
                e.improvements.get('cost_reduction', 0) for e in applied_events
            ]) if applied_events else 0,
            'avg_confidence': statistics.mean([
                e.confidence for e in applied_events
            ]) if applied_events else 0,
            'optimization_types': {
                opt_type: len([e for e in applied_events if e.optimization_type == opt_type])
                for opt_type in set(e.optimization_type for e in applied_events)
            } if applied_events else {},
            'last_optimization': applied_events[-1].timestamp.isoformat() if applied_events else None
        }
    
    async def _analytics_loop(self):
        """분석 백그라운드 루프"""
        while True:
            try:
                # 주기적 분석 작업
                await self._cleanup_old_events()
                await self._update_analytics_cache()
                
                await asyncio.sleep(3600)  # 1시간마다 실행
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analytics loop error: {e}")
                await asyncio.sleep(300)  # 오류 시 5분 대기
    
    async def _cleanup_old_events(self):
        """오래된 이벤트 정리"""
        cutoff_date = datetime.now() - timedelta(days=90)  # 90일 이전 데이터 삭제
        
        initial_count = len(self.optimization_events)
        self.optimization_events = [
            e for e in self.optimization_events if e.timestamp >= cutoff_date
        ]
        
        removed_count = initial_count - len(self.optimization_events)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old optimization events")
    
    async def _update_analytics_cache(self):
        """분석 캐시 업데이트"""
        # 오래된 캐시 항목 제거
        now = datetime.now()
        expired_keys = [
            key for key, value in self.analytics_cache.items()
            if now - value['timestamp'] > timedelta(seconds=self.cache_ttl)
        ]
        
        for key in expired_keys:
            del self.analytics_cache[key]
    
    def _invalidate_cache(self):
        """캐시 무효화"""
        self.analytics_cache.clear()
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """분석 요약 정보"""
        total_events = len(self.optimization_events)
        applied_events = len([e for e in self.optimization_events if e.applied])
        
        return {
            'total_optimization_events': total_events,
            'successful_optimizations': applied_events,
            'success_rate': (applied_events / total_events * 100) if total_events > 0 else 0,
            'tracked_workflows': len(self.workflow_baselines),
            'cache_size': len(self.analytics_cache),
            'data_retention_days': 90,
            'last_event': self.optimization_events[-1].timestamp.isoformat() if self.optimization_events else None
        }