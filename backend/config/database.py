"""
Database Configuration Settings.

Centralized database configuration for PostgreSQL, Redis, and Milvus.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    # PostgreSQL Configuration
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5433/agenticrag",
        env="DATABASE_URL"
    )
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5433, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="agenticrag", env="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    
    # Connection Pool Configuration
    DB_POOL_SIZE: int = Field(default=20, description="Base connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=30, description="Maximum additional connections")
    DB_POOL_PRE_PING: bool = Field(default=True, description="Verify connections before use")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Recycle connections after N seconds")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Connection timeout in seconds")
    DB_ECHO_POOL: bool = Field(default=False, description="Enable pool debugging")
    DB_STATEMENT_TIMEOUT: int = Field(default=30000, description="Statement timeout in ms")
    
    # Read Replica Configuration
    READ_REPLICA_URLS: Optional[str] = Field(default=None, description="Comma-separated replica URLs")
    ENABLE_READ_REPLICAS: bool = Field(default=False, description="Enable read/write splitting")
    
    @property
    def read_replica_urls_list(self) -> List[str]:
        """Parse comma-separated read replica URLs."""
        if not self.READ_REPLICA_URLS:
            return []
        return [url.strip() for url in self.READ_REPLICA_URLS.split(',') if url.strip()]
    
    @property
    def async_database_url(self) -> str:
        """Get async database URL for asyncpg."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url


class RedisSettings(BaseSettings):
    """Redis cache configuration."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6380, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


class MilvusSettings(BaseSettings):
    """Milvus vector database configuration."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    MILVUS_HOST: str = Field(default="localhost", env="MILVUS_HOST")
    MILVUS_PORT: int = Field(default=19530, env="MILVUS_PORT")
    MILVUS_COLLECTION_NAME: str = Field(default="documents", env="MILVUS_COLLECTION_NAME")
    MILVUS_LTM_COLLECTION_NAME: str = Field(default="long_term_memory")
    MILVUS_KEEP_LOADED: bool = Field(default=True, description="Keep collection loaded in memory")
    MILVUS_POOL_SIZE: int = Field(default=5, description="Connection pool size")
    MILVUS_MAX_IDLE_TIME: int = Field(default=300, description="Max idle time before refresh")


# Singleton instances
_db_settings: Optional[DatabaseSettings] = None
_redis_settings: Optional[RedisSettings] = None
_milvus_settings: Optional[MilvusSettings] = None


def get_database_settings() -> DatabaseSettings:
    """Get database settings singleton."""
    global _db_settings
    if _db_settings is None:
        _db_settings = DatabaseSettings()
    return _db_settings


def get_redis_settings() -> RedisSettings:
    """Get Redis settings singleton."""
    global _redis_settings
    if _redis_settings is None:
        _redis_settings = RedisSettings()
    return _redis_settings


def get_milvus_settings() -> MilvusSettings:
    """Get Milvus settings singleton."""
    global _milvus_settings
    if _milvus_settings is None:
        _milvus_settings = MilvusSettings()
    return _milvus_settings
