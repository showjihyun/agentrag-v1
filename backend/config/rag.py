"""
RAG Configuration Settings.

Centralized configuration for RAG pipeline, routing, and query processing.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RAGSettings(BaseSettings):
    """RAG pipeline configuration."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    # Hybrid Search Configuration
    ENABLE_HYBRID_SEARCH: bool = Field(default=True, description="Enable hybrid search")
    VECTOR_SEARCH_WEIGHT: float = Field(default=0.7, description="Semantic similarity weight")
    KEYWORD_SEARCH_WEIGHT: float = Field(default=0.3, description="Keyword matching weight")
    
    # Query Expansion
    ENABLE_QUERY_EXPANSION: bool = Field(default=False, description="Enable query expansion")
    QUERY_EXPANSION_METHOD: str = Field(default="hyde", description="Expansion method")
    
    # Speculative RAG
    ENABLE_SPECULATIVE_RAG: bool = Field(default=True, description="Enable speculative RAG")
    SPECULATIVE_TIMEOUT: float = Field(default=2.0, description="Speculative path timeout")
    AGENTIC_TIMEOUT: float = Field(default=15.0, description="Agentic path timeout")
    
    # Default Query Mode
    DEFAULT_QUERY_MODE: str = Field(default="balanced", description="Default mode: fast, balanced, deep")
    
    @field_validator("DEFAULT_QUERY_MODE")
    @classmethod
    def validate_query_mode(cls, v: str) -> str:
        """Validate default query mode."""
        valid_modes = ["fast", "balanced", "deep"]
        if v.lower() not in valid_modes:
            raise ValueError(f"Invalid DEFAULT_QUERY_MODE: '{v}'. Must be one of: {', '.join(valid_modes)}")
        return v.lower()


class RoutingSettings(BaseSettings):
    """Adaptive routing configuration."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    # Adaptive Routing
    ADAPTIVE_ROUTING_ENABLED: bool = Field(default=True, description="Enable adaptive routing")
    
    # Complexity Thresholds
    ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE: float = Field(
        default=0.35,
        description="Below this: FAST mode"
    )
    ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX: float = Field(
        default=0.70,
        description="Above this: DEEP mode"
    )
    
    # Mode Timeouts
    FAST_MODE_TIMEOUT: float = Field(default=1.0, description="FAST mode timeout")
    BALANCED_MODE_TIMEOUT: float = Field(default=3.0, description="BALANCED mode timeout")
    DEEP_MODE_TIMEOUT: float = Field(default=15.0, description="DEEP mode timeout")
    
    # Mode Parameters
    FAST_MODE_TOP_K: int = Field(default=5, description="Documents for FAST mode")
    BALANCED_MODE_TOP_K: int = Field(default=10, description="Documents for BALANCED mode")
    DEEP_MODE_TOP_K: int = Field(default=15, description="Documents for DEEP mode")
    
    # Parallel Execution
    ENABLE_PARALLEL_AGENTS: bool = Field(default=True, description="Enable parallel agents")
    PARALLEL_INITIAL_RETRIEVAL: bool = Field(default=True, description="Parallel initial retrieval")
    PARALLEL_AGENT_TIMEOUT: float = Field(default=5.0, description="Parallel agent timeout")
    PARALLEL_MAX_WORKERS: int = Field(default=3, description="Max concurrent agents")
    PARALLEL_GRACEFUL_DEGRADATION: bool = Field(default=True, description="Continue if some fail")
    
    @field_validator("ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE", "ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate complexity thresholds."""
        if v <= 0.0 or v >= 1.0:
            raise ValueError(f"Threshold ({v}) must be between 0.0 and 1.0")
        return v
    
    @model_validator(mode="after")
    def validate_thresholds_order(self) -> "RoutingSettings":
        """Validate threshold ordering."""
        if self.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE >= self.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX:
            raise ValueError(
                f"SIMPLE threshold ({self.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE}) "
                f"must be less than COMPLEX threshold ({self.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX})"
            )
        return self


class HybridRAGSettings(BaseSettings):
    """Hybrid RAG (Static + Agentic) configuration."""
    
    model_config = {"extra": "ignore", "env_file": ".env"}
    
    # Enable Hybrid RAG
    HYBRID_RAG_ENABLED: bool = Field(default=True, description="Enable Hybrid RAG")
    
    # Complexity Thresholds
    COMPLEXITY_THRESHOLD_SIMPLE: float = Field(default=0.3, description="Below: Static RAG")
    COMPLEXITY_THRESHOLD_COMPLEX: float = Field(default=0.7, description="Above: Agentic RAG")
    
    # Confidence Thresholds
    CONFIDENCE_THRESHOLD_HIGH: float = Field(default=0.7, description="High confidence")
    CONFIDENCE_THRESHOLD_LOW: float = Field(default=0.4, description="Low confidence, escalate")
    
    # Static RAG Parameters
    STATIC_RAG_TOP_K: int = Field(default=5, description="Documents for static RAG")
    STATIC_RAG_TIMEOUT: float = Field(default=2.0, description="Static RAG timeout")
    
    # Agentic RAG Parameters
    AGENTIC_RAG_MAX_ITERATIONS: int = Field(default=10, description="Max ReAct iterations")
    
    # Escalation
    ENABLE_AUTO_ESCALATION: bool = Field(default=True, description="Auto escalate to agentic")
    ESCALATION_CONFIDENCE_THRESHOLD: float = Field(default=0.4, description="Escalation threshold")


# Singleton instances
_rag_settings = None
_routing_settings = None
_hybrid_rag_settings = None


def get_rag_settings() -> RAGSettings:
    """Get RAG settings singleton."""
    global _rag_settings
    if _rag_settings is None:
        _rag_settings = RAGSettings()
    return _rag_settings


def get_routing_settings() -> RoutingSettings:
    """Get routing settings singleton."""
    global _routing_settings
    if _routing_settings is None:
        _routing_settings = RoutingSettings()
    return _routing_settings


def get_hybrid_rag_settings() -> HybridRAGSettings:
    """Get hybrid RAG settings singleton."""
    global _hybrid_rag_settings
    if _hybrid_rag_settings is None:
        _hybrid_rag_settings = HybridRAGSettings()
    return _hybrid_rag_settings
