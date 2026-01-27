"""Knowledgebase Service for managing agent knowledgebases.

한글/영어 이중 언어 지원:
- 한글 형태소 분석 기반 토큰화
- 한글 최적화 청킹
- 하이브리드 검색 (Vector + BM25)
- 쿼리 확장
"""

import logging
import uuid
import asyncio
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from backend.db.models.agent_builder import (
    Knowledgebase,
    KnowledgebaseDocument,
    KnowledgebaseVersion
)
from backend.models.agent_builder import (
    KnowledgebaseCreate,
    KnowledgebaseUpdate,
    KnowledgebaseSearchResult
)

logger = logging.getLogger(__name__)

# 한글 처리기 lazy import
def _get_korean_processor():
    """한글 처리기 lazy import"""
    try:
        from backend.services.agent_builder.knowledgebase_korean_processor import (
            get_knowledgebase_korean_processor,
            ChunkConfig,
            SearchConfig,
            SearchMode
        )
        return get_knowledgebase_korean_processor()
    except ImportError as e:
        logger.warning(f"Korean processor not available: {e}")
        return None


class KnowledgebaseService:
    """Service for managing knowledgebases."""
    
    def __init__(self, db: Session):
        """
        Initialize Knowledgebase Service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_knowledgebase(
        self,
        user_id: str,
        kb_data: KnowledgebaseCreate
    ) -> Knowledgebase:
        """
        Create a new knowledgebase.
        
        Args:
            user_id: User ID creating the knowledgebase
            kb_data: Knowledgebase creation data
            
        Returns:
            Created Knowledgebase model
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Generate unique collection name
            collection_name = f"kb_{uuid.uuid4().hex[:16]}"
            
            # Determine embedding model
            embedding_model = kb_data.embedding_model or "jhgan/ko-sroberta-multitask"
            
            # Get the correct embedding dimension for the model
            from backend.services.embedding import EmbeddingService
            embedding_dim = EmbeddingService.get_model_dimension(embedding_model)
            
            logger.info(
                f"Creating knowledgebase with model={embedding_model}, "
                f"dimension={embedding_dim}"
            )
            
            kb = Knowledgebase(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=kb_data.name,
                description=kb_data.description,
                milvus_collection_name=collection_name,
                embedding_model=embedding_model,
                embedding_dimension=embedding_dim,  # Store dimension in DB
                chunk_size=kb_data.chunk_size,
                chunk_overlap=kb_data.chunk_overlap,
                kg_enabled=getattr(kb_data, 'kg_enabled', False)
            )
            
            self.db.add(kb)
            self.db.flush()
            
            # Create initial version
            version = KnowledgebaseVersion(
                id=str(uuid.uuid4()),
                knowledgebase_id=kb.id,
                version_number=1,
                document_snapshot=[]
            )
            self.db.add(version)
            
            self.db.commit()
            self.db.refresh(kb)
            
            logger.info(
                f"Created knowledgebase: {kb.id} ({kb.name}) "
                f"with collection {collection_name} (dim={embedding_dim})"
            )
            return kb
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create knowledgebase: {e}", exc_info=True)
            raise
    
    def get_knowledgebase(self, kb_id: str) -> Optional[Knowledgebase]:
        """
        Get knowledgebase by ID.
        
        Args:
            kb_id: Knowledgebase ID
            
        Returns:
            Knowledgebase model or None if not found
        """
        return self.db.query(Knowledgebase).filter(
            Knowledgebase.id == kb_id
        ).first()
    
    def update_knowledgebase(
        self,
        kb_id: str,
        kb_data: KnowledgebaseUpdate
    ) -> Optional[Knowledgebase]:
        """
        Update knowledgebase.
        
        Args:
            kb_id: Knowledgebase ID
            kb_data: Update data
            
        Returns:
            Updated Knowledgebase model or None if not found
        """
        try:
            kb = self.get_knowledgebase(kb_id)
            if not kb:
                return None
            
            if kb_data.name is not None:
                kb.name = kb_data.name
            
            if kb_data.description is not None:
                kb.description = kb_data.description
            
            if kb_data.chunk_size is not None:
                kb.chunk_size = kb_data.chunk_size
            
            if kb_data.chunk_overlap is not None:
                kb.chunk_overlap = kb_data.chunk_overlap
            
            if hasattr(kb_data, 'kg_enabled') and kb_data.kg_enabled is not None:
                kb.kg_enabled = kb_data.kg_enabled
            
            kb.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(kb)
            
            logger.info(f"Updated knowledgebase: {kb_id}")
            return kb
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update knowledgebase: {e}", exc_info=True)
            raise
    
    def delete_knowledgebase(self, kb_id: str) -> bool:
        """
        Delete knowledgebase including Milvus collection and files.
        
        Args:
            kb_id: Knowledgebase ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            kb = self.get_knowledgebase(kb_id)
            if not kb:
                return False
            
            # Delete Milvus collection
            try:
                from backend.services.milvus import MilvusManager
                from backend.services.embedding import EmbeddingService
                
                embedding_service = EmbeddingService()
                milvus_manager = MilvusManager(
                    collection_name=kb.milvus_collection_name,
                    embedding_dim=embedding_service.dimension
                )
                milvus_manager.drop_collection()
                logger.info(f"Dropped Milvus collection: {kb.milvus_collection_name}")
            except Exception as e:
                logger.warning(f"Failed to drop Milvus collection: {e}")
            
            # Delete uploaded files
            try:
                import shutil
                import os
                upload_dir = f"uploads/kb_{kb_id}"
                if os.path.exists(upload_dir):
                    shutil.rmtree(upload_dir)
                    logger.info(f"Deleted upload directory: {upload_dir}")
            except Exception as e:
                logger.warning(f"Failed to delete upload directory: {e}")
            
            # Delete associated documents
            from backend.db.models.document import Document
            doc_ids = [
                doc.document_id for doc in 
                self.db.query(KnowledgebaseDocument).filter(
                    KnowledgebaseDocument.knowledgebase_id == kb_id
                ).all()
            ]
            
            if doc_ids:
                self.db.query(Document).filter(Document.id.in_(doc_ids)).delete(
                    synchronize_session=False
                )
            
            # Delete knowledgebase (cascades to KnowledgebaseDocument, KnowledgebaseVersion)
            self.db.delete(kb)
            self.db.commit()
            
            logger.info(f"Deleted knowledgebase: {kb_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete knowledgebase: {e}", exc_info=True)
            raise
    
    def list_knowledgebases(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Knowledgebase], int]:
        """
        List knowledgebases with filters.
        
        Args:
            filters: Filter criteria
            skip: Number of records to skip
            limit: Maximum number of records
            
        Returns:
            Tuple of (knowledgebases, total_count)
        """
        from sqlalchemy.orm import joinedload
        
        query = self.db.query(Knowledgebase).options(
            joinedload(Knowledgebase.documents)
        )
        
        if "user_id" in filters:
            query = query.filter(Knowledgebase.user_id == filters["user_id"])
        
        if "search" in filters:
            search = f"%{filters['search']}%"
            query = query.filter(
                (Knowledgebase.name.ilike(search)) |
                (Knowledgebase.description.ilike(search))
            )
        
        total = query.count()
        kbs = query.order_by(Knowledgebase.created_at.desc()).offset(skip).limit(limit).all()
        
        return kbs, total
    
    async def add_documents(
        self,
        kb_id: str,
        files: List[Any]
    ) -> List[KnowledgebaseDocument]:
        """
        Add documents to knowledgebase with batch processing.
        
        Args:
            kb_id: Knowledgebase ID
            files: List of uploaded files
            
        Returns:
            List of created KnowledgebaseDocument models
        """
        try:
            kb = self.get_knowledgebase(kb_id)
            if not kb:
                raise ValueError(f"Knowledgebase {kb_id} not found")
            
            # Process documents in batches
            batch_size = 5
            documents = []
            
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]
                
                # Process batch in parallel
                tasks = [
                    self._process_single_document(kb_id, kb, file)
                    for file in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect successful results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Document processing failed: {result}")
                    elif result:
                        documents.append(result)
            
            # Commit all changes
            try:
                self.db.commit()
                logger.info(f"Added {len(documents)} documents to knowledgebase {kb_id}")
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to commit documents: {e}")
                raise
            
            return documents
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to add documents: {e}", exc_info=True)
            raise
    
    async def _process_single_document(
        self,
        kb_id: str,
        kb: Knowledgebase,
        file: Any
    ) -> Optional[KnowledgebaseDocument]:
        """
        Process a single document asynchronously.
        
        한글/영어 이중 언어 지원:
        - 한글 전처리 (한자 변환, 띄어쓰기 정규화)
        - 한글 최적화 청킹 (문장 경계 인식)
        - BM25 인덱스 구축
        
        Args:
            kb_id: Knowledgebase ID
            kb: Knowledgebase model
            file: Uploaded file
            
        Returns:
            KnowledgebaseDocument model or None if failed
        """
        try:
            # Import required services
            from backend.services.document_processor import DocumentProcessor
            from backend.services.embedding import EmbeddingService
            from backend.services.milvus import MilvusManager
            from backend.db.models.document import Document
            import os
            
            # 1. Save file
            upload_dir = f"uploads/kb_{kb_id}"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, file.filename)
            
            # Read file content
            content = await asyncio.to_thread(file.file.read)
            
            # Write file
            await asyncio.to_thread(
                lambda: open(file_path, "wb").write(content)
            )
            
            # 2. Create document record
            doc = Document(
                id=uuid.uuid4(),
                user_id=kb.user_id,
                filename=file.filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size_bytes=len(content),
                mime_type=file.content_type or "application/octet-stream",
                status="processing"
            )
            self.db.add(doc)
            self.db.flush()
            
            # 3. Extract and chunk text (in thread pool)
            doc_processor = DocumentProcessor()
            processed_doc, chunks = await doc_processor.process_document(
                file_content=content,
                filename=file.filename,
                file_size=len(content)
            )
            
            # 4. 한글 처리기로 청크 후처리
            korean_processor = _get_korean_processor()
            processed_chunks = []
            
            if korean_processor:
                for chunk in chunks:
                    # 텍스트 전처리 (한자 변환, 띄어쓰기 정규화)
                    processed_text = korean_processor.preprocess_text(chunk.text)
                    
                    # 언어 감지
                    language = korean_processor.detect_language(processed_text)
                    
                    # 토큰화 (BM25용)
                    tokens, _ = korean_processor.tokenize(processed_text, extract_nouns=True)
                    
                    processed_chunks.append({
                        "text": processed_text,
                        "tokens": tokens,
                        "language": language.value,
                        "chunk_index": chunk.chunk_index
                    })
                
                logger.info(
                    f"Processed {len(processed_chunks)} chunks with Korean processor"
                )
            else:
                # Fallback: 기본 처리
                for chunk in chunks:
                    processed_chunks.append({
                        "text": chunk.text,
                        "tokens": chunk.text.lower().split(),
                        "language": "unknown",
                        "chunk_index": chunk.chunk_index
                    })
            
            # 5. Generate embeddings using KB's embedding model
            embedding_model = kb.embedding_model or "jhgan/ko-sroberta-multitask"
            embedding_service = EmbeddingService(model_name=embedding_model)
            
            # Get embedding dimension from KB or service
            embedding_dim = getattr(kb, 'embedding_dimension', None) or embedding_service.dimension
            
            logger.info(
                f"Using embedding model: {embedding_model} (dimension: {embedding_dim})"
            )
            
            texts = [pc["text"] for pc in processed_chunks]
            
            # Batch embeddings for efficiency (embed_batch is already async)
            embeddings = await embedding_service.embed_batch(texts)
            
            # 6. Store in Milvus in batches
            milvus_manager = MilvusManager(
                collection_name=kb.milvus_collection_name,
                embedding_dim=embedding_dim
            )
            
            # Prepare batch insert data
            insert_data = []
            for pc, embedding in zip(processed_chunks, embeddings):
                insert_data.append({
                    "text": pc["text"],
                    "embedding": embedding,
                    "metadata": {
                        "document_id": str(doc.id),
                        "knowledgebase_id": kb_id,
                        "chunk_index": pc["chunk_index"],
                        "filename": file.filename,
                        "language": pc["language"]
                    }
                })
            
            # Batch insert to Milvus (already async)
            logger.info(f"Inserting {len(insert_data)} chunks to Milvus for document {file.filename}")
            await self._batch_insert_to_milvus(
                milvus_manager,
                insert_data
            )
            logger.info(f"Successfully inserted {len(insert_data)} chunks to Milvus")
            
            # 7. BM25 인덱스 업데이트
            if korean_processor:
                from backend.services.agent_builder.knowledgebase_korean_processor import ProcessedChunk
                
                bm25_chunks = [
                    ProcessedChunk(
                        chunk_id=f"{doc.id}_{pc['chunk_index']}",
                        text=pc["text"],
                        tokens=pc["tokens"],
                        language=korean_processor.detect_language(pc["text"]),
                        size=len(pc["text"]),
                        metadata={"document_id": str(doc.id)}
                    )
                    for pc in processed_chunks
                ]
                
                korean_processor.update_bm25_index(
                    collection_id=kb.milvus_collection_name,
                    new_chunks=bm25_chunks
                )
            
            # 8. Create KnowledgebaseDocument record (association table)
            kb_doc = KnowledgebaseDocument(
                id=uuid.uuid4(),
                knowledgebase_id=kb_id,
                document_id=doc.id
            )
            self.db.add(kb_doc)
            
            # Update document with chunk count
            doc.chunk_count = len(processed_chunks)
            doc.status = "completed"
            doc.processing_completed_at = datetime.utcnow()
            
            logger.info(
                f"Processed document {file.filename} for knowledgebase {kb_id} "
                f"({len(processed_chunks)} chunks)"
            )
            
            # Return the Document object (not KnowledgebaseDocument)
            return doc
            
        except Exception as e:
            logger.error(
                f"Failed to process document {file.filename}: {e}",
                exc_info=True
            )
            # Update document status to failed
            try:
                if 'doc' in locals():
                    doc.status = "failed"
                    doc.error_message = str(e)
                    self.db.flush()
            except:
                pass
            return None
    
    async def _batch_insert_to_milvus(
        self,
        milvus_manager,
        insert_data: List[Dict[str, Any]]
    ):
        """
        Batch insert data to Milvus.
        
        Args:
            milvus_manager: Milvus manager instance
            insert_data: List of data to insert
            
        Raises:
            Exception: If insertion fails
        """
        try:
            # Prepare embeddings and metadata for batch insert
            embeddings = [item["embedding"] for item in insert_data]
            metadata_list = []
            
            for i, item in enumerate(insert_data):
                # Milvus expects specific metadata fields
                meta = {
                    "id": str(uuid.uuid4()),
                    "text": item["text"],
                    "document_id": item["metadata"]["document_id"],
                    "chunk_index": item["metadata"]["chunk_index"],
                    "document_name": item["metadata"]["filename"],
                    "knowledgebase_id": item["metadata"]["knowledgebase_id"],
                    "file_type": "pdf",  # TODO: get from actual file type
                    "upload_date": datetime.utcnow().isoformat()
                }
                metadata_list.append(meta)
            
            # Insert in batches of 100
            batch_size = 100
            total_inserted = 0
            
            for i in range(0, len(embeddings), batch_size):
                batch_embeddings = embeddings[i:i + batch_size]
                batch_metadata = metadata_list[i:i + batch_size]
                
                try:
                    ids = await milvus_manager.insert_embeddings(
                        embeddings=batch_embeddings,
                        metadata=batch_metadata
                    )
                    total_inserted += len(ids)
                    logger.info(f"Inserted batch {i//batch_size + 1}: {len(ids)} entities")
                except Exception as e:
                    logger.error(f"Failed to insert batch {i//batch_size + 1}: {e}", exc_info=True)
                    raise
            
            logger.info(f"Successfully inserted {total_inserted} total entities to Milvus")
            
        except Exception as e:
            logger.error(f"Milvus batch insert failed: {e}", exc_info=True)
            raise

    
    async def search_knowledgebase(
        self,
        kb_id: str,
        query: str,
        top_k: int = 10,
        search_mode: str = "hybrid",
        expand_query: bool = True
    ) -> List[KnowledgebaseSearchResult]:
        """
        Search knowledgebase using hybrid search (Vector + BM25).
        
        한글/영어 이중 언어 지원:
        - 한글 형태소 분석 기반 토큰화
        - 하이브리드 검색 (Vector + BM25)
        - 쿼리 확장 (동의어, 관련어)
        
        Args:
            kb_id: Knowledgebase ID
            query: Search query
            top_k: Number of results to return
            search_mode: "vector", "keyword", "hybrid" (default: hybrid)
            expand_query: Whether to expand query with synonyms
            
        Returns:
            List of search results
        """
        try:
            kb = self.get_knowledgebase(kb_id)
            if not kb:
                raise ValueError(f"Knowledgebase {kb_id} not found")
            
            # Import required services
            from backend.services.embedding import EmbeddingService
            from backend.services.milvus import MilvusManager
            
            # Use KB's embedding model
            embedding_model = kb.embedding_model or "jhgan/ko-sroberta-multitask"
            embedding_service = EmbeddingService(model_name=embedding_model)
            
            # Get embedding dimension from KB or service
            embedding_dim = getattr(kb, 'embedding_dimension', None) or embedding_service.dimension
            
            milvus_manager = MilvusManager(
                collection_name=kb.milvus_collection_name,
                embedding_dim=embedding_dim
            )
            
            logger.info(
                f"Searching KB {kb_id} with model: {embedding_model} (dim: {embedding_dim})"
            )
            
            # 한글 처리기 가져오기
            korean_processor = _get_korean_processor()
            
            # 쿼리 전처리
            processed_query = query
            if korean_processor:
                processed_query = korean_processor.preprocess_query(query)
                language = korean_processor.detect_language(query)
                logger.info(f"Query language detected: {language.value}")
            
            # 쿼리 확장 (선택적)
            queries_to_search = [processed_query]
            if expand_query and korean_processor:
                expanded = korean_processor.expand_query(processed_query)
                queries_to_search = expanded[:3]  # 최대 3개 쿼리
                logger.info(f"Query expanded: {queries_to_search}")
            
            # 벡터 검색 수행
            vector_results = []
            if search_mode in ["vector", "hybrid"]:
                for q in queries_to_search:
                    query_embedding = await embedding_service.embed_text(q)
                    
                    results = await milvus_manager.search(
                        query_embedding=query_embedding,
                        top_k=top_k * 2,
                        filters=f'knowledgebase_id == "{kb_id}"'
                    )
                    
                    for result in results:
                        vector_results.append((
                            str(result.id),
                            result.text,
                            float(result.score)
                        ))
            
            # 하이브리드 검색 (Vector + BM25)
            if search_mode == "hybrid" and korean_processor:
                hybrid_results = await korean_processor.hybrid_search(
                    collection_id=kb.milvus_collection_name,
                    query=processed_query,
                    vector_results=vector_results,
                    top_k=top_k
                )
                
                # Convert to KnowledgebaseSearchResult
                search_results = []
                for result in hybrid_results:
                    search_results.append(
                        KnowledgebaseSearchResult(
                            chunk_id=result["chunk_id"],
                            document_id=result.get("document_id", ""),
                            text=result["text"],
                            score=result["score"],
                            metadata={
                                "sources": result.get("sources", []),
                                "is_hybrid": result.get("is_hybrid", False)
                            }
                        )
                    )
            else:
                # 벡터 검색만 사용
                # 중복 제거 및 정렬
                seen = set()
                unique_results = []
                for chunk_id, text, score in sorted(vector_results, key=lambda x: x[2], reverse=True):
                    if chunk_id not in seen:
                        seen.add(chunk_id)
                        unique_results.append((chunk_id, text, score))
                
                search_results = []
                for chunk_id, text, score in unique_results[:top_k]:
                    search_results.append(
                        KnowledgebaseSearchResult(
                            chunk_id=chunk_id,
                            document_id="",
                            text=text,
                            score=score,
                            metadata={"sources": ["vector"]}
                        )
                    )
            
            logger.info(
                f"Search in knowledgebase {kb_id} returned {len(search_results)} results "
                f"(mode={search_mode}, expand={expand_query})"
            )
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search knowledgebase: {e}", exc_info=True)
            raise
    
    def get_versions(self, kb_id: str) -> List[KnowledgebaseVersion]:
        """
        Get version history for knowledgebase.
        
        Args:
            kb_id: Knowledgebase ID
            
        Returns:
            List of KnowledgebaseVersion models
        """
        return self.db.query(KnowledgebaseVersion).filter(
            KnowledgebaseVersion.knowledgebase_id == kb_id
        ).order_by(KnowledgebaseVersion.created_at.desc()).all()
    
    def rollback_version(
        self,
        kb_id: str,
        version_id: str
    ) -> Knowledgebase:
        """
        Rollback knowledgebase to previous version.
        
        Args:
            kb_id: Knowledgebase ID
            version_id: Version ID to rollback to
            
        Returns:
            Updated Knowledgebase model
        """
        try:
            kb = self.get_knowledgebase(kb_id)
            if not kb:
                raise ValueError(f"Knowledgebase {kb_id} not found")
            
            # Get version
            version = self.db.query(KnowledgebaseVersion).filter(
                KnowledgebaseVersion.id == version_id,
                KnowledgebaseVersion.knowledgebase_id == kb_id
            ).first()
            
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            # Load version snapshot
            snapshot = version.snapshot or {}
            
            # Create new version before rollback (for safety)
            current_snapshot = {
                "name": kb.name,
                "description": kb.description,
                "chunk_size": kb.chunk_size,
                "chunk_overlap": kb.chunk_overlap,
                "embedding_model": kb.embedding_model,
                "document_count": self.db.query(KnowledgebaseDocument).filter(
                    KnowledgebaseDocument.knowledgebase_id == kb_id
                ).count()
            }
            
            rollback_version = KnowledgebaseVersion(
                id=str(uuid.uuid4()),
                knowledgebase_id=kb_id,
                version_number=f"rollback_{version.version_number}",
                change_description=f"Rollback to version {version.version_number}",
                snapshot=current_snapshot,
                created_by=kb.user_id
            )
            self.db.add(rollback_version)
            
            # Restore knowledgebase settings from snapshot
            if "name" in snapshot:
                kb.name = snapshot["name"]
            if "description" in snapshot:
                kb.description = snapshot["description"]
            if "chunk_size" in snapshot:
                kb.chunk_size = snapshot["chunk_size"]
            if "chunk_overlap" in snapshot:
                kb.chunk_overlap = snapshot["chunk_overlap"]
            if "embedding_model" in snapshot:
                kb.embedding_model = snapshot["embedding_model"]
            
            kb.updated_at = datetime.utcnow()
            
            # Note: Document restoration would require:
            # 1. Clearing current Milvus collection
            # 2. Re-processing documents from snapshot
            # This is complex and should be done carefully in production
            
            self.db.commit()
            self.db.refresh(kb)
            
            logger.info(f"Rolled back knowledgebase {kb_id} to version {version_id}")
            return kb
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to rollback version: {e}", exc_info=True)
            raise
        
        return kb
    
    def get_document_status(
        self,
        kb_id: str,
        document_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get document processing status.
        
        Args:
            kb_id: Knowledgebase ID
            document_id: Document ID
            
        Returns:
            Dictionary with status information or None if not found
        """
        try:
            from backend.db.models.document import Document
            
            # Query the Document (not KnowledgebaseDocument)
            doc = self.db.query(Document).filter(
                Document.id == document_id
            ).first()
            
            if not doc:
                return None
            
            # Verify it belongs to the knowledgebase
            kb_doc = self.db.query(KnowledgebaseDocument).filter(
                KnowledgebaseDocument.document_id == document_id,
                KnowledgebaseDocument.knowledgebase_id == kb_id
            ).first()
            
            if not kb_doc:
                return None
            
            # Get status from Document model
            status = doc.status or "completed"
            progress = 100 if status == "completed" else 50
            error = doc.error_message
            
            return {
                "document_id": str(doc.id),
                "filename": doc.filename,
                "status": status,
                "progress": progress,
                "error": error,
                "chunk_count": doc.chunk_count or 0,
                "file_size": doc.file_size_bytes,
                "created_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "updated_at": doc.processing_completed_at.isoformat() if doc.processing_completed_at else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get document status: {e}", exc_info=True)
            return None
