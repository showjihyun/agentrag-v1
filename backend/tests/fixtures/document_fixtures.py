"""Document-related test fixtures."""

import pytest
from typing import Dict, Any
from io import BytesIO


@pytest.fixture
def sample_document_data() -> Dict[str, Any]:
    """Sample document data for testing."""
    return {
        "filename": "test.pdf",
        "file_path": "/uploads/test.pdf",
        "file_size": 1024,
        "mime_type": "application/pdf",
    }


@pytest.fixture
def sample_pdf_file() -> BytesIO:
    """Sample PDF file content for upload testing."""
    # Minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
196
%%EOF"""
    return BytesIO(pdf_content)


@pytest.fixture
def sample_text_file() -> BytesIO:
    """Sample text file for upload testing."""
    content = b"This is a sample text document for testing purposes."
    return BytesIO(content)


@pytest.fixture
def large_document_data() -> Dict[str, Any]:
    """Large document data for performance testing."""
    return {
        "filename": "large_document.pdf",
        "file_path": "/uploads/large_document.pdf",
        "file_size": 10 * 1024 * 1024,  # 10MB
        "mime_type": "application/pdf",
    }


@pytest.fixture
def multiple_documents_data() -> list[Dict[str, Any]]:
    """Multiple document data for batch testing."""
    return [
        {
            "filename": f"document_{i}.pdf",
            "file_path": f"/uploads/document_{i}.pdf",
            "file_size": 1024 * (i + 1),
            "mime_type": "application/pdf",
        }
        for i in range(5)
    ]
