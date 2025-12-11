"""
Documents domain API routers

Groups all document-related endpoints:
- documents.py: Document CRUD operations
- document_preview.py: Document preview generation
- knowledge_base.py: Knowledge base management
- paddleocr_advanced.py: Advanced OCR processing
"""

# Re-export routers for easy access
# Usage: from backend.api.documents import documents_router

__all__ = [
    "documents",
    "document_preview",
    "knowledge_base",
    "paddleocr_advanced",
]
