# Environment configuration
from pydantic_settings import BaseSettings
from typing import Optional, List
from pydantic import Field, field_validator, ValidationError, model_validator
import logging
import sys
import os

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application configuration settings.

    Loads configuration from environment variables and .env file.
    Uses Pydantic for validation and type safety.

    Configuration categories:
    - LLM: Language model provider and settings
    - Milvus: Vector database configuration
    - PostgreSQL: Relational database configuration
    - Redis: Cache and session storage
    - Embedding: Text embedding model settings
    - RAG: Retrieval-augmented generation features
    - Performance: Timeouts, pool sizes, etc.
    """

    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "case_sensitive": True,
    }  # Ignore extra fields from .env

    # LLM Configuration
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "llama3.1"
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_FALLBACK_PROVIDERS: Optional[str] = (
        None  # Comma-separated list of fallback providers
    )

    # LLM Performance Settings
    LLM_TIMEOUT_LOCAL: int = 30  # Timeout for local providers (Ollama)
    LLM_TIMEOUT_CLOUD: int = 60  # Timeout for cloud providers

    # Milvus Configuration
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "documents"
    MILVUS_LTM_COLLECTION_NAME: str = "long_term_memory"
    MILVUS_KEEP_LOADED: bool = True  # Keep collection loaded in memory
    MILVUS_POOL_SIZE: int = 5  # Connection pool size
    MILVUS_MAX_IDLE_TIME: int = 300  # Max idle time before refresh (seconds)

    # PostgreSQL Configuration (Phase 5)
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5433/agenticrag", env="DATABASE_URL")
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5433, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="agenticrag", env="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="postgres", env="POSTGRES_PASSWORD")

    # Connection Pool Configuration (Optimized)
    DB_POOL_SIZE: int = 20  # Base connection pool size
    DB_MAX_OVERFLOW: int = 30  # Maximum additional connections
    DB_POOL_PRE_PING: bool = True  # Verify connections before use
    DB_POOL_RECYCLE: int = 3600  # Recycle connections after 1 hour
    DB_POOL_TIMEOUT: int = 30  # Connection timeout in seconds
    DB_ECHO_POOL: bool = False  # Enable pool debugging (dev only)
    DB_STATEMENT_TIMEOUT: int = 30000  # Statement timeout in milliseconds (30s)
    
    # Read Replica Configuration (Priority 10)
    READ_REPLICA_URLS: Optional[str] = None  # Comma-separated list of read replica URLs
    ENABLE_READ_REPLICAS: bool = False  # Enable read/write splitting
    
    @property
    def read_replica_urls_list(self) -> List[str]:
        """Parse comma-separated read replica URLs"""
        if not self.READ_REPLICA_URLS:
            return []
        return [url.strip() for url in self.READ_REPLICA_URLS.split(',') if url.strip()]

    # Authentication Configuration (Phase 5)
    # JWT_SECRET_KEY must be set via environment variable in production
    JWT_SECRET_KEY: str = Field(
        default="dev_secret_key_change_in_production_min_32_chars",
        env="JWT_SECRET_KEY",
        min_length=32,
        description="JWT secret key - MUST be set via JWT_SECRET_KEY env var in production"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    
    @model_validator(mode='after')
    def validate_secrets(self):
        """Validate that secrets are properly configured in production."""
        if not self.DEBUG:
            # In production, ensure JWT_SECRET_KEY is not the default
            default_key = "dev_secret_key_change_in_production_min_32_chars"
            if self.JWT_SECRET_KEY == default_key:
                logger.warning(
                    "⚠️  SECURITY WARNING: Using default JWT_SECRET_KEY in non-DEBUG mode! "
                    "Set JWT_SECRET_KEY environment variable for production."
                )
        return self

    # File Storage Configuration (Phase 5)
    FILE_STORAGE_BACKEND: str = "local"  # local | s3 | minio
    LOCAL_STORAGE_PATH: str = "./uploads"
    S3_BUCKET_NAME: Optional[str] = None
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION: str = "us-east-1"
    MAX_FILE_SIZE_MB: int = 10
    MAX_BATCH_FILES: int = 100
    MAX_BATCH_SIZE_MB: int = 100

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6380, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")

    # Embedding Configuration
    # Best Korean models (in order of quality):
    # 1. jhgan/ko-sroberta-multitask (768d, BEST for Korean - specialized Korean model)
    # 2. BM-K/KoSimCSE-roberta (768d, excellent for Korean semantic similarity)
    # 3. sentence-transformers/paraphrase-multilingual-mpnet-base-v2 (768d, multilingual, good Korean support)
    # 4. sentence-transformers/distiluse-base-multilingual-cased-v2 (512d, faster, decent Korean)
    EMBEDDING_MODEL: str = "jhgan/ko-sroberta-multitask"

    # Hybrid Search Configuration (optimized for Korean)
    ENABLE_HYBRID_SEARCH: bool = True
    VECTOR_SEARCH_WEIGHT: float = 0.7  # Semantic similarity
    KEYWORD_SEARCH_WEIGHT: float = 0.3  # Exact keyword matching

    # Query Expansion Configuration
    ENABLE_QUERY_EXPANSION: bool = False  # Disabled by default (adds latency)
    QUERY_EXPANSION_METHOD: str = "hyde"  # "hyde", "multi", "semantic", or "all"

    # Reranking Configuration (Korean-Optimized)
    ENABLE_RERANKING: bool = False  # Disabled by default (requires model download)
    RERANK_METHOD: str = "cross_encoder"  # "cross_encoder", "mmr", or "hybrid"
    
    # Adaptive Reranking (Auto-selects best model based on content)
    ENABLE_ADAPTIVE_RERANKING: bool = True  # Use adaptive reranker (recommended) ⭐
    KOREAN_RERANKER_MODEL: str = "Dongjin-kr/ko-reranker"  # For Korean-only content
    MULTILINGUAL_RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"  # For multilingual content
    
    # Legacy single model (used if adaptive reranking disabled)
    # Best reranker models:
    # 1. BAAI/bge-reranker-v2-m3 (BEST - SOTA multilingual, excellent Korean support) ⭐
    # 2. Dongjin-kr/ko-reranker (Korean-specialized cross-encoder)
    # 3. BAAI/bge-reranker-v2-gemma (Gemma-based, high quality)
    # 4. cross-encoder/ms-marco-MiniLM-L-6-v2 (English-focused, faster)
    CROSS_ENCODER_MODEL: str = "BAAI/bge-reranker-v2-m3"

    # Caching Configuration
    ENABLE_SEARCH_CACHE: bool = True
    CACHE_L1_TTL: int = 3600  # L1 cache TTL (1 hour)
    CACHE_L2_THRESHOLD: int = 3  # Promote to L2 after 3 searches
    CACHE_L2_MAX_SIZE: int = 1000  # Maximum L2 cache entries

    # Hybrid Query System (Speculative RAG) Configuration
    ENABLE_SPECULATIVE_RAG: bool = True  # Enable hybrid speculative + agentic system
    SPECULATIVE_TIMEOUT: float = 2.0  # Timeout for speculative path in seconds
    AGENTIC_TIMEOUT: float = 15.0  # Timeout for agentic path in seconds

    # Parallel Agent Execution Configuration (Task 12)
    ENABLE_PARALLEL_AGENTS: bool = True  # Enable parallel agent execution in DEEP mode
    PARALLEL_INITIAL_RETRIEVAL: bool = True  # Parallel vector/web/local search at start
    PARALLEL_AGENT_TIMEOUT: float = 5.0  # Timeout for individual parallel agents
    PARALLEL_MAX_WORKERS: int = 3  # Maximum concurrent agent executions
    PARALLEL_GRACEFUL_DEGRADATION: bool = True  # Continue if some agents fail
    DEFAULT_QUERY_MODE: str = (
        "balanced"  # Default mode: fast, balanced, or deep (when hybrid enabled)
    )

    # Adaptive Routing Configuration
    ADAPTIVE_ROUTING_ENABLED: bool = (
        True  # Enable intelligent query-complexity-based routing
    )

    # Adaptive Complexity Thresholds (for intelligent routing)
    ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE: float = 0.35  # Below this: FAST mode
    ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX: float = 0.70  # Above this: DEEP mode
    # Between thresholds: BALANCED mode

    # Mode Timeouts (performance targets)
    FAST_MODE_TIMEOUT: float = 1.0  # Target: <1s (p95)
    BALANCED_MODE_TIMEOUT: float = 3.0  # Target: <3s initial response (p95)
    DEEP_MODE_TIMEOUT: float = 15.0  # Target: <15s comprehensive response (p95)

    # Mode Parameters (retrieval configuration)
    FAST_MODE_TOP_K: int = 5  # Number of documents for FAST mode
    BALANCED_MODE_TOP_K: int = 10  # Number of documents for BALANCED mode
    DEEP_MODE_TOP_K: int = 15  # Number of documents for DEEP mode

    # Mode-Specific Caching Configuration
    FAST_MODE_CACHE_TTL: int = 3600  # FAST mode cache TTL (1 hour)
    BALANCED_MODE_CACHE_TTL: int = 1800  # BALANCED mode cache TTL (30 minutes)
    DEEP_MODE_CACHE_TTL: int = 7200  # DEEP mode cache TTL (2 hours)

    # Auto-Tuning Configuration
    ENABLE_AUTO_THRESHOLD_TUNING: bool = True  # Enable automatic threshold adjustment
    TUNING_INTERVAL_HOURS: int = 24  # How often to run threshold tuning
    TUNING_MIN_SAMPLES: int = 1000  # Minimum samples required for tuning
    TUNING_DRY_RUN: bool = True  # Run tuning in dry-run mode (no automatic changes)

    # Pattern Learning Configuration
    ENABLE_PATTERN_LEARNING: bool = True  # Enable query pattern learning
    MIN_SAMPLES_FOR_LEARNING: int = 100  # Minimum samples to start learning
    PATTERN_SIMILARITY_THRESHOLD: float = (
        0.8  # Similarity threshold for pattern matching
    )
    PATTERN_LEARNING_WINDOW_DAYS: int = 30  # Days of history to consider for learning

    # Target Mode Distribution (for auto-tuning)
    TARGET_FAST_MODE_PERCENTAGE: float = 0.45  # Target: 40-50% FAST mode
    TARGET_BALANCED_MODE_PERCENTAGE: float = 0.35  # Target: 30-40% BALANCED mode
    TARGET_DEEP_MODE_PERCENTAGE: float = 0.20  # Target: 20-30% DEEP mode

    @field_validator("DEFAULT_QUERY_MODE")
    @classmethod
    def validate_default_query_mode(cls, v: str) -> str:
        """Validate default query mode is valid"""
        valid_modes = ["fast", "balanced", "deep"]
        if v.lower() not in valid_modes:
            raise ValueError(
                f"Invalid DEFAULT_QUERY_MODE: '{v}'. Must be one of: {', '.join(valid_modes)}"
            )
        return v.lower()

    @field_validator("ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE")
    @classmethod
    def validate_adaptive_complexity_threshold_simple(cls, v: float) -> float:
        """Validate adaptive simple complexity threshold"""
        if v <= 0.0 or v >= 1.0:
            raise ValueError(
                f"ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE ({v}) must be between 0.0 and 1.0"
            )
        return v

    @field_validator("ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX")
    @classmethod
    def validate_adaptive_complexity_threshold_complex(cls, v: float) -> float:
        """Validate adaptive complex complexity threshold"""
        if v <= 0.0 or v >= 1.0:
            raise ValueError(
                f"ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX ({v}) must be between 0.0 and 1.0"
            )
        return v

    @field_validator("FAST_MODE_TIMEOUT")
    @classmethod
    def validate_fast_mode_timeout(cls, v: float) -> float:
        """Validate FAST mode timeout"""
        if v <= 0.0:
            raise ValueError("FAST_MODE_TIMEOUT must be positive")
        if v > 5.0:
            logger.warning(f"FAST_MODE_TIMEOUT ({v}s) is high for FAST mode")
        return v

    @field_validator("BALANCED_MODE_TIMEOUT")
    @classmethod
    def validate_balanced_mode_timeout(cls, v: float) -> float:
        """Validate BALANCED mode timeout"""
        if v <= 0.0:
            raise ValueError("BALANCED_MODE_TIMEOUT must be positive")
        if v > 10.0:
            logger.warning(f"BALANCED_MODE_TIMEOUT ({v}s) is high for BALANCED mode")
        return v

    @field_validator("DEEP_MODE_TIMEOUT")
    @classmethod
    def validate_deep_mode_timeout(cls, v: float) -> float:
        """Validate DEEP mode timeout"""
        if v <= 0.0:
            raise ValueError("DEEP_MODE_TIMEOUT must be positive")
        if v > 30.0:
            logger.warning(f"DEEP_MODE_TIMEOUT ({v}s) is very high for DEEP mode")
        return v

    @field_validator("FAST_MODE_TOP_K", "BALANCED_MODE_TOP_K", "DEEP_MODE_TOP_K")
    @classmethod
    def validate_mode_top_k(cls, v: int) -> int:
        """Validate mode top_k parameters"""
        if v < 1:
            raise ValueError("Mode top_k must be at least 1")
        if v > 50:
            logger.warning(f"Mode top_k ({v}) is very high, may impact performance")
        return v

    @field_validator(
        "FAST_MODE_CACHE_TTL", "BALANCED_MODE_CACHE_TTL", "DEEP_MODE_CACHE_TTL"
    )
    @classmethod
    def validate_mode_cache_ttl(cls, v: int) -> int:
        """Validate mode cache TTL"""
        if v < 60:
            raise ValueError("Mode cache TTL must be at least 60 seconds")
        if v > 86400:
            logger.warning(f"Mode cache TTL ({v}s) is very long (>24h)")
        return v

    @field_validator("TUNING_INTERVAL_HOURS")
    @classmethod
    def validate_tuning_interval(cls, v: int) -> int:
        """Validate tuning interval"""
        if v < 1:
            raise ValueError("TUNING_INTERVAL_HOURS must be at least 1")
        if v > 168:  # 1 week
            logger.warning(f"TUNING_INTERVAL_HOURS ({v}) is very long (>1 week)")
        return v

    @field_validator("TUNING_MIN_SAMPLES")
    @classmethod
    def validate_tuning_min_samples(cls, v: int) -> int:
        """Validate minimum samples for tuning"""
        if v < 10:
            raise ValueError("TUNING_MIN_SAMPLES must be at least 10")
        if v > 10000:
            logger.warning(f"TUNING_MIN_SAMPLES ({v}) is very high")
        return v

    @field_validator("MIN_SAMPLES_FOR_LEARNING")
    @classmethod
    def validate_min_samples_for_learning(cls, v: int) -> int:
        """Validate minimum samples for pattern learning"""
        if v < 10:
            raise ValueError("MIN_SAMPLES_FOR_LEARNING must be at least 10")
        if v > 1000:
            logger.warning(f"MIN_SAMPLES_FOR_LEARNING ({v}) is very high")
        return v

    @field_validator("PATTERN_SIMILARITY_THRESHOLD")
    @classmethod
    def validate_pattern_similarity_threshold(cls, v: float) -> float:
        """Validate pattern similarity threshold"""
        if v <= 0.0 or v > 1.0:
            raise ValueError(
                f"PATTERN_SIMILARITY_THRESHOLD ({v}) must be between 0.0 and 1.0"
            )
        return v

    @field_validator("PATTERN_LEARNING_WINDOW_DAYS")
    @classmethod
    def validate_pattern_learning_window(cls, v: int) -> int:
        """Validate pattern learning window"""
        if v < 1:
            raise ValueError("PATTERN_LEARNING_WINDOW_DAYS must be at least 1")
        if v > 365:
            logger.warning(f"PATTERN_LEARNING_WINDOW_DAYS ({v}) is very long (>1 year)")
        return v

    @field_validator(
        "TARGET_FAST_MODE_PERCENTAGE",
        "TARGET_BALANCED_MODE_PERCENTAGE",
        "TARGET_DEEP_MODE_PERCENTAGE",
    )
    @classmethod
    def validate_target_mode_percentage(cls, v: float) -> float:
        """Validate target mode percentages"""
        if v < 0.0 or v > 1.0:
            raise ValueError(
                f"Target mode percentage ({v}) must be between 0.0 and 1.0"
            )
        return v

    # Hybrid RAG Configuration (Static + Agentic Pipeline)
    HYBRID_RAG_ENABLED: bool = True  # Enable Hybrid RAG system with routing

    # Complexity Thresholds (for routing decisions)
    COMPLEXITY_THRESHOLD_SIMPLE: float = 0.3  # Below this: Static RAG
    COMPLEXITY_THRESHOLD_COMPLEX: float = 0.7  # Above this: Agentic RAG
    # Between thresholds: Static RAG with validation

    # Confidence Thresholds (for escalation decisions)
    CONFIDENCE_THRESHOLD_HIGH: float = 0.7  # High confidence, no escalation needed
    CONFIDENCE_THRESHOLD_LOW: float = 0.4  # Low confidence, escalate to agentic

    # Static RAG Pipeline Parameters
    STATIC_RAG_TOP_K: int = 5  # Number of documents to retrieve for static RAG
    STATIC_RAG_TIMEOUT: float = 2.0  # Timeout for static RAG pipeline (seconds)
    ENABLE_STATIC_RAG_CACHE: bool = True  # Enable caching for static RAG responses
    STATIC_RAG_CACHE_TTL: int = 3600  # Static RAG cache TTL (1 hour)

    # Agentic RAG Pipeline Parameters
    AGENTIC_RAG_MAX_ITERATIONS: int = (
        10  # Maximum ReAct iterations for agentic pipeline
    )

    # Escalation Configuration
    ENABLE_AUTO_ESCALATION: bool = (
        True  # Enable automatic escalation from static to agentic
    )
    ESCALATION_CONFIDENCE_THRESHOLD: float = 0.4  # Confidence threshold for escalation

    @field_validator("COMPLEXITY_THRESHOLD_SIMPLE")
    @classmethod
    def validate_complexity_threshold_simple(cls, v: float) -> float:
        """Validate simple complexity threshold"""
        if v <= 0.0 or v >= 1.0:
            raise ValueError(
                f"COMPLEXITY_THRESHOLD_SIMPLE ({v}) must be between 0.0 and 1.0"
            )
        return v

    @field_validator("COMPLEXITY_THRESHOLD_COMPLEX")
    @classmethod
    def validate_complexity_threshold_complex(cls, v: float) -> float:
        """Validate complex complexity threshold"""
        if v <= 0.0 or v >= 1.0:
            raise ValueError(
                f"COMPLEXITY_THRESHOLD_COMPLEX ({v}) must be between 0.0 and 1.0"
            )
        return v

    @field_validator("CONFIDENCE_THRESHOLD_HIGH")
    @classmethod
    def validate_confidence_threshold_high(cls, v: float) -> float:
        """Validate high confidence threshold"""
        if v <= 0.0 or v >= 1.0:
            raise ValueError(
                f"CONFIDENCE_THRESHOLD_HIGH ({v}) must be between 0.0 and 1.0"
            )
        return v

    @field_validator("CONFIDENCE_THRESHOLD_LOW")
    @classmethod
    def validate_confidence_threshold_low(cls, v: float) -> float:
        """Validate low confidence threshold"""
        if v <= 0.0 or v >= 1.0:
            raise ValueError(
                f"CONFIDENCE_THRESHOLD_LOW ({v}) must be between 0.0 and 1.0"
            )
        return v

    @field_validator("STATIC_RAG_TOP_K")
    @classmethod
    def validate_static_rag_top_k(cls, v: int) -> int:
        """Validate static RAG top_k parameter"""
        if v < 1:
            raise ValueError("STATIC_RAG_TOP_K must be at least 1")
        if v > 50:
            logger.warning(
                f"STATIC_RAG_TOP_K ({v}) is very high, may impact performance"
            )
        return v

    @field_validator("STATIC_RAG_TIMEOUT")
    @classmethod
    def validate_static_rag_timeout(cls, v: float) -> float:
        """Validate static RAG timeout"""
        if v < 0.5:
            raise ValueError("STATIC_RAG_TIMEOUT must be at least 0.5 seconds")
        if v > 10.0:
            logger.warning(f"STATIC_RAG_TIMEOUT ({v}s) is very high")
        return v

    @field_validator("AGENTIC_RAG_MAX_ITERATIONS")
    @classmethod
    def validate_agentic_rag_max_iterations(cls, v: int) -> int:
        """Validate agentic RAG max iterations"""
        if v < 1:
            raise ValueError("AGENTIC_RAG_MAX_ITERATIONS must be at least 1")
        if v > 50:
            logger.warning(f"AGENTIC_RAG_MAX_ITERATIONS ({v}) is very high")
        return v

    @field_validator("STATIC_RAG_CACHE_TTL")
    @classmethod
    def validate_static_rag_cache_ttl(cls, v: int) -> int:
        """Validate static RAG cache TTL"""
        if v < 60:
            raise ValueError("STATIC_RAG_CACHE_TTL must be at least 60 seconds")
        if v > 86400:
            logger.warning(f"STATIC_RAG_CACHE_TTL ({v}s) is very long (>24h)")
        return v

    # Performance Optimization (Phase 1)
    ENABLE_QUERY_FAST_PATH: bool = True  # Enable fast path for simple queries
    EMBEDDING_BATCH_SIZE_SMALL: int = 10  # Threshold for small documents
    EMBEDDING_BATCH_SIZE_MEDIUM: int = 32  # Batch size for medium documents
    EMBEDDING_BATCH_SIZE_LARGE: int = 64  # Batch size for large documents

    # Performance Optimization (Phase 2)
    ENABLE_LLM_CACHE: bool = True  # Enable LLM response caching
    LLM_CACHE_TTL: int = 3600  # LLM cache TTL in seconds (1 hour)
    ENABLE_BACKGROUND_TASKS: bool = True  # Enable background task processing
    MAX_CONCURRENT_TASKS: int = 5  # Maximum concurrent background tasks
    BACKGROUND_UPLOAD_THRESHOLD: int = (
        5242880  # File size threshold for background processing (5MB)
    )

    @field_validator("CACHE_L1_TTL")
    @classmethod
    def validate_cache_l1_ttl(cls, v: int) -> int:
        """Validate L1 cache TTL"""
        if v < 60:
            raise ValueError("CACHE_L1_TTL must be at least 60 seconds")
        if v > 86400:
            logger.warning(f"CACHE_L1_TTL ({v}s) is very long (>24h)")
        return v

    @field_validator("CACHE_L2_THRESHOLD")
    @classmethod
    def validate_cache_l2_threshold(cls, v: int) -> int:
        """Validate L2 cache promotion threshold"""
        if v < 1:
            raise ValueError("CACHE_L2_THRESHOLD must be at least 1")
        if v > 100:
            logger.warning(f"CACHE_L2_THRESHOLD ({v}) is very high")
        return v

    @field_validator("CACHE_L2_MAX_SIZE")
    @classmethod
    def validate_cache_l2_max_size(cls, v: int) -> int:
        """Validate L2 cache maximum size"""
        if v < 10:
            raise ValueError("CACHE_L2_MAX_SIZE must be at least 10")
        if v > 100000:
            logger.warning(f"CACHE_L2_MAX_SIZE ({v}) is very large")
        return v

    # Document Processing
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    CHUNKING_STRATEGY: str = "semantic"  # semantic, sentence, paragraph, heading, fixed
    MAX_FILE_SIZE: int = 52428800  # 50MB (increased from 10MB)
    

    
    # Image Processing - PaddleOCR Advanced
    # https://github.com/PaddlePaddle/PaddleOCR
    # 
    # Features:
    # 1. PP-OCRv5: Latest OCR engine (98%+ accuracy)
    # 2. PP-StructureV3: Table structure recognition (98%+ accuracy)
    # 3. Layout Analysis: Automatic document structure detection
    # 4. Multi-language Support: 80+ languages (Korean optimized)
    #
    ENABLE_PADDLEOCR: bool = True  # PaddleOCR 활성화
    PADDLEOCR_USE_GPU: bool = True  # GPU 사용 (자동 감지, 없으면 CPU)
    PADDLEOCR_LANG: str = "korean"  # 언어 설정 (korean, en, ch, japan, etc.)
    PADDLEOCR_USE_ANGLE_CLS: bool = True  # 각도 분류기 (회전된 텍스트 처리)
    
    # Advanced Features
    PADDLEOCR_ENABLE_TABLE: bool = True  # PP-StructureV3 표 인식 활성화
    PADDLEOCR_ENABLE_LAYOUT: bool = True  # 레이아웃 분석 활성화
    PADDLEOCR_SHOW_LOG: bool = False  # PaddleOCR 로그 표시
    
    # PaddleOCR Advanced - Phase 1: PP-ChatOCRv4 (Document Q&A)
    ENABLE_PP_CHATOCR: bool = True  # PP-ChatOCR 문서 Q&A 활성화
    PP_CHATOCR_VERSION: str = "PP-ChatOCRv4"  # ChatOCR 버전
    PP_CHATOCR_USE_LLM: bool = True  # LLM 사용 여부 (False면 단순 검색)
    
    # PaddleOCR Advanced - Phase 2: PaddleOCR-VL (Multimodal Parsing) ✅
    ENABLE_PADDLEOCR_VL: bool = True  # PaddleOCR-VL 멀티모달 파싱
    PADDLEOCR_VL_MODEL: str = "PP-OCRv4"  # VL 모델 버전
    
    # PaddleOCR Advanced - Phase 3: PP-DocTranslation (Document Translation) ✅
    ENABLE_PP_DOC_TRANSLATION: bool = True  # PP-DocTranslation
    PP_DOC_TRANSLATION_SERVICE: str = "auto"  # 'auto', 'google', 'deepl', 'papago'
    
    # Translation API Keys (Optional - Phase 3)
    DEEPL_API_KEY: Optional[str] = None
    PAPAGO_CLIENT_ID: Optional[str] = None
    PAPAGO_CLIENT_SECRET: Optional[str] = None
    


    # Memory Configuration
    STM_TTL: int = 3600  # 1 hour
    MAX_CONVERSATION_HISTORY: int = 20

    # Application Configuration
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json | text
    LOG_FILE: Optional[str] = "logs/app.log"

    # Optimization Flags (Phase 1)
    USE_DIRECT_AGENTS: bool = True  # Use optimized direct agents (50-70% faster)
    USE_OPTIMIZED_REACT: bool = True  # Use optimized ReAct loop (30-40% faster)
    ENABLE_OPENTELEMETRY: bool = False  # Enable distributed tracing

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider is supported"""
        valid_providers = ["ollama", "openai", "claude"]
        if v.lower() not in valid_providers:
            raise ValueError(
                f"Invalid LLM_PROVIDER: '{v}'. Must be one of: {', '.join(valid_providers)}\n"
                f"Please check your .env file and set LLM_PROVIDER to a valid option."
            )
        return v.lower()

    @field_validator("CHUNK_SIZE")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        """Validate chunk size is reasonable"""
        if v < 100:
            raise ValueError(
                f"CHUNK_SIZE ({v}) is too small. Minimum recommended value is 100 characters."
            )
        if v > 5000:
            logger.warning(
                f"CHUNK_SIZE ({v}) is very large. This may impact performance. "
                f"Recommended range: 200-1000 characters."
            )
        return v

    @field_validator("CHUNK_OVERLAP")
    @classmethod
    def validate_chunk_overlap(cls, v: int) -> int:
        """Validate chunk overlap is reasonable"""
        if v < 0:
            raise ValueError("CHUNK_OVERLAP cannot be negative.")
        return v

    @field_validator("MAX_FILE_SIZE")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        """Validate max file size is reasonable"""
        if v < 1024:  # Less than 1KB
            raise ValueError(
                f"MAX_FILE_SIZE ({v} bytes) is too small. Minimum recommended value is 1024 bytes (1KB)."
            )
        if v > 104857600:  # More than 100MB
            logger.warning(
                f"MAX_FILE_SIZE ({v} bytes) is very large. This may cause memory issues. "
                f"Recommended maximum: 10485760 bytes (10MB)."
            )
        return v

    @field_validator("STM_TTL")
    @classmethod
    def validate_stm_ttl(cls, v: int) -> int:
        """Validate STM TTL is reasonable"""
        if v < 60:
            logger.warning(
                f"STM_TTL ({v} seconds) is very short. Conversations may expire too quickly. "
                f"Recommended minimum: 300 seconds (5 minutes)."
            )
        if v > 86400:  # More than 24 hours
            logger.warning(
                f"STM_TTL ({v} seconds) is very long. This may consume excessive memory. "
                f"Recommended maximum: 3600 seconds (1 hour)."
            )
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid LOG_LEVEL: '{v}'. Must be one of: {', '.join(valid_levels)}"
            )
        return v.upper()

    @model_validator(mode="after")
    def validate_chunk_overlap_vs_size(self) -> "Settings":
        """Validate chunk overlap is not larger than chunk size"""
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError(
                f"CHUNK_OVERLAP ({self.CHUNK_OVERLAP}) must be smaller than CHUNK_SIZE ({self.CHUNK_SIZE}). "
                f"Recommended: CHUNK_OVERLAP should be 10-20% of CHUNK_SIZE."
            )
        return self

    @model_validator(mode="after")
    def validate_hybrid_rag_thresholds(self) -> "Settings":
        """Validate Hybrid RAG threshold relationships"""
        # Validate complexity thresholds are properly ordered
        if self.COMPLEXITY_THRESHOLD_SIMPLE >= self.COMPLEXITY_THRESHOLD_COMPLEX:
            raise ValueError(
                f"COMPLEXITY_THRESHOLD_SIMPLE ({self.COMPLEXITY_THRESHOLD_SIMPLE}) must be less than "
                f"COMPLEXITY_THRESHOLD_COMPLEX ({self.COMPLEXITY_THRESHOLD_COMPLEX})"
            )

        # Validate confidence thresholds are properly ordered
        if self.CONFIDENCE_THRESHOLD_LOW >= self.CONFIDENCE_THRESHOLD_HIGH:
            raise ValueError(
                f"CONFIDENCE_THRESHOLD_LOW ({self.CONFIDENCE_THRESHOLD_LOW}) must be less than "
                f"CONFIDENCE_THRESHOLD_HIGH ({self.CONFIDENCE_THRESHOLD_HIGH})"
            )

        return self

    @model_validator(mode="after")
    def validate_adaptive_routing_config(self) -> "Settings":
        """Validate Adaptive Routing configuration relationships"""
        # Validate adaptive complexity thresholds are properly ordered
        if (
            self.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE
            >= self.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX
        ):
            raise ValueError(
                f"ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE ({self.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE}) "
                f"must be less than ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX ({self.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX})"
            )

        # Validate mode timeouts are properly ordered
        if self.FAST_MODE_TIMEOUT >= self.BALANCED_MODE_TIMEOUT:
            logger.warning(
                f"FAST_MODE_TIMEOUT ({self.FAST_MODE_TIMEOUT}s) should be less than "
                f"BALANCED_MODE_TIMEOUT ({self.BALANCED_MODE_TIMEOUT}s)"
            )

        if self.BALANCED_MODE_TIMEOUT >= self.DEEP_MODE_TIMEOUT:
            logger.warning(
                f"BALANCED_MODE_TIMEOUT ({self.BALANCED_MODE_TIMEOUT}s) should be less than "
                f"DEEP_MODE_TIMEOUT ({self.DEEP_MODE_TIMEOUT}s)"
            )

        # Validate mode top_k are properly ordered
        if self.FAST_MODE_TOP_K > self.BALANCED_MODE_TOP_K:
            logger.warning(
                f"FAST_MODE_TOP_K ({self.FAST_MODE_TOP_K}) should not exceed "
                f"BALANCED_MODE_TOP_K ({self.BALANCED_MODE_TOP_K})"
            )

        if self.BALANCED_MODE_TOP_K > self.DEEP_MODE_TOP_K:
            logger.warning(
                f"BALANCED_MODE_TOP_K ({self.BALANCED_MODE_TOP_K}) should not exceed "
                f"DEEP_MODE_TOP_K ({self.DEEP_MODE_TOP_K})"
            )

        # Validate target mode percentages sum to approximately 1.0
        total_percentage = (
            self.TARGET_FAST_MODE_PERCENTAGE
            + self.TARGET_BALANCED_MODE_PERCENTAGE
            + self.TARGET_DEEP_MODE_PERCENTAGE
        )

        if abs(total_percentage - 1.0) > 0.05:  # Allow 5% tolerance
            logger.warning(
                f"Target mode percentages sum to {total_percentage:.2f}, "
                f"should be close to 1.0 (FAST: {self.TARGET_FAST_MODE_PERCENTAGE}, "
                f"BALANCED: {self.TARGET_BALANCED_MODE_PERCENTAGE}, "
                f"DEEP: {self.TARGET_DEEP_MODE_PERCENTAGE})"
            )

        return self

    @model_validator(mode="after")
    def validate_provider_requirements(self) -> "Settings":
        """Validate that required credentials are provided for the selected provider"""
        provider = self.LLM_PROVIDER.lower()

        # Check primary provider
        is_valid, error_msg = self.validate_provider_config(provider)
        if not is_valid:
            logger.error(
                f"Configuration error for primary provider '{provider}': {error_msg}"
            )
            # Don't raise error here, let the application handle it gracefully

        # Check fallback providers
        fallback_providers = self.get_fallback_providers()
        for fallback in fallback_providers:
            is_valid, error_msg = self.validate_provider_config(fallback)
            if not is_valid:
                logger.warning(
                    f"Fallback provider '{fallback}' is not properly configured: {error_msg}"
                )

        return self

    def get_fallback_providers(self) -> List[str]:
        """
        Get list of fallback providers in order of preference.

        Returns:
            List of provider names to try if primary provider fails
        """
        if not self.LLM_FALLBACK_PROVIDERS:
            return []

        fallbacks = [
            p.strip().lower()
            for p in self.LLM_FALLBACK_PROVIDERS.split(",")
            if p.strip()
        ]

        # Validate fallback providers
        valid_providers = ["ollama", "openai", "claude"]
        validated_fallbacks = []
        for provider in fallbacks:
            if provider in valid_providers and provider != self.LLM_PROVIDER:
                validated_fallbacks.append(provider)
            elif self.DEBUG:  # Only log in debug mode
                logger.warning(f"Ignoring invalid fallback provider: {provider}")

        return validated_fallbacks

    def validate_provider_config(self, provider: str) -> tuple[bool, Optional[str]]:
        """
        Validate configuration for a specific provider.

        Args:
            provider: Provider name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        provider = provider.lower()

        if provider == "openai":
            if not self.OPENAI_API_KEY:
                return False, (
                    "OpenAI API key is required but not configured. "
                    "Please set OPENAI_API_KEY environment variable. "
                    "Get your API key from: https://platform.openai.com/api-keys"
                )

        elif provider == "claude":
            if not self.ANTHROPIC_API_KEY:
                return False, (
                    "Anthropic API key is required but not configured. "
                    "Please set ANTHROPIC_API_KEY environment variable. "
                    "Get your API key from: https://console.anthropic.com/settings/keys"
                )

        elif provider == "ollama":
            # Ollama doesn't require API key, but we can check if URL is set
            if not self.OLLAMA_BASE_URL:
                return False, (
                    "Ollama base URL is not configured. "
                    "Please set OLLAMA_BASE_URL environment variable (default: http://localhost:11434). "
                    "Install Ollama from: https://ollama.ai"
                )

        else:
            return False, f"Unknown provider: {provider}"

        return True, None

    def get_available_providers(self) -> List[str]:
        """
        Get list of providers that have valid configuration.

        Returns:
            List of provider names that are properly configured
        """
        available = []

        for provider in ["ollama", "openai", "claude"]:
            is_valid, _ = self.validate_provider_config(provider)
            if is_valid:
                available.append(provider)

        return available

    def get_provider_config_status(self) -> dict:
        """
        Get detailed configuration status for all providers.

        Returns:
            Dictionary with provider configuration details
        """
        status = {
            "primary_provider": self.LLM_PROVIDER,
            "primary_model": self.LLM_MODEL,
            "fallback_providers": self.get_fallback_providers(),
            "providers": {},
        }

        for provider in ["ollama", "openai", "claude"]:
            is_valid, error_msg = self.validate_provider_config(provider)
            status["providers"][provider] = {
                "configured": is_valid,
                "error": error_msg if not is_valid else None,
            }

            # Add provider-specific details
            if provider == "ollama":
                status["providers"][provider]["base_url"] = self.OLLAMA_BASE_URL
            elif provider == "openai":
                status["providers"][provider]["has_api_key"] = bool(self.OPENAI_API_KEY)
            elif provider == "claude":
                status["providers"][provider]["has_api_key"] = bool(
                    self.ANTHROPIC_API_KEY
                )

        return status

    # ==========================================
    # Agent Builder Configuration
    # ==========================================
    
    # Agent Builder Feature Toggle
    AGENT_BUILDER_ENABLED: bool = True
    
    # Resource Limits per User
    AGENT_BUILDER_MAX_AGENTS_PER_USER: int = 50
    AGENT_BUILDER_MAX_WORKFLOWS_PER_USER: int = 100
    AGENT_BUILDER_MAX_BLOCKS_PER_USER: int = 200
    AGENT_BUILDER_MAX_KNOWLEDGEBASES_PER_USER: int = 20
    
    # Block Execution Configuration
    BLOCK_EXECUTOR_TYPE: str = "restricted"  # "restricted" or "docker"
    BLOCK_EXECUTOR_TIMEOUT: int = 5  # seconds
    BLOCK_EXECUTOR_MAX_MEMORY: int = 128  # MB
    
    # Secret Management
    SECRET_ENCRYPTION_KEY: str = Field(
        default="change-this-in-production-use-strong-key",
        env="SECRET_ENCRYPTION_KEY"
    )
    SECRET_KEY_ROTATION_DAYS: int = 90
    
    # Execution Scheduler
    SCHEDULER_CHECK_INTERVAL: int = 60  # seconds
    SCHEDULER_MAX_CONCURRENT_JOBS: int = 10
    
    # Permission System
    PERMISSION_CACHE_TTL: int = 300  # seconds (5 minutes)
    PERMISSION_CACHE_MAX_SIZE: int = 1000
    
    # Workflow Execution
    WORKFLOW_MAX_EXECUTION_TIME: int = 300  # seconds (5 minutes)
    WORKFLOW_MAX_STEPS: int = 100
    
    # Agent Execution
    AGENT_EXECUTION_TIMEOUT: int = 60  # seconds
    AGENT_MAX_TOOL_CALLS: int = 20
    
    # Knowledgebase Configuration
    KB_DEFAULT_CHUNK_SIZE: int = 500
    KB_DEFAULT_CHUNK_OVERLAP: int = 50
    KB_MAX_DOCUMENTS_PER_KB: int = 1000
    KB_MAX_FILE_SIZE_MB: int = 50

    def print_config_summary(self) -> None:
        """
        Print a human-readable configuration summary.
        Useful for debugging and verifying configuration.
        """
        print("\n" + "=" * 70)
        print("AGENTIC RAG SYSTEM - CONFIGURATION SUMMARY")
        print("=" * 70)

        # LLM Configuration
        print("\n[LLM Configuration]")
        print(f"  Primary Provider: {self.LLM_PROVIDER}")
        print(f"  Primary Model: {self.LLM_MODEL}")
        print(f"  Local Timeout: {self.LLM_TIMEOUT_LOCAL}s")
        print(f"  Cloud Timeout: {self.LLM_TIMEOUT_CLOUD}s")

        fallbacks = self.get_fallback_providers()
        if fallbacks:
            print(f"  Fallback Providers: {', '.join(fallbacks)}")
        else:
            print(f"  Fallback Providers: None")

        # Provider Status
        print("\n[Provider Status]")
        for provider in ["ollama", "openai", "claude"]:
            is_valid, error_msg = self.validate_provider_config(provider)
            status_icon = "[OK]" if is_valid else "[X]"
            status_text = "Configured" if is_valid else "Not Configured"
            print(f"  {status_icon} {provider.capitalize()}: {status_text}")
            if not is_valid and self.DEBUG:
                print(f"      -> {error_msg}")

        # Database Configuration
        print("\n[Database Configuration]")
        print(f"  Milvus: {self.MILVUS_HOST}:{self.MILVUS_PORT}")
        print(f"    - Documents Collection: {self.MILVUS_COLLECTION_NAME}")
        print(f"    - LTM Collection: {self.MILVUS_LTM_COLLECTION_NAME}")
        print(f"    - Keep Loaded: {self.MILVUS_KEEP_LOADED}")
        print(f"  Redis: {self.REDIS_HOST}:{self.REDIS_PORT} (DB: {self.REDIS_DB})")
        print(f"    - Max Connections: {self.REDIS_MAX_CONNECTIONS}")

        # Embedding Configuration
        print("\n[Embedding Configuration]")
        print(f"  Model: {self.EMBEDDING_MODEL}")

        # Performance Configuration
        print("\n[Performance Configuration]")
        print(f"  Fast Path Enabled: {self.ENABLE_QUERY_FAST_PATH}")
        print(f"  Embedding Batch Sizes:")
        print(f"    - Small (<{self.EMBEDDING_BATCH_SIZE_SMALL}): All at once")
        print(f"    - Medium: {self.EMBEDDING_BATCH_SIZE_MEDIUM}")
        print(f"    - Large: {self.EMBEDDING_BATCH_SIZE_LARGE}")

        # Hybrid RAG Configuration
        print("\n[Hybrid RAG Configuration]")
        print(f"  Hybrid RAG Enabled: {self.HYBRID_RAG_ENABLED}")
        if self.HYBRID_RAG_ENABLED:
            print(f"  Complexity Thresholds:")
            print(f"    - Simple (Static RAG): < {self.COMPLEXITY_THRESHOLD_SIMPLE}")
            print(
                f"    - Medium (Static + Validation): {self.COMPLEXITY_THRESHOLD_SIMPLE} - {self.COMPLEXITY_THRESHOLD_COMPLEX}"
            )
            print(f"    - Complex (Agentic RAG): > {self.COMPLEXITY_THRESHOLD_COMPLEX}")
            print(f"  Confidence Thresholds:")
            print(f"    - High (No Escalation): >= {self.CONFIDENCE_THRESHOLD_HIGH}")
            print(
                f"    - Medium: {self.CONFIDENCE_THRESHOLD_LOW} - {self.CONFIDENCE_THRESHOLD_HIGH}"
            )
            print(f"    - Low (Escalate): < {self.CONFIDENCE_THRESHOLD_LOW}")
            print(f"  Static RAG:")
            print(f"    - Top K: {self.STATIC_RAG_TOP_K}")
            print(f"    - Timeout: {self.STATIC_RAG_TIMEOUT}s")
            print(f"    - Cache Enabled: {self.ENABLE_STATIC_RAG_CACHE}")
            print(f"    - Cache TTL: {self.STATIC_RAG_CACHE_TTL}s")
            print(f"  Agentic RAG:")
            print(f"    - Max Iterations: {self.AGENTIC_RAG_MAX_ITERATIONS}")
            print(f"  Auto Escalation: {self.ENABLE_AUTO_ESCALATION}")

        # Adaptive Routing Configuration
        print("\n[Adaptive Routing Configuration]")
        print(f"  Adaptive Routing Enabled: {self.ADAPTIVE_ROUTING_ENABLED}")
        if self.ADAPTIVE_ROUTING_ENABLED:
            print(f"  Complexity Thresholds:")
            print(f"    - FAST mode: < {self.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE}")
            print(
                f"    - BALANCED mode: {self.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE} - {self.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX}"
            )
            print(f"    - DEEP mode: > {self.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX}")
            print(f"  Mode Timeouts:")
            print(f"    - FAST: {self.FAST_MODE_TIMEOUT}s")
            print(f"    - BALANCED: {self.BALANCED_MODE_TIMEOUT}s")
            print(f"    - DEEP: {self.DEEP_MODE_TIMEOUT}s")
            print(f"  Mode Parameters (top_k):")
            print(f"    - FAST: {self.FAST_MODE_TOP_K}")
            print(f"    - BALANCED: {self.BALANCED_MODE_TOP_K}")
            print(f"    - DEEP: {self.DEEP_MODE_TOP_K}")
            print(f"  Mode Cache TTLs:")
            print(
                f"    - FAST: {self.FAST_MODE_CACHE_TTL}s ({self.FAST_MODE_CACHE_TTL / 60:.0f} min)"
            )
            print(
                f"    - BALANCED: {self.BALANCED_MODE_CACHE_TTL}s ({self.BALANCED_MODE_CACHE_TTL / 60:.0f} min)"
            )
            print(
                f"    - DEEP: {self.DEEP_MODE_CACHE_TTL}s ({self.DEEP_MODE_CACHE_TTL / 60:.0f} min)"
            )
            print(f"  Auto-Tuning:")
            print(f"    - Enabled: {self.ENABLE_AUTO_THRESHOLD_TUNING}")
            print(f"    - Interval: {self.TUNING_INTERVAL_HOURS}h")
            print(f"    - Min Samples: {self.TUNING_MIN_SAMPLES}")
            print(f"    - Dry Run: {self.TUNING_DRY_RUN}")
            print(f"  Pattern Learning:")
            print(f"    - Enabled: {self.ENABLE_PATTERN_LEARNING}")
            print(f"    - Min Samples: {self.MIN_SAMPLES_FOR_LEARNING}")
            print(f"    - Similarity Threshold: {self.PATTERN_SIMILARITY_THRESHOLD}")
            print(f"    - Window: {self.PATTERN_LEARNING_WINDOW_DAYS} days")
            print(f"  Target Distribution:")
            print(f"    - FAST: {self.TARGET_FAST_MODE_PERCENTAGE * 100:.0f}%")
            print(f"    - BALANCED: {self.TARGET_BALANCED_MODE_PERCENTAGE * 100:.0f}%")
            print(f"    - DEEP: {self.TARGET_DEEP_MODE_PERCENTAGE * 100:.0f}%")

        # Document Processing
        print("\n[Document Processing]")
        print(f"  Chunk Size: {self.CHUNK_SIZE} characters")
        print(f"  Chunk Overlap: {self.CHUNK_OVERLAP} characters")
        print(f"  Max File Size: {self.MAX_FILE_SIZE / 1024 / 1024:.1f} MB")

        # Memory Configuration
        print("\n[Memory Configuration]")
        print(f"  STM TTL: {self.STM_TTL} seconds ({self.STM_TTL / 60:.1f} minutes)")
        print(f"  Max Conversation History: {self.MAX_CONVERSATION_HISTORY} messages")

        # Application Configuration
        print("\n[Application Configuration]")
        print(f"  Debug Mode: {self.DEBUG}")
        print(f"  Log Level: {self.LOG_LEVEL}")

        print("\n" + "=" * 70 + "\n")

    def validate_required_config(self) -> tuple[bool, List[str]]:
        """
        Validate that all required configuration is present and valid.

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Validate primary provider configuration
        is_valid, error_msg = self.validate_provider_config(self.LLM_PROVIDER)
        if not is_valid:
            errors.append(f"Primary LLM provider '{self.LLM_PROVIDER}': {error_msg}")

        # Validate required fields
        if not self.MILVUS_HOST:
            errors.append("MILVUS_HOST is required but not set")

        if not self.REDIS_HOST:
            errors.append("REDIS_HOST is required but not set")

        if not self.EMBEDDING_MODEL:
            errors.append("EMBEDDING_MODEL is required but not set")

        if not self.LLM_MODEL:
            errors.append("LLM_MODEL is required but not set")

        return (len(errors) == 0, errors)


# Initialize settings
try:
    settings = Settings()

    # Validate configuration
    is_valid, errors = settings.validate_required_config()

    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")

        # Only print config summary if explicitly requested via environment variable
        if settings.DEBUG and os.getenv("PRINT_CONFIG_SUMMARY", "false").lower() == "true":
            settings.print_config_summary()

        # Don't exit, let the application handle it
        logger.warning(
            "Application may not function correctly with invalid configuration"
        )
    else:
        logger.info("Configuration loaded successfully")
        # Only print config summary if explicitly requested via environment variable
        if settings.DEBUG and os.getenv("PRINT_CONFIG_SUMMARY", "false").lower() == "true":
            settings.print_config_summary()

except ValidationError as e:
    logger.error("Failed to load configuration:")
    for error in e.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        logger.error(f"  - {field}: {message}")

    logger.error(
        "\nPlease check your .env file and ensure all required variables are set correctly."
    )
    logger.error("See .env.example for a template with all available options.")

    # Re-raise to prevent application from starting with invalid config
    raise
