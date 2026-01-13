"""
Base Agent Plugin Interface

Agent들을 Plugin 형태로 작동시키기 위한 기본 인터페이스
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from backend.models.plugin import IPlugin, PluginManifest
from backend.agents.base import BaseAgent


class AgentCapability(BaseModel):
    """Agent 능력 정의"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    required_permissions: List[str] = []


class AgentExecutionContext(BaseModel):
    """Agent 실행 컨텍스트"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    orchestration_pattern: Optional[str] = None
    parent_agent_id: Optional[str] = None
    execution_metadata: Dict[str, Any] = {}
    security_context: Dict[str, Any] = {}


class IAgentPlugin(IPlugin, ABC):
    """Agent Plugin 기본 인터페이스"""
    
    @abstractmethod
    def get_agent_type(self) -> str:
        """Agent 타입 반환"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """Agent가 제공하는 능력들 반환"""
        pass
    
    @abstractmethod
    def get_agent_instance(self) -> BaseAgent:
        """실제 Agent 인스턴스 반환"""
        pass
    
    @abstractmethod
    def execute_agent(
        self, 
        input_data: Dict[str, Any], 
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """Agent 실행"""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """입력 데이터 검증"""
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Agent 상태 확인"""
        pass
    
    def get_agent_metadata(self) -> Dict[str, Any]:
        """Agent 메타데이터 반환"""
        return {
            "agent_type": self.get_agent_type(),
            "capabilities": [cap.dict() for cap in self.get_capabilities()],
            "plugin_info": self.get_manifest().dict(),
            "health_status": self.get_health_status()
        }
    
    def supports_capability(self, capability_name: str) -> bool:
        """특정 능력 지원 여부 확인"""
        return any(cap.name == capability_name for cap in self.get_capabilities())


class BaseAgentPlugin(IAgentPlugin):
    """Agent Plugin 기본 구현 클래스"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._agent_instance = None
        self._initialized = False
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """플러그인 초기화"""
        try:
            self.config.update(config)
            self._agent_instance = self._create_agent_instance()
            self._initialized = True
            return True
        except Exception as e:
            print(f"Agent plugin initialization failed: {e}")
            return False
    
    def cleanup(self) -> None:
        """플러그인 정리"""
        if self._agent_instance and hasattr(self._agent_instance, 'cleanup'):
            self._agent_instance.cleanup()
        self._initialized = False
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """IPlugin 인터페이스 구현 - Agent 실행을 위한 래퍼"""
        if not self._initialized:
            raise RuntimeError("Agent plugin not initialized")
        
        input_data = context.get('input_data', {})
        execution_context = AgentExecutionContext(**context.get('execution_context', {}))
        
        return self.execute_agent(input_data, execution_context)
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """설정 검증"""
        errors = []
        
        # 기본 설정 검증
        required_fields = self._get_required_config_fields()
        for field in required_fields:
            if field not in config:
                errors.append(f"Required configuration field missing: {field}")
        
        # Agent별 추가 검증
        errors.extend(self._validate_agent_specific_config(config))
        
        return errors
    
    def get_agent_instance(self) -> BaseAgent:
        """Agent 인스턴스 반환"""
        if not self._initialized or not self._agent_instance:
            raise RuntimeError("Agent plugin not initialized")
        return self._agent_instance
    
    def get_health_status(self) -> Dict[str, Any]:
        """기본 상태 확인"""
        return {
            "initialized": self._initialized,
            "agent_available": self._agent_instance is not None,
            "last_check": "2025-01-10T00:00:00Z",
            "status": "healthy" if self._initialized else "not_initialized"
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> List[str]:
        """기본 입력 검증"""
        errors = []
        
        for capability in self.get_capabilities():
            if capability.name in input_data:
                # 각 능력별 입력 스키마 검증 (간단한 예시)
                required_fields = capability.input_schema.get('required', [])
                capability_data = input_data[capability.name]
                
                for field in required_fields:
                    if field not in capability_data:
                        errors.append(f"Required field missing for {capability.name}: {field}")
        
        return errors
    
    @abstractmethod
    def _create_agent_instance(self) -> BaseAgent:
        """실제 Agent 인스턴스 생성 (하위 클래스에서 구현)"""
        pass
    
    def _get_required_config_fields(self) -> List[str]:
        """필수 설정 필드 반환 (하위 클래스에서 오버라이드 가능)"""
        return []
    
    def _validate_agent_specific_config(self, config: Dict[str, Any]) -> List[str]:
        """Agent별 추가 설정 검증 (하위 클래스에서 오버라이드 가능)"""
        return []