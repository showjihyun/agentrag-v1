"""Knowledgebase Service for managing agent knowledgebases."""

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
            
            kb = Knowledgebase(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=kb_data.name,
                description=kb_data.description,
                milvus_collection_name=collection_name,
                embedding_model=kb_data.embedding_model or "jhgan/ko-sroberta-multitask",
                chunk_size=kb_data.chunk_size,
                chunk_overlap=kb_data.chunk_overlap
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
            
            logger.info(f"Created knowledgebase: {kb.id} ({kb.name})")
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
        Delete knowledgebase.
        
        Args:
            kb_id: Knowledgebase ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            kb = self.get_knowledgebase(kb_id)
            if not kb:
                return False
            
            # TODO: Delete Milvus collection
            # from backend.services.milvus import MilvusService
            # milvus_service = MilvusService()
            # milvus_service.drop_collection(kb.milvus_collection_name)
            
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
            
            # 4. Generate embeddings in batches
            embedding_service = EmbeddingService()
            texts = [chunk.text for chunk in chunks]
            
            # Batch embeddings for efficiency (embed_batch is already async)
            embeddings = await embedding_service.embed_batch(texts)
            
            # 5. Store in Milvus in batches
            milvus_manager = MilvusManager(
                collection_name=kb.milvus_collection_name,
                embedding_dim=embedding_service.dimension
            )
            
            # Prepare batch insert data
            insert_data = []
            for chunk, embedding in zip(chunks, embeddings):
                insert_data.append({
                    "text": chunk.text,
                    "embedding": embedding,
                    "metadata": {
                        "document_id": str(doc.id),
                        "knowledgebase_id": kb_id,
                        "chunk_index": chunk.chunk_index,
                        "filename": file.filename
                    }
                })
            
            # Batch insert to Milvus (already async)
            await self._batch_insert_to_milvus(
                milvus_manager,
                insert_data
            )
            
            # 6. Create KnowledgebaseDocument record (association table)
            kb_doc = KnowledgebaseDocument(
                id=uuid.uuid4(),
                knowledgebase_id=kb_id,
                document_id=doc.id
            )
            self.db.add(kb_doc)
            
            # Update document with chunk count
            doc.chunk_count = len(chunks)
            doc.status = "completed"
            doc.processing_completed_at = datetime.utcnow()
            
            logger.info(
                f"Processed document {file.filename} for knowledgebase {kb_id} "
                f"({len(chunks)} chunks)"
            )
            
            # Return the Document object (not KnowledgebaseDocument)
            return doc
            
        except Exception as e:
            logger.error(
                f"Failed to process document {file.filename}: {e}",
                exc_info=True
            )
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
        """
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
        for i in range(0, len(embeddings), batch_size):
            batch_embeddings = embeddings[i:i + batch_size]
            batch_metadata = metadata_list[i:i + batch_size]
            
            await milvus_manager.insert_embeddings(
                embeddings=batch_embeddings,
                metadata=batch_metadata
            )
    
    async def search_knowledgebase(
        self,
        kb_id: str,
        query: str,
        top_k: int = 10
    ) -> List[KnowledgebaseSearchResult]:
        """
        Search knowledgebase using hybrid search.
        
        Args:
            kb_id: Knowledgebase ID
            query: Search query
            top_k: Number of results to return
            
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
            
            embedding_service = EmbeddingService()
            milvus_manager = MilvusManager(
                collection_name=kb.milvus_collection_name,
                embedding_dim=embedding_service.dimension
            )
            
            # Generate query embedding
            query_embedding = await embedding_service.embed_text(query)
            
            # Perform vector search with knowledgebase filter
            results = await milvus_manager.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filters=f'knowledgebase_id == "{kb_id}"'
            )
            
            # Convert to KnowledgebaseSearchResult
            search_results = []
            for result in results:
                search_results.append(
                    KnowledgebaseSearchResult(
                        chunk_id=str(result.id),
                        document_id=result.document_id,
                        text=result.text,
                        score=result.score,
                        metadata=result.metadata
                    )
                )
            
            logger.info(f"Search in knowledgebase {kb_id} returned {len(search_results)} results")
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
