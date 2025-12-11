"""
Cost Optimization Engine for Agent Builder.

Optimizes LLM costs through smart model selection, caching, and batching.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from collections import defaultdict
import json
import hashlib

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class ModelTier(str, Enum):
    """Model performance tiers."""
    PREMIUM = "premium"      # GPT-4, Claude 3 Opus
    STANDARD = "standard"    # GPT-3.5, Claude 3 Sonnet
    ECONOMY = "economy"      # Llama 2, Mistral
    LOCAL = "local"          # Ollama models


class CostMetrics:
    """Cost tracking metrics."""
    
    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_cost_usd = 0.0
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.avg_cost_per_request = 0.0
        self.cost_by_model: Dict[str, float] = defaultdict(float)
        self.tokens_by_model: Dict[str, int] = defaultdict(int)


class ModelPricing:
    """Model pricing information."""
    
    # Pricing per 1K tokens (USD)
    PRICING = {
        # OpenAI
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        
        # Anthropic
        "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku": {"prompt": 0.00025, "completion": 0.00125},
        
        # Cohere
        "command": {"prompt": 0.001, "completion": 0.002},
        "command-light": {"prompt": 0.0003, "completion": 0.0006},
        
        # Local models (free)
        "llama2": {"prompt": 0.0, "completion": 0.0},
        "mistral": {"prompt": 0.0, "completion": 0.0},
        "codellama": {"prompt": 0.0, "completion": 0.0},
    }
    
    @classmethod
    def get_cost(
        cls,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for model usage."""
        pricing = cls.PRICING.get(model, {"prompt": 0.0, "completion": 0.0})
        
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        
        return prompt_cost + completion_cost
    
    @classmethod
    def get_model_tier(cls, model: str) -> ModelTier:
        """Get model tier."""
        if model in ["gpt-4", "claude-3-opus"]:
            return ModelTier.PREMIUM
        elif model in ["gpt-3.5-turbo", "gpt-4-turbo", "claude-3-sonnet", "command"]:
            return ModelTier.STANDARD
        elif model in ["claude-3-haiku", "command-light"]:
            return ModelTier.ECONOMY
        else:
            return ModelTier.LOCAL


