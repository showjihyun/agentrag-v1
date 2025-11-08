"""
Document Preview API

Provides endpoints for previewing documents with OCR and layout analysis.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import logging
from pathlib import Path
import io
import tempfile
from uuid import UUID

from backend.services.paddleocr_processor import get_paddleocr_processor
from backend.config import settings
from backend.db.repositories.document_repository import DocumentRepository
from backend.db.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/document-preview", tags=["document-preview"])


def get_document_path(document_id: str, db: Session) -> str:
    """
    Get the actual file path for a document from the database.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        str: File path
        
    Raises:
        HTTPException: If document not found
    """
    try:
        from backend.db.models.document import Document
        
        # Query document directly without user_id verification
        # (preview is public once you have the document_id)
        document = db.query(Document).filter(Document.id == UUID(document_id)).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = Path(document.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found on disk")
        
        return str(file_path)
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document path: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get document path: {str(e)}")


def convert_document_to_images(file_path: str, page: int = 1) -> tuple[bytes, int]:
    """
    Convert document to image for preview.
    
    Args:
        file_path: Path to document file
        page: Page number (1-indexed)
        
    Returns:
        Tuple of (image_bytes, total_pages)
    """
    from PIL import Image
    import fitz  # PyMuPDF for PDF
    
    file_path_obj = Path(file_path)
    ext = file_path_obj.suffix.lower()
    
    # Handle PDF
    if ext == '.pdf':
        doc = fitz.open(file_path)
        total_pages = len(doc)
        
        if page < 1 or page > total_pages:
            page = 1
        
        # Render page to image
        page_obj = doc[page - 1]
        pix = page_obj.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
        img_data = pix.tobytes("png")
        doc.close()
        
        return img_data, total_pages
    
    # Handle DOCX, PPTX
    elif ext in ['.docx', '.pptx', '.doc', '.ppt']:
        # Convert to PDF first, then to image
        try:
            import subprocess
            
            # Use LibreOffice to convert to PDF
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_pdf = Path(temp_dir) / "temp.pdf"
                
                # Convert to PDF using LibreOffice (if available)
                result = subprocess.run(
                    ['soffice', '--headless', '--convert-to', 'pdf', '--outdir', temp_dir, file_path],
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode == 0 and temp_pdf.exists():
                    # Now convert PDF to image
                    return convert_document_to_images(str(temp_pdf), page)
                else:
                    # Fallback: return placeholder
                    raise Exception("LibreOffice conversion failed")
        except Exception as e:
            logger.warning(f"Failed to convert {ext} to image: {e}")
            # Return placeholder image
            img = Image.new('RGB', (800, 1000), color='white')
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), f"Preview not available for {ext} files", fill='black')
            
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue(), 1
    
    # Handle HWP
    elif ext in ['.hwp', '.hwpx']:
        # HWP requires special handling
        # For now, return placeholder
        img = Image.new('RGB', (800, 1000), color='white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), f"HWP preview: Use text extraction", fill='black')
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue(), 1
    
    # Handle images
    elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']:
        with Image.open(file_path) as img:
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            return img_bytes.getvalue(), 1
    
    else:
        raise ValueError(f"Unsupported file type: {ext}")


@router.get("/{document_id}/info")
async def get_document_info(document_id: str, db: Session = Depends(get_db)):
    """
    Get document information including page count.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        Document information
    """
    try:
        # Get document path from database
        doc_path = Path(get_document_path(document_id, db))
        ext = doc_path.suffix.lower()
        
        # Get page count
        total_pages = 1
        if ext == '.pdf':
            import fitz
            doc = fitz.open(str(doc_path))
            total_pages = len(doc)
            doc.close()
        
        return JSONResponse(content={
            "document_id": document_id,
            "filename": doc_path.name,
            "file_type": ext.lstrip('.'),
            "total_pages": total_pages,
            "file_size": doc_path.stat().st_size,
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document info: {str(e)}"
        )


@router.get("/{document_id}/page/{page}")
async def get_document_page(
    document_id: str,
    page: int = 1,
    db: Session = Depends(get_db),
):
    """
    Get a specific page of a document as an image.
    
    Args:
        document_id: Document ID
        page: Page number (1-indexed)
        db: Database session
        
    Returns:
        PNG image of the page
    """
    try:
        # Get document path from database
        doc_path = get_document_path(document_id, db)
        
        # Convert to image
        img_bytes, total_pages = convert_document_to_images(doc_path, page)
        
        return StreamingResponse(
            io.BytesIO(img_bytes),
            media_type="image/png",
            headers={
                "X-Total-Pages": str(total_pages),
                "X-Current-Page": str(page),
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document page: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document page: {str(e)}"
        )


@router.get("/{document_id}/preview")
async def get_document_preview(
    document_id: str,
    page: Optional[int] = Query(1, ge=1, description="Page number (for PDFs)"),
    include_ocr: bool = Query(True, description="Include OCR text"),
    include_layout: bool = Query(True, description="Include layout analysis"),
    db: Session = Depends(get_db),
):
    """
    Get document preview with OCR and layout analysis.
    
    Args:
        document_id: Document ID
        page: Page number (for multi-page documents)
        include_ocr: Include OCR text extraction
        include_layout: Include layout analysis
        db: Database session
        
    Returns:
        Document preview data with OCR results and layout information
    """
    try:
        # Get document path from database
        doc_path = Path(get_document_path(document_id, db))
        ext = doc_path.suffix.lower()
        
        # Check if it's an image file
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        is_image = ext in image_extensions
        
        # Get total pages
        total_pages = 1
        if ext == '.pdf':
            import fitz
            doc = fitz.open(str(doc_path))
            total_pages = len(doc)
            doc.close()
        
        result = {
            "document_id": document_id,
            "filename": doc_path.name,
            "file_type": ext.lstrip('.'),
            "is_image": is_image,
            "total_pages": total_pages,
            "current_page": page,
        }
        
        if is_image and (include_ocr or include_layout):
            # Use PaddleOCR for image processing
            processor = get_paddleocr_processor()
            
            if include_ocr:
                # Extract text with bounding boxes
                text_boxes = processor.extract_text_with_boxes(str(doc_path))
                # text_boxes is a list of dicts with 'text', 'bbox', 'confidence'
                result["ocr_text"] = "\n".join([box['text'] for box in text_boxes])
                result["text_boxes"] = text_boxes
            
            if include_layout:
                # Analyze layout
                layout_result = processor.analyze_layout(str(doc_path))
                result["layout"] = layout_result
            
            # Get image dimensions
            from PIL import Image
            with Image.open(doc_path) as img:
                result["width"] = img.width
                result["height"] = img.height
        
        # For non-image files, provide page image URL
        if not is_image:
            result["page_url"] = f"/api/documents/{document_id}/page/{page}"
        else:
            result["preview_url"] = f"/uploads/{document_id}/{doc_path.name}"
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating document preview: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate document preview: {str(e)}"
        )


@router.get("/{document_id}/ocr")
async def get_document_ocr(
    document_id: str,
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    db: Session = Depends(get_db),
):
    """
    Get OCR results for a document.
    
    Args:
        document_id: Document ID
        page: Page number
        db: Database session
        
    Returns:
        OCR results with text and bounding boxes
    """
    try:
        # Get document path from database
        doc_path = Path(get_document_path(document_id, db))
        
        # Use PaddleOCR
        processor = get_paddleocr_processor()
        ocr_result = processor.extract_text_with_boxes(str(doc_path))
        
        return JSONResponse(content={
            "document_id": document_id,
            "filename": doc_path.name,
            "text": ocr_result.get("text", ""),
            "boxes": ocr_result.get("boxes", []),
            "confidence": ocr_result.get("confidence", 0.0),
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting OCR: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract OCR: {str(e)}"
        )


@router.get("/{document_id}/layout")
async def get_document_layout(
    document_id: str,
    page: Optional[int] = Query(1, ge=1, description="Page number"),
    db: Session = Depends(get_db),
):
    """
    Get layout analysis for a document.
    
    Args:
        document_id: Document ID
        page: Page number
        db: Database session
        
    Returns:
        Layout analysis results
    """
    try:
        # Get document path from database
        doc_path = Path(get_document_path(document_id, db))
        
        # Use PaddleOCR for layout analysis
        processor = get_paddleocr_processor()
        layout_result = processor.analyze_layout(str(doc_path))
        
        return JSONResponse(content={
            "document_id": document_id,
            "filename": doc_path.name,
            "layout": layout_result,
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing layout: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze layout: {str(e)}"
        )


@router.get("/{document_id}/image")
async def get_document_image(document_id: str, db: Session = Depends(get_db)):
    """
    Get the original image file for image documents.
    
    Args:
        document_id: Document ID
        db: Database session
        
    Returns:
        Original image file
    """
    try:
        # Get document path from database
        doc_path = Path(get_document_path(document_id, db))
        ext = doc_path.suffix.lower()
        
        # Check if it's an image
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        if ext not in image_extensions:
            raise HTTPException(status_code=400, detail="Document is not an image")
        
        # Determine media type
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
        }
        media_type = media_type_map.get(ext, 'application/octet-stream')
        
        # Return image file
        with open(doc_path, 'rb') as f:
            image_data = f.read()
        
        return StreamingResponse(
            io.BytesIO(image_data),
            media_type=media_type,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document image: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document image: {str(e)}"
        )
