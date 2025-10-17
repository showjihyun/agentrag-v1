"""
Unit tests for DocumentProcessor.

Tests cover:
- File type detection and validation
- Text extraction for each file type (PDF, TXT, DOCX, HWP, HWPX)
- Text chunking with various sizes
- Metadata extraction
- Error handling for invalid inputs
- End-to-end document processing
"""

import pytest
import io
import xml.etree.ElementTree as ET
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from backend.services.document_processor import (
    DocumentProcessor,
    DocumentProcessingError,
)
from backend.models.document import Document, TextChunk


class TestDocumentProcessorInitialization:
    """Test DocumentProcessor initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        processor = DocumentProcessor()

        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 50
        assert processor.max_file_size == 10485760

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        processor = DocumentProcessor(
            chunk_size=1000, chunk_overlap=100, max_file_size=5242880
        )

        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 100
        assert processor.max_file_size == 5242880

    def test_init_invalid_chunk_size(self):
        """Test initialization fails with invalid chunk_size."""
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            DocumentProcessor(chunk_size=0)

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            DocumentProcessor(chunk_size=-100)

    def test_init_invalid_chunk_overlap(self):
        """Test initialization fails with invalid chunk_overlap."""
        with pytest.raises(ValueError, match="chunk_overlap cannot be negative"):
            DocumentProcessor(chunk_overlap=-10)

    def test_init_overlap_exceeds_size(self):
        """Test initialization fails when overlap >= chunk_size."""
        with pytest.raises(
            ValueError, match="chunk_overlap must be less than chunk_size"
        ):
            DocumentProcessor(chunk_size=100, chunk_overlap=100)

        with pytest.raises(
            ValueError, match="chunk_overlap must be less than chunk_size"
        ):
            DocumentProcessor(chunk_size=100, chunk_overlap=150)

    def test_init_invalid_max_file_size(self):
        """Test initialization fails with invalid max_file_size."""
        with pytest.raises(ValueError, match="max_file_size must be positive"):
            DocumentProcessor(max_file_size=0)


class TestFileTypeDetection:
    """Test file type detection."""

    def test_detect_pdf(self):
        """Test PDF file type detection."""
        processor = DocumentProcessor()

        assert processor.detect_file_type("document.pdf") == "pdf"
        assert processor.detect_file_type("Document.PDF") == "pdf"
        assert processor.detect_file_type("my.file.pdf") == "pdf"

    def test_detect_txt(self):
        """Test TXT file type detection."""
        processor = DocumentProcessor()

        assert processor.detect_file_type("document.txt") == "txt"
        assert processor.detect_file_type("README.TXT") == "txt"

    def test_detect_docx(self):
        """Test DOCX file type detection."""
        processor = DocumentProcessor()

        assert processor.detect_file_type("document.docx") == "docx"
        assert processor.detect_file_type("Report.DOCX") == "docx"

    def test_detect_hwp(self):
        """Test HWP file type detection."""
        processor = DocumentProcessor()

        assert processor.detect_file_type("document.hwp") == "hwp"

    def test_detect_hwpx(self):
        """Test HWPX file type detection."""
        processor = DocumentProcessor()

        assert processor.detect_file_type("document.hwpx") == "hwpx"

    def test_detect_unsupported_type(self):
        """Test detection fails for unsupported file types."""
        processor = DocumentProcessor()

        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.detect_file_type("document.exe")

        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.detect_file_type("image.jpg")

    def test_detect_no_extension(self):
        """Test detection fails for files without extension."""
        processor = DocumentProcessor()

        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.detect_file_type("document")

    def test_detect_empty_filename(self):
        """Test detection fails for empty filename."""
        processor = DocumentProcessor()

        with pytest.raises(ValueError, match="filename cannot be empty"):
            processor.detect_file_type("")


class TestFileSizeValidation:
    """Test file size validation."""

    def test_validate_valid_size(self):
        """Test validation passes for valid file size."""
        processor = DocumentProcessor(max_file_size=1000000)

        # Should not raise
        processor.validate_file_size(500000)
        processor.validate_file_size(1000000)

    def test_validate_exceeds_max(self):
        """Test validation fails when size exceeds maximum."""
        processor = DocumentProcessor(max_file_size=1000000)

        with pytest.raises(ValueError, match="File size .* exceeds maximum"):
            processor.validate_file_size(1500000)

    def test_validate_zero_size(self):
        """Test validation fails for zero size."""
        processor = DocumentProcessor()

        with pytest.raises(ValueError, match="file_size must be positive"):
            processor.validate_file_size(0)

    def test_validate_negative_size(self):
        """Test validation fails for negative size."""
        processor = DocumentProcessor()

        with pytest.raises(ValueError, match="file_size must be positive"):
            processor.validate_file_size(-100)


class TestTextExtractionTXT:
    """Test text extraction from TXT files."""

    def test_extract_txt_utf8(self):
        """Test extraction from UTF-8 encoded TXT."""
        processor = DocumentProcessor()
        content = "This is a test document.\nWith multiple lines.".encode("utf-8")

        text = processor.extract_text_from_txt(content)

        assert "This is a test document" in text
        assert "With multiple lines" in text

    def test_extract_txt_with_unicode(self):
        """Test extraction from TXT with unicode characters."""
        processor = DocumentProcessor()
        content = "Hello 世界 مرحبا Привет".encode("utf-8")

        text = processor.extract_text_from_txt(content)

        assert "Hello" in text
        assert "世界" in text

    def test_extract_txt_latin1(self):
        """Test extraction from Latin-1 encoded TXT."""
        processor = DocumentProcessor()
        content = "Café résumé naïve".encode("latin-1")

        text = processor.extract_text_from_txt(content)

        assert "Caf" in text  # Should decode successfully

    def test_extract_txt_empty(self):
        """Test extraction from empty TXT."""
        processor = DocumentProcessor()
        content = b""

        text = processor.extract_text_from_txt(content)

        assert text == ""


class TestTextExtractionPDF:
    """Test text extraction from PDF files."""

    @patch("backend.services.document_processor.PdfReader")
    def test_extract_pdf_success(self, mock_pdf_reader):
        """Test successful PDF text extraction."""
        processor = DocumentProcessor()

        # Mock PDF reader
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"

        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        content = b"fake pdf content"
        text = processor.extract_text_from_pdf(content)

        assert "Page 1 content" in text
        assert "Page 2 content" in text

    @patch("backend.services.document_processor.PdfReader")
    def test_extract_pdf_no_text(self, mock_pdf_reader):
        """Test PDF extraction fails when no text found."""
        processor = DocumentProcessor()

        # Mock PDF with no text
        mock_page = Mock()
        mock_page.extract_text.return_value = ""

        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        content = b"fake pdf content"

        with pytest.raises(DocumentProcessingError, match="No text could be extracted"):
            processor.extract_text_from_pdf(content)

    @patch("backend.services.document_processor.PdfReader")
    def test_extract_pdf_partial_failure(self, mock_pdf_reader):
        """Test PDF extraction continues when some pages fail."""
        processor = DocumentProcessor()

        # Mock PDF with one failing page
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.side_effect = Exception("Page error")
        mock_page3 = Mock()
        mock_page3.extract_text.return_value = "Page 3 content"

        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf_reader.return_value = mock_reader

        content = b"fake pdf content"
        text = processor.extract_text_from_pdf(content)

        # Should have content from pages 1 and 3
        assert "Page 1 content" in text
        assert "Page 3 content" in text

    @patch("backend.services.document_processor.PdfReader")
    def test_extract_pdf_reader_failure(self, mock_pdf_reader):
        """Test PDF extraction fails when reader fails."""
        processor = DocumentProcessor()

        mock_pdf_reader.side_effect = Exception("PDF corrupted")

        content = b"fake pdf content"

        with pytest.raises(
            DocumentProcessingError, match="Failed to extract text from PDF"
        ):
            processor.extract_text_from_pdf(content)


class TestTextExtractionDOCX:
    """Test text extraction from DOCX files."""

    @patch("backend.services.document_processor.DocxDocument")
    def test_extract_docx_success(self, mock_docx):
        """Test successful DOCX text extraction."""
        processor = DocumentProcessor()

        # Mock DOCX paragraphs
        mock_para1 = Mock()
        mock_para1.text = "First paragraph"
        mock_para2 = Mock()
        mock_para2.text = "Second paragraph"

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_docx.return_value = mock_doc

        content = b"fake docx content"
        text = processor.extract_text_from_docx(content)

        assert "First paragraph" in text
        assert "Second paragraph" in text

    @patch("backend.services.document_processor.DocxDocument")
    def test_extract_docx_empty_paragraphs(self, mock_docx):
        """Test DOCX extraction skips empty paragraphs."""
        processor = DocumentProcessor()

        # Mock DOCX with empty paragraphs
        mock_para1 = Mock()
        mock_para1.text = "Content"
        mock_para2 = Mock()
        mock_para2.text = "   "  # Whitespace only
        mock_para3 = Mock()
        mock_para3.text = "More content"

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
        mock_docx.return_value = mock_doc

        content = b"fake docx content"
        text = processor.extract_text_from_docx(content)

        assert "Content" in text
        assert "More content" in text
        # Should not have excessive whitespace
        assert text.count("\n\n\n") == 0

    @patch("backend.services.document_processor.DocxDocument")
    def test_extract_docx_no_text(self, mock_docx):
        """Test DOCX extraction fails when no text found."""
        processor = DocumentProcessor()

        # Mock DOCX with no content
        mock_doc = Mock()
        mock_doc.paragraphs = []
        mock_docx.return_value = mock_doc

        content = b"fake docx content"

        with pytest.raises(DocumentProcessingError, match="No text could be extracted"):
            processor.extract_text_from_docx(content)

    @patch("backend.services.document_processor.DocxDocument")
    def test_extract_docx_reader_failure(self, mock_docx):
        """Test DOCX extraction fails when reader fails."""
        processor = DocumentProcessor()

        mock_docx.side_effect = Exception("DOCX corrupted")

        content = b"fake docx content"

        with pytest.raises(
            DocumentProcessingError, match="Failed to extract text from DOCX"
        ):
            processor.extract_text_from_docx(content)


class TestTextExtractionHWP:
    """Test text extraction from HWP files."""

    @patch("backend.services.document_processor.olefile.isOleFile")
    @patch("backend.services.document_processor.olefile.OleFileIO")
    def test_extract_hwp_success(self, mock_ole_class, mock_is_ole):
        """Test successful HWP text extraction."""
        processor = DocumentProcessor()

        # Mock OLE file structure
        mock_is_ole.return_value = True

        mock_ole = Mock()
        mock_ole.exists.return_value = False  # No password protection
        mock_ole.listdir.return_value = [
            ["BodyText", "Section0"],
            ["BodyText", "Section1"],
        ]

        # Mock stream content
        mock_stream1 = Mock()
        mock_stream1.read.return_value = "Section 1 text".encode("utf-16le")
        mock_stream2 = Mock()
        mock_stream2.read.return_value = "Section 2 text".encode("utf-16le")

        mock_ole.openstream.side_effect = [mock_stream1, mock_stream2]
        mock_ole_class.return_value = mock_ole

        content = b"fake hwp content"
        text = processor.extract_text_from_hwp(content)

        assert "Section 1 text" in text
        assert "Section 2 text" in text
        mock_ole.close.assert_called_once()

    @patch("backend.services.document_processor.olefile.isOleFile")
    def test_extract_hwp_invalid_ole(self, mock_is_ole):
        """Test HWP extraction fails for invalid OLE file."""
        processor = DocumentProcessor()
        mock_is_ole.return_value = False

        content = b"fake hwp content"

        with pytest.raises(DocumentProcessingError, match="Invalid HWP file"):
            processor.extract_text_from_hwp(content)

    @patch("backend.services.document_processor.olefile.isOleFile")
    @patch("backend.services.document_processor.olefile.OleFileIO")
    def test_extract_hwp_password_protected(self, mock_ole_class, mock_is_ole):
        """Test HWP extraction fails for password-protected files."""
        processor = DocumentProcessor()

        mock_is_ole.return_value = True

        mock_ole = Mock()
        mock_ole.exists.return_value = True
        mock_stream = Mock()
        mock_stream.read.return_value = b"Password protected content"
        mock_ole.openstream.return_value = mock_stream
        mock_ole_class.return_value = mock_ole

        content = b"fake hwp content"

        with pytest.raises(DocumentProcessingError, match="password-protected"):
            processor.extract_text_from_hwp(content)

        mock_ole.close.assert_called_once()

    @patch("backend.services.document_processor.olefile.isOleFile")
    @patch("backend.services.document_processor.olefile.OleFileIO")
    def test_extract_hwp_no_text(self, mock_ole_class, mock_is_ole):
        """Test HWP extraction fails when no text found."""
        processor = DocumentProcessor()

        mock_is_ole.return_value = True

        mock_ole = Mock()
        mock_ole.exists.return_value = False
        mock_ole.listdir.return_value = []  # No BodyText sections
        mock_ole_class.return_value = mock_ole

        content = b"fake hwp content"

        with pytest.raises(DocumentProcessingError, match="No text could be extracted"):
            processor.extract_text_from_hwp(content)

        mock_ole.close.assert_called_once()

    @patch("backend.services.document_processor.olefile.isOleFile")
    @patch("backend.services.document_processor.olefile.OleFileIO")
    def test_extract_hwp_partial_failure(self, mock_ole_class, mock_is_ole):
        """Test HWP extraction continues when some sections fail."""
        processor = DocumentProcessor()

        mock_is_ole.return_value = True

        mock_ole = Mock()
        mock_ole.exists.return_value = False
        mock_ole.listdir.return_value = [
            ["BodyText", "Section0"],
            ["BodyText", "Section1"],
            ["BodyText", "Section2"],
        ]

        # First section succeeds, second fails, third succeeds
        mock_stream1 = Mock()
        mock_stream1.read.return_value = "Section 1 text".encode("utf-16le")
        mock_stream2 = Mock()
        mock_stream2.read.side_effect = Exception("Read error")
        mock_stream3 = Mock()
        mock_stream3.read.return_value = "Section 3 text".encode("utf-16le")

        mock_ole.openstream.side_effect = [mock_stream1, mock_stream2, mock_stream3]
        mock_ole_class.return_value = mock_ole

        content = b"fake hwp content"
        text = processor.extract_text_from_hwp(content)

        assert "Section 1 text" in text
        assert "Section 3 text" in text
        mock_ole.close.assert_called_once()

    @patch("backend.services.document_processor.olefile.isOleFile")
    @patch("backend.services.document_processor.olefile.OleFileIO")
    def test_extract_hwp_ole_failure(self, mock_ole_class, mock_is_ole):
        """Test HWP extraction fails when OLE reader fails."""
        processor = DocumentProcessor()

        mock_is_ole.return_value = True
        mock_ole_class.side_effect = Exception("OLE corrupted")

        content = b"fake hwp content"

        with pytest.raises(
            DocumentProcessingError, match="Failed to extract text from HWP"
        ):
            processor.extract_text_from_hwp(content)


class TestTextExtractionHWPX:
    """Test text extraction from HWPX files."""

    @patch("backend.services.document_processor.zipfile.is_zipfile")
    @patch("backend.services.document_processor.zipfile.ZipFile")
    def test_extract_hwpx_success(self, mock_zip_class, mock_is_zip):
        """Test successful HWPX text extraction."""
        processor = DocumentProcessor()

        mock_is_zip.return_value = True

        # Mock ZIP file structure
        mock_file_info = Mock()
        mock_file_info.flag_bits = 0  # Not encrypted

        mock_zip = Mock()
        mock_zip.__enter__ = Mock(return_value=mock_zip)
        mock_zip.__exit__ = Mock(return_value=False)
        mock_zip.filelist = [mock_file_info]
        mock_zip.namelist.return_value = [
            "Contents/section0.xml",
            "Contents/section1.xml",
        ]

        # Mock XML content
        xml1 = b'<?xml version="1.0"?><root><text>Section 1 content</text></root>'
        xml2 = b'<?xml version="1.0"?><root><text>Section 2 content</text></root>'
        mock_zip.read.side_effect = [xml1, xml2]

        mock_zip_class.return_value = mock_zip

        content = b"fake hwpx content"
        text = processor.extract_text_from_hwpx(content)

        assert "Section 1 content" in text
        assert "Section 2 content" in text

    @patch("backend.services.document_processor.zipfile.is_zipfile")
    def test_extract_hwpx_invalid_zip(self, mock_is_zip):
        """Test HWPX extraction fails for invalid ZIP file."""
        processor = DocumentProcessor()
        mock_is_zip.return_value = False

        content = b"fake hwpx content"

        with pytest.raises(DocumentProcessingError, match="Invalid HWPX file"):
            processor.extract_text_from_hwpx(content)

    @patch("backend.services.document_processor.zipfile.is_zipfile")
    @patch("backend.services.document_processor.zipfile.ZipFile")
    def test_extract_hwpx_password_protected(self, mock_zip_class, mock_is_zip):
        """Test HWPX extraction fails for password-protected files."""
        processor = DocumentProcessor()

        mock_is_zip.return_value = True

        # Mock encrypted file
        mock_file_info = Mock()
        mock_file_info.flag_bits = 0x1  # Bit 0 indicates encryption

        mock_zip = Mock()
        mock_zip.__enter__ = Mock(return_value=mock_zip)
        mock_zip.__exit__ = Mock(return_value=False)
        mock_zip.filelist = [mock_file_info]

        mock_zip_class.return_value = mock_zip

        content = b"fake hwpx content"

        with pytest.raises(DocumentProcessingError, match="password-protected"):
            processor.extract_text_from_hwpx(content)

    @patch("backend.services.document_processor.zipfile.is_zipfile")
    @patch("backend.services.document_processor.zipfile.ZipFile")
    def test_extract_hwpx_no_sections(self, mock_zip_class, mock_is_zip):
        """Test HWPX extraction fails when no section files found."""
        processor = DocumentProcessor()

        mock_is_zip.return_value = True

        mock_file_info = Mock()
        mock_file_info.flag_bits = 0

        mock_zip = Mock()
        mock_zip.__enter__ = Mock(return_value=mock_zip)
        mock_zip.__exit__ = Mock(return_value=False)
        mock_zip.filelist = [mock_file_info]
        mock_zip.namelist.return_value = ["other_file.xml"]  # No section files

        mock_zip_class.return_value = mock_zip

        content = b"fake hwpx content"

        with pytest.raises(DocumentProcessingError, match="No section files found"):
            processor.extract_text_from_hwpx(content)

    @patch("backend.services.document_processor.zipfile.is_zipfile")
    @patch("backend.services.document_processor.zipfile.ZipFile")
    def test_extract_hwpx_no_text(self, mock_zip_class, mock_is_zip):
        """Test HWPX extraction fails when no text found."""
        processor = DocumentProcessor()

        mock_is_zip.return_value = True

        mock_file_info = Mock()
        mock_file_info.flag_bits = 0

        mock_zip = Mock()
        mock_zip.__enter__ = Mock(return_value=mock_zip)
        mock_zip.__exit__ = Mock(return_value=False)
        mock_zip.filelist = [mock_file_info]
        mock_zip.namelist.return_value = ["Contents/section0.xml"]

        # Empty XML
        xml = b'<?xml version="1.0"?><root></root>'
        mock_zip.read.return_value = xml

        mock_zip_class.return_value = mock_zip

        content = b"fake hwpx content"

        with pytest.raises(DocumentProcessingError, match="No text could be extracted"):
            processor.extract_text_from_hwpx(content)

    @patch("backend.services.document_processor.zipfile.is_zipfile")
    @patch("backend.services.document_processor.zipfile.ZipFile")
    def test_extract_hwpx_partial_failure(self, mock_zip_class, mock_is_zip):
        """Test HWPX extraction continues when some sections fail."""
        processor = DocumentProcessor()

        mock_is_zip.return_value = True

        mock_file_info = Mock()
        mock_file_info.flag_bits = 0

        mock_zip = Mock()
        mock_zip.__enter__ = Mock(return_value=mock_zip)
        mock_zip.__exit__ = Mock(return_value=False)
        mock_zip.filelist = [mock_file_info]
        mock_zip.namelist.return_value = [
            "Contents/section0.xml",
            "Contents/section1.xml",
            "Contents/section2.xml",
        ]

        # First succeeds, second has bad XML, third succeeds
        xml1 = b'<?xml version="1.0"?><root><text>Section 1</text></root>'
        xml2 = b"<invalid xml"
        xml3 = b'<?xml version="1.0"?><root><text>Section 3</text></root>'
        mock_zip.read.side_effect = [xml1, xml2, xml3]

        mock_zip_class.return_value = mock_zip

        content = b"fake hwpx content"
        text = processor.extract_text_from_hwpx(content)

        assert "Section 1" in text
        assert "Section 3" in text

    @patch("backend.services.document_processor.zipfile.is_zipfile")
    @patch("backend.services.document_processor.zipfile.ZipFile")
    def test_extract_hwpx_zip_failure(self, mock_zip_class, mock_is_zip):
        """Test HWPX extraction fails when ZIP reader fails."""
        processor = DocumentProcessor()

        mock_is_zip.return_value = True
        mock_zip_class.side_effect = Exception("ZIP corrupted")

        content = b"fake hwpx content"

        with pytest.raises(
            DocumentProcessingError, match="Failed to extract text from HWPX"
        ):
            processor.extract_text_from_hwpx(content)


class TestXMLTextExtraction:
    """Test XML text extraction helper method."""

    def test_extract_text_from_simple_xml(self):
        """Test extraction from simple XML element."""
        processor = DocumentProcessor()

        xml_string = "<root>Simple text</root>"
        element = ET.fromstring(xml_string)

        text = processor._extract_text_from_xml(element)

        assert "Simple text" in text

    def test_extract_text_from_nested_xml(self):
        """Test extraction from nested XML elements."""
        processor = DocumentProcessor()

        xml_string = (
            "<root><para>First paragraph</para><para>Second paragraph</para></root>"
        )
        element = ET.fromstring(xml_string)

        text = processor._extract_text_from_xml(element)

        assert "First paragraph" in text
        assert "Second paragraph" in text

    def test_extract_text_from_xml_with_tail(self):
        """Test extraction includes tail text."""
        processor = DocumentProcessor()

        xml_string = "<root>Before <child>inside</child> after</root>"
        element = ET.fromstring(xml_string)

        text = processor._extract_text_from_xml(element)

        assert "Before" in text
        assert "inside" in text
        assert "after" in text

    def test_extract_text_from_empty_xml(self):
        """Test extraction from empty XML element."""
        processor = DocumentProcessor()

        xml_string = "<root></root>"
        element = ET.fromstring(xml_string)

        text = processor._extract_text_from_xml(element)

        assert text.strip() == ""


class TestTextExtraction:
    """Test generic text extraction routing."""

    @patch.object(DocumentProcessor, "extract_text_from_pdf")
    def test_extract_routes_to_pdf(self, mock_extract):
        """Test extract_text routes to PDF extractor."""
        processor = DocumentProcessor()
        mock_extract.return_value = "PDF text"

        content = b"fake content"
        text = processor.extract_text(content, "pdf")

        mock_extract.assert_called_once_with(content)
        assert text == "PDF text"

    @patch.object(DocumentProcessor, "extract_text_from_txt")
    def test_extract_routes_to_txt(self, mock_extract):
        """Test extract_text routes to TXT extractor."""
        processor = DocumentProcessor()
        mock_extract.return_value = "TXT text"

        content = b"fake content"
        text = processor.extract_text(content, "txt")

        mock_extract.assert_called_once_with(content)
        assert text == "TXT text"

    @patch.object(DocumentProcessor, "extract_text_from_docx")
    def test_extract_routes_to_docx(self, mock_extract):
        """Test extract_text routes to DOCX extractor."""
        processor = DocumentProcessor()
        mock_extract.return_value = "DOCX text"

        content = b"fake content"
        text = processor.extract_text(content, "docx")

        mock_extract.assert_called_once_with(content)
        assert text == "DOCX text"

    def test_extract_invalid_file_type(self):
        """Test extract_text fails with invalid file type."""
        processor = DocumentProcessor()
        content = b"fake content"

        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.extract_text(content, "invalid")

    def test_extract_empty_content(self):
        """Test extract_text fails with empty content."""
        processor = DocumentProcessor()

        with pytest.raises(ValueError, match="file_content cannot be empty"):
            processor.extract_text(b"", "pdf")


class TestTextChunking:
    """Test text chunking functionality."""

    def test_chunk_simple_text(self):
        """Test chunking of simple text."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        text = "This is a test. " * 20  # ~320 characters
        document_id = "test_doc"

        chunks = processor.chunk_text(text, document_id)

        assert len(chunks) > 1
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)
        assert all(chunk.document_id == document_id for chunk in chunks)
        assert all(chunk.chunk_index == i for i, chunk in enumerate(chunks))

    def test_chunk_respects_size(self):
        """Test that chunks respect size limits."""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        text = "Word " * 100  # Long text
        document_id = "test_doc"

        chunks = processor.chunk_text(text, document_id)

        # Most chunks should be around chunk_size
        for chunk in chunks[:-1]:  # Exclude last chunk
            assert len(chunk.text) <= processor.chunk_size + 50  # Some tolerance

    def test_chunk_with_overlap(self):
        """Test that chunks have overlap."""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        text = (
            "This is sentence one. This is sentence two. This is sentence three. " * 5
        )
        document_id = "test_doc"

        chunks = processor.chunk_text(text, document_id)

        if len(chunks) > 1:
            # Check that consecutive chunks have some overlap
            for i in range(len(chunks) - 1):
                # The end of one chunk should appear near the start of the next
                # (due to overlap)
                assert chunks[i].end_char > chunks[i + 1].start_char

    def test_chunk_sentence_boundary(self):
        """Test that chunking prefers sentence boundaries."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        document_id = "test_doc"

        chunks = processor.chunk_text(text, document_id)

        # Chunks should end at sentence boundaries when possible
        for chunk in chunks[:-1]:  # Exclude last chunk
            if "." in chunk.text:
                assert chunk.text.rstrip().endswith(".")

    def test_chunk_short_text(self):
        """Test chunking of text shorter than chunk_size."""
        processor = DocumentProcessor(chunk_size=500, chunk_overlap=50)
        text = "This is a short text."
        document_id = "test_doc"

        chunks = processor.chunk_text(text, document_id)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].chunk_index == 0

    def test_chunk_empty_text(self):
        """Test chunking fails with empty text."""
        processor = DocumentProcessor()

        with pytest.raises(ValueError, match="text cannot be empty"):
            processor.chunk_text("", "test_doc")

    def test_chunk_whitespace_only(self):
        """Test chunking fails with whitespace-only text."""
        processor = DocumentProcessor()

        with pytest.raises(ValueError, match="text cannot be only whitespace"):
            processor.chunk_text("   \n\t  ", "test_doc")

    def test_chunk_empty_document_id(self):
        """Test chunking fails with empty document_id."""
        processor = DocumentProcessor()

        with pytest.raises(ValueError, match="document_id cannot be empty"):
            processor.chunk_text("Some text", "")

    def test_chunk_ids_unique(self):
        """Test that chunk IDs are unique."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        text = "Text " * 100
        document_id = "test_doc"

        chunks = processor.chunk_text(text, document_id)
        chunk_ids = [chunk.chunk_id for chunk in chunks]

        assert len(chunk_ids) == len(set(chunk_ids))  # All unique

    def test_chunk_positions_sequential(self):
        """Test that chunk positions are sequential."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        text = "Text " * 100
        document_id = "test_doc"

        chunks = processor.chunk_text(text, document_id)

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
            if i > 0:
                # Current chunk should start at or after previous chunk
                assert chunk.start_char >= chunks[i - 1].start_char


class TestMetadataExtraction:
    """Test metadata extraction."""

    def test_extract_basic_metadata(self):
        """Test extraction of basic metadata."""
        processor = DocumentProcessor()

        metadata = processor.extract_metadata(
            filename="test.pdf", file_size=1024, file_type="pdf"
        )

        assert metadata["filename"] == "test.pdf"
        assert metadata["file_size"] == 1024
        assert metadata["file_type"] == "pdf"
        assert "upload_date" in metadata
        assert "processor_version" in metadata

    def test_extract_metadata_with_text(self):
        """Test metadata extraction with text statistics."""
        processor = DocumentProcessor()
        text = "This is a test document.\nWith multiple lines and words."

        metadata = processor.extract_metadata(
            filename="test.txt", file_size=2048, file_type="txt", text=text
        )

        assert "character_count" in metadata
        assert "word_count" in metadata
        assert "line_count" in metadata
        assert metadata["character_count"] == len(text)
        assert metadata["word_count"] > 0
        assert metadata["line_count"] >= 2

    def test_extract_metadata_upload_date_format(self):
        """Test that upload_date is in ISO format."""
        processor = DocumentProcessor()

        metadata = processor.extract_metadata(
            filename="test.pdf", file_size=1024, file_type="pdf"
        )

        # Should be parseable as ISO datetime
        upload_date = metadata["upload_date"]
        datetime.fromisoformat(upload_date)  # Should not raise


class TestEndToEndProcessing:
    """Test end-to-end document processing."""

    @pytest.mark.asyncio
    @patch.object(DocumentProcessor, "extract_text")
    async def test_process_document_success(self, mock_extract):
        """Test successful end-to-end document processing."""
        processor = DocumentProcessor(chunk_size=50, chunk_overlap=10)
        mock_extract.return_value = "This is extracted text. " * 10

        content = b"fake file content"
        filename = "test.pdf"
        file_size = len(content)

        document, chunks = await processor.process_document(
            content, filename, file_size
        )

        assert isinstance(document, Document)
        assert document.filename == filename
        assert document.file_type == "pdf"
        assert document.file_size == file_size
        assert document.processing_status == "completed"
        assert document.chunk_count == len(chunks)
        assert len(chunks) > 0
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)

    @pytest.mark.asyncio
    @patch.object(DocumentProcessor, "extract_text")
    async def test_process_document_extraction_failure(self, mock_extract):
        """Test document processing handles extraction failure."""
        processor = DocumentProcessor()
        mock_extract.side_effect = DocumentProcessingError("Extraction failed")

        content = b"fake file content"
        filename = "test.pdf"
        file_size = len(content)

        with pytest.raises(DocumentProcessingError):
            await processor.process_document(content, filename, file_size)

    @pytest.mark.asyncio
    async def test_process_document_file_too_large(self):
        """Test document processing fails for oversized files."""
        processor = DocumentProcessor(max_file_size=100)

        content = b"x" * 200
        filename = "test.txt"
        file_size = len(content)

        with pytest.raises(ValueError, match="File size .* exceeds maximum"):
            await processor.process_document(content, filename, file_size)

    @pytest.mark.asyncio
    async def test_process_document_unsupported_type(self):
        """Test document processing fails for unsupported file types."""
        processor = DocumentProcessor()

        content = b"fake content"
        filename = "test.exe"
        file_size = len(content)

        with pytest.raises(ValueError, match="Unsupported file type"):
            await processor.process_document(content, filename, file_size)

    @pytest.mark.asyncio
    @patch.object(DocumentProcessor, "extract_text")
    async def test_process_document_generates_id(self, mock_extract):
        """Test that document processing generates unique IDs."""
        processor = DocumentProcessor()
        mock_extract.return_value = "Test text"

        content = b"fake content"
        filename = "test.txt"
        file_size = len(content)

        doc1, _ = await processor.process_document(content, filename, file_size)
        doc2, _ = await processor.process_document(content, filename, file_size)

        # Should have different IDs
        assert doc1.document_id != doc2.document_id

    @pytest.mark.asyncio
    @patch.object(DocumentProcessor, "extract_text")
    async def test_process_document_metadata_populated(self, mock_extract):
        """Test that document metadata is properly populated."""
        processor = DocumentProcessor()
        mock_extract.return_value = "Test text content"

        content = b"fake content"
        filename = "test.txt"
        file_size = len(content)

        document, _ = await processor.process_document(content, filename, file_size)

        assert document.metadata is not None
        assert "filename" in document.metadata
        assert "file_type" in document.metadata
        assert "character_count" in document.metadata
