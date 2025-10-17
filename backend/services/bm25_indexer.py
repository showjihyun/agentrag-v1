# BM25 Indexer Service - Automatic indexing on document upload
import logging
from typing import List, Dict
from backend.services.persistent_bm25 import get_persistent_bm25_service

logger = logging.getLogger(__name__)


class BM25Indexer:
    """
    Service for automatically indexing documents in BM25 search.

    Integrates with document upload pipeline to ensure all documents
    are indexed for keyword search.
    """

    def __init__(self):
        self.bm25_service = get_persistent_bm25_service()
        self.indexed_count = 0

    async def index_chunks(self, chunks: List[Dict[str, str]]) -> int:
        """
        Index document chunks for BM25 search.

        Args:
            chunks: List of chunks with 'id' and 'text' keys
                   Example: [{'id': 'chunk_1', 'text': 'content...'}]

        Returns:
            Number of chunks indexed
        """
        if not chunks:
            logger.warning("No chunks to index")
            return 0

        try:
            # Convert to BM25 format
            documents = [
                {
                    "id": chunk.get("id") or chunk.get("chunk_id"),
                    "content": chunk.get("text") or chunk.get("content", ""),
                }
                for chunk in chunks
            ]

            # Filter out empty content
            documents = [doc for doc in documents if doc["content"].strip()]

            if not documents:
                logger.warning("All chunks have empty content")
                return 0

            # Index in BM25 (incremental add)
            await self.bm25_service.add_documents(documents)

            self.indexed_count += len(documents)
            logger.info(
                f"Indexed {len(documents)} chunks in BM25 (total: {self.indexed_count})"
            )

            return len(documents)

        except Exception as e:
            logger.error(f"Failed to index chunks in BM25: {e}", exc_info=True)
            # Don't raise - BM25 indexing failure shouldn't block document upload
            return 0

    async def reindex_all(self, all_chunks: List[Dict[str, str]]) -> int:
        """
        Rebuild entire BM25 index from scratch.

        Useful for:
        - Initial setup
        - After BM25 parameter changes
        - Recovery from corruption

        Args:
            all_chunks: All chunks from all documents

        Returns:
            Number of chunks indexed
        """
        logger.info(f"Rebuilding BM25 index with {len(all_chunks)} chunks")

        try:
            documents = [
                {
                    "id": chunk.get("id") or chunk.get("chunk_id"),
                    "content": chunk.get("text") or chunk.get("content", ""),
                }
                for chunk in all_chunks
            ]

            documents = [doc for doc in documents if doc["content"].strip()]

            await self.bm25_service.index_documents(documents)

            self.indexed_count = len(documents)
            logger.info(f"BM25 index rebuilt: {self.indexed_count} chunks")

            return self.indexed_count

        except Exception as e:
            logger.error(f"Failed to rebuild BM25 index: {e}", exc_info=True)
            raise

    def get_stats(self) -> Dict[str, int]:
        """Get indexing statistics"""
        return {
            "total_indexed": self.indexed_count,
            "is_indexed": self.bm25_service.indexed,
        }


# Global indexer instance
_bm25_indexer = None


def get_bm25_indexer() -> BM25Indexer:
    """Get global BM25 indexer instance"""
    global _bm25_indexer
    if _bm25_indexer is None:
        _bm25_indexer = BM25Indexer()
    return _bm25_indexer
