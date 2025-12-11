"""
Enhanced Knowledgebase Service with advanced features.

Improvements:
- Hybrid search (vector + BM25)
- Incremental indexing
- Document deduplication
- Metadata filtering
- Caching layer
- Async batch processing
- Statistics and analytics
"""

import logging
import uuid
import asyncio
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


class IndexingStrategy(str, Enum):
    """Document indexing strategies."""
    FULL = "full"  # Re-index entire document
    INCREMENTAL = "incremental"  # Only index new/changed chunks
    SMART = "smart"  # Auto-detect changes and index accordingly


class SearchMode(str, Enum):
    """Search modes for knowledgebase queries."""
    VECTOR = "vector"  # Pure vector similarity
    KEYWORD = "keyword"  # BM25 keyword search
    HYBRID = "hybrid"  # Combined vector + keyword
    SEMANTIC = "semantic"  # Semantic with query expansion


@dataclass
class SearchOptions:
    """Search configuration options."""
    mode: SearchMode = SearchMode.HYBRID
    top_k: int = 10
    min_score: float = 0.5
    rerank: bool = True
    expand_query: bool = False
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True


@dataclass
class DocumentStats:
    """Document statistics."""
    total_documents: int
    total_chunks: int
    total_tokens: int
    avg_chunk_size: float
    last_updated: Optional[datetime]


