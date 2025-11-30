"""
Persistent BM25 Index Manager

Provides persistent storage for BM25 indexes with:
- File-based persistence
- Redis caching
- Automatic rebuild on startup
- Incremental updates
"""

import logging
import pickle
import os
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class PersistentBM25Index:
    """
    Persistent BM25 index with file and Redis backing.
    
    Features:
    - Automatic persistence to disk
    - Redis caching for fast access
    - Incremental document updates
    - Index versioning
    """
    
    def __init__(
        self,
        index_name: str,
        storage_path: str = "data/bm25_indexes",
        redis_client=None,
        auto_save: bool = True,
        save_interval: int = 100,  # Save every N updates
    ):
        self.index_name = index_name
        self.storage_path = Path(storage_path)
        self.redis = redis_client
        self.auto_save = auto_save
        self.save_interval = save_interval
        
        # Index state
        self._index = None
        self._documents: List[str] = []
        self._doc_ids: List[str] = []
        self._metadata: Dict[str, Any] = {}
        self._update_count = 0
        self._version = 0
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing index
        self._load_index()
    
    @property
    def index_file(self) -> Path:
        """Get index file path."""
        return self.storage_path / f"{self.index_name}.pkl"
    
    @property
    def metadata_file(self) -> Path:
        """Get metadata file path."""
        return self.storage_path / f"{self.index_name}_meta.json"
    
    def _load_index(self):
        """Load index from disk."""
        try:
            if self.index_file.exists():
                with open(self.index_file, "rb") as f:
                    data = pickle.load(f)
                    self._index = data.get("index")
                    self._documents = data.get("documents", [])
                    self._doc_ids = data.get("doc_ids", [])
                    self._version = data.get("version", 0)
                
                logger.info(f"Loaded BM25 index '{self.index_name}' with {len(self._documents)} documents")
            
            if self.metadata_file.exists():
                with open(self.metadata_file, "r") as f:
                    self._metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            self._index = None
            self._documents = []
            self._doc_ids = []
    
    def _save_index(self):
        """Save index to disk."""
        try:
            data = {
                "index": self._index,
                "documents": self._documents,
                "doc_ids": self._doc_ids,
                "version": self._version,
            }
            
            with open(self.index_file, "wb") as f:
                pickle.dump(data, f)
            
            self._metadata["last_saved"] = datetime.utcnow().isoformat()
            self._metadata["document_count"] = len(self._documents)
            self._metadata["version"] = self._version
            
            with open(self.metadata_file, "w") as f:
                json.dump(self._metadata, f, indent=2)
            
            logger.debug(f"Saved BM25 index '{self.index_name}'")
        except Exception as e:
            logger.error(f"Failed to save BM25 index: {e}")
    
    async def _cache_to_redis(self):
        """Cache index to Redis for fast access."""
        if not self.redis:
            return
        
        try:
            key = f"bm25:index:{self.index_name}"
            data = pickle.dumps({
                "index": self._index,
                "documents": self._documents,
                "doc_ids": self._doc_ids,
                "version": self._version,
            })
            await self.redis.set(key, data, ex=3600)  # 1 hour TTL
        except Exception as e:
            logger.warning(f"Failed to cache BM25 index to Redis: {e}")
    
    async def _load_from_redis(self) -> bool:
        """Try to load index from Redis cache."""
        if not self.redis:
            return False
        
        try:
            key = f"bm25:index:{self.index_name}"
            data = await self.redis.get(key)
            if data:
                loaded = pickle.loads(data)
                if loaded.get("version", 0) >= self._version:
                    self._index = loaded.get("index")
                    self._documents = loaded.get("documents", [])
                    self._doc_ids = loaded.get("doc_ids", [])
                    self._version = loaded.get("version", 0)
                    return True
        except Exception as e:
            logger.warning(f"Failed to load BM25 index from Redis: {e}")
        
        return False
    
    def build_index(self, documents: List[str], doc_ids: Optional[List[str]] = None):
        """
        Build BM25 index from documents.
        
        Args:
            documents: List of document texts
            doc_ids: Optional list of document IDs
        """
        from rank_bm25 import BM25Okapi
        
        # Tokenize documents
        tokenized = [self._tokenize(doc) for doc in documents]
        
        # Build index
        self._index = BM25Okapi(tokenized)
        self._documents = documents
        self._doc_ids = doc_ids or [str(i) for i in range(len(documents))]
        self._version += 1
        
        # Save
        self._save_index()
        
        logger.info(f"Built BM25 index '{self.index_name}' with {len(documents)} documents")
    
    def add_document(self, document: str, doc_id: Optional[str] = None):
        """
        Add a single document to the index.
        
        Note: This rebuilds the entire index. For bulk additions, use build_index.
        """
        self._documents.append(document)
        self._doc_ids.append(doc_id or str(len(self._doc_ids)))
        
        # Rebuild index
        from rank_bm25 import BM25Okapi
        tokenized = [self._tokenize(doc) for doc in self._documents]
        self._index = BM25Okapi(tokenized)
        self._version += 1
        
        self._update_count += 1
        if self.auto_save and self._update_count >= self.save_interval:
            self._save_index()
            self._update_count = 0
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a document from the index.
        
        Args:
            doc_id: Document ID to remove
            
        Returns:
            True if document was removed
        """
        try:
            idx = self._doc_ids.index(doc_id)
            self._documents.pop(idx)
            self._doc_ids.pop(idx)
            
            # Rebuild index
            from rank_bm25 import BM25Okapi
            tokenized = [self._tokenize(doc) for doc in self._documents]
            self._index = BM25Okapi(tokenized)
            self._version += 1
            
            self._update_count += 1
            if self.auto_save and self._update_count >= self.save_interval:
                self._save_index()
                self._update_count = 0
            
            return True
        except ValueError:
            return False
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search the index.
        
        Args:
            query: Search query
            top_k: Number of results to return
            score_threshold: Minimum score threshold
            
        Returns:
            List of search results with doc_id, document, and score
        """
        if self._index is None or len(self._documents) == 0:
            return []
        
        # Tokenize query
        tokenized_query = self._tokenize(query)
        
        # Get scores
        scores = self._index.get_scores(tokenized_query)
        
        # Get top results
        results = []
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        for idx in sorted_indices[:top_k]:
            score = scores[idx]
            if score >= score_threshold:
                results.append({
                    "doc_id": self._doc_ids[idx],
                    "document": self._documents[idx],
                    "score": float(score),
                })
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for BM25."""
        # Simple whitespace tokenization with lowercasing
        # For Korean, consider using konlpy
        import re
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        return tokens
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics."""
        return {
            "name": self.index_name,
            "document_count": len(self._documents),
            "version": self._version,
            "has_index": self._index is not None,
            "storage_path": str(self.storage_path),
            "metadata": self._metadata,
        }
    
    def force_save(self):
        """Force save index to disk."""
        self._save_index()
        self._update_count = 0


