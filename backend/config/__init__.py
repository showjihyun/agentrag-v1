"""
Configuration Module.

Provides centralized access to all configuration settings.
Settings are organized by domain for better maintainability.

Usage:
    from backend.config import settings  # Legacy unified settings
    
    # Or use domain-specific settings:
    from backend.config.database import get_database_settings
    from backend.config.llm import get_llm_settings
    from backend.config.rag import get_rag_settings
    from backend.config.cache import get_cache_settings
"""

# Re-export legacy settings for backward compatibility
# IMPORTANT: This must be imported from the original config.py file
# to maintain backward compatibility with existing code
try:
    from backend.config.warnings_filter import *
except ImportError:
    pass

# Import the original Settings class and settings instance
# This is the main settings object used throughout the application
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field
import os
import sys

# Add parent directory to path to import from config.py
_config_module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _config_module_path not in sys.path:
    sys.path.insert(0, _config_module_path)

# Import settings from the original config.py (one level up)
# The original config.py contains the full Settings class
import importlib.util
_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.py")

if os.path.exists(_config_path):
    _spec = importlib.util.spec_from_file_location("_legacy_config", _config_path)
    _legacy_config = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_legacy_config)
    
    # Re-export the settings instance
    settings = _legacy_config.settings
    Settings = _legacy_config.Settings
else:
    # Fallback: create minimal settings if original not found
    class Settings(BaseSettings):
        DEBUG: bool = False
        LOG_LEVEL: str = "INFO"
        DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5433/agenticrag"
        
        model_config = {"extra": "ignore", "env_file": ".env"}
    
    settings = Settings()

# Domain-specific settings getters
from backend.config.database import (
    get_database_settings,
    get_redis_settings,
    get_milvus_settings,
    DatabaseSettings,
    RedisSettings,
    MilvusSettings,
)
from backend.config.llm import (
    get_llm_settings,
    get_embedding_settings,
    get_reranker_settings,
    LLMSettings,
    EmbeddingSettings,
    RerankerSettings,
)
from backend.config.rag import (
    get_rag_settings,
    get_routing_settings,
    get_hybrid_rag_settings,
    RAGSettings,
    RoutingSettings,
    HybridRAGSettings,
)
from backend.config.cache import (
    get_cache_settings,
    CacheSettings,
)

__all__ = [
    # Legacy settings (backward compatibility)
    "settings",
    "Settings",
    # Database
    "get_database_settings",
    "get_redis_settings", 
    "get_milvus_settings",
    "DatabaseSettings",
    "RedisSettings",
    "MilvusSettings",
    # LLM
    "get_llm_settings",
    "get_embedding_settings",
    "get_reranker_settings",
    "LLMSettings",
    "EmbeddingSettings",
    "RerankerSettings",
    # RAG
    "get_rag_settings",
    "get_routing_settings",
    "get_hybrid_rag_settings",
    "RAGSettings",
    "RoutingSettings",
    "HybridRAGSettings",
    # Cache
    "get_cache_settings",
    "CacheSettings",
]
