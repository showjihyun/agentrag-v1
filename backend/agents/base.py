"""
Base Agent Class

모든 Agent들의 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Agent 설정"""
    name: str
    description: str
    capabilities: List[str] = []
    max_retries: int = 3
    timeout: float = 30.0
    metadata: Dict[str, Any] = {}


class BaseAgent(ABC):
    """모든 Agent의 기본 클래스"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.description = config.description
        self.capabilities = config.capabilities
        self.max_retries = config.max_retries
        self.timeout = config.timeout
        self.metadata = config.metadata
        
        self.logger = logging.getLogger(f"agent.{self.name}")
        
    @abstractmethod
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Agent 실행"""
        pass
    
    @abstractmethod
    async def validate_input(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """입력 검증"""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Agent 능력 반환"""
        return self.capabilities
    
    def get_metadata(self) -> Dict[str, Any]:
        """Agent 메타데이터 반환"""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            **self.metadata
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Agent 상태 확인"""
        return {
            "status": "healthy",
            "name": self.name,
            "capabilities": self.capabilities,
            "timestamp": str(datetime.now())
        }