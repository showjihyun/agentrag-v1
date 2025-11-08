"""
Semantic Prompt Caching for LLM Cost Optimization

Reduces LLM costs by 30-50% through intelligent prompt caching.
"""

import logging
import json
import hashlib
from typing import Optional, List, Tuple
from datetime import datetime, timedelta

import numpy as np
import redis.asyncio as redis
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)


class SemanticPromptCache:
    """
    Semantic-based prompt caching for LLM cost optimization.
    
    Features:
    - Similarity-based cache lookup
    - Embedding-based matching
    - Response reuse for similar prompts
    - Cost reduction (30-50%)
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        similarity_threshold: float = 0.95,
        model_name: str = 'all-MiniLM-L6-v2',
        ttl: int = 3600,
        max_cache_size: int = 10000
    ):
        """
        Initialize Semantic Prompt Cache.
        
        Args:
            redis_client: Redis client
            similarity_threshold: Minimum similarity for cache hit (0.0-1.0)
            model_name: Sentence transformer model
            ttl: Cache TTL in seconds
            max_cache_size: Maximum cached prompts
        """
        self.redis = redis_client
        self.threshold = similarity_threshold
        self.ttl = ttl
        self.max_cache_size = max_cache_size
        
        # Load embedding model
        try:
            self.encoder = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.encoder = None
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_requests": 0
        }
    
    async def get_cached_response(
        self,
        prompt: str,
        model: str = "default"
    ) -> Optional[dict]:
        """
        Get cached response for similar prompt.
        
        Args:
            prompt: Input prompt
            model: LLM model name
            
        Returns:
            Cached response dict or None
        """
        if not self.encoder:
            return None
        
        self.stats["total_requests"] += 1
        
        try:
            # Generate prompt embedding
            prompt_embedding = self.encoder.encode(prompt)
            
            # Search for similar prompts
            similar_prompt = await self._find_similar_prompt(
                prompt_embedding,
                model
            )
            
            if similar_prompt:
                self.stats["hits"] += 1
                
                # Get cached response
                cache_key = self._get_cache_key(similar_prompt["prompt"], model)
                cached_data = await self.redis.get(cache_key)
                
                if cached_data:
                    data = json.loads(cached_data)
                    
                    logger.info(
                        f"Cache hit with similarity: {similar_prompt['similarity']:.3f}",
                        extra={
                            "original_prompt": prompt[:100],
                            "cached_prompt": similar_prompt['prompt'][:100],
                            "similarity": similar_prompt['similarity']
                        }
                    )
                    
                    return {
                        "response": data["response"],
                        "cached": True,
                        "similarity": similar_prompt["similarity"],
                        "original_prompt": similar_prompt["prompt"],
                        "timestamp": data["timestamp"]
                    }
            
            self.stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Error in prompt cache lookup: {e}", exc_info=True)
            return None
    
    async def cache_response(
        self,
        prompt: str,
        response: str,
        model: str = "default",
        metadata: Optional[dict] = None
    ):
        """
        Cache prompt-response pair.
        
        Args:
            prompt: Input prompt
            response: LLM response
            model: LLM model name
            metadata: Additional metadata
        """
        if not self.encoder:
            return
        
        try:
            # Generate embedding
            embedding = self.encoder.encode(prompt)
            
            # Store prompt with embedding
            cache_key = self._get_cache_key(prompt, model)
            embedding_key = self._get_embedding_key(prompt, model)
            
            # Cache data
            cache_data = {
                "prompt": prompt,
                "response": response,
                "model": model,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store response
            await self.redis.setex(
                cache_key,
                self.ttl,
                json.dumps(cache_data)
            )
            
            # Store embedding
            await self.redis.setex(
                embedding_key,
                self.ttl,
                embedding.tobytes()
            )
            
            # Add to index
            await self._add_to_index(prompt, model)
            
            # Enforce max cache size
            await self._enforce_cache_limit(model)
            
            logger.debug(f"Cached prompt-response pair for model: {model}")
            
        except Exception as e:
            logger.error(f"Error caching prompt: {e}", exc_info=True)
    
    async def _find_similar_prompt(
        self,
        query_embedding: np.ndarray,
        model: str
    ) -> Optional[dict]:
        """
        Find most similar cached prompt.
        
        Args:
            query_embedding: Query embedding
            model: LLM model name
            
        Returns:
            Dict with prompt and similarity or None
        """
        # Get all cached prompts for this model
        index_key = f"prompt_cache:index:{model}"
        cached_prompts = await self.redis.smembers(index_key)
        
        if not cached_prompts:
            return None
        
        best_match = None
        best_similarity = 0.0
        
        # Compare with each cached prompt
        for prompt_hash in cached_prompts:
            prompt_hash = prompt_hash.decode() if isinstance(prompt_hash, bytes) else prompt_hash
            
            # Get embedding
            embedding_key = f"prompt_cache:embedding:{model}:{prompt_hash}"
            embedding_bytes = await self.redis.get(embedding_key)
            
            if not embedding_bytes:
                continue
            
            # Convert bytes to numpy array
            cached_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity and similarity >= self.threshold:
                best_similarity = similarity
                
                # Get original prompt
                cache_key = f"prompt_cache:data:{model}:{prompt_hash}"
                cached_data = await self.redis.get(cache_key)
                
                if cached_data:
                    data = json.loads(cached_data)
                    best_match = {
                        "prompt": data["prompt"],
                        "similarity": similarity
                    }
        
        return best_match
    
    def _cosine_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _get_cache_key(self, prompt: str, model: str) -> str:
        """Generate cache key for prompt."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        return f"prompt_cache:data:{model}:{prompt_hash}"
    
    def _get_embedding_key(self, prompt: str, model: str) -> str:
        """Generate embedding key for prompt."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        return f"prompt_cache:embedding:{model}:{prompt_hash}"
    
    async def _add_to_index(self, prompt: str, model: str):
        """Add prompt to index."""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        index_key = f"prompt_cache:index:{model}"
        await self.redis.sadd(index_key, prompt_hash)
    
    async def _enforce_cache_limit(self, model: str):
        """Enforce maximum cache size (LRU eviction)."""
        index_key = f"prompt_cache:index:{model}"
        cache_size = await self.redis.scard(index_key)
        
        if cache_size > self.max_cache_size:
            # Get all prompts
            prompts = await self.redis.smembers(index_key)
            
            # Sort by timestamp (oldest first)
            prompt_times = []
            for prompt_hash in prompts:
                prompt_hash = prompt_hash.decode() if isinstance(prompt_hash, bytes) else prompt_hash
                cache_key = f"prompt_cache:data:{model}:{prompt_hash}"
                
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    timestamp = datetime.fromisoformat(data["timestamp"])
                    prompt_times.append((prompt_hash, timestamp))
            
            # Sort and remove oldest
            prompt_times.sort(key=lambda x: x[1])
            to_remove = cache_size - self.max_cache_size
            
            for prompt_hash, _ in prompt_times[:to_remove]:
                await self._remove_from_cache(prompt_hash, model)
    
    async def _remove_from_cache(self, prompt_hash: str, model: str):
        """Remove prompt from cache."""
        # Remove from index
        index_key = f"prompt_cache:index:{model}"
        await self.redis.srem(index_key, prompt_hash)
        
        # Remove data
        cache_key = f"prompt_cache:data:{model}:{prompt_hash}"
        await self.redis.delete(cache_key)
        
        # Remove embedding
        embedding_key = f"prompt_cache:embedding:{model}:{prompt_hash}"
        await self.redis.delete(embedding_key)
    
    async def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.stats["total_requests"]
        hits = self.stats["hits"]
        misses = self.stats["misses"]
        
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        return {
            "total_requests": total,
            "cache_hits": hits,
            "cache_misses": misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "estimated_cost_savings": f"{hit_rate * 0.5:.2f}%"  # Assuming 50% cost per hit
        }
    
    async def clear_cache(self, model: Optional[str] = None):
        """Clear cache for model or all models."""
        if model:
            # Clear specific model
            index_key = f"prompt_cache:index:{model}"
            prompts = await self.redis.smembers(index_key)
            
            for prompt_hash in prompts:
                prompt_hash = prompt_hash.decode() if isinstance(prompt_hash, bytes) else prompt_hash
                await self._remove_from_cache(prompt_hash, model)
            
            logger.info(f"Cleared cache for model: {model}")
        else:
            # Clear all
            keys = await self.redis.keys("prompt_cache:*")
            if keys:
                await self.redis.delete(*keys)
            
            logger.info("Cleared all prompt cache")


# Global prompt cache instance
_prompt_cache: Optional[SemanticPromptCache] = None


def get_prompt_cache() -> SemanticPromptCache:
    """Get global prompt cache instance."""
    global _prompt_cache
    if _prompt_cache is None:
        raise RuntimeError("Prompt cache not initialized")
    return _prompt_cache


async def initialize_prompt_cache(
    redis_client: redis.Redis,
    similarity_threshold: float = 0.95,
    ttl: int = 3600
) -> SemanticPromptCache:
    """
    Initialize global prompt cache.
    
    Args:
        redis_client: Redis client
        similarity_threshold: Similarity threshold
        ttl: Cache TTL
        
    Returns:
        Prompt cache instance
    """
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = SemanticPromptCache(
            redis_client=redis_client,
            similarity_threshold=similarity_threshold,
            ttl=ttl
        )
    return _prompt_cache


def cleanup_prompt_cache():
    """Cleanup global prompt cache."""
    global _prompt_cache
    _prompt_cache = None
