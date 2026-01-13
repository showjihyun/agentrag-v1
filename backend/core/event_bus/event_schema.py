"""
Event Schema Validation System

이벤트 스키마 검증 및 버전 관리 시스템
"""
from typing import Dict, Any, Optional, List, Type
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
import json


class EventType(str, Enum):
    """이벤트 타입 정의"""
    # Plugin 관련 이벤트
    PLUGIN_STATE_CHANGED = "plugin_state_changed"
    PLUGIN_REGISTERED = "plugin_registered"
    PLUGIN_UNREGISTERED = "plugin_unregistered"
    
    # Agent 실행 관련 이벤트
    AGENT_EXECUTION_STARTED = "agent_execution_started"
    AGENT_EXECUTION_COMPLETED = "agent_execution_completed"
    AGENT_EXECUTION_FAILED = "agent_execution_failed"
    
    # 오케스트레이션 관련 이벤트
    ORCHESTRATION_STARTED = "orchestration_started"
    ORCHESTRATION_COMPLETED = "orchestration_completed"
    ORCHESTRATION_FAILED = "orchestration_failed"
    
    # 합의 관련 이벤트
    VOTE_REQUEST = "vote_request"
    VOTE_RESPONSE = "vote_response"
    CONSENSUS_REACHED = "consensus_reached"
    
    # 군집 지능 관련 이벤트
    PHEROMONE_DEPOSIT = "pheromone_deposit"
    SWARM_CONVERGENCE = "swarm_convergence"
    
    # 동적 라우팅 관련 이벤트
    PERFORMANCE_METRICS = "performance_metrics"
    ROUTING_DECISION = "routing_decision"
    
    # Custom Agent 관련 이벤트
    CUSTOM_AGENT_CREATED = "custom_agent_created"
    CUSTOM_AGENT_UPDATED = "custom_agent_updated"
    CUSTOM_AGENT_DELETED = "custom_agent_deleted"