class SmartCache:
    """
    Semantic caching for LLM responses.
    
    Uses embedding similarity to find cached responses for similar queries.
    """
    
    def __init__(
        self,
        embedding_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        similarity_threshold: float = 0.95
    ):
        """
        Initialize smart cache.
        
        Args:
            embedding_service: Service for generating embeddings
            cache_manager: Cache manager (Redis)
            similarity_threshold: Minimum similarity for cache hit
        """
        self.embedding_service = embedding_service
        self.cache_manager = cache_manager
        self.similarity_threshold = similarity_threshold
        
        # In-memory cache (use Redis in production)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.embeddings: Dict[str, List[float]] = {}
    
    async def get(
        self,
        query: str,
        model: str
    ) -> Optional[str]:
        """
        Get cached response for query.
        
        Args:
            query: Query string
            model: Model name
            
        Returns:
            Cached response or None
        """
        # Exact match
        cache_key = self._generate_cache_key(query, model)
        if cache_key in self.cache:
            logger.debug(f"Cache hit (exact): {cache_key}")
            return self.cache[cache_key]["response"]
        
        # Semantic match
        if self.embedding_service:
            similar_key = await self._find_similar_query(query, model)
            if similar_key:
                logger.debug(f"Cache hit (semantic): {similar_key}")
                return self.cache[similar_key]["response"]
        
        logger.debug("Cache miss")
        return None
    
    async def set(
        self,
        query: str,
        model: str,
        response: str,
        ttl: int = 3600
    ):
        """
        Cache response.
        
        Args:
            query: Query string
            model: Model name
            response: Response to cache
            ttl: Time to live in seconds
        """
        cache_key = self._generate_cache_key(query, model)
        
        # Generate embedding
        embedding = None
        if self.embedding_service:
            embedding = await self._generate_embedding(query)
            self.embeddings[cache_key] = embedding
        
        # Store in cache
        self.cache[cache_key] = {
            "query": query,
            "model": model,
            "response": response,
            "embedding": embedding,
            "created_at": datetime.now(timezone.utc),
            "ttl": ttl
        }
        
        logger.debug(f"Cached response: {cache_key}")
    
    async def _find_similar_query(
        self,
        query: str,
        model: str
    ) -> Optional[str]:
        """Find similar cached query using embeddings."""
        if not self.embedding_service:
            return None
        
        query_embedding = await self._generate_embedding(query)
        
        if not query_embedding:
            return None
        
        # Find most similar
        best_similarity = 0.0
        best_key = None
        
        for cache_key, cached_embedding in self.embeddings.items():
            if self.cache[cache_key]["model"] != model:
                continue
            
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity and similarity >= self.similarity_threshold:
                best_similarity = similarity
                best_key = cache_key
        
        return best_key
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            return await self.embedding_service.embed_text(text)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Calculate cosine similarity."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _generate_cache_key(self, query: str, model: str) -> str:
        """Generate cache key."""
        content = f"{model}:{query}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class CostOptimizer:
    """
    Cost optimization engine for LLM usage.
    
    Features:
    - Smart model selection
    - Semantic caching
    - Batch processing
    - Cost tracking
    - Budget management
    """
    
    def __init__(
        self,
        db: Session,
        embedding_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None
    ):
        """
        Initialize cost optimizer.
        
        Args:
            db: Database session
            embedding_service: Service for embeddings
            cache_manager: Cache manager
        """
        self.db = db
        self.embedding_service = embedding_service
        self.cache_manager = cache_manager
        
        # Smart cache
        self.smart_cache = SmartCache(
            embedding_service=embedding_service,
            cache_manager=cache_manager
        )
        
        # Cost tracking
        self.metrics = CostMetrics()
        self.agent_metrics: Dict[str, CostMetrics] = defaultdict(CostMetrics)
        
        # Memory management
        self._max_agent_metrics = 1000
        self._cleanup_interval = 3600  # 1 hour
        self._last_cleanup = datetime.now(timezone.utc)
        
        logger.info("CostOptimizer initialized")
    
    async def optimize_for_cost(
        self,
        task: str,
        budget_usd: float,
        quality_threshold: float = 0.8,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Optimize model selection for cost.
        
        Args:
            task: Task description
            budget_usd: Budget in USD
            quality_threshold: Minimum quality score (0-1)
            max_tokens: Maximum tokens
            
        Returns:
            Optimization recommendation
        """
        logger.info(f"Optimizing for budget: ${budget_usd}")
        
        # Analyze task complexity
        complexity = await self._analyze_task_complexity(task)
        
        # Select optimal model
        model = await self._select_optimal_model(
            complexity=complexity,
            budget=budget_usd,
            quality_threshold=quality_threshold
        )
        
        # Estimate cost
        estimated_cost = self._estimate_cost(model, max_tokens)
        
        # Check cache
        cache_available = await self.smart_cache.get(task, model) is not None
        
        # Determine strategy
        strategy = self._determine_strategy(
            complexity=complexity,
            budget=budget_usd,
            estimated_cost=estimated_cost
        )
        
        return {
            "recommended_model": model,
            "model_tier": ModelPricing.get_model_tier(model).value,
            "estimated_cost_usd": estimated_cost,
            "cache_available": cache_available,
            "strategy": strategy,
            "complexity": complexity,
            "within_budget": estimated_cost <= budget_usd
        }
    
    async def track_execution(
        self,
        agent_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached: bool = False
    ):
        """
        Track execution costs.
        
        Args:
            agent_id: Agent ID
            model: Model used
            prompt_tokens: Prompt tokens
            completion_tokens: Completion tokens
            cached: Whether response was cached
        """
        # Calculate cost
        cost = ModelPricing.get_cost(model, prompt_tokens, completion_tokens)
        
        # Update global metrics
        self.metrics.total_tokens += prompt_tokens + completion_tokens
        self.metrics.prompt_tokens += prompt_tokens
        self.metrics.completion_tokens += completion_tokens
        self.metrics.total_cost_usd += cost
        self.metrics.request_count += 1
        self.metrics.cost_by_model[model] += cost
        self.metrics.tokens_by_model[model] += prompt_tokens + completion_tokens
        
        if cached:
            self.metrics.cache_hits += 1
        else:
            self.metrics.cache_misses += 1
        
        self.metrics.avg_cost_per_request = (
            self.metrics.total_cost_usd / self.metrics.request_count
        )
        
        # Update agent metrics
        agent_metrics = self.agent_metrics[agent_id]
        agent_metrics.total_tokens += prompt_tokens + completion_tokens
        agent_metrics.prompt_tokens += prompt_tokens
        agent_metrics.completion_tokens += completion_tokens
        agent_metrics.total_cost_usd += cost
        agent_metrics.request_count += 1
        agent_metrics.cost_by_model[model] += cost
        agent_metrics.tokens_by_model[model] += prompt_tokens + completion_tokens
        
        if cached:
            agent_metrics.cache_hits += 1
        else:
            agent_metrics.cache_misses += 1
        
        agent_metrics.avg_cost_per_request = (
            agent_metrics.total_cost_usd / agent_metrics.request_count
        )
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Tracked execution: agent={agent_id}, model={model}, "
                f"tokens={prompt_tokens + completion_tokens}, cost=${cost:.4f}, cached={cached}"
            )
        
        # Periodic cleanup
        now = datetime.now(timezone.utc)
        if (now - self._last_cleanup).total_seconds() > self._cleanup_interval:
            await self._cleanup_old_metrics()
    
    async def _cleanup_old_metrics(self):
        """Clean up old agent metrics to prevent memory leak."""
        if len(self.agent_metrics) > self._max_agent_metrics:
            # Keep only most active agents
            sorted_agents = sorted(
                self.agent_metrics.items(),
                key=lambda x: x[1].request_count,
                reverse=True
            )
            
            # Keep top 80%
            keep_count = int(self._max_agent_metrics * 0.8)
            self.agent_metrics = dict(sorted_agents[:keep_count])
            
            logger.info(f"Cleaned up agent metrics, kept {keep_count} agents")
        
        self._last_cleanup = datetime.now(timezone.utc)
    
    def get_cost_report(
        self,
        agent_id: Optional[str] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get cost report.
        
        Args:
            agent_id: Agent ID (None for global)
            time_range: Time range (start, end)
            
        Returns:
            Cost report
        """
        metrics = self.agent_metrics[agent_id] if agent_id else self.metrics
        
        cache_hit_rate = 0.0
        if metrics.request_count > 0:
            cache_hit_rate = metrics.cache_hits / metrics.request_count
        
        return {
            "total_cost_usd": round(metrics.total_cost_usd, 4),
            "total_tokens": metrics.total_tokens,
            "prompt_tokens": metrics.prompt_tokens,
            "completion_tokens": metrics.completion_tokens,
            "request_count": metrics.request_count,
            "avg_cost_per_request": round(metrics.avg_cost_per_request, 4),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "cache_hits": metrics.cache_hits,
            "cache_misses": metrics.cache_misses,
            "cost_by_model": {
                model: round(cost, 4)
                for model, cost in metrics.cost_by_model.items()
            },
            "tokens_by_model": dict(metrics.tokens_by_model),
            "cost_savings_from_cache": round(
                self._calculate_cache_savings(metrics), 4
            )
        }
    
    async def _analyze_task_complexity(self, task: str) -> float:
        """
        Analyze task complexity.
        
        Returns complexity score (0-1).
        """
        # Simple heuristics
        complexity = 0.5  # Base complexity
        
        # Length factor
        word_count = len(task.split())
        if word_count > 100:
            complexity += 0.2
        elif word_count > 50:
            complexity += 0.1
        
        # Keywords indicating complexity
        complex_keywords = [
            "analyze", "compare", "evaluate", "synthesize",
            "complex", "detailed", "comprehensive", "in-depth"
        ]
        
        task_lower = task.lower()
        for keyword in complex_keywords:
            if keyword in task_lower:
                complexity += 0.1
                break
        
        return min(1.0, complexity)
    
    async def _select_optimal_model(
        self,
        complexity: float,
        budget: float,
        quality_threshold: float
    ) -> str:
        """Select optimal model based on complexity and budget."""
        # Model selection logic
        if complexity >= 0.8 and budget >= 0.01:
            # High complexity, need premium model
            return "gpt-4-turbo"
        elif complexity >= 0.6 and budget >= 0.005:
            # Medium-high complexity
            return "gpt-3.5-turbo"
        elif complexity >= 0.4 and budget >= 0.001:
            # Medium complexity
            return "claude-3-haiku"
        elif budget > 0:
            # Low complexity, economy model
            return "command-light"
        else:
            # No budget, use local model
            return "llama2"
    
    def _estimate_cost(
        self,
        model: str,
        max_tokens: int
    ) -> float:
        """Estimate cost for model and tokens."""
        # Assume 50/50 split between prompt and completion
        prompt_tokens = max_tokens // 2
        completion_tokens = max_tokens // 2
        
        return ModelPricing.get_cost(model, prompt_tokens, completion_tokens)
    
    def _determine_strategy(
        self,
        complexity: float,
        budget: float,
        estimated_cost: float
    ) -> str:
        """Determine optimization strategy."""
        if estimated_cost > budget:
            return "use_cheaper_model"
        elif complexity < 0.5:
            return "use_cache_aggressively"
        else:
            return "balanced"
    
    def _calculate_cache_savings(self, metrics: CostMetrics) -> float:
        """Calculate cost savings from caching."""
        if metrics.cache_hits == 0:
            return 0.0
        
        # Estimate average cost per request
        avg_cost = metrics.avg_cost_per_request
        
        # Savings = cache hits * average cost
        return metrics.cache_hits * avg_cost


# Example usage
EXAMPLE_USAGE = """
# Initialize
optimizer = CostOptimizer(db, embedding_service, cache_manager)

# Optimize for cost
recommendation = await optimizer.optimize_for_cost(
    task="Analyze this document and provide insights",
    budget_usd=0.01,
    quality_threshold=0.8,
    max_tokens=2000
)
# {
#   "recommended_model": "gpt-3.5-turbo",
#   "estimated_cost_usd": 0.0035,
#   "cache_available": False,
#   "strategy": "balanced",
#   "within_budget": True
# }

# Track execution
await optimizer.track_execution(
    agent_id="agent_123",
    model="gpt-3.5-turbo",
    prompt_tokens=500,
    completion_tokens=300,
    cached=False
)

# Get cost report
report = optimizer.get_cost_report(agent_id="agent_123")
# {
#   "total_cost_usd": 0.0035,
#   "total_tokens": 800,
#   "request_count": 1,
#   "cache_hit_rate": 0.0,
#   "cost_by_model": {"gpt-3.5-turbo": 0.0035}
# }

# Use smart cache
cached_response = await optimizer.smart_cache.get(
    query="What is AI?",
    model="gpt-3.5-turbo"
)

if not cached_response:
    # Make LLM call
    response = await llm_service.generate(...)
    
    # Cache response
    await optimizer.smart_cache.set(
        query="What is AI?",
        model="gpt-3.5-turbo",
        response=response
    )
"""
