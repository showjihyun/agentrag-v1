"""
LLM Configuration Settings.

Centralized configuration for LLM providers and models.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class LLMSettings(BaseSettings):
    """LLM provider configuration."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    # Provider Configuration
    LLM_PROVIDER: str = Field(default="ollama", description="LLM provider: ollama, openai, claude")
    LLM_MODEL: str = Field(default="llama3.1", description="Model name")
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    
    # Fallback Configuration
    LLM_FALLBACK_PROVIDERS: Optional[str] = Field(
        default=None,
        description="Comma-separated list of fallback providers"
    )
    
    # Timeout Settings
    LLM_TIMEOUT_LOCAL: int = Field(default=30, description="Timeout for local providers (Ollama)")
    LLM_TIMEOUT_CLOUD: int = Field(default=60, description="Timeout for cloud providers")
    
    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        valid_providers = ["ollama", "openai", "claude"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Invalid LLM_PROVIDER: '{v}'. Must be one of: {', '.join(valid_providers)}")
        return v.lower()
    
    @property
    def fallback_providers_list(self) -> List[str]:
        """Parse comma-separated fallback providers."""
        if not self.LLM_FALLBACK_PROVIDERS:
            return []
        return [p.strip() for p in self.LLM_FALLBACK_PROVIDERS.split(',') if p.strip()]
    
    @property
    def timeout(self) -> int:
        """Get appropriate timeout based on provider."""
        if self.LLM_PROVIDER == "ollama":
            return self.LLM_TIMEOUT_LOCAL
        return self.LLM_TIMEOUT_CLOUD


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    # Model Configuration
    # Best Korean models (in order of quality):
    # 1. jhgan/ko-sroberta-multitask (768d, BEST for Korean)
    # 2. BM-K/KoSimCSE-roberta (768d, excellent for Korean)
    # 3. sentence-transformers/paraphrase-multilingual-mpnet-base-v2 (768d)
    EMBEDDING_MODEL: str = Field(
        default="jhgan/ko-sroberta-multitask",
        description="Embedding model name"
    )
    
    # Batch Processing
    EMBEDDING_BATCH_SIZE_SMALL: int = Field(default=10, description="Batch size for small docs")
    EMBEDDING_BATCH_SIZE_MEDIUM: int = Field(default=32, description="Batch size for medium docs")
    EMBEDDING_BATCH_SIZE_LARGE: int = Field(default=64, description="Batch size for large docs")


class RerankerSettings(BaseSettings):
    """Reranker model configuration."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    # Reranking Configuration
    ENABLE_RERANKING: bool = Field(default=False, description="Enable reranking")
    RERANK_METHOD: str = Field(default="cross_encoder", description="Rerank method")
    
    # Adaptive Reranking (Auto-selects best model)
    ENABLE_ADAPTIVE_RERANKING: bool = Field(default=True, description="Use adaptive reranker")
    KOREAN_RERANKER_MODEL: str = Field(
        default="Dongjin-kr/ko-reranker",
        description="Korean-specific reranker"
    )
    MULTILINGUAL_RERANKER_MODEL: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        description="Multilingual reranker"
    )
    
    # Legacy single model
    CROSS_ENCODER_MODEL: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        description="Cross-encoder model"
    )


# Singleton instances
_llm_settings = None
_embedding_settings = None
_reranker_settings = None


def get_llm_settings() -> LLMSettings:
    """Get LLM settings singleton."""
    global _llm_settings
    if _llm_settings is None:
        _llm_settings = LLMSettings()
    return _llm_settings


def get_embedding_settings() -> EmbeddingSettings:
    """Get embedding settings singleton."""
    global _embedding_settings
    if _embedding_settings is None:
        _embedding_settings = EmbeddingSettings()
    return _embedding_settings


def get_reranker_settings() -> RerankerSettings:
    """Get reranker settings singleton."""
    global _reranker_settings
    if _reranker_settings is None:
        _reranker_settings = RerankerSettings()
    return _reranker_settings