class EventSchema(BaseModel):
    """기본 이벤트 스키마"""
    event_type: EventType
    version: str = Field(default="1.0", description="스키마 버전")
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="고유 이벤트 ID")
    correlation_id: Optional[str] = Field(None, description="연관 이벤트 추적 ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="이벤트 발생 시간")
    source: str = Field(..., description="이벤트 발생 소스")
    payload: Dict[str, Any] = Field(..., description="이벤트 데이터")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
    
    class Config:
        use_enum_values = True


# 특화된 이벤트 스키마들

class PluginStateChangedEvent(EventSchema):
    """Plugin 상태 변경 이벤트"""
    event_type: EventType = EventType.PLUGIN_STATE_CHANGED
    
    class PayloadSchema(BaseModel):
        plugin_id: str
        plugin_type: str
        old_state: str
        new_state: str
        health_metrics: Dict[str, Any]
    
    payload: PayloadSchema


class AgentExecutionStartedEvent(EventSchema):
    """Agent 실행 시작 이벤트"""
    event_type: EventType = EventType.AGENT_EXECUTION_STARTED
    
    class PayloadSchema(BaseModel):
        execution_id: str
        agent_type: str
        input_data: Dict[str, Any]
        context: Dict[str, Any]
        communication_mode: str = "direct"
    
    payload: PayloadSchema


class AgentExecutionCompletedEvent(EventSchema):
    """Agent 실행 완료 이벤트"""
    event_type: EventType = EventType.AGENT_EXECUTION_COMPLETED
    
    class PayloadSchema(BaseModel):
        execution_id: str
        agent_type: str
        result: Dict[str, Any]
        success: bool
        execution_time: Optional[float] = None
    
    payload: PayloadSchema


class OrchestrationStartedEvent(EventSchema):
    """오케스트레이션 시작 이벤트"""
    event_type: EventType = EventType.ORCHESTRATION_STARTED
    
    class PayloadSchema(BaseModel):
        session_id: str
        pattern: str
        agents: List[str]
        task: Dict[str, Any]
    
    payload: PayloadSchema


class VoteRequestEvent(EventSchema):
    """투표 요청 이벤트"""
    event_type: EventType = EventType.VOTE_REQUEST
    
    class PayloadSchema(BaseModel):
        vote_id: str
        session_id: str
        topic: str
        agents: List[str]
        options: List[str]
        deadline: Optional[datetime] = None
    
    payload: PayloadSchema


class PerformanceMetricsEvent(EventSchema):
    """성능 메트릭 이벤트"""
    event_type: EventType = EventType.PERFORMANCE_METRICS
    
    class PayloadSchema(BaseModel):
        agent_type: str
        metrics: Dict[str, float]
        measurement_window: str
        timestamp: datetime
    
    payload: PayloadSchema


class EventSchemaRegistry:
    """이벤트 스키마 레지스트리"""
    
    def __init__(self):
        self._schemas: Dict[EventType, Type[EventSchema]] = {
            EventType.PLUGIN_STATE_CHANGED: PluginStateChangedEvent,
            EventType.AGENT_EXECUTION_STARTED: AgentExecutionStartedEvent,
            EventType.AGENT_EXECUTION_COMPLETED: AgentExecutionCompletedEvent,
            EventType.ORCHESTRATION_STARTED: OrchestrationStartedEvent,
            EventType.VOTE_REQUEST: VoteRequestEvent,
            EventType.PERFORMANCE_METRICS: PerformanceMetricsEvent,
        }
        
        # 기본 스키마로 등록되지 않은 이벤트들은 기본 EventSchema 사용
        self._default_schema = EventSchema
    
    def get_schema(self, event_type: EventType) -> Type[EventSchema]:
        """이벤트 타입에 해당하는 스키마 반환"""
        return self._schemas.get(event_type, self._default_schema)
    
    def register_schema(self, event_type: EventType, schema_class: Type[EventSchema]):
        """새로운 스키마 등록"""
        self._schemas[event_type] = schema_class
    
    def validate_event(self, event_type: EventType, data: Dict[str, Any]) -> EventSchema:
        """이벤트 데이터 검증"""
        schema_class = self.get_schema(event_type)
        
        # event_type이 데이터에 없으면 추가
        if 'event_type' not in data:
            data['event_type'] = event_type
        
        # source가 없으면 기본값 설정
        if 'source' not in data:
            data['source'] = 'unknown'
        
        try:
            return schema_class(**data)
        except Exception as e:
            raise EventValidationError(f"Event validation failed for {event_type}: {e}")
    
    def list_schemas(self) -> Dict[str, str]:
        """등록된 스키마 목록"""
        return {
            event_type.value: schema_class.__name__
            for event_type, schema_class in self._schemas.items()
        }


class EventValidationError(Exception):
    """이벤트 검증 에러"""
    pass


class EventVersionManager:
    """이벤트 스키마 버전 관리"""
    
    def __init__(self):
        self._version_compatibility: Dict[str, List[str]] = {
            "1.0": ["1.0"],  # 1.0은 1.0과만 호환
            "1.1": ["1.0", "1.1"],  # 1.1은 1.0, 1.1과 호환
            "2.0": ["2.0"],  # 2.0은 2.0과만 호환 (Breaking change)
        }
    
    def is_compatible(self, producer_version: str, consumer_version: str) -> bool:
        """버전 호환성 확인"""
        compatible_versions = self._version_compatibility.get(consumer_version, [])
        return producer_version in compatible_versions
    
    def get_latest_version(self) -> str:
        """최신 버전 반환"""
        versions = list(self._version_compatibility.keys())
        return max(versions, key=lambda v: tuple(map(int, v.split('.'))))
    
    def migrate_event(self, event: EventSchema, target_version: str) -> EventSchema:
        """이벤트를 대상 버전으로 마이그레이션"""
        if event.version == target_version:
            return event
        
        # 버전별 마이그레이션 로직
        if event.version == "1.0" and target_version == "1.1":
            return self._migrate_1_0_to_1_1(event)
        
        raise EventMigrationError(f"No migration path from {event.version} to {target_version}")
    
    def _migrate_1_0_to_1_1(self, event: EventSchema) -> EventSchema:
        """1.0에서 1.1로 마이그레이션"""
        # 예시: 1.1에서 correlation_id가 필수가 되었다면
        event_dict = event.dict()
        event_dict['version'] = "1.1"
        
        if not event_dict.get('correlation_id'):
            event_dict['correlation_id'] = event_dict['event_id']
        
        return EventSchema(**event_dict)


class EventMigrationError(Exception):
    """이벤트 마이그레이션 에러"""
    pass


# 전역 레지스트리 인스턴스
event_schema_registry = EventSchemaRegistry()
event_version_manager = EventVersionManager()