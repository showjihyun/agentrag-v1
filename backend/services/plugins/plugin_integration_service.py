"""
Plugin Integration Service

Integrates enhanced security manager and error handling with existing plugin systems.
Provides a unified interface for plugin management with improved security and reliability.
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Type
from datetime import datetime

from backend.services.plugins.enhanced_security_manager import (
    EnhancedPluginSecurityManager,
    SecurityContext,
    SecureAgentExecutionRequest,
    UserRole,
    PluginPermission
)
from backend.services.plugins.security_manager import PluginSecurityManager
from backend.services.plugins.agents.enhanced_agent_plugin_manager import (
    EnhancedAgentPluginManager,
    AgentExecutionResult
)
from backend.services.plugins.agents.agent_plugin_manager import AgentPluginManager
from backend.core.error_handling.plugin_errors import (
    enhanced_plugin_error_handler,
    PluginException,
    PluginErrorCode,
    handle_plugin_errors,
    plugin_error_context
)
from backend.core.event_bus import EventBus
from backend.core.dependencies import get_redis_client

logger = logging.getLogger(__name__)


class PluginIntegrationService:
    """플러그인 통합 서비스 - 기존 시스템과 향상된 시스템을 연결"""
    
    def __init__(self):
        # Enhanced components
        self.enhanced_security_manager = EnhancedPluginSecurityManager()
        self.enhanced_agent_manager = EnhancedAgentPluginManager()
        self.error_handler = enhanced_plugin_error_handler
        
        # Legacy components (for backward compatibility)
        self.legacy_security_manager = PluginSecurityManager()
        self.legacy_agent_manager: Optional[AgentPluginManager] = None
        
        # Integration flags
        self.use_enhanced_security = True
        self.use_enhanced_agent_manager = True
        self.migration_mode = False
        
        self._initialized = False
    
    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """통합 서비스 초기화"""
        try:
            config = config or {}
            
            logger.info("Initializing Plugin Integration Service...")
            
            # Enhanced components 초기화
            if self.use_enhanced_agent_manager:
                await self.enhanced_agent_manager.initialize(config)
                logger.info("Enhanced Agent Plugin Manager initialized")
            
            # Legacy components 초기화 (호환성을 위해)
            if config.get("enable_legacy_support", False):
                self.legacy_agent_manager = AgentPluginManager()
                await self.legacy_agent_manager.initialize(config)
                logger.info("Legacy Agent Plugin Manager initialized for compatibility")
            
            # Migration mode 설정
            self.migration_mode = config.get("migration_mode", False)
            if self.migration_mode:
                logger.info("Running in migration mode - both systems active")
            
            self._initialized = True
            logger.info("Plugin Integration Service initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Plugin Integration Service: {str(e)}")
            return False
    
    async def create_security_context(
        self,
        user_id: str,
        user_role: str,
        session_id: str,
        ip_address: Optional[str] = None
    ) -> SecurityContext:
        """보안 컨텍스트 생성 (통합 인터페이스)"""
        
        # 문자열을 UserRole enum으로 변환
        try:
            role_enum = UserRole(user_role.lower())
        except ValueError:
            logger.warning(f"Unknown user role: {user_role}, defaulting to USER")
            role_enum = UserRole.USER
        
        if self.use_enhanced_security:
            return self.enhanced_security_manager.create_security_context(
                user_id, role_enum, session_id, ip_address
            )
        else:
            # Legacy fallback - create a basic security context
            return SecurityContext(
                user_id=user_id,
                user_role=role_enum,
                permissions=set(),
                rate_limit_remaining=100,
                session_id=session_id,
                ip_address=ip_address
            )
    
    @handle_plugin_errors(attempt_recovery=True, max_retries=2)
    async def execute_agent(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        security_context: SecurityContext,
        priority: int = 5,
        use_queue: bool = False
    ) -> AgentExecutionResult:
        """Agent 실행 (통합 인터페이스)"""
        
        if not self._initialized:
            raise PluginException(
                code=PluginErrorCode.CONFIGURATION_ERROR,
                message="Plugin Integration Service not initialized",
                plugin_id=agent_type,
                user_id=security_context.user_id
            )
        
        async with plugin_error_context(
            plugin_id=agent_type,
            user_id=security_context.user_id,
            operation="integrated_agent_execution"
        ) as trace_id:
            
            if self.use_enhanced_agent_manager:
                # Enhanced system 사용
                return await self.enhanced_agent_manager.execute_single_agent(
                    agent_type, input_data, security_context, priority, use_queue
                )
            
            elif self.legacy_agent_manager:
                # Legacy system 사용
                result = await self.legacy_agent_manager.execute_single_agent(
                    agent_type, input_data, 
                    security_context.user_id, 
                    security_context.session_id
                )
                
                # Legacy 결과를 새로운 형식으로 변환
                return AgentExecutionResult(
                    success=True,
                    result=result,
                    execution_time=0.0,
                    trace_id=trace_id,
                    agent_type=agent_type,
                    user_id=security_context.user_id
                )
            
            else:
                raise PluginException(
                    code=PluginErrorCode.CONFIGURATION_ERROR,
                    message="No agent manager available",
                    plugin_id=agent_type,
                    user_id=security_context.user_id
                )
    
    async def execute_orchestration(
        self,
        pattern: str,
        agents: List[str],
        task: Dict[str, Any],
        security_context: SecurityContext,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """오케스트레이션 실행 (통합 인터페이스)"""
        
        if self.use_enhanced_agent_manager:
            return await self.enhanced_agent_manager.execute_orchestration(
                pattern, agents, task, security_context, config
            )
        
        elif self.legacy_agent_manager:
            return await self.legacy_agent_manager.execute_orchestration(
                pattern, agents, task, 
                security_context.user_id, 
                security_context.session_id
            )
        
        else:
            raise PluginException(
                code=PluginErrorCode.CONFIGURATION_ERROR,
                message="No orchestration manager available",
                user_id=security_context.user_id
            )
    
    async def validate_plugin_security(
        self,
        plugin_path: str,
        manifest: Any,
        security_context: SecurityContext
    ) -> Dict[str, Any]:
        """플러그인 보안 검증 (통합 인터페이스)"""
        
        if self.use_enhanced_security:
            validation_result = await self.enhanced_security_manager.validate_plugin_comprehensive(
                plugin_path, manifest, security_context
            )
            
            return {
                "is_valid": validation_result.is_valid,
                "score": validation_result.score,
                "threats": [
                    {
                        "type": threat.threat_type.value,
                        "level": threat.level.value,
                        "description": threat.description,
                        "location": threat.location,
                        "line_number": threat.line_number
                    }
                    for threat in validation_result.threats
                ],
                "validation_time": validation_result.validation_time
            }
        
        else:
            # Legacy validation
            validation_result = await self.legacy_security_manager.validate_plugin(
                plugin_path, manifest
            )
            
            return {
                "is_valid": validation_result.is_valid,
                "score": validation_result.score,
                "threats": [
                    {
                        "type": threat.threat_type.value,
                        "level": threat.level.value,
                        "description": threat.description,
                        "location": threat.location,
                        "line_number": threat.line_number
                    }
                    for threat in validation_result.threats
                ],
                "validation_time": 0.0
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        status = {
            "integration_service": {
                "initialized": self._initialized,
                "enhanced_security_enabled": self.use_enhanced_security,
                "enhanced_agent_manager_enabled": self.use_enhanced_agent_manager,
                "migration_mode": self.migration_mode
            }
        }
        
        if self.use_enhanced_agent_manager:
            status["enhanced_agent_manager"] = await self.enhanced_agent_manager.get_performance_summary()
        
        if self.legacy_agent_manager:
            legacy_status = await self.legacy_agent_manager.get_agent_status()
            status["legacy_agent_manager"] = legacy_status
        
        # 에러 통계
        status["error_statistics"] = self.error_handler.get_error_statistics()
        
        return status
    
    async def get_security_summary(self, user_id: str) -> Dict[str, Any]:
        """보안 요약 정보"""
        if self.use_enhanced_security:
            return self.enhanced_security_manager.get_security_summary(user_id)
        else:
            return {"message": "Enhanced security not enabled"}
    
    async def migrate_to_enhanced_system(self) -> Dict[str, Any]:
        """향상된 시스템으로 마이그레이션"""
        if not self.migration_mode:
            return {
                "success": False,
                "error": "Migration mode not enabled"
            }
        
        try:
            logger.info("Starting migration to enhanced system...")
            
            # 기존 시스템에서 데이터 추출
            migration_data = {}
            
            if self.legacy_agent_manager:
                legacy_status = await self.legacy_agent_manager.get_agent_status()
                migration_data["agents"] = legacy_status.get("agents", [])
            
            # Enhanced 시스템 활성화
            self.use_enhanced_security = True
            self.use_enhanced_agent_manager = True
            
            logger.info("Migration to enhanced system completed")
            
            return {
                "success": True,
                "migrated_data": migration_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def rollback_to_legacy_system(self) -> Dict[str, Any]:
        """레거시 시스템으로 롤백"""
        try:
            logger.info("Rolling back to legacy system...")
            
            # Enhanced 시스템 비활성화
            self.use_enhanced_security = False
            self.use_enhanced_agent_manager = False
            
            # Legacy 시스템이 없으면 초기화
            if not self.legacy_agent_manager:
                self.legacy_agent_manager = AgentPluginManager()
                await self.legacy_agent_manager.initialize()
            
            logger.info("Rollback to legacy system completed")
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def shutdown(self):
        """통합 서비스 종료"""
        logger.info("Shutting down Plugin Integration Service...")
        
        try:
            if self.enhanced_agent_manager:
                await self.enhanced_agent_manager.shutdown()
            
            if self.legacy_agent_manager:
                await self.legacy_agent_manager.shutdown()
            
            logger.info("Plugin Integration Service shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")


# 전역 인스턴스
plugin_integration_service = PluginIntegrationService()


async def get_plugin_integration_service() -> PluginIntegrationService:
    """플러그인 통합 서비스 인스턴스 반환"""
    if not plugin_integration_service._initialized:
        await plugin_integration_service.initialize()
    
    return plugin_integration_service