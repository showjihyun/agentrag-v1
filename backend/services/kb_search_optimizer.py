"""
Knowledgebase Search Optimizer.

Advanced optimization for KB search including:
- Adaptive timeout based on KB size
- Search result caching
- Query preprocessing
- Performance tracking
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class KBSearchMetrics:
    """Metrics for KB search performance"""
    kb_id: str
    search_time: float
    result_count: int
    cache_hit: bool
    error: Optional[str] = None


@dataclass
class KBProfile:
    """Profile information for a knowledgebase"""
    kb_id: str
    document_count: int
    avg_search_time: float
    last_updated: datetime
    collection_size: int  # Number of vectors


class KBSearchOptimizer:
    """
    Optimizer for knowledgebase search operations.
    
    Features:
    - Adaptive timeouts based on KB size
    - Search result caching
    - Performance profiling
    - Query preprocessing
    """
    
    def __init__(self, redis_client, cache_ttl: int = 300):
        """
        Initialize optimizer.
        
        Args:
            redis_client: Redis client for caching
            cache_ttl: Cache TTL in seconds (default: 5 minutes)
        """
        self.redis_client = redis_client
        self.cache_ttl = cache_ttl
        self.kb_profiles: Dict[str, KBProfile] = {}
        self.search_metrics: List[KBSearchMetrics] = []
        
        logger.info("KBSearchOptimizer initialized")
    
    def calculate_adaptive_timeout(
        self,
        kb_ids: List[str],
        base_timeout: float = 1.0
    ) -> float:
        """
        Calculate adaptive timeout based on KB profiles.
        
        Larger KBs get more time, smaller KBs get less.
        
        Args:
            kb_ids: List of KB IDs to search
            base_timeout: Base timeout in seconds
            
        Returns:
            Adaptive timeout in seconds
        """
        if not kb_ids:
            return base_timeout
        
        # Get max document count from profiles
        max_docs = 0
        for kb_id in kb_ids:
            profile = self.kb_profiles.get(kb_id)
            if profile:
                max_docs = max(max_docs, profile.document_count)
        
        # Adaptive timeout based on document count
        if max_docs == 0:
            return base_timeout
        elif max_docs < 100:
            return base_timeout * 0.8  # Small KB: 0.8s
        elif max_docs < 1000:
            return base_timeout * 1.0  # Medium KB: 1.0s
        elif max_docs < 10000:
            return base_timeout * 1.5  # Large KB: 1.5s
        else:
            return base_timeout * 2.0  # Very large KB: 2.0s
    
    async def search_with_cache(
        self,
        kb_id: str,
        query_hash: str,
        search_func,
        *args,
        **kwargs
    ) -> Tuple[List[Any], bool]:
        """
        Search with caching.
        
        Args:
            kb_id: Knowledgebase ID
            query_hash: Hash of the query
            search_func: Async search function
            *args, **kwargs: Arguments for search function
            
        Returns:
            Tuple of (results, cache_hit)
        """
        cache_key = f"kb_search:{kb_id}:{query_hash}"
        
        # Check cache
        try:
            cached = await self.redis_client.get(cache_key)
            if cached:
                import json
                results = json.loads(cached)
                logger.debug(f"Cache hit for KB {kb_id}")
                return results, True
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
        
        # Cache miss - perform search
        results = await search_func(*args, **kwargs)
        
        # Store in cache
        try:
            import json
            # Convert results to JSON-serializable format
            serializable_results = [
                {
                    'id': getattr(r, 'id', None),
                    'content': getattr(r, 'content', str(r)),
                    'score': getattr(r, 'score', 0),
                    'metadata': getattr(r, 'metadata', {})
                }
                for r in results
            ]
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(serializable_results)
            )
        except Exception as e:
            logger.warning(f"Cache store failed: {e}")
        
        return results, False
    
    async def search_kbs_optimized(
        self,
        kb_ids: List[str],
        search_func,
        query_hash: str,
        *args,
        **kwargs
    ) -> Tuple[List[Any], List[KBSearchMetrics]]:
        """
        Search multiple KBs with optimization.
        
        Features:
        - Adaptive timeouts
        - Result caching
        - Performance tracking
        - Parallel execution
        
        Args:
            kb_ids: List of KB IDs
            search_func: Search function for single KB
            query_hash: Hash of query for caching
            *args, **kwargs: Arguments for search function
            
        Returns:
            Tuple of (all results, metrics)
        """
        if not kb_ids:
            return [], []
        
        # Calculate adaptive timeout
        timeout = self.calculate_adaptive_timeout(kb_ids)
        
        logger.info(
            f"Searching {len(kb_ids)} KBs with adaptive timeout: {timeout:.2f}s"
        )
        
        # Create search tasks with caching
        tasks = []
        for kb_id in kb_ids:
            task = self._search_single_kb_with_metrics(
                kb_id,
                query_hash,
                search_func,
                *args,
                **kwargs
            )
            tasks.append(task)
        
        # Execute in parallel with timeout
        try:
            results_with_metrics = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"KB search timeout after {timeout:.2f}s")
            results_with_metrics = [
                ([], KBSearchMetrics(kb_id, timeout, 0, False, "timeout"))
                for kb_id in kb_ids
            ]
        
        # Collect results and metrics
        all_results = []
        all_metrics = []
        
        for kb_id, result in zip(kb_ids, results_with_metrics):
            if isinstance(result, Exception):
                logger.error(f"KB search failed for {kb_id}: {result}")
                all_metrics.append(
                    KBSearchMetrics(kb_id, 0, 0, False, str(result))
                )
            else:
                results, metrics = result
                all_results.extend(results)
                all_metrics.append(metrics)
        
        # Store metrics
        self.search_metrics.extend(all_metrics)
        
        # Log summary
        total_results = len(all_results)
        cache_hits = sum(1 for m in all_metrics if m.cache_hit)
        avg_time = sum(m.search_time for m in all_metrics) / len(all_metrics) if all_metrics else 0
        
        logger.info(
            f"KB search completed: {total_results} results, "
            f"{cache_hits}/{len(kb_ids)} cache hits, "
            f"avg time: {avg_time:.3f}s"
        )
        
        return all_results, all_metrics
    
    async def _search_single_kb_with_metrics(
        self,
        kb_id: str,
        query_hash: str,
        search_func,
        *args,
        **kwargs
    ) -> Tuple[List[Any], KBSearchMetrics]:
        """
        Search single KB with metrics tracking.
        
        Args:
            kb_id: Knowledgebase ID
            query_hash: Query hash for caching
            search_func: Search function
            *args, **kwargs: Search arguments
            
        Returns:
            Tuple of (results, metrics)
        """
        start_time = time.time()
        
        try:
            # Search with cache
            results, cache_hit = await self.search_with_cache(
                kb_id,
                query_hash,
                search_func,
                kb_id,
                *args,
                **kwargs
            )
            
            search_time = time.time() - start_time
            
            metrics = KBSearchMetrics(
                kb_id=kb_id,
                search_time=search_time,
                result_count=len(results),
                cache_hit=cache_hit,
                error=None
            )
            
            return results, metrics
            
        except Exception as e:
            search_time = time.time() - start_time
            logger.error(f"KB search failed for {kb_id}: {e}")
            
            metrics = KBSearchMetrics(
                kb_id=kb_id,
                search_time=search_time,
                result_count=0,
                cache_hit=False,
                error=str(e)
            )
            
            return [], metrics
    
    def update_kb_profile(
        self,
        kb_id: str,
        document_count: int,
        collection_size: int,
        search_time: Optional[float] = None
    ):
        """
        Update KB profile for adaptive optimization.
        
        Args:
            kb_id: Knowledgebase ID
            document_count: Number of documents
            collection_size: Number of vectors
            search_time: Optional search time to update average
        """
        profile = self.kb_profiles.get(kb_id)
        
        if profile:
            # Update existing profile
            profile.document_count = document_count
            profile.collection_size = collection_size
            profile.last_updated = datetime.utcnow()
            
            if search_time is not None:
                # Update moving average
                profile.avg_search_time = (
                    profile.avg_search_time * 0.7 + search_time * 0.3
                )
        else:
            # Create new profile
            profile = KBProfile(
                kb_id=kb_id,
                document_count=document_count,
                avg_search_time=search_time or 0.5,
                last_updated=datetime.utcnow(),
                collection_size=collection_size
            )
            self.kb_profiles[kb_id] = profile
        
        logger.debug(f"Updated KB profile for {kb_id}: {document_count} docs")
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search statistics.
        
        Returns:
            Dictionary with search statistics
        """
        if not self.search_metrics:
            return {
                'total_searches': 0,
                'avg_search_time': 0,
                'cache_hit_rate': 0,
                'error_rate': 0
            }
        
        total = len(self.search_metrics)
        cache_hits = sum(1 for m in self.search_metrics if m.cache_hit)
        errors = sum(1 for m in self.search_metrics if m.error)
        avg_time = sum(m.search_time for m in self.search_metrics) / total
        
        return {
            'total_searches': total,
            'avg_search_time': avg_time,
            'cache_hit_rate': cache_hits / total if total > 0 else 0,
            'error_rate': errors / total if total > 0 else 0,
            'kb_profiles': len(self.kb_profiles)
        }
    
    def clear_old_metrics(self, hours: int = 24):
        """
        Clear metrics older than specified hours.
        
        Args:
            hours: Hours to keep metrics
        """
        # For now, just clear all (in production, add timestamp to metrics)
        if len(self.search_metrics) > 1000:
            self.search_metrics = self.search_metrics[-500:]
            logger.info("Cleared old search metrics")


# Global optimizer instance
_optimizer: Optional[KBSearchOptimizer] = None


def get_kb_search_optimizer(redis_client) -> KBSearchOptimizer:
    """
    Get or create global KB search optimizer.
    
    Args:
        redis_client: Redis client
        
    Returns:
        KBSearchOptimizer instance
    """
    global _optimizer
    
    if _optimizer is None:
        _optimizer = KBSearchOptimizer(redis_client)
    
    return _optimizer
