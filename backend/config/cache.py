"""
Cache Configuration Settings.

Centralized cache configuration for multi-level caching strategy.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import logging

logger = logging.getLogger(__name__)


class CacheSettings(BaseSettings):
    """Cache configuration settings."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    # General Cache Settings
    ENABLE_SEARCH_CACHE: bool = Field(default=True, description="Enable search result caching")
    
    # L1 Cache (In-Memory)
    CACHE_L1_TTL: int = Field(default=3600, description="L1 cache TTL in seconds")
    CACHE_L1_MAX_SIZE: int = Field(default=1000, description="Maximum L1 cache entries")
    
    # L2 Cache (Redis)
    CACHE_L2_TTL: int = Field(default=7200, description="L2 cache TTL in seconds")
    CACHE_L2_THRESHOLD: int = Field(default=3, description="Hits before promoting to L2")
    CACHE_L2_MAX_SIZE: int = Field(default=10000, description="Maximum L2 cache entries")
    
    # LLM Response Cache
    ENABLE_LLM_CACHE: bool = Field(default=True, description="Enable LLM response caching")
    LLM_CACHE_TTL: int = Field(default=3600, description="LLM cache TTL in seconds")
    
    # Mode-Specific Cache TTLs
    FAST_MODE_CACHE_TTL: int = Field(default=3600, description="FAST mode cache TTL")
    BALANCED_MODE_CACHE_TTL: int = Field(default=1800, description="BALANCED mode cache TTL")
    DEEP_MODE_CACHE_TTL: int = Field(default=7200, description="DEEP mode cache TTL")
    
    # Static RAG Cache
    ENABLE_STATIC_RAG_CACHE: bool = Field(default=True, description="Enable static RAG caching")
    STATIC_RAG_CACHE_TTL: int = Field(default=3600, description="Static RAG cache TTL")
    
    @field_validator("CACHE_L1_TTL", "CACHE_L2_TTL", "LLM_CACHE_TTL")
    @classmethod
    def validate_cache_ttl(cls, v: int) -> int:
        """Validate cache TTL values."""
        if v < 60:
            raise ValueError("Cache TTL must be at least 60 seconds")
        if v > 86400:
            logger.warning(f"Cache TTL ({v}s) is very long (>24h)")
        return v
    
    @field_validator("CACHE_L2_THRESHOLD")
    @classmethod
    def validate_l2_threshold(cls, v: int) -> int:
        """Validate L2 promotion threshold."""
        if v < 1:
            raise ValueError("L2 threshold must be at least 1")
        if v > 100:
            logger.warning(f"L2 threshold ({v}) is very high")
        return v


# Singleton instance
_cache_settings = None


def get_cache_settings() -> CacheSettings:
    """Get cache settings singleton."""
    global _cache_settings
    if _cache_settings is None:
        _cache_settings = CacheSettings()
    return _cache_settings
