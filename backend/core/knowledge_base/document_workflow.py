"""
Document Processing Workflow for Knowledge Base Integration.

Reuses existing document processing infrastructure and provides
workflow-compatible interface for document upload and processing.
"""

import logging
from typing import List, Dict, Any, Optional, BinaryIO
from datetime import datetime
import uuid

from backend.services.document_processor import DocumentProcessor
from backend.models.document import Document, TextChunk

logger = logging.getLogger(__name__)


class DocumentWorkflow:
    """
    Workflow-compatible document processing service.
    
    Reuses existing DocumentProcessor and provides simplified interface
    for workflow blocks to upload and process documents.
    """

    def __init__(self):
        """Initialize document workflow."""
        # Reuse existing document processor
        self.processor = DocumentProcessor()
        
        logger.info("DocumentWorkflow initialized")

    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """
        Process a document file and extract text chunks.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            metadata: Optional metadata (author, keywords, etc.)
            
        Returns:
            Document: Processed document with chunks
            
        Raises:
            ValueError: If file is invalid
            RuntimeError: If processing fails
        """
        try:
            # Validate file size
            file_size = len(file_content)
            self.processor.validate_file_size(file_size)
            
            # Detect file type
            file_type = self.processor.detect_file_type(filename)
            
            logger.info(
                f"Processing document: {filename} ({file_type}, {file_size} bytes)"
            )
            
            # Extract text based on file type
            if file_type == "pdf":
                text = self.processor.extract_text_from_pdf(file_content)
            elif file_type == "txt":
                text = self.processor.extract_text_from_txt(file_content)
            elif file_type == "docx":
                text = self.processor.extract_text_from_docx(file_content)
            elif file_type == "hwp":
                text = self.processor.extract_text_from_hwp(file_content)
            elif file_type == "hwpx":
                text = self.processor.extract_text_from_hwpx(file_content)
            elif file_type == "md":
                text = self.processor.extract_text_from_md(file_content)
            elif file_type == "pptx":
                text = self.processor.extract_text_from_pptx(file_content)
            elif file_type in ["png", "jpg", "jpeg", "gif", "bmp", "webp"]:
                # Image OCR processing
                text = await self.processor.extract_text_from_image(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            # Create document
            document_id = str(uuid.uuid4())
            
            # Merge provided metadata with defaults
            doc_metadata = {
                "author": "",
                "creation_date": int(datetime.now().timestamp()),
                "language": "en",
                "keywords": "",
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            document = Document(
                id=document_id,
                name=filename,
                file_type=file_type,
                content=text,
                upload_date=datetime.now(),
                metadata=doc_metadata,
            )
            
            # Chunk text using existing semantic chunker
            chunks = self.processor.semantic_chunker.chunk_text(
                text=text,
                document_id=document_id,
                document_name=filename,
                metadata=doc_metadata,
            )
            
            document.chunks = chunks
            
            logger.info(
                f"Document processed: {filename} -> {len(chunks)} chunks "
                f"({len(text)} characters)"
            )
            
            return document
            
        except Exception as e:
            error_msg = f"Failed to process document '{filename}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def process_batch(
        self,
        files: List[Dict[str, Any]],
    ) -> List[Document]:
        """
        Process multiple documents in batch.
        
        Args:
            files: List of file dictionaries with 'content', 'filename', 'metadata'
            
        Returns:
            List of processed documents
            
        Raises:
            RuntimeError: If batch processing fails
        """
        try:
            documents = []
            
            for file_info in files:
                file_content = file_info["content"]
                filename = file_info["filename"]
                metadata = file_info.get("metadata")
                
                try:
                    document = await self.process_document(
                        file_content=file_content,
                        filename=filename,
                        metadata=metadata,
                    )
                    documents.append(document)
                    
                except Exception as e:
                    logger.error(f"Failed to process {filename}: {str(e)}")
                    # Continue with other files
                    continue
            
            logger.info(
                f"Batch processing completed: {len(documents)}/{len(files)} successful"
            )
            
            return documents
            
        except Exception as e:
            error_msg = f"Batch processing failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.
        
        Returns:
            List of supported file extensions
        """
        return list(self.processor.SUPPORTED_TYPES.keys())

    def validate_file(
        self,
        filename: str,
        file_size: int,
    ) -> Dict[str, Any]:
        """
        Validate file before processing.
        
        Args:
            filename: File name
            file_size: File size in bytes
            
        Returns:
            dict: Validation result with 'valid' and 'error' keys
        """
        try:
            # Check file type
            file_type = self.processor.detect_file_type(filename)
            
            # Check file size
            self.processor.validate_file_size(file_size)
            
            return {
                "valid": True,
                "file_type": file_type,
                "file_size": file_size,
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
            }


# Global workflow instance
_workflow: Optional[DocumentWorkflow] = None


def get_document_workflow() -> DocumentWorkflow:
    """
    Get or create global document workflow instance.
    
    Returns:
        DocumentWorkflow: Global workflow instance
    """
    global _workflow
    
    if _workflow is None:
        _workflow = DocumentWorkflow()
    
    return _workflow
