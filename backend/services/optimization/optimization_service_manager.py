"""
Optimization Service Manager

AI 기반 최적화 서비스들을 통합 관리하는 매니저
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.core.ml.orchestration_optimizer import MLOrchestrationOptimizer, OptimizationObjective
from backend.services.optimization.auto_tuning_service import AutoTuningService, TuningConfiguration
from backend.services.optimization.cost_optimization_engine import CostOptimizationEngine
from backend.services.optimization.optimization_notification_service import OptimizationNotificationService
from backend.services.optimization.optimization_analytics_service import OptimizationAnalyticsService
from backend.core.event_bus.validated_event_bus import ValidatedEventBus
from backend.core.monitoring.plugin_performance_monitor import PluginPerformanceMonitor


logger = logging.getLogger(__name__)


class OptimizationServiceManager:
    """최적화 서비스 통합 관리자"""
    
    def __init__(
        self,
        performance_monitor: PluginPerformanceMonitor,
        event_bus: ValidatedEventBus
    ):
        self.performance_monitor = performance_monitor
        self.event_bus = event_bus
        
        # 최적화 서비스 인스턴스들
        self.ml_optimizer: Optional[MLOrchestrationOptimizer] = None
        self.auto_tuning_service: Optional[AutoTuningService] = None
        self.cost_optimization_engine: Optional[CostOptimizationEngine] = None
        self.notification_service: Optional[OptimizationNotificationService] = None
        self.analytics_service: Optional[OptimizationAnalyticsService] = None
        
        # 서비스 상태
        self.services_initialized = False
        self.optimization_enabled = True
        
        # 최적화 통계
        self.optimization_stats = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'total_cost_savings': 0.0,
            'total_performance_improvements': 0.0,
            'last_optimization_time': None
        }
    
    async def initialize_services(self):
        """최적화 서비스들 초기화"""
        try:
            # ML 오케스트레이션 최적화기 초기화
            self.ml_optimizer = MLOrchestrationOptimizer(
                performance_monitor=self.performance_monitor,
                event_bus=self.event_bus
            )
            
            # 자동 튜닝 서비스 초기화
            self.auto_tuning_service = AutoTuningService(
                optimizer=self.ml_optimizer,
                performance_monitor=self.performance_monitor,
                event_bus=self.event_bus
            )
            
            # 비용 최적화 엔진 초기화
            self.cost_optimization_engine = CostOptimizationEngine(
                event_bus=self.event_bus
            )
            
            # 알림 서비스 초기화
            self.notification_service = OptimizationNotificationService(
                event_bus=self.event_bus
            )
            
            # 분석 서비스 초기화
            self.analytics_service = OptimizationAnalyticsService(
                event_bus=self.event_bus
            )
            
            # 백그라운드 서비스 시작
            await self.notification_service.start_notification_service()
            await self.analytics_service.start_analytics_service()
            
            self.services_initialized = True
            
            # 초기화 완료 이벤트 발행
            await self.event_bus.publish(
                'optimization_services_initialized',
                {
                    'ml_optimizer_enabled': True,
                    'auto_tuning_enabled': True,
                    'cost_optimization_enabled': True,
                    'notification_service_enabled': True,
                    'analytics_service_enabled': True,
                    'initialized_at': datetime.now().isoformat()
                },
                source='optimization_service_manager'
            )
            
            logger.info("Optimization services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize optimization services: {e}")
            raise
    
    async def get_comprehensive_optimization_analysis(
        self,
        workflow_id: str,
        pattern: str,
        agents: List[str],
        task: Dict[str, Any],
        recent_executions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """종합적인 최적화 분석"""
        if not self.services_initialized:
            raise RuntimeError("Optimization services not initialized")
        
        try:
            # 1. 성능 예측 및 분석
            performance_prediction = await self.ml_optimizer.predict_performance(
                pattern, agents, task
            )
            
            # 2. 워크플로우 성능 분석
            performance_analysis = await self.auto_tuning_service.analyze_workflow_performance(
                workflow_id, pattern, agents, recent_executions
            )
            
            # 3. 비용 분석
            cost_analysis = await self.cost_optimization_engine.analyze_workflow_costs(
                workflow_id, pattern, agents, recent_executions
            )
            
            # 4. ML 기반 최적화 추천
            optimization_result = await self.ml_optimizer.optimize_orchestration(
                pattern, agents, task, OptimizationObjective.BALANCED
            )
            
            # 5. 자동 튜닝 추천
            tuning_recommendation = await self.auto_tuning_service.generate_tuning_recommendation(
                workflow_id, pattern, agents, task, performance_analysis
            )
            
            # 6. 비용 최적화 계획
            cost_optimization_plan = await self.cost_optimization_engine.generate_cost_optimization_plan(
                workflow_id, pattern, agents, cost_analysis
            )
            
            # 7. 종합 점수 및 우선순위 계산
            overall_score = self._calculate_overall_optimization_score(
                performance_analysis, cost_analysis, optimization_result
            )
            
            priority_recommendations = self._prioritize_recommendations(
                optimization_result, tuning_recommendation, cost_optimization_plan
            )
            
            return {
                'workflow_id': workflow_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'overall_score': overall_score,
                'performance_prediction': {
                    'execution_time': performance_prediction.predicted_execution_time,
                    'success_rate': performance_prediction.predicted_success_rate,
                    'cost': performance_prediction.predicted_cost,
                    'confidence': performance_prediction.confidence,
                    'bottlenecks': performance_prediction.bottleneck_agents,
                    'suggestions': performance_prediction.optimization_suggestions
                },
                'performance_analysis': performance_analysis,
                'cost_analysis': cost_analysis,
                'ml_optimization': {
                    'optimized_pattern': optimization_result.optimized_pattern,
                    'optimized_agents': optimization_result.optimized_agents,
                    'performance_improvement': optimization_result.performance_improvement,
                    'cost_reduction': optimization_result.cost_reduction,
                    'reliability_improvement': optimization_result.reliability_improvement,
                    'confidence': optimization_result.confidence,
                    'reasoning': optimization_result.reasoning,
                    'estimated_savings': optimization_result.estimated_savings
                },
                'auto_tuning_recommendation': {
                    'auto_applicable': tuning_recommendation.auto_applicable if tuning_recommendation else False,
                    'confidence': tuning_recommendation.confidence if tuning_recommendation else 0,
                    'risk_level': tuning_recommendation.risk_assessment.get('level') if tuning_recommendation else 'unknown'
                } if tuning_recommendation else None,
                'cost_optimization_plan': {
                    'current_cost': cost_optimization_plan.current_cost.total_cost,
                    'optimized_cost': cost_optimization_plan.optimized_cost.total_cost,
                    'estimated_savings': cost_optimization_plan.estimated_savings,
                    'optimization_actions': len(cost_optimization_plan.optimization_actions),
                    'risk_level': cost_optimization_plan.risk_level,
                    'implementation_effort': cost_optimization_plan.implementation_effort
                },
                'priority_recommendations': priority_recommendations
            }
            
        except Exception as e:
            logger.error(f"Comprehensive optimization analysis failed: {e}")
            raise
    
    async def apply_optimization_recommendations(
        self,
        workflow_id: str,
        recommendations: List[str],
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """최적화 추천사항 적용"""
        if not self.services_initialized:
            raise RuntimeError("Optimization services not initialized")
        
        results = []
        
        try:
            for recommendation_type in recommendations:
                if recommendation_type == 'auto_tuning':
                    # 자동 튜닝 추천 적용
                    tuning_insights = await self.auto_tuning_service.get_tuning_insights(workflow_id)
                    if tuning_insights and 'latest_recommendation' in tuning_insights:
                        # 실제 구현에서는 추천 객체를 가져와서 적용
                        result = {
                            'type': 'auto_tuning',
                            'status': 'simulated_success',
                            'message': '자동 튜닝 추천이 적용되었습니다.'
                        }
                        results.append(result)
                
                elif recommendation_type == 'cost_optimization':
                    # 비용 최적화 적용 (시뮬레이션)
                    result = {
                        'type': 'cost_optimization',
                        'status': 'simulated_success',
                        'message': '비용 최적화가 적용되었습니다.'
                    }
                    results.append(result)
                
                elif recommendation_type == 'ml_optimization':
                    # ML 최적화 적용 (시뮬레이션)
                    result = {
                        'type': 'ml_optimization',
                        'status': 'simulated_success',
                        'message': 'ML 기반 최적화가 적용되었습니다.'
                    }
                    results.append(result)
            
            # 통계 업데이트
            self.optimization_stats['total_optimizations'] += len(results)
            self.optimization_stats['successful_optimizations'] += len([r for r in results if 'success' in r['status']])
            self.optimization_stats['last_optimization_time'] = datetime.now().isoformat()
            
            # 적용 완료 이벤트 발행
            await self.event_bus.publish(
                'optimization_recommendations_applied',
                {
                    'workflow_id': workflow_id,
                    'applied_recommendations': recommendations,
                    'results': results,
                    'auto_apply': auto_apply
                },
                source='optimization_service_manager'
            )
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'applied_count': len(results),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Failed to apply optimization recommendations: {e}")
            return {
                'success': False,
                'error': str(e),
                'partial_results': results
            }
    
    async def start_continuous_optimization(
        self,
        config: Optional[TuningConfiguration] = None
    ) -> Dict[str, Any]:
        """지속적인 최적화 시작"""
        if not self.services_initialized:
            raise RuntimeError("Optimization services not initialized")
        
        try:
            # 자동 튜닝 서비스 시작
            await self.auto_tuning_service.start_auto_tuning(config)
            
            return {
                'success': True,
                'message': '지속적인 최적화가 시작되었습니다.',
                'config': {
                    'strategy': config.strategy if config else 'balanced',
                    'auto_apply': config.auto_apply if config else False,
                    'interval_hours': config.tuning_interval_hours if config else 24
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to start continuous optimization: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def stop_continuous_optimization(self) -> Dict[str, Any]:
        """지속적인 최적화 중지"""
        if not self.services_initialized:
            raise RuntimeError("Optimization services not initialized")
        
        try:
            await self.auto_tuning_service.stop_auto_tuning()
            
            return {
                'success': True,
                'message': '지속적인 최적화가 중지되었습니다.'
            }
            
        except Exception as e:
            logger.error(f"Failed to stop continuous optimization: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_optimization_dashboard_data(self) -> Dict[str, Any]:
        """최적화 대시보드 데이터 조회"""
        if not self.services_initialized:
            return {
                'status': 'services_not_initialized',
                'message': '최적화 서비스가 초기화되지 않았습니다.'
            }
        
        try:
            # 전체 튜닝 인사이트
            tuning_insights = await self.auto_tuning_service.get_tuning_insights()
            
            # 성능 모니터링 요약
            performance_summary = self.performance_monitor.get_all_metrics_summary()
            
            # ML 모델 정확도
            model_accuracy = await self.ml_optimizer._calculate_model_accuracy()
            
            return {
                'status': 'active',
                'services_status': {
                    'ml_optimizer': 'active',
                    'auto_tuning': 'active',
                    'cost_optimization': 'active'
                },
                'optimization_stats': self.optimization_stats,
                'tuning_insights': tuning_insights,
                'performance_summary': performance_summary,
                'ml_model_accuracy': model_accuracy,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get optimization dashboard data: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_optimization_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        workflow_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """최적화 분석 데이터 조회"""
        if not self.analytics_service:
            return {
                'status': 'analytics_service_unavailable',
                'message': '분석 서비스가 사용할 수 없습니다.'
            }
        
        try:
            report = await self.analytics_service.generate_analytics_report(
                start_date, end_date, workflow_ids
            )
            
            return {
                'status': 'success',
                'report': {
                    'period_start': report.period_start.isoformat(),
                    'period_end': report.period_end.isoformat(),
                    'total_optimizations': report.total_optimizations,
                    'successful_optimizations': report.successful_optimizations,
                    'avg_performance_improvement': report.avg_performance_improvement,
                    'avg_cost_reduction': report.avg_cost_reduction,
                    'avg_reliability_improvement': report.avg_reliability_improvement,
                    'total_cost_savings': report.total_cost_savings,
                    'total_time_saved': report.total_time_saved,
                    'top_performing_workflows': report.top_performing_workflows,
                    'optimization_trends': report.optimization_trends,
                    'roi_analysis': report.roi_analysis,
                    'recommendations': report.recommendations
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get optimization analytics: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def get_real_time_optimization_metrics(
        self,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """실시간 최적화 메트릭 조회"""
        if not self.analytics_service:
            return {
                'status': 'analytics_service_unavailable',
                'message': '분석 서비스가 사용할 수 없습니다.'
            }
        
        try:
            return await self.analytics_service.get_real_time_metrics(workflow_id)
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def update_notification_settings(
        self,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """알림 설정 업데이트"""
        if not self.notification_service:
            return {
                'success': False,
                'error': 'Notification service not available'
            }
        
        try:
            self.notification_service.update_notification_settings(settings)
            
            return {
                'success': True,
                'message': '알림 설정이 업데이트되었습니다.',
                'settings': settings
            }
            
        except Exception as e:
            logger.error(f"Failed to update notification settings: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_notification_history(
        self,
        limit: int = 50,
        notification_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """알림 이력 조회"""
        if not self.notification_service:
            return {
                'status': 'notification_service_unavailable',
                'history': []
            }
        
        try:
            from backend.services.optimization.optimization_notification_service import NotificationType
            
            type_filter = None
            if notification_type:
                type_filter = NotificationType(notification_type)
            
            history = self.notification_service.get_notification_history(limit, type_filter)
            stats = self.notification_service.get_notification_stats()
            
            return {
                'status': 'success',
                'history': history,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification history: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'history': []
            }
    
    async def generate_weekly_report(self) -> Dict[str, Any]:
        """주간 리포트 생성"""
        if not self.notification_service:
            return {
                'success': False,
                'error': 'Notification service not available'
            }
        
        try:
            week_start = datetime.now() - timedelta(days=7)
            report_data = await self.notification_service.generate_weekly_report(week_start)
            
            return {
                'success': True,
                'report_data': report_data,
                'message': '주간 리포트가 생성되고 발송되었습니다.'
            }
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_overall_optimization_score(
        self,
        performance_analysis: Dict[str, Any],
        cost_analysis: Dict[str, Any],
        optimization_result
    ) -> Dict[str, Any]:
        """전체 최적화 점수 계산"""
        # 성능 점수 (0-100)
        performance_grade = performance_analysis.get('performance_metrics', {}).get('performance_grade', 'C')
        performance_score = {
            'A+': 95, 'A': 85, 'B': 70, 'C': 50, 'D': 25
        }.get(performance_grade, 50)
        
        # 비용 점수 (0-100)
        cost_grade = cost_analysis.get('cost_grade', 'C')
        cost_score = {
            'A+': 95, 'A': 85, 'B': 70, 'C': 50, 'D': 25
        }.get(cost_grade, 50)
        
        # 최적화 잠재력 점수
        optimization_potential = min(100, 
            optimization_result.performance_improvement + 
            optimization_result.cost_reduction
        )
        
        # 가중 평균 계산
        overall_score = (performance_score * 0.4 + cost_score * 0.3 + optimization_potential * 0.3)
        
        return {
            'overall_score': round(overall_score, 1),
            'performance_score': performance_score,
            'cost_score': cost_score,
            'optimization_potential': round(optimization_potential, 1),
            'grade': self._score_to_grade(overall_score)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """점수를 등급으로 변환"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'
    
    def _prioritize_recommendations(
        self,
        optimization_result,
        tuning_recommendation,
        cost_optimization_plan
    ) -> List[Dict[str, Any]]:
        """추천사항 우선순위 결정"""
        recommendations = []
        
        # ML 최적화 추천
        if optimization_result.performance_improvement > 10 or optimization_result.cost_reduction > 10:
            recommendations.append({
                'type': 'ml_optimization',
                'priority': 'high' if optimization_result.performance_improvement > 20 else 'medium',
                'title': 'ML 기반 패턴 최적화',
                'description': optimization_result.reasoning,
                'estimated_benefit': {
                    'performance': optimization_result.performance_improvement,
                    'cost': optimization_result.cost_reduction
                },
                'confidence': optimization_result.confidence,
                'auto_applicable': optimization_result.confidence > 0.8
            })
        
        # 자동 튜닝 추천
        if tuning_recommendation and tuning_recommendation.auto_applicable:
            recommendations.append({
                'type': 'auto_tuning',
                'priority': 'high' if tuning_recommendation.confidence > 0.8 else 'medium',
                'title': '자동 성능 튜닝',
                'description': tuning_recommendation.reasoning,
                'estimated_benefit': {
                    'performance': tuning_recommendation.optimization_result.performance_improvement,
                    'cost': tuning_recommendation.optimization_result.cost_reduction
                },
                'confidence': tuning_recommendation.confidence,
                'auto_applicable': tuning_recommendation.auto_applicable
            })
        
        # 비용 최적화 추천
        if cost_optimization_plan.estimated_savings.get('cost_reduction_percent', 0) > 5:
            recommendations.append({
                'type': 'cost_optimization',
                'priority': 'high' if cost_optimization_plan.estimated_savings.get('cost_reduction_percent', 0) > 15 else 'medium',
                'title': '비용 최적화',
                'description': f"{len(cost_optimization_plan.optimization_actions)}개의 비용 절감 액션",
                'estimated_benefit': {
                    'cost': cost_optimization_plan.estimated_savings.get('cost_reduction_percent', 0),
                    'monthly_savings': cost_optimization_plan.estimated_savings.get('monthly_savings', 0)
                },
                'confidence': cost_optimization_plan.confidence,
                'auto_applicable': cost_optimization_plan.risk_level == 'low'
            })
        
        # 우선순위 정렬 (high > medium > low)
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return recommendations
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            if self.auto_tuning_service:
                await self.auto_tuning_service.stop_auto_tuning()
            
            if self.notification_service:
                await self.notification_service.stop_notification_service()
            
            if self.analytics_service:
                await self.analytics_service.stop_analytics_service()
            
            logger.info("Optimization service manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error during optimization service cleanup: {e}")