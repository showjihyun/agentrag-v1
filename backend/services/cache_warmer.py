# Cache Warmer Service
"""
Cache warming service for preloading common queries.

Warms up the speculative cache with frequently asked questions
to ensure fast responses for first-time users.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class CacheWarmer:
    """
    Service for warming up caches with common queries.
    
    Features:
    - Preload common queries on startup
    - Periodic cache refresh
    - Query popularity tracking
    - Configurable warming strategies
    """

    def __init__(
        self,
        speculative_processor,
        redis_client,
        common_queries_file: str = "./data/common_queries.json",
        min_query_frequency: int = 5,
        refresh_interval_hours: int = 24
    ):
        """
        Initialize Cache Warmer.
        
        Args:
            speculative_processor: SpeculativeProcessor instance
            redis_client: Redis client for query tracking
            common_queries_file: Path to common queries JSON file
            min_query_frequency: Minimum frequency to consider query "common"
            refresh_interval_hours: Hours between cache refreshes
        """
        self.speculative_processor = speculative_processor
        self.redis_client = redis_client
        self.common_queries_file = common_queries_file
        self.min_query_frequency = min_query_frequency
        self.refresh_interval_hours = refresh_interval_hours
        
        # Query tracking
        self.query_frequency_key = "cache_warmer:query_frequency"
        self.last_warm_key = "cache_warmer:last_warm"
        
        # Warming state
        self.is_warming = False
        self.warmed_count = 0
        
        logger.info(
            f"CacheWarmer initialized: refresh_interval={refresh_interval_hours}h, "
            f"min_frequency={min_query_frequency}"
        )

    async def warm_cache_on_startup(self) -> int:
        """
        Warm cache on application startup.
        
        Returns:
            Number of queries warmed
        """
        if self.is_warming:
            logger.warning("Cache warming already in progress")
            return 0
        
        self.is_warming = True
        warmed = 0
        
        try:
            logger.info("Starting cache warming on startup...")
            
            # Load common queries
            common_queries = await self._load_common_queries()
            
            if not common_queries:
                logger.warning("No common queries found for warming")
                return 0
            
            # Warm cache for each query
            for query in common_queries:
                try:
                    await self._warm_single_query(query)
                    warmed += 1
                    
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Failed to warm query '{query[:50]}...': {e}")
                    continue
            
            # Update last warm timestamp
            await self.redis_client.set(
                self.last_warm_key,
                datetime.now().isoformat()
            )
            
            self.warmed_count = warmed
            
            logger.info(f"Cache warming completed: {warmed}/{len(common_queries)} queries warmed")
            
            return warmed
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return warmed
            
        finally:
            self.is_warming = False

    async def _warm_single_query(self, query: str) -> bool:
        """
        Warm cache for a single query.
        
        Args:
            query: Query to warm
        
        Returns:
            bool: True if successful
        """
        try:
            # Process query through speculative path
            response = await self.speculative_processor.process(
                query=query,
                session_id=None,  # No session for warming
                top_k=5,
                enable_cache=True
            )
            
            # Check if response is valid
            if response and response.response:
                logger.debug(f"Warmed cache for: {query[:50]}...")
                return True
            else:
                logger.debug(f"Failed to warm (invalid response): {query[:50]}...")
                return False
                
        except Exception as e:
            logger.warning(f"Error warming query: {e}")
            return False

    async def _load_common_queries(self) -> List[str]:
        """
        Load common queries from file and Redis tracking.
        
        Returns:
            List of common queries
        """
        queries = set()
        
        # Load from file
        try:
            import os
            if os.path.exists(self.common_queries_file):
                with open(self.common_queries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_queries = data.get('queries', [])
                    queries.update(file_queries)
                    logger.info(f"Loaded {len(file_queries)} queries from file")
        except Exception as e:
            logger.warning(f"Failed to load queries from file: {e}")
        
        # Load from Redis tracking
        try:
            tracked_queries = await self._get_popular_queries_from_redis()
            queries.update(tracked_queries)
            logger.info(f"Loaded {len(tracked_queries)} queries from Redis tracking")
        except Exception as e:
            logger.warning(f"Failed to load queries from Redis: {e}")
        
        return list(queries)

    async def _get_popular_queries_from_redis(self) -> List[str]:
        """
        Get popular queries from Redis tracking.
        
        Returns:
            List of popular queries
        """
        try:
            # Get all query frequencies
            frequencies = await self.redis_client.hgetall(self.query_frequency_key)
            
            if not frequencies:
                return []
            
            # Filter by minimum frequency
            popular = [
                query.decode('utf-8') if isinstance(query, bytes) else query
                for query, freq in frequencies.items()
                if int(freq) >= self.min_query_frequency
            ]
            
            # Sort by frequency (descending)
            popular.sort(
                key=lambda q: int(frequencies.get(q.encode('utf-8') if isinstance(q, str) else q, 0)),
                reverse=True
            )
            
            # Return top 50
            return popular[:50]
            
        except Exception as e:
            logger.error(f"Failed to get popular queries: {e}")
            return []

    async def track_query(self, query: str) -> None:
        """
        Track query frequency for future warming.
        
        Args:
            query: Query to track
        """
        try:
            # Increment query frequency
            await self.redis_client.hincrby(
                self.query_frequency_key,
                query,
                1
            )
            
        except Exception as e:
            logger.debug(f"Failed to track query: {e}")

    async def schedule_periodic_refresh(self) -> None:
        """
        Schedule periodic cache refresh.
        
        Runs in background, refreshing cache every N hours.
        """
        logger.info(
            f"Starting periodic cache refresh "
            f"(interval: {self.refresh_interval_hours}h)"
        )
        
        while True:
            try:
                # Wait for refresh interval
                await asyncio.sleep(self.refresh_interval_hours * 3600)
                
                # Check if warming is needed
                last_warm = await self.redis_client.get(self.last_warm_key)
                
                if last_warm:
                    last_warm_time = datetime.fromisoformat(
                        last_warm.decode('utf-8') if isinstance(last_warm, bytes) else last_warm
                    )
                    time_since_warm = datetime.now() - last_warm_time
                    
                    if time_since_warm < timedelta(hours=self.refresh_interval_hours):
                        logger.info("Cache refresh not needed yet")
                        continue
                
                # Perform refresh
                logger.info("Starting scheduled cache refresh...")
                warmed = await self.warm_cache_on_startup()
                logger.info(f"Scheduled refresh completed: {warmed} queries warmed")
                
            except asyncio.CancelledError:
                logger.info("Periodic refresh cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic refresh: {e}")
                # Continue despite errors

    async def add_common_query(self, query: str) -> bool:
        """
        Add a query to the common queries file.
        
        Args:
            query: Query to add
        
        Returns:
            bool: True if successful
        """
        try:
            import os
            
            # Load existing queries
            queries = []
            if os.path.exists(self.common_queries_file):
                with open(self.common_queries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    queries = data.get('queries', [])
            
            # Add new query if not exists
            if query not in queries:
                queries.append(query)
                
                # Save back to file
                os.makedirs(os.path.dirname(self.common_queries_file), exist_ok=True)
                with open(self.common_queries_file, 'w', encoding='utf-8') as f:
                    json.dump({'queries': queries}, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Added common query: {query[:50]}...")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to add common query: {e}")
            return False

    async def remove_common_query(self, query: str) -> bool:
        """
        Remove a query from the common queries file.
        
        Args:
            query: Query to remove
        
        Returns:
            bool: True if successful
        """
        try:
            import os
            
            if not os.path.exists(self.common_queries_file):
                return False
            
            # Load existing queries
            with open(self.common_queries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                queries = data.get('queries', [])
            
            # Remove query
            if query in queries:
                queries.remove(query)
                
                # Save back to file
                with open(self.common_queries_file, 'w', encoding='utf-8') as f:
                    json.dump({'queries': queries}, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Removed common query: {query[:50]}...")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove common query: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get cache warmer statistics"""
        return {
            "is_warming": self.is_warming,
            "warmed_count": self.warmed_count,
            "refresh_interval_hours": self.refresh_interval_hours,
            "min_query_frequency": self.min_query_frequency
        }


# Global cache warmer instance
_cache_warmer: Optional[CacheWarmer] = None


def get_cache_warmer(
    speculative_processor,
    redis_client,
    common_queries_file: str = "./data/common_queries.json"
) -> CacheWarmer:
    """Get global cache warmer instance"""
    global _cache_warmer
    if _cache_warmer is None:
        _cache_warmer = CacheWarmer(
            speculative_processor=speculative_processor,
            redis_client=redis_client,
            common_queries_file=common_queries_file
        )
    return _cache_warmer
