"""
Document Processing Services Module.

This module contains all document-related services including:
- Document parsing and processing
- Chunking strategies
- OCR processing (PaddleOCR)
- Table extraction
"""

from backend.services.document_processor import DocumentProcessor
from backend.services.document_service import DocumentService
from backend.services.semantic_chunker import SemanticChunker
from backend.services.contextual_chunker import ContextualChunker
from backend.services.paddleocr_processor import PaddleOCRProcessor

__all__ = [
    "DocumentProcessor",
    "DocumentService",
    "SemanticChunker",
    "ContextualChunker",
    "PaddleOCRProcessor",
]
