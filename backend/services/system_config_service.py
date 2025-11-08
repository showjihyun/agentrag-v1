"""
System Configuration Service

Manages system-wide configuration stored in PostgreSQL.
"""

import logging
from typing import Optional, Any
import json
import asyncpg
from backend.config import settings
from backend.models.enums import ConfigType

logger = logging.getLogger(__name__)


async def get_db_connection():
    """Get async database connection."""
    return await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
    )


class SystemConfigService:
    """Service for managing system configuration."""
    
    @staticmethod
    async def get_config(key: str, default: Any = None) -> Optional[Any]:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        conn = None
        try:
            conn = await get_db_connection()
            result = await conn.fetchrow(
                "SELECT config_value, config_type FROM system_config WHERE config_key = $1",
                key
            )
            
            if not result:
                return default
            
            value = result['config_value']
            config_type = result['config_type']
            
            # Convert based on type
            if config_type == ConfigType.INTEGER:
                return int(value)
            elif config_type == ConfigType.FLOAT:
                return float(value)
            elif config_type == ConfigType.JSON:
                return json.loads(value)
            else:  # string
                return value
                    
        except asyncpg.exceptions.UndefinedTableError:
            logger.warning(
                "system_config table does not exist - returning default",
                extra={"key": key}
            )
            return default
        except Exception as e:
            logger.error(
                "Error getting config",
                extra={
                    "key": key,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return default
        finally:
            if conn:
                await conn.close()
    
    @staticmethod
    async def set_config(key: str, value: Any, config_type: str = 'string', description: str = None) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            config_type: Type of value (string, integer, float, json)
            description: Optional description
            
        Returns:
            True if successful
        """
        conn = None
        try:
            # Convert value to string
            if config_type == ConfigType.JSON:
                value_str = json.dumps(value)
            else:
                value_str = str(value)
            
            conn = await get_db_connection()
            await conn.execute(
                """
                INSERT INTO system_config (config_key, config_value, config_type, description)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (config_key) 
                DO UPDATE SET 
                    config_value = EXCLUDED.config_value,
                    config_type = EXCLUDED.config_type,
                    description = COALESCE(EXCLUDED.description, system_config.description),
                    updated_at = CURRENT_TIMESTAMP
                """,
                key, value_str, config_type, description
            )
            
            logger.info(
                "Set config",
                extra={
                    "key": key,
                    "value": value_str,
                    "config_type": config_type
                }
            )
            return True
            
        except asyncpg.exceptions.UndefinedTableError:
            logger.warning(
                "system_config table does not exist - skipping config storage",
                extra={"key": key}
            )
            return False
        except Exception as e:
            logger.error(
                "Error setting config",
                extra={
                    "key": key,
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return False
        finally:
            if conn:
                await conn.close()
    
    @staticmethod
    async def get_embedding_info() -> dict:
        """
        Get current embedding model information.
        
        Returns:
            Dictionary with model_name and dimension
        """
        model_name = await SystemConfigService.get_config('embedding_model_name', 'jhgan/ko-sroberta-multitask')
        dimension = await SystemConfigService.get_config('embedding_dimension', 768)
        
        return {
            'model_name': model_name,
            'dimension': dimension,
        }
    
    @staticmethod
    async def update_embedding_info(model_name: str, dimension: int) -> bool:
        """
        Update embedding model information.
        
        Args:
            model_name: Embedding model name
            dimension: Embedding dimension
            
        Returns:
            True if successful
        """
        success1 = await SystemConfigService.set_config(
            'embedding_model_name', 
            model_name, 
            'string',
            'Current embedding model name'
        )
        
        success2 = await SystemConfigService.set_config(
            'embedding_dimension', 
            dimension, 
            'integer',
            'Embedding vector dimension'
        )
        
        return success1 and success2
    
    @staticmethod
    async def initialize_embedding_config():
        """
        Initialize embedding configuration from current settings.
        This should be called on application startup.
        """
        from backend.config import settings
        from backend.utils.embedding_utils import get_embedding_dimension
        
        try:
            model_name = settings.EMBEDDING_MODEL
            dimension = get_embedding_dimension(model_name)
            
            await SystemConfigService.update_embedding_info(model_name, dimension)
            logger.info(
                "Initialized embedding config",
                extra={
                    "model_name": model_name,
                    "dimension": dimension
                }
            )
            
        except Exception as e:
            logger.error(
                "Error initializing embedding config",
                extra={"error_type": type(e).__name__},
                exc_info=True
            )