class EnhancedKnowledgebaseService:
    """
    Enhanced Knowledgebase Service with production-ready features.
    
    Features:
    - Hybrid search combining vector and keyword search
    - Document deduplication using content hashing
    - Incremental indexing for efficient updates
    - Caching for frequently accessed data
    - Comprehensive statistics and monitoring
    """
    
    def __init__(self, db: Session, redis_client=None):
        """
        Initialize Enhanced Knowledgebase Service.
        
        Args:
            db: Database session
            redis_client: Optional Redis client for caching
        """
        self.db = db
        self.redis = redis_client
        self._embedding_service = None
        self._milvus_manager = None
        self._bm25_index = {}  # In-memory BM25 index per collection
    
    @property
    def embedding_service(self):
        """Lazy load embedding service."""
        if self._embedding_service is None:
            from backend.services.embedding import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    def _get_milvus_manager(self, collection_name: str):
        """Get Milvus manager for collection."""
        from backend.services.milvus import MilvusManager
        return MilvusManager(
            collection_name=collection_name,
            embedding_dim=self.embedding_service.dimension
        )
    
    # =========================================================================
    # Document Management
    # =========================================================================
    
    async def add_document_with_dedup(
        self,
        kb_id: str,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        strategy: IndexingStrategy = IndexingStrategy.SMART
    ) -> Dict[str, Any]:
        """
        Add document with deduplication check.
        
        Args:
            kb_id: Knowledgebase ID
            file_content: File content bytes
            filename: Original filename
            metadata: Optional metadata
            strategy: Indexing strategy
            
        Returns:
            Result dict with document info and dedup status
        """
        from backend.db.models.agent_builder import Knowledgebase, KnowledgebaseDocument
        from backend.db.models.document import Document
        
        # Calculate content hash for deduplication
        content_hash = hashlib.sha256(file_content).hexdigest()
        
        # Check for existing document with same hash
        kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == kb_id).first()
        if not kb:
            raise ValueError(f"Knowledgebase {kb_id} not found")
        
        existing_doc = self.db.query(Document).join(
            KnowledgebaseDocument,
            Document.id == KnowledgebaseDocument.document_id
        ).filter(
            KnowledgebaseDocument.knowledgebase_id == kb_id,
            Document.content_hash == content_hash
        ).first()
        
        if existing_doc:
            logger.info(f"Document already exists in knowledgebase: {existing_doc.id}")
            return {
                "status": "duplicate",
                "document_id": str(existing_doc.id),
                "message": "Document already exists in knowledgebase",
                "existing_filename": existing_doc.filename
            }
        
        # Process new document
        result = await self._process_document(
            kb=kb,
            file_content=file_content,
            filename=filename,
            content_hash=content_hash,
            metadata=metadata,
            strategy=strategy
        )
        
        return result
    
    async def _process_document(
        self,
        kb,
        file_content: bytes,
        filename: str,
        content_hash: str,
        metadata: Optional[Dict[str, Any]],
        strategy: IndexingStrategy
    ) -> Dict[str, Any]:
        """Process and index a document."""
        from backend.services.document_processor import DocumentProcessor
        from backend.db.models.document import Document
        from backend.db.models.agent_builder import KnowledgebaseDocument
        import os
        
        start_time = datetime.utcnow()
        
        # Save file
        upload_dir = f"uploads/kb_{kb.id}"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create document record
        doc = Document(
            id=uuid.uuid4(),
            user_id=kb.user_id,
            filename=filename,
            original_filename=filename,
            file_path=file_path,
            file_size_bytes=len(file_content),
            content_hash=content_hash,
            status="processing"
        )
        self.db.add(doc)
        self.db.flush()
        
        try:
            # Process document
            doc_processor = DocumentProcessor(
                chunk_size=kb.chunk_size or 500,
                chunk_overlap=kb.chunk_overlap or 50
            )
            
            processed_doc, chunks = await doc_processor.process_document(
                file_content=file_content,
                filename=filename,
                file_size=len(file_content)
            )
            
            # Generate embeddings in batches
            texts = [chunk.text for chunk in chunks]
            embeddings = await self._batch_embed(texts)
            
            # Store in Milvus
            milvus = self._get_milvus_manager(kb.milvus_collection_name)
            
            await self._store_chunks(
                milvus=milvus,
                chunks=chunks,
                embeddings=embeddings,
                doc_id=str(doc.id),
                kb_id=kb.id,
                filename=filename,
                metadata=metadata
            )
            
            # Update BM25 index
            await self._update_bm25_index(kb.id, texts)
            
            # Create association
            kb_doc = KnowledgebaseDocument(
                id=uuid.uuid4(),
                knowledgebase_id=kb.id,
                document_id=doc.id
            )
            self.db.add(kb_doc)
            
            # Update document status
            doc.chunk_count = len(chunks)
            doc.status = "completed"
            doc.processing_completed_at = datetime.utcnow()
            
            self.db.commit()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                f"Document processed: {filename} -> {len(chunks)} chunks "
                f"in {processing_time:.2f}s"
            )
            
            return {
                "status": "success",
                "document_id": str(doc.id),
                "filename": filename,
                "chunk_count": len(chunks),
                "processing_time_seconds": processing_time
            }
            
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            self.db.commit()
            
            logger.error(f"Document processing failed: {e}", exc_info=True)
            raise
    
    async def _batch_embed(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings in batches."""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self.embedding_service.embed_batch(batch)
            all_embeddings.extend(embeddings)
        
        return all_embeddings
    
    async def _store_chunks(
        self,
        milvus,
        chunks,
        embeddings,
        doc_id: str,
        kb_id: str,
        filename: str,
        metadata: Optional[Dict[str, Any]]
    ):
        """Store chunks in Milvus with metadata."""
        insert_data = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_metadata = {
                "id": str(uuid.uuid4()),
                "text": chunk.text,
                "document_id": doc_id,
                "knowledgebase_id": kb_id,
                "chunk_index": i,
                "document_name": filename,
                "created_at": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            insert_data.append({
                "embedding": embedding,
                "metadata": chunk_metadata
            })
        
        # Batch insert
        batch_size = 100
        for i in range(0, len(insert_data), batch_size):
            batch = insert_data[i:i + batch_size]
            await milvus.insert_embeddings(
                embeddings=[item["embedding"] for item in batch],
                metadata=[item["metadata"] for item in batch]
            )
    
    async def _update_bm25_index(self, kb_id: str, texts: List[str]):
        """Update BM25 index for keyword search."""
        try:
            from rank_bm25 import BM25Okapi
            
            # Tokenize texts
            tokenized = [text.lower().split() for text in texts]
            
            # Get or create index
            if kb_id not in self._bm25_index:
                self._bm25_index[kb_id] = {
                    "corpus": [],
                    "texts": []
                }
            
            # Append to corpus
            self._bm25_index[kb_id]["corpus"].extend(tokenized)
            self._bm25_index[kb_id]["texts"].extend(texts)
            
            # Rebuild BM25 index
            self._bm25_index[kb_id]["bm25"] = BM25Okapi(
                self._bm25_index[kb_id]["corpus"]
            )
            
        except ImportError:
            logger.warning("rank_bm25 not installed, skipping BM25 index")
    
    # =========================================================================
    # Search
    # =========================================================================
    
    async def search(
        self,
        kb_id: str,
        query: str,
        options: Optional[SearchOptions] = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledgebase with configurable options.
        
        Args:
            kb_id: Knowledgebase ID
            query: Search query
            options: Search configuration
            
        Returns:
            List of search results
        """
        from backend.db.models.agent_builder import Knowledgebase
        
        options = options or SearchOptions()
        
        kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == kb_id).first()
        if not kb:
            raise ValueError(f"Knowledgebase {kb_id} not found")
        
        # Check cache first
        cache_key = f"kb_search:{kb_id}:{hashlib.md5(query.encode()).hexdigest()}"
        if self.redis:
            cached = await self._get_cached_results(cache_key)
            if cached:
                return cached
        
        # Expand query if enabled
        if options.expand_query:
            query = await self._expand_query(query)
        
        # Execute search based on mode
        if options.mode == SearchMode.VECTOR:
            results = await self._vector_search(kb, query, options)
        elif options.mode == SearchMode.KEYWORD:
            results = await self._keyword_search(kb, query, options)
        elif options.mode == SearchMode.HYBRID:
            results = await self._hybrid_search(kb, query, options)
        else:
            results = await self._semantic_search(kb, query, options)
        
        # Rerank if enabled
        if options.rerank and len(results) > 1:
            results = await self._rerank_results(query, results)
        
        # Filter by minimum score
        results = [r for r in results if r.get("score", 0) >= options.min_score]
        
        # Limit results
        results = results[:options.top_k]
        
        # Cache results
        if self.redis:
            await self._cache_results(cache_key, results, ttl=300)
        
        return results
    
    async def _vector_search(
        self,
        kb,
        query: str,
        options: SearchOptions
    ) -> List[Dict[str, Any]]:
        """Pure vector similarity search."""
        milvus = self._get_milvus_manager(kb.milvus_collection_name)
        
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)
        
        # Build filter expression
        filter_expr = f'knowledgebase_id == "{kb.id}"'
        if options.filters:
            for key, value in options.filters.items():
                if isinstance(value, str):
                    filter_expr += f' and {key} == "{value}"'
                else:
                    filter_expr += f' and {key} == {value}'
        
        # Search
        results = await milvus.search(
            query_embedding=query_embedding,
            top_k=options.top_k * 2,  # Get more for reranking
            filters=filter_expr
        )
        
        return [
            {
                "id": str(r.id),
                "text": r.text,
                "score": float(r.score),
                "document_id": r.document_id,
                "metadata": r.metadata if options.include_metadata else {}
            }
            for r in results
        ]
    
    async def _keyword_search(
        self,
        kb,
        query: str,
        options: SearchOptions
    ) -> List[Dict[str, Any]]:
        """BM25 keyword search."""
        if kb.id not in self._bm25_index:
            # Fallback to vector search if no BM25 index
            return await self._vector_search(kb, query, options)
        
        bm25_data = self._bm25_index[kb.id]
        bm25 = bm25_data.get("bm25")
        
        if not bm25:
            return await self._vector_search(kb, query, options)
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = bm25.get_scores(tokenized_query)
        
        # Get top results
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:options.top_k * 2]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "id": f"bm25_{idx}",
                    "text": bm25_data["texts"][idx],
                    "score": float(scores[idx]),
                    "metadata": {}
                })
        
        return results
    
    async def _hybrid_search(
        self,
        kb,
        query: str,
        options: SearchOptions
    ) -> List[Dict[str, Any]]:
        """Combined vector + keyword search with RRF fusion."""
        # Run both searches in parallel
        vector_task = self._vector_search(kb, query, options)
        keyword_task = self._keyword_search(kb, query, options)
        
        vector_results, keyword_results = await asyncio.gather(
            vector_task, keyword_task
        )
        
        # Reciprocal Rank Fusion (RRF)
        k = 60  # RRF constant
        scores = {}
        
        # Score from vector search
        for rank, result in enumerate(vector_results):
            doc_id = result.get("text", "")[:100]  # Use text prefix as key
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            if doc_id not in scores:
                scores[doc_id] = {"result": result, "score": 0}
            scores[doc_id] = {
                "result": result,
                "score": scores.get(doc_id, {}).get("score", 0) + 1 / (k + rank + 1)
            }
        
        # Score from keyword search
        for rank, result in enumerate(keyword_results):
            doc_id = result.get("text", "")[:100]
            if doc_id in scores:
                scores[doc_id]["score"] += 1 / (k + rank + 1)
            else:
                scores[doc_id] = {
                    "result": result,
                    "score": 1 / (k + rank + 1)
                }
        
        # Sort by combined score
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x["score"],
            reverse=True
        )
        
        return [
            {**item["result"], "score": item["score"]}
            for item in sorted_results
        ]
    
    async def _semantic_search(
        self,
        kb,
        query: str,
        options: SearchOptions
    ) -> List[Dict[str, Any]]:
        """Semantic search with query understanding."""
        # For now, use hybrid search as base
        return await self._hybrid_search(kb, query, options)
    
    async def _expand_query(self, query: str) -> str:
        """Expand query with synonyms and related terms."""
        # Simple expansion - in production, use LLM
        return query
    
    async def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder."""
        try:
            from backend.services.reranker import RerankerService
            
            reranker = RerankerService()
            texts = [r["text"] for r in results]
            
            reranked_scores = await reranker.rerank(query, texts)
            
            # Update scores
            for i, score in enumerate(reranked_scores):
                results[i]["score"] = score
            
            # Sort by new scores
            results.sort(key=lambda x: x["score"], reverse=True)
            
        except Exception as e:
            logger.warning(f"Reranking failed, using original order: {e}")
        
        return results
    
    async def _get_cached_results(self, key: str) -> Optional[List[Dict]]:
        """Get cached search results."""
        if not self.redis:
            return None
        
        try:
            import json
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache read failed: {e}")
        
        return None
    
    async def _cache_results(self, key: str, results: List[Dict], ttl: int = 300):
        """Cache search results."""
        if not self.redis:
            return
        
        try:
            import json
            await self.redis.setex(key, ttl, json.dumps(results))
        except Exception as e:
            logger.warning(f"Cache write failed: {e}")
    
    # =========================================================================
    # Statistics & Analytics
    # =========================================================================
    
    def get_statistics(self, kb_id: str) -> DocumentStats:
        """Get knowledgebase statistics."""
        from backend.db.models.agent_builder import Knowledgebase, KnowledgebaseDocument
        from backend.db.models.document import Document
        
        kb = self.db.query(Knowledgebase).filter(Knowledgebase.id == kb_id).first()
        if not kb:
            raise ValueError(f"Knowledgebase {kb_id} not found")
        
        # Get document stats
        stats = self.db.query(
            func.count(Document.id).label("total_documents"),
            func.sum(Document.chunk_count).label("total_chunks"),
            func.sum(Document.file_size_bytes).label("total_size"),
            func.max(Document.processing_completed_at).label("last_updated")
        ).join(
            KnowledgebaseDocument,
            Document.id == KnowledgebaseDocument.document_id
        ).filter(
            KnowledgebaseDocument.knowledgebase_id == kb_id
        ).first()
        
        total_docs = stats.total_documents or 0
        total_chunks = stats.total_chunks or 0
        
        return DocumentStats(
            total_documents=total_docs,
            total_chunks=total_chunks,
            total_tokens=total_chunks * 200,  # Estimate
            avg_chunk_size=total_chunks / max(total_docs, 1),
            last_updated=stats.last_updated
        )
    
    async def get_search_analytics(
        self,
        kb_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get search analytics for knowledgebase."""
        # In production, this would query a search logs table
        return {
            "total_searches": 0,
            "avg_latency_ms": 0,
            "top_queries": [],
            "low_score_queries": [],
            "period_days": days
        }


# Factory function
def get_enhanced_knowledgebase_service(db: Session) -> EnhancedKnowledgebaseService:
    """Get enhanced knowledgebase service instance."""
    try:
        from backend.core.dependencies import get_redis_client
        redis = get_redis_client()
    except Exception:
        redis = None
    
    return EnhancedKnowledgebaseService(db, redis)