class BM25IndexManager:
    """
    Manages multiple BM25 indexes.
    
    Features:
    - Multiple named indexes
    - Automatic index lifecycle management
    - Background persistence
    """
    
    def __init__(
        self,
        storage_path: str = "data/bm25_indexes",
        redis_client=None,
    ):
        self.storage_path = storage_path
        self.redis = redis_client
        self._indexes: Dict[str, PersistentBM25Index] = {}
        self._lock = asyncio.Lock()
    
    async def get_or_create_index(
        self,
        index_name: str,
        documents: Optional[List[str]] = None,
        doc_ids: Optional[List[str]] = None,
    ) -> PersistentBM25Index:
        """
        Get or create a BM25 index.
        
        Args:
            index_name: Name of the index
            documents: Optional documents to initialize with
            doc_ids: Optional document IDs
            
        Returns:
            BM25 index instance
        """
        async with self._lock:
            if index_name not in self._indexes:
                index = PersistentBM25Index(
                    index_name=index_name,
                    storage_path=self.storage_path,
                    redis_client=self.redis,
                )
                
                # Build if documents provided and index is empty
                if documents and len(index._documents) == 0:
                    index.build_index(documents, doc_ids)
                
                self._indexes[index_name] = index
            
            return self._indexes[index_name]
    
    async def delete_index(self, index_name: str) -> bool:
        """Delete an index."""
        async with self._lock:
            if index_name in self._indexes:
                index = self._indexes.pop(index_name)
                
                # Delete files
                try:
                    if index.index_file.exists():
                        os.remove(index.index_file)
                    if index.metadata_file.exists():
                        os.remove(index.metadata_file)
                except Exception as e:
                    logger.error(f"Failed to delete index files: {e}")
                
                return True
            return False
    
    async def save_all(self):
        """Save all indexes to disk."""
        for index in self._indexes.values():
            index.force_save()
    
    def list_indexes(self) -> List[Dict[str, Any]]:
        """List all indexes with stats."""
        return [index.get_stats() for index in self._indexes.values()]


# Global manager instance
_bm25_manager: Optional[BM25IndexManager] = None


def get_bm25_manager(
    storage_path: str = "data/bm25_indexes",
    redis_client=None,
) -> BM25IndexManager:
    """Get or create global BM25 manager."""
    global _bm25_manager
    if _bm25_manager is None:
        _bm25_manager = BM25IndexManager(storage_path, redis_client)
    return _bm25_manager
