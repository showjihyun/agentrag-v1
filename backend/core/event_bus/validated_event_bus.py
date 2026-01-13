"""
Validated Event Bus

스키마 검증 기능이 포함된 Event Bus
"""
from typing import Dict, Any, Optional, Callable, List
import asyncio
import logging
from datetime import datetime

# Import EventBus directly from the module file to avoid circular import
import importlib.util
import os

# Get the path to the event_bus.py file
event_bus_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'event_bus.py')
spec = importlib.util.spec_from_file_location("event_bus_module", event_bus_path)
event_bus_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_bus_module)
EventBus = event_bus_module.EventBus

from backend.core.event_bus.event_schema import (
    EventType, EventSchema, EventSchemaRegistry, EventVersionManager,
    EventValidationError, event_schema_registry, event_version_manager
)


logger = logging.getLogger(__name__)


class ValidatedEventBus(EventBus):
    """스키마 검증이 포함된 Event Bus"""
    
    def __init__(self, redis_client, schema_registry: Optional[EventSchemaRegistry] = None):
        super().__init__(redis_client)
        self.schema_registry = schema_registry or event_schema_registry
        self.version_manager = event_version_manager
        self._validation_enabled = True
        self._strict_mode = False  # True면 검증 실패 시 예외 발생, False면 경고만
        
        # 검증 통계
        self._validation_stats = {
            'total_events': 0,
            'validation_success': 0,
            'validation_failures': 0,
            'schema_migrations': 0
        }
    
    def enable_validation(self, enabled: bool = True):
        """검증 기능 활성화/비활성화"""
        self._validation_enabled = enabled
        logger.info(f"Event validation {'enabled' if enabled else 'disabled'}")
    
    def set_strict_mode(self, strict: bool = True):
        """엄격 모드 설정"""
        self._strict_mode = strict
        logger.info(f"Event validation strict mode {'enabled' if strict else 'disabled'}")
    
    async def publish(
        self, 
        event_type: str, 
        data: Dict[str, Any],
        source: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Optional[EventSchema]:
        """검증된 이벤트 발행"""
        self._validation_stats['total_events'] += 1
        
        try:
            # EventType으로 변환
            if isinstance(event_type, str):
                try:
                    event_type_enum = EventType(event_type)
                except ValueError:
                    if self._strict_mode:
                        raise EventValidationError(f"Unknown event type: {event_type}")
                    else:
                        logger.warning(f"Unknown event type: {event_type}, using as-is")
                        event_type_enum = event_type
            else:
                event_type_enum = event_type
            
            # 검증이 활성화된 경우에만 검증 수행
            validated_event = None
            if self._validation_enabled:
                # 기본 필드 추가
                event_data = data.copy()
                if source:
                    event_data['source'] = source
                if correlation_id:
                    event_data['correlation_id'] = correlation_id
                
                # 스키마 검증
                validated_event = self.schema_registry.validate_event(event_type_enum, event_data)
                
                # 검증 성공 통계
                self._validation_stats['validation_success'] += 1
                
                # 검증된 이벤트 데이터 사용
                publish_data = validated_event.dict()
            else:
                # 검증 없이 원본 데이터 사용
                publish_data = data
            
            # 부모 클래스의 publish 메서드 호출
            await super().publish(event_type, publish_data)
            
            return validated_event
            
        except EventValidationError as e:
            self._validation_stats['validation_failures'] += 1
            
            if self._strict_mode:
                raise
            else:
                logger.warning(f"Event validation failed: {e}")
                # 검증 실패해도 원본 데이터로 발행
                await super().publish(event_type, data)
                return None
        
        except Exception as e:
            self._validation_stats['validation_failures'] += 1
            logger.error(f"Event publishing failed: {e}")
            
            if self._strict_mode:
                raise
            else:
                # 최후의 수단으로 원본 데이터 발행 시도
                try:
                    await super().publish(event_type, data)
                except:
                    pass
                return None
    
    async def publish_validated_event(self, event: EventSchema):
        """이미 검증된 이벤트 발행"""
        event_dict = event.dict()
        await super().publish(event.event_type, event_dict)
    
    def subscribe_with_validation(
        self, 
        event_type: str, 
        handler: Callable[[EventSchema], Any],
        validate_incoming: bool = True
    ):
        """검증 기능이 포함된 구독"""
        
        async def validated_handler(event_data: Dict[str, Any]):
            """검증된 핸들러 래퍼"""
            try:
                if validate_incoming and self._validation_enabled:
                    # 수신된 이벤트 검증
                    event_type_enum = EventType(event_type) if isinstance(event_type, str) else event_type
                    validated_event = self.schema_registry.validate_event(event_type_enum, event_data)
                    
                    # 버전 호환성 확인 및 마이그레이션
                    current_version = self.version_manager.get_latest_version()
                    if validated_event.version != current_version:
                        if self.version_manager.is_compatible(validated_event.version, current_version):
                            validated_event = self.version_manager.migrate_event(validated_event, current_version)
                            self._validation_stats['schema_migrations'] += 1
                        else:
                            logger.warning(f"Incompatible event version: {validated_event.version}")
                    
                    return await handler(validated_event)
                else:
                    # 검증 없이 원본 데이터로 EventSchema 생성
                    event_schema = EventSchema(
                        event_type=event_type,
                        source=event_data.get('source', 'unknown'),
                        payload=event_data
                    )
                    return await handler(event_schema)
                    
            except EventValidationError as e:
                logger.error(f"Incoming event validation failed: {e}")
                if not self._strict_mode:
                    # 검증 실패해도 원본 데이터로 처리 시도
                    try:
                        event_schema = EventSchema(
                            event_type=event_type,
                            source=event_data.get('source', 'unknown'),
                            payload=event_data
                        )
                        return await handler(event_schema)
                    except:
                        pass
            except Exception as e:
                logger.error(f"Event handler failed: {e}")
        
        # 부모 클래스의 subscribe 메서드 사용
        super().subscribe(event_type, validated_handler)
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """검증 통계 반환"""
        total = self._validation_stats['total_events']
        success_rate = (self._validation_stats['validation_success'] / total * 100) if total > 0 else 0
        
        return {
            **self._validation_stats,
            'success_rate': round(success_rate, 2),
            'validation_enabled': self._validation_enabled,
            'strict_mode': self._strict_mode,
            'last_updated': datetime.now().isoformat()
        }
    
    def reset_validation_stats(self):
        """검증 통계 초기화"""
        self._validation_stats = {
            'total_events': 0,
            'validation_success': 0,
            'validation_failures': 0,
            'schema_migrations': 0
        }
    
    async def validate_event_batch(
        self, 
        events: List[Dict[str, Any]]
    ) -> List[Optional[EventSchema]]:
        """이벤트 배치 검증"""
        validated_events = []
        
        for event_data in events:
            try:
                event_type = event_data.get('event_type')
                if not event_type:
                    logger.warning("Event missing event_type field")
                    validated_events.append(None)
                    continue
                
                event_type_enum = EventType(event_type)
                validated_event = self.schema_registry.validate_event(event_type_enum, event_data)
                validated_events.append(validated_event)
                
            except Exception as e:
                logger.error(f"Batch validation failed for event: {e}")
                validated_events.append(None)
        
        return validated_events
    
    def register_custom_schema(self, event_type: EventType, schema_class):
        """커스텀 스키마 등록"""
        self.schema_registry.register_schema(event_type, schema_class)
        logger.info(f"Registered custom schema for {event_type}: {schema_class.__name__}")
    
    def get_schema_info(self) -> Dict[str, Any]:
        """스키마 정보 반환"""
        return {
            'registered_schemas': self.schema_registry.list_schemas(),
            'supported_versions': list(self.version_manager._version_compatibility.keys()),
            'latest_version': self.version_manager.get_latest_version()
        }


# 전역 검증된 Event Bus 팩토리
def create_validated_event_bus(redis_client) -> ValidatedEventBus:
    """검증된 Event Bus 생성"""
    return ValidatedEventBus(redis_client)


# 이벤트 발행 헬퍼 함수들
async def publish_plugin_state_changed(
    event_bus: ValidatedEventBus,
    plugin_id: str,
    plugin_type: str,
    old_state: str,
    new_state: str,
    health_metrics: Dict[str, Any],
    source: str = "plugin_lifecycle_manager"
):
    """Plugin 상태 변경 이벤트 발행"""
    return await event_bus.publish(
        EventType.PLUGIN_STATE_CHANGED,
        {
            'plugin_id': plugin_id,
            'plugin_type': plugin_type,
            'old_state': old_state,
            'new_state': new_state,
            'health_metrics': health_metrics
        },
        source=source
    )


async def publish_agent_execution_started(
    event_bus: ValidatedEventBus,
    execution_id: str,
    agent_type: str,
    input_data: Dict[str, Any],
    context: Dict[str, Any],
    communication_mode: str = "direct",
    source: str = "agent_plugin_registry"
):
    """Agent 실행 시작 이벤트 발행"""
    return await event_bus.publish(
        EventType.AGENT_EXECUTION_STARTED,
        {
            'execution_id': execution_id,
            'agent_type': agent_type,
            'input_data': input_data,
            'context': context,
            'communication_mode': communication_mode
        },
        source=source
    )


async def publish_orchestration_started(
    event_bus: ValidatedEventBus,
    session_id: str,
    pattern: str,
    agents: List[str],
    task: Dict[str, Any],
    source: str = "orchestration_manager"
):
    """오케스트레이션 시작 이벤트 발행"""
    return await event_bus.publish(
        EventType.ORCHESTRATION_STARTED,
        {
            'session_id': session_id,
            'pattern': pattern,
            'agents': agents,
            'task': task
        },
        source=source
    )