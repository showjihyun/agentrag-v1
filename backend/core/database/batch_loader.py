"""
Batch Loader - DataLoader Pattern for N+1 Query Prevention

Automatically batches and caches database queries to prevent N+1 problems.
"""

from typing import List, Dict, Any, Callable, Optional, TypeVar, Generic
from collections import defaultdict
import asyncio

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')
K = TypeVar('K')


class DataLoader(Generic[K, T]):
    """
    DataLoader implementation for batching and caching
    
    Example:
        # Define batch load function
        async def batch_load_users(user_ids: List[int]) -> List[User]:
            users = await db.query(User).filter(User.id.in_(user_ids)).all()
            return users
        
        # Create loader
        user_loader = DataLoader(batch_load_users)
        
        # Load individual items (automatically batched)
        user1 = await user_loader.load(1)
        user2 = await user_loader.load(2)
        user3 = await user_loader.load(3)
        # Only 1 query executed: SELECT * FROM users WHERE id IN (1, 2, 3)
    """
    
    def __init__(
        self,
        batch_load_fn: Callable[[List[K]], Any],
        max_batch_size: int = 100,
        cache: bool = True
    ):
        """
        Initialize DataLoader
        
        Args:
            batch_load_fn: Function that loads multiple items by keys
            max_batch_size: Maximum batch size
            cache: Enable caching
        """
        self.batch_load_fn = batch_load_fn
        self.max_batch_size = max_batch_size
        self.cache_enabled = cache
        
        # Cache
        self._cache: Dict[K, T] = {}
        
        # Batching
        self._queue: List[tuple[K, asyncio.Future]] = []
        self._batch_scheduled = False
        
        self.logger = get_logger(__name__)
    
    async def load(self, key: K) -> Optional[T]:
        """
        Load single item by key
        
        Args:
            key: Item key
            
        Returns:
            Loaded item or None
        """
        # Check cache
        if self.cache_enabled and key in self._cache:
            self.logger.debug("dataloader_cache_hit", key=key)
            return self._cache[key]
        
        # Add to queue
        future = asyncio.Future()
        self._queue.append((key, future))
        
        # Schedule batch if not already scheduled
        if not self._batch_scheduled:
            self._batch_scheduled = True
            asyncio.create_task(self._dispatch_batch())
        
        # Wait for result
        return await future
    
    async def load_many(self, keys: List[K]) -> List[Optional[T]]:
        """
        Load multiple items by keys
        
        Args:
            keys: List of keys
            
        Returns:
            List of loaded items
        """
        return await asyncio.gather(*[self.load(key) for key in keys])
    
    async def _dispatch_batch(self):
        """Dispatch batched load"""
        # Wait for event loop tick to collect more items
        await asyncio.sleep(0)
        
        if not self._queue:
            self._batch_scheduled = False
            return
        
        # Get batch
        batch = self._queue[:self.max_batch_size]
        self._queue = self._queue[self.max_batch_size:]
        self._batch_scheduled = bool(self._queue)
        
        # Extract keys and futures
        keys = [key for key, _ in batch]
        futures = [future for _, future in batch]
        
        try:
            # Load batch
            self.logger.debug(
                "dataloader_batch_load",
                batch_size=len(keys),
                keys=keys[:10]  # Log first 10 keys
            )
            
            results = await self.batch_load_fn(keys)
            
            # Create key -> result mapping
            result_map = {self._get_key(item): item for item in results}
            
            # Resolve futures
            for key, future in batch:
                result = result_map.get(key)
                
                # Cache result
                if self.cache_enabled and result is not None:
                    self._cache[key] = result
                
                # Resolve future
                if not future.done():
                    future.set_result(result)
            
        except Exception as e:
            self.logger.error(
                "dataloader_batch_load_failed",
                error=str(e),
                batch_size=len(keys)
            )
            
            # Reject all futures
            for _, future in batch:
                if not future.done():
                    future.set_exception(e)
        
        # Schedule next batch if queue not empty
        if self._queue:
            asyncio.create_task(self._dispatch_batch())
    
    def _get_key(self, item: T) -> K:
        """Extract key from item (override if needed)"""
        if hasattr(item, 'id'):
            return item.id
        return item
    
    def clear(self):
        """Clear cache"""
        self._cache.clear()
        self.logger.debug("dataloader_cache_cleared")
    
    def prime(self, key: K, value: T):
        """Prime cache with value"""
        if self.cache_enabled:
            self._cache[key] = value


# Example usage patterns

async def batch_load_workflows(workflow_ids: List[int], db) -> List[Any]:
    """Batch load workflows"""
    from backend.db.models.flows import Agentflow
    
    workflows = db.query(Agentflow).filter(
        Agentflow.id.in_(workflow_ids)
    ).all()
    
    return workflows


async def batch_load_users(user_ids: List[int], db) -> List[Any]:
    """Batch load users"""
    from backend.db.models.user import User
    
    users = db.query(User).filter(
        User.id.in_(user_ids)
    ).all()
    
    return users


class LoaderRegistry:
    """Registry for DataLoaders"""
    
    def __init__(self):
        self._loaders: Dict[str, DataLoader] = {}
    
    def register(self, name: str, loader: DataLoader):
        """Register loader"""
        self._loaders[name] = loader
    
    def get(self, name: str) -> Optional[DataLoader]:
        """Get loader by name"""
        return self._loaders.get(name)
    
    def clear_all(self):
        """Clear all loader caches"""
        for loader in self._loaders.values():
            loader.clear()


# Global registry
_loader_registry = LoaderRegistry()


def get_loader_registry() -> LoaderRegistry:
    """Get global loader registry"""
    return _loader_registry


# Example integration in FastAPI dependency:
"""
from backend.core.database.batch_loader import DataLoader, get_loader_registry
from backend.db.database import get_db

async def get_workflow_loader(db: Session = Depends(get_db)):
    registry = get_loader_registry()
    
    loader = registry.get('workflows')
    if not loader:
        async def batch_fn(ids):
            return await batch_load_workflows(ids, db)
        
        loader = DataLoader(batch_fn)
        registry.register('workflows', loader)
    
    return loader

# Usage in endpoint:
@router.get("/workflows/{id}")
async def get_workflow(
    id: int,
    loader: DataLoader = Depends(get_workflow_loader)
):
    workflow = await loader.load(id)
    return workflow

# N+1 problem solved:
@router.get("/workflows")
async def list_workflows(
    db: Session = Depends(get_db),
    loader: DataLoader = Depends(get_workflow_loader)
):
    workflows = db.query(Workflow).limit(10).all()
    
    # Load users for all workflows (batched!)
    users = await loader.load_many([w.user_id for w in workflows])
    
    # Only 2 queries:
    # 1. SELECT * FROM workflows LIMIT 10
    # 2. SELECT * FROM users WHERE id IN (...)
    
    return workflows
"""
