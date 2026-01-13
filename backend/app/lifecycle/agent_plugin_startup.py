"""
Agent Plugin System Startup

애플리케이션 시작 시 Agent Plugin 시스템을 초기화하는 모듈
"""
import asyncio
import logging
from typing import Dict, Any

from backend.services.plugins.agents.agent_plugin_manager import initialize_agent_plugin_system
from backend.core.dependencies import get_redis_client
from backend.config import get_settings


logger = logging.getLogger(__name__)


async def initialize_agent_plugins() -> bool:
    """Agent Plugin 시스템 초기화"""
    try:
        settings = get_settings()
        
        # Agent Plugin 설정 구성
        agent_config = {
            # Vector Search Agent 설정
            "vector_search_config": {
                "embedding_model": settings.EMBEDDING_MODEL or "jhgan/ko-sroberta-multitask",
                "similarity_threshold": 0.7,
                "max_results": 10,
                "collection_name": "documents"
            },
            
            # Web Search Agent 설정
            "web_search_config": {
                "max_results": 10,
                "timeout": 30,
                "safe_search": "moderate",
                "region": "kr-kr"
            },
            
            # Local Data Agent 설정
            "local_data_config": {
                "base_path": "./uploads",
                "allowed_extensions": [".pdf", ".docx", ".txt", ".md", ".hwp", ".hwpx"],
                "max_file_size": 104857600,  # 100MB
                "enable_ocr": True,
                "ocr_language": "korean"
            },
            
            # Aggregator Agent 설정
            "aggregator_config": {
                "orchestration_pattern": "adaptive",
                "max_agents": 10,
                "timeout_seconds": 300,
                "event_bus_config": {
                    "stream_name": "agent_orchestration",
                    "consumer_group": "aggregator_agents",
                    "max_retries": 3
                },
                "communication_protocols": {
                    "consensus_threshold": 0.7,
                    "swarm_pheromone_decay": 0.1,
                    "routing_metric_weight": {
                        "performance": 0.4,
                        "load": 0.3,
                        "accuracy": 0.3
                    }
                }
            }
        }
        
        # Agent Plugin 시스템 초기화
        manager = await initialize_agent_plugin_system(agent_config)
        
        logger.info("Agent Plugin system initialized successfully")
        
        # 시스템 상태 확인
        status = await manager.get_agent_status()
        logger.info(f"Registered agents: {len(status.get('agents', []))}")
        logger.info(f"Available patterns: {len(status.get('orchestration_patterns', []))}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Agent Plugin system: {e}")
        return False


async def shutdown_agent_plugins():
    """Agent Plugin 시스템 종료"""
    try:
        from backend.services.plugins.agents.agent_plugin_manager import _agent_plugin_manager
        
        if _agent_plugin_manager:
            await _agent_plugin_manager.shutdown()
            logger.info("Agent Plugin system shutdown completed")
            
    except Exception as e:
        logger.error(f"Error during Agent Plugin system shutdown: {e}")


# FastAPI 이벤트 핸들러용 함수들
def create_startup_handler():
    """FastAPI startup 이벤트 핸들러 생성"""
    async def startup_handler():
        logger.info("Starting Agent Plugin system...")
        success = await initialize_agent_plugins()
        if not success:
            logger.error("Agent Plugin system initialization failed")
            # 실패해도 애플리케이션은 계속 실행 (Agent 기능만 비활성화)
    
    return startup_handler


def create_shutdown_handler():
    """FastAPI shutdown 이벤트 핸들러 생성"""
    async def shutdown_handler():
        logger.info("Shutting down Agent Plugin system...")
        await shutdown_agent_plugins()
    
    return shutdown_handler