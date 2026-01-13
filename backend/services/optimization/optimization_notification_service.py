"""
Optimization Notification Service

최적화 관련 알림 및 리포트를 관리하는 서비스
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from backend.core.event_bus.validated_event_bus import ValidatedEventBus


logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """알림 유형"""
    THRESHOLD_VIOLATION = "threshold_violation"
    OPTIMIZATION_COMPLETED = "optimization_completed"
    COST_ALERT = "cost_alert"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    WEEKLY_REPORT = "weekly_report"
    MONTHLY_REPORT = "monthly_report"


class NotificationChannel(str, Enum):
    """알림 채널"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


@dataclass
class NotificationTemplate:
    """알림 템플릿"""
    type: NotificationType
    title_template: str
    message_template: str
    priority: str  # high, medium, low
    channels: List[NotificationChannel]


@dataclass
class OptimizationNotification:
    """최적화 알림"""
    id: str
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    priority: str
    channels: List[NotificationChannel]
    recipients: List[str]
    created_at: datetime
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed


class OptimizationNotificationService:
    """최적화 알림 서비스"""
    
    def __init__(self, event_bus: ValidatedEventBus):
        self.event_bus = event_bus
        self.notification_queue: List[OptimizationNotification] = []
        self.notification_history: List[OptimizationNotification] = []
        
        # 알림 템플릿 정의
        self.templates = self._initialize_templates()
        
        # 알림 설정
        self.notification_settings = {
            'email_enabled': True,
            'slack_enabled': False,
            'threshold_violations': True,
            'optimization_results': True,
            'weekly_reports': True,
            'batch_size': 10,
            'retry_attempts': 3
        }
        
        # 백그라운드 작업
        self._notification_task: Optional[asyncio.Task] = None
        
    def _initialize_templates(self) -> Dict[NotificationType, NotificationTemplate]:
        """알림 템플릿 초기화"""
        return {
            NotificationType.THRESHOLD_VIOLATION: NotificationTemplate(
                type=NotificationType.THRESHOLD_VIOLATION,
                title_template="⚠️ 성능 임계값 위반 알림",
                message_template="""
워크플로우 '{workflow_name}'에서 성능 임계값 위반이 감지되었습니다.

📊 위반 내용:
{violations}

🔧 권장 조치:
- 워크플로우 설정을 검토하세요
- 자동 최적화를 활성화하세요
- 성능 모니터링을 확인하세요

📈 최적화 대시보드: {dashboard_url}
                """,
                priority="high",
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP]
            ),
            
            NotificationType.OPTIMIZATION_COMPLETED: NotificationTemplate(
                type=NotificationType.OPTIMIZATION_COMPLETED,
                title_template="✅ 워크플로우 최적화 완료",
                message_template="""
워크플로우 '{workflow_name}'의 최적화가 성공적으로 완료되었습니다.

📈 개선 결과:
• 성능 개선: {performance_improvement}%
• 비용 절감: {cost_reduction}%
• 안정성 향상: {reliability_improvement}%

💰 예상 월간 절약: ${monthly_savings}

🎯 최적화 유형: {optimization_type}
📊 신뢰도: {confidence}%

자세한 내용은 최적화 대시보드에서 확인하세요.
                """,
                priority="medium",
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP]
            ),
            
            NotificationType.COST_ALERT: NotificationTemplate(
                type=NotificationType.COST_ALERT,
                title_template="💰 비용 증가 알림",
                message_template="""
워크플로우 실행 비용이 설정된 임계값을 초과했습니다.

📊 비용 현황:
• 현재 월간 비용: ${current_cost}
• 예산 대비: {budget_percentage}%
• 증가율: {increase_percentage}%

🔧 권장 조치:
- 비용 최적화를 실행하세요
- 워크플로우 사용량을 검토하세요
- 예산 설정을 조정하세요

💡 비용 최적화로 최대 {potential_savings}% 절감 가능합니다.
                """,
                priority="high",
                channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK, NotificationChannel.IN_APP]
            ),
            
            NotificationType.PERFORMANCE_DEGRADATION: NotificationTemplate(
                type=NotificationType.PERFORMANCE_DEGRADATION,
                title_template="📉 성능 저하 감지",
                message_template="""
워크플로우 '{workflow_name}'에서 성능 저하가 감지되었습니다.

📊 성능 변화:
• 평균 실행 시간: {avg_execution_time}초 (이전 대비 +{time_increase}%)
• 성공률: {success_rate}% (이전 대비 {success_rate_change}%)
• 오류율 증가: {error_rate_increase}%

🔍 가능한 원인:
{possible_causes}

🔧 자동 최적화를 통해 성능을 개선할 수 있습니다.
                """,
                priority="medium",
                channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP]
            ),
            
            NotificationType.WEEKLY_REPORT: NotificationTemplate(
                type=NotificationType.WEEKLY_REPORT,
                title_template="📊 주간 최적화 리포트",
                message_template="""
지난 주 최적화 성과를 요약해드립니다.

📈 전체 성과:
• 최적화된 워크플로우: {optimized_workflows}개
• 평균 성능 개선: {avg_performance_improvement}%
• 총 비용 절감: ${total_cost_savings}
• 시간 절약: {time_saved}시간

🏆 주요 성과:
{top_achievements}

📊 상세 분석:
{detailed_analysis}

다음 주 최적화 계획을 확인하세요.
                """,
                priority="low",
                channels=[NotificationChannel.EMAIL]
            )
        }
    
    async def start_notification_service(self):
        """알림 서비스 시작"""
        if self._notification_task and not self._notification_task.done():
            return
        
        self._notification_task = asyncio.create_task(self._notification_loop())
        
        # 이벤트 구독
        await self._subscribe_to_events()
        
        logger.info("Optimization notification service started")
    
    async def stop_notification_service(self):
        """알림 서비스 중지"""
        if self._notification_task and not self._notification_task.done():
            self._notification_task.cancel()
            try:
                await self._notification_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Optimization notification service stopped")
    
    async def _subscribe_to_events(self):
        """이벤트 구독"""
        # 성능 임계값 위반 이벤트
        self.event_bus.subscribe(
            'performance_threshold_violation',
            self._handle_threshold_violation
        )
        
        # 최적화 완료 이벤트
        self.event_bus.subscribe(
            'optimization_recommendations_applied',
            self._handle_optimization_completed
        )
        
        # 비용 증가 이벤트
        self.event_bus.subscribe(
            'cost_increase_detected',
            self._handle_cost_alert
        )
        
        # 성능 저하 이벤트
        self.event_bus.subscribe(
            'performance_degradation_detected',
            self._handle_performance_degradation
        )
    
    async def _handle_threshold_violation(self, event_data: Dict[str, Any]):
        """성능 임계값 위반 처리"""
        if not self.notification_settings['threshold_violations']:
            return
        
        workflow_id = event_data.get('workflow_id')
        violations = event_data.get('violations', [])
        
        # 위반 내용 포맷팅
        violation_text = "\n".join([
            f"• {v['type']}: {v['current']} (임계값: {v['threshold']})"
            for v in violations
        ])
        
        notification = await self._create_notification(
            NotificationType.THRESHOLD_VIOLATION,
            {
                'workflow_name': f'워크플로우 {workflow_id}',
                'violations': violation_text,
                'dashboard_url': f'/optimization/dashboard?workflow={workflow_id}'
            },
            recipients=['admin@company.com']  # 실제로는 설정에서 가져옴
        )
        
        await self._queue_notification(notification)
    
    async def _handle_optimization_completed(self, event_data: Dict[str, Any]):
        """최적화 완료 처리"""
        if not self.notification_settings['optimization_results']:
            return
        
        workflow_id = event_data.get('workflow_id')
        results = event_data.get('results', [])
        
        # 결과 집계
        total_performance = sum(r.get('performance_improvement', 0) for r in results)
        total_cost = sum(r.get('cost_reduction', 0) for r in results)
        avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results) if results else 0
        
        notification = await self._create_notification(
            NotificationType.OPTIMIZATION_COMPLETED,
            {
                'workflow_name': f'워크플로우 {workflow_id}',
                'performance_improvement': f"{total_performance:.1f}",
                'cost_reduction': f"{total_cost:.1f}",
                'reliability_improvement': "5.0",  # 예시값
                'monthly_savings': "120",
                'optimization_type': "자동 최적화",
                'confidence': f"{avg_confidence * 100:.0f}"
            },
            recipients=['user@company.com']
        )
        
        await self._queue_notification(notification)
    
    async def _handle_cost_alert(self, event_data: Dict[str, Any]):
        """비용 알림 처리"""
        current_cost = event_data.get('current_cost', 0)
        budget = event_data.get('budget', 1000)
        increase_rate = event_data.get('increase_rate', 0)
        
        notification = await self._create_notification(
            NotificationType.COST_ALERT,
            {
                'current_cost': f"{current_cost:.2f}",
                'budget_percentage': f"{(current_cost / budget * 100):.1f}",
                'increase_percentage': f"{increase_rate:.1f}",
                'potential_savings': "25"
            },
            recipients=['admin@company.com', 'finance@company.com']
        )
        
        await self._queue_notification(notification)
    
    async def _handle_performance_degradation(self, event_data: Dict[str, Any]):
        """성능 저하 처리"""
        workflow_id = event_data.get('workflow_id')
        metrics = event_data.get('metrics', {})
        
        notification = await self._create_notification(
            NotificationType.PERFORMANCE_DEGRADATION,
            {
                'workflow_name': f'워크플로우 {workflow_id}',
                'avg_execution_time': f"{metrics.get('avg_execution_time', 0):.1f}",
                'time_increase': f"{metrics.get('time_increase', 0):.1f}",
                'success_rate': f"{metrics.get('success_rate', 0) * 100:.1f}",
                'success_rate_change': f"{metrics.get('success_rate_change', 0):.1f}",
                'error_rate_increase': f"{metrics.get('error_rate_increase', 0):.1f}",
                'possible_causes': "• 데이터 볼륨 증가\n• 외부 API 응답 지연\n• 리소스 부족"
            },
            recipients=['ops@company.com']
        )
        
        await self._queue_notification(notification)
    
    async def generate_weekly_report(self, week_start: datetime) -> Dict[str, Any]:
        """주간 리포트 생성"""
        week_end = week_start + timedelta(days=7)
        
        # 주간 데이터 수집 (실제로는 데이터베이스에서 조회)
        report_data = {
            'optimized_workflows': 12,
            'avg_performance_improvement': 28.5,
            'total_cost_savings': 1250.0,
            'time_saved': 45.2,
            'top_achievements': [
                "• 문서 처리 워크플로우 35% 성능 향상",
                "• 고객 지원 자동화 비용 40% 절감",
                "• 데이터 분석 파이프라인 안정성 95% 달성"
            ],
            'detailed_analysis': {
                'performance_trends': "전반적으로 상승 추세",
                'cost_efficiency': "목표 대비 120% 달성",
                'user_satisfaction': "4.8/5.0 점수"
            }
        }
        
        # 주간 리포트 알림 생성
        notification = await self._create_notification(
            NotificationType.WEEKLY_REPORT,
            {
                'optimized_workflows': str(report_data['optimized_workflows']),
                'avg_performance_improvement': f"{report_data['avg_performance_improvement']:.1f}",
                'total_cost_savings': f"{report_data['total_cost_savings']:.0f}",
                'time_saved': f"{report_data['time_saved']:.1f}",
                'top_achievements': "\n".join(report_data['top_achievements']),
                'detailed_analysis': f"""
• 성능 트렌드: {report_data['detailed_analysis']['performance_trends']}
• 비용 효율성: {report_data['detailed_analysis']['cost_efficiency']}
• 사용자 만족도: {report_data['detailed_analysis']['user_satisfaction']}
                """.strip()
            },
            recipients=['management@company.com', 'ops@company.com']
        )
        
        await self._queue_notification(notification)
        
        return report_data
    
    async def _create_notification(
        self,
        notification_type: NotificationType,
        template_data: Dict[str, Any],
        recipients: List[str]
    ) -> OptimizationNotification:
        """알림 생성"""
        template = self.templates[notification_type]
        
        # 템플릿 렌더링
        title = template.title_template.format(**template_data)
        message = template.message_template.format(**template_data)
        
        # 활성화된 채널만 선택
        active_channels = []
        for channel in template.channels:
            if channel == NotificationChannel.EMAIL and self.notification_settings['email_enabled']:
                active_channels.append(channel)
            elif channel == NotificationChannel.SLACK and self.notification_settings['slack_enabled']:
                active_channels.append(channel)
            elif channel == NotificationChannel.IN_APP:
                active_channels.append(channel)
        
        notification = OptimizationNotification(
            id=f"notif_{datetime.now().timestamp()}",
            type=notification_type,
            title=title,
            message=message,
            data=template_data,
            priority=template.priority,
            channels=active_channels,
            recipients=recipients,
            created_at=datetime.now()
        )
        
        return notification
    
    async def _queue_notification(self, notification: OptimizationNotification):
        """알림을 큐에 추가"""
        self.notification_queue.append(notification)
        logger.info(f"Notification queued: {notification.type} - {notification.title}")
    
    async def _notification_loop(self):
        """알림 처리 루프"""
        while True:
            try:
                if self.notification_queue:
                    # 배치 처리
                    batch = self.notification_queue[:self.notification_settings['batch_size']]
                    self.notification_queue = self.notification_queue[self.notification_settings['batch_size']:]
                    
                    for notification in batch:
                        await self._send_notification(notification)
                
                # 주간 리포트 스케줄링 (매주 월요일 오전 9시)
                await self._check_weekly_report_schedule()
                
                await asyncio.sleep(30)  # 30초마다 확인
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Notification loop error: {e}")
                await asyncio.sleep(60)  # 오류 시 1분 대기
    
    async def _send_notification(self, notification: OptimizationNotification):
        """알림 전송"""
        try:
            for channel in notification.channels:
                if channel == NotificationChannel.EMAIL:
                    await self._send_email(notification)
                elif channel == NotificationChannel.SLACK:
                    await self._send_slack(notification)
                elif channel == NotificationChannel.IN_APP:
                    await self._send_in_app(notification)
            
            notification.status = "sent"
            notification.sent_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {e}")
            notification.status = "failed"
        
        finally:
            self.notification_history.append(notification)
            
            # 이력 크기 제한 (최근 1000개만 유지)
            if len(self.notification_history) > 1000:
                self.notification_history = self.notification_history[-1000:]
    
    async def _send_email(self, notification: OptimizationNotification):
        """이메일 전송 (시뮬레이션)"""
        logger.info(f"📧 Email sent: {notification.title} to {notification.recipients}")
        # 실제 구현에서는 SMTP 또는 이메일 서비스 API 사용
    
    async def _send_slack(self, notification: OptimizationNotification):
        """Slack 전송 (시뮬레이션)"""
        logger.info(f"💬 Slack sent: {notification.title}")
        # 실제 구현에서는 Slack API 사용
    
    async def _send_in_app(self, notification: OptimizationNotification):
        """인앱 알림 전송"""
        await self.event_bus.publish(
            'in_app_notification',
            {
                'notification_id': notification.id,
                'type': notification.type,
                'title': notification.title,
                'message': notification.message,
                'priority': notification.priority,
                'recipients': notification.recipients,
                'created_at': notification.created_at.isoformat()
            },
            source='optimization_notification_service'
        )
    
    async def _check_weekly_report_schedule(self):
        """주간 리포트 스케줄 확인"""
        now = datetime.now()
        
        # 매주 월요일 오전 9시에 리포트 생성
        if (now.weekday() == 0 and  # 월요일
            now.hour == 9 and 
            now.minute < 30 and  # 30분 내에 실행
            self.notification_settings['weekly_reports']):
            
            week_start = now - timedelta(days=7)
            await self.generate_weekly_report(week_start)
    
    def get_notification_history(
        self, 
        limit: int = 50,
        notification_type: Optional[NotificationType] = None
    ) -> List[Dict[str, Any]]:
        """알림 이력 조회"""
        history = self.notification_history
        
        if notification_type:
            history = [n for n in history if n.type == notification_type]
        
        # 최신순 정렬
        history.sort(key=lambda x: x.created_at, reverse=True)
        
        return [
            {
                'id': n.id,
                'type': n.type,
                'title': n.title,
                'priority': n.priority,
                'status': n.status,
                'created_at': n.created_at.isoformat(),
                'sent_at': n.sent_at.isoformat() if n.sent_at else None,
                'recipients_count': len(n.recipients)
            }
            for n in history[:limit]
        ]
    
    def update_notification_settings(self, settings: Dict[str, Any]):
        """알림 설정 업데이트"""
        self.notification_settings.update(settings)
        logger.info("Notification settings updated")
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """알림 통계"""
        total_notifications = len(self.notification_history)
        sent_notifications = len([n for n in self.notification_history if n.status == "sent"])
        failed_notifications = len([n for n in self.notification_history if n.status == "failed"])
        
        # 유형별 통계
        type_stats = {}
        for notification in self.notification_history:
            type_stats[notification.type] = type_stats.get(notification.type, 0) + 1
        
        return {
            'total_notifications': total_notifications,
            'sent_notifications': sent_notifications,
            'failed_notifications': failed_notifications,
            'success_rate': (sent_notifications / total_notifications * 100) if total_notifications > 0 else 0,
            'type_distribution': type_stats,
            'queue_size': len(self.notification_queue)
        }