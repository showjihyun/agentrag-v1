# Persistent BM25 Index Service
"""
Persistent BM25 index using pickle for serialization.

This service provides disk-based BM25 indexing to avoid re-indexing on restart.
Uses pickle for fast serialization/deserialization.
"""

import logging
import pickle
import os
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from backend.services.bm25_search import BM25

logger = logging.getLogger(__name__)


class PersistentBM25Service:
    """
    Persistent BM25 service with disk-based index storage.
    
    Features:
    - Automatic index persistence to disk
    - Fast loading on startup
    - Incremental updates
    - Index versioning
    """

    def __init__(
        self,
        index_path: str = "./data/bm25_index",
        auto_save: bool = True,
        save_interval: int = 100  # Save every N documents
    ):
        """
        Initialize Persistent BM25 Service.
        
        Args:
            index_path: Directory path for storing index files
            auto_save: Automatically save index after updates
            save_interval: Number of documents between auto-saves
        """
        self.index_path = Path(index_path)
        self.auto_save = auto_save
        self.save_interval = save_interval
        
        # Create index directory if it doesn't exist
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Index files
        self.index_file = self.index_path / "bm25_index.pkl"
        self.metadata_file = self.index_path / "metadata.pkl"
        
        # BM25 instance
        self.bm25: Optional[BM25] = None
        self.indexed = False
        
        # Metadata
        self.metadata = {
            "version": "1.0",
            "num_docs": 0,
            "last_updated": None,
            "doc_count_since_save": 0
        }
        
        # Try to load existing index
        self._load_index()
        
        logger.info(
            f"PersistentBM25Service initialized: "
            f"index_path={index_path}, indexed={self.indexed}, "
            f"docs={self.metadata['num_docs']}"
        )

    def _load_index(self) -> bool:
        """
        Load BM25 index from disk.
        
        Returns:
            bool: True if index was loaded successfully
        """
        try:
            if not self.index_file.exists():
                logger.info("No existing BM25 index found")
                return False
            
            # Load BM25 index
            with open(self.index_file, 'rb') as f:
                self.bm25 = pickle.load(f)
            
            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
            
            self.indexed = True
            
            logger.info(
                f"Loaded BM25 index: {self.metadata['num_docs']} documents, "
                f"last updated: {self.metadata['last_updated']}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            # Reset to empty state
            self.bm25 = None
            self.indexed = False
            return False

    def _save_index(self) -> bool:
        """
        Save BM25 index to disk.
        
        Returns:
            bool: True if index was saved successfully
        """
        try:
            if self.bm25 is None:
                logger.warning("No BM25 index to save")
                return False
            
            # Save BM25 index
            with open(self.index_file, 'wb') as f:
                pickle.dump(self.bm25, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Update and save metadata
            from datetime import datetime
            self.metadata['last_updated'] = datetime.now().isoformat()
            self.metadata['doc_count_since_save'] = 0
            
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            logger.info(f"Saved BM25 index: {self.metadata['num_docs']} documents")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save BM25 index: {e}")
            return False

    async def index_documents(self, documents: List[Dict[str, str]]) -> int:
        """
        Index documents for BM25 search.
        
        Args:
            documents: List of documents with 'id' and 'content' keys
        
        Returns:
            Number of documents indexed
        """
        if not documents:
            logger.warning("No documents to index")
            return 0
        
        try:
            corpus = [doc["content"] for doc in documents]
            doc_ids = [doc["id"] for doc in documents]
            
            # Create new BM25 index
            self.bm25 = BM25()
            self.bm25.fit(corpus, doc_ids)
            self.indexed = True
            
            # Update metadata
            self.metadata['num_docs'] = len(documents)
            self.metadata['doc_count_since_save'] += len(documents)
            
            logger.info(f"Indexed {len(documents)} documents for BM25 search")
            
            # Auto-save if enabled
            if self.auto_save:
                if self.metadata['doc_count_since_save'] >= self.save_interval:
                    self._save_index()
            
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            return 0

    async def add_documents(self, new_documents: List[Dict[str, str]]) -> int:
        """
        Add new documents to existing index (incremental update).
        
        Args:
            new_documents: List of new documents to add
        
        Returns:
            Number of documents added
        """
        if not new_documents:
            return 0
        
        try:
            # If no existing index, just index all
            if not self.indexed or self.bm25 is None:
                return await self.index_documents(new_documents)
            
            # Combine with existing documents
            existing_corpus = [" ".join(doc) for doc in self.bm25.corpus]
            existing_ids = self.bm25.doc_ids
            
            new_corpus = [doc["content"] for doc in new_documents]
            new_ids = [doc["id"] for doc in new_documents]
            
            # Rebuild index with all documents
            all_corpus = existing_corpus + new_corpus
            all_ids = existing_ids + new_ids
            
            self.bm25 = BM25()
            self.bm25.fit(all_corpus, all_ids)
            
            # Update metadata
            self.metadata['num_docs'] = len(all_ids)
            self.metadata['doc_count_since_save'] += len(new_documents)
            
            logger.info(
                f"Added {len(new_documents)} documents to BM25 index "
                f"(total: {self.metadata['num_docs']})"
            )
            
            # Auto-save if threshold reached
            if self.auto_save:
                if self.metadata['doc_count_since_save'] >= self.save_interval:
                    self._save_index()
            
            return len(new_documents)
            
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return 0

    async def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search documents using BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of (doc_id, score) tuples
        """
        if not self.indexed or self.bm25 is None:
            logger.warning("BM25 index not built, returning empty results")
            return []
        
        results = self.bm25.search(query, top_k)
        
        logger.debug(
            f"BM25 search completed: query='{query[:50]}...', "
            f"results={len(results)}"
        )
        
        return results

    def force_save(self) -> bool:
        """
        Force save index to disk immediately.
        
        Returns:
            bool: True if successful
        """
        return self._save_index()

    def get_stats(self) -> Dict:
        """Get index statistics"""
        return {
            "indexed": self.indexed,
            "num_docs": self.metadata['num_docs'],
            "last_updated": self.metadata['last_updated'],
            "index_size_bytes": self.index_file.stat().st_size if self.index_file.exists() else 0,
            "doc_count_since_save": self.metadata['doc_count_since_save']
        }

    def clear_index(self) -> bool:
        """
        Clear index from memory and disk.
        
        Returns:
            bool: True if successful
        """
        try:
            # Clear memory
            self.bm25 = None
            self.indexed = False
            self.metadata['num_docs'] = 0
            self.metadata['doc_count_since_save'] = 0
            
            # Delete files
            if self.index_file.exists():
                self.index_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
            
            logger.info("Cleared BM25 index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear index: {e}")
            return False


# Global persistent BM25 service instance
_persistent_bm25_service: Optional[PersistentBM25Service] = None


def get_persistent_bm25_service(
    index_path: str = "./data/bm25_index",
    auto_save: bool = True
) -> PersistentBM25Service:
    """Get global persistent BM25 service instance"""
    global _persistent_bm25_service
    if _persistent_bm25_service is None:
        _persistent_bm25_service = PersistentBM25Service(
            index_path=index_path,
            auto_save=auto_save
        )
    return _persistent_bm25_service
