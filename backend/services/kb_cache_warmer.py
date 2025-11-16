"""
Knowledgebase Cache Warmer.

Pre-populates cache with common queries for faster response times.
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class KBCacheWarmer:
    """
    Cache warmer for knowledgebase queries.
    
    Features:
    - Pre-cache common queries
    - Agent-specific warming
    - Scheduled warming
    - Performance tracking
    """
    
    def __init__(self, speculative_processor):
        """
        Initialize cache warmer.
        
        Args:
            speculative_processor: SpeculativeProcessor instance
        """
        self.processor = speculative_processor
        self.warming_stats = {
            'total_warmed': 0,
            'last_warming': None,
            'errors': 0
        }
        
        logger.info("KBCacheWarmer initialized")
    
    async def warm_agent_cache(
        self,
        agent_id: str,
        kb_ids: List[str],
        common_queries: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Warm cache for an agent's knowledgebases.
        
        Args:
            agent_id: Agent ID
            kb_ids: List of knowledgebase IDs
            common_queries: Optional list of common queries
            
        Returns:
            Warming statistics
        """
        if not kb_ids:
            logger.info(f"No KBs to warm for agent {agent_id}")
            return {'warmed': 0, 'errors': 0}
        
        # Default common queries if not provided
        if not common_queries:
            common_queries = self._get_default_queries()
        
        logger.info(
            f"Warming cache for agent {agent_id}: "
            f"{len(kb_ids)} KBs, {len(common_queries)} queries"
        )
        
        start_time = datetime.utcnow()
        warmed = 0
        errors = 0
        
        # Warm each query
        for query in common_queries:
            try:
                await self.processor.process_with_knowledgebase(
                    query=query,
                    knowledgebase_ids=kb_ids,
                    enable_cache=True
                )
                warmed += 1
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Cache warming failed for query '{query}': {e}")
                errors += 1
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Update stats
        self.warming_stats['total_warmed'] += warmed
        self.warming_stats['last_warming'] = datetime.utcnow()
        self.warming_stats['errors'] += errors
        
        logger.info(
            f"Cache warming completed for agent {agent_id}: "
            f"{warmed} queries warmed, {errors} errors, "
            f"duration: {duration:.2f}s"
        )
        
        return {
            'agent_id': agent_id,
            'kb_count': len(kb_ids),
            'queries_warmed': warmed,
            'errors': errors,
            'duration_seconds': duration
        }
    
    async def warm_multiple_agents(
        self,
        agent_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Warm cache for multiple agents.
        
        Args:
            agent_configs: List of agent configurations
                Each config: {'agent_id': str, 'kb_ids': List[str], 'queries': List[str]}
                
        Returns:
            List of warming results
        """
        logger.info(f"Warming cache for {len(agent_configs)} agents")
        
        results = []
        for config in agent_configs:
            result = await self.warm_agent_cache(
                agent_id=config['agent_id'],
                kb_ids=config['kb_ids'],
                common_queries=config.get('queries')
            )
            results.append(result)
        
        return results
    
    def _get_default_queries(self) -> List[str]:
        """
        Get default common queries for warming.
        
        Returns:
            List of common queries
        """
        return [
            "What is this about?",
            "How does it work?",
            "What are the main features?",
            "How do I get started?",
            "What are the requirements?",
            "How do I configure this?",
            "What are the best practices?",
            "How do I troubleshoot issues?",
            "What are the limitations?",
            "Where can I find more information?"
        ]
    
    def get_warming_stats(self) -> Dict[str, Any]:
        """
        Get cache warming statistics.
        
        Returns:
            Warming statistics
        """
        return {
            **self.warming_stats,
            'last_warming': self.warming_stats['last_warming'].isoformat() 
                if self.warming_stats['last_warming'] else None
        }


# Example usage function
async def warm_agent_cache_on_startup(
    agent_id: str,
    kb_ids: List[str],
    speculative_processor
):
    """
    Warm cache for an agent on startup.
    
    Args:
        agent_id: Agent ID
        kb_ids: Knowledgebase IDs
        speculative_processor: SpeculativeProcessor instance
    """
    warmer = KBCacheWarmer(speculative_processor)
    result = await warmer.warm_agent_cache(agent_id, kb_ids)
    logger.info(f"Startup cache warming result: {result}")
    return result
