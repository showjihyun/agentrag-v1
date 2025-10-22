"""
PaddleOCR Advanced API Endpoints

Provides REST API for:
- PP-ChatOCRv4: Document Q&A
- PaddleOCR-VL: Multimodal document parsing (future)
- PP-DocTranslation: Document translation (future)
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from PIL import Image
import io

from backend.services.paddleocr_processor import get_paddleocr_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/paddleocr-advanced", tags=["PaddleOCR Advanced"])


@router.post("/chat-with-document")
async def chat_with_document(
    file: UploadFile = File(...),
    question: str = Form(...),
    context: Optional[str] = Form(None),
    use_llm: bool = Form(True)
):
    """
    PP-ChatOCRv4: 문서 기반 Q&A
    
    문서 이미지를 업로드하고 질문하면 문서 내용을 기반으로 답변합니다.
    
    Args:
        file: 문서 이미지 파일 (PNG, JPG, PDF 등)
        question: 질문 (예: "이 문서의 핵심 내용은?")
        context: 추가 컨텍스트 (선택사항)
        use_llm: LLM 사용 여부 (True: 고급 답변, False: 단순 검색)
        
    Returns:
        JSON with answer, confidence, and sources
        
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/paddleocr-advanced/chat-with-document" \
          -F "file=@document.png" \
          -F "question=이 문서의 주요 내용은 무엇인가요?" \
          -F "use_llm=true"
        ```
    """
    try:
        # 파일 검증
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only images are supported."
            )
        
        # 파일 읽기
        contents = await file.read()
        
        # 이미지 로드
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load image: {str(e)}"
            )
        
        # PP-ChatOCR 처리
        processor = get_paddleocr_processor(
            enable_chatocr=True,
            enable_table_recognition=True
        )
        
        result = processor.chat_with_document(
            image=image,
            question=question,
            context=context,
            use_llm=use_llm
        )
        
        # 에러 체크
        if 'error' in result and result.get('confidence', 0) == 0.0:
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "question": result['question'],
                "answer": result['answer'],
                "confidence": result['confidence'],
                "sources": result.get('sources', []),
                "tables_found": result.get('tables_found', 0),
                "chatocr_version": result.get('chatocr_version', 'PP-ChatOCRv4')
            },
            "metadata": {
                "document_length": len(result.get('document_text', '')),
                "use_llm": use_llm
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parse-multimodal")
async def parse_multimodal_document(
    file: UploadFile = File(...),
    parse_mode: str = Form("full"),
    enable_visual_features: bool = Form(True)
):
    """
    PaddleOCR-VL: 멀티모달 문서 파싱
    
    텍스트와 이미지를 함께 이해하는 Vision-Language 파싱
    
    Args:
        file: 이미지 파일 (PNG, JPG, etc.)
        parse_mode: 파싱 모드
            - 'full': 전체 파싱 (텍스트 + 구조)
            - 'text_only': 텍스트만 추출
            - 'structure_only': 구조만 분석 (표, 레이아웃)
        enable_visual_features: 시각적 특징 추출 활성화
        
    Returns:
        JSON with multimodal parsing results including:
        - text: 추출된 텍스트
        - tables: 표 구조 및 내용
        - figures: 그림 영역
        - layout: 레이아웃 구조
        - visual_features: 시각적 특징 (색상, 밝기 등)
        - multimodal_features: 문서 타입, 밀도, 복잡도
        
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/paddleocr-advanced/parse-multimodal" \
          -F "file=@document.png" \
          -F "parse_mode=full" \
          -F "enable_visual_features=true"
        ```
    """
    try:
        # 파일 검증
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only images are supported."
            )
        
        # 파일 읽기
        contents = await file.read()
        
        # 이미지 로드
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load image: {str(e)}"
            )
        
        # 파싱 모드 검증
        valid_modes = ['full', 'text_only', 'structure_only']
        if parse_mode not in valid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parse_mode: {parse_mode}. Must be one of: {', '.join(valid_modes)}"
            )
        
        # PaddleOCR-VL 처리
        processor = get_paddleocr_processor(
            enable_paddleocr_vl=True,
            enable_table_recognition=True,
            enable_layout_analysis=True
        )
        
        result = processor.parse_document_vl(
            image=image,
            parse_mode=parse_mode,
            enable_visual_features=enable_visual_features
        )
        
        # 에러 체크
        if 'error' in result:
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "parse_mode": result['parse_mode'],
                "text": result.get('text', ''),
                "text_boxes": result.get('text_boxes', []),
                "tables": result.get('tables', []),
                "figures": result.get('figures', []),
                "layout": result.get('layout', []),
                "visual_features": result.get('visual_features', {}),
                "multimodal_features": result.get('multimodal_features', {})
            },
            "metadata": {
                "text_length": len(result.get('text', '')),
                "num_text_boxes": len(result.get('text_boxes', [])),
                "num_tables": len(result.get('tables', [])),
                "num_figures": len(result.get('figures', [])),
                "num_layout_regions": len(result.get('layout', [])),
                "document_type": result.get('multimodal_features', {}).get('document_type', 'unknown')
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multimodal parsing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate-document")
async def translate_document(
    file: UploadFile = File(...),
    target_lang: str = Form("en"),
    preserve_layout: bool = Form(True),
    translation_service: str = Form("auto")
):
    """
    PP-DocTranslation: 문서 번역
    
    문서의 레이아웃을 유지하면서 번역합니다.
    
    Args:
        file: 문서 이미지 파일 (PNG, JPG, etc.)
        target_lang: 목표 언어
            - 'en': English
            - 'ko': Korean
            - 'ja': Japanese
            - 'zh': Chinese
            - 'es': Spanish
            - 'fr': French
            - 'de': German
            - etc.
        preserve_layout: 레이아웃 보존 여부
        translation_service: 번역 서비스
            - 'auto': 최고 품질 자동 선택 (DeepL > Papago > Google > Simple)
            - 'google': Google Translate (무료)
            - 'deepl': DeepL (고품질, API 키 필요)
            - 'papago': Naver Papago (한글 특화, API 키 필요)
            - 'simple': 단순 폴백 (번역 안됨)
        
    Returns:
        JSON with translated text and layout information
        
    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/paddleocr-advanced/translate-document" \
          -F "file=@document.png" \
          -F "target_lang=en" \
          -F "preserve_layout=true" \
          -F "translation_service=auto"
        ```
    """
    try:
        # 파일 검증
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only images are supported."
            )
        
        # 파일 읽기
        contents = await file.read()
        
        # 이미지 로드
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to load image: {str(e)}"
            )
        
        # 번역 서비스 검증
        valid_services = ['auto', 'google', 'deepl', 'papago', 'simple']
        if translation_service not in valid_services:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid translation_service: {translation_service}. "
                       f"Must be one of: {', '.join(valid_services)}"
            )
        
        # PP-DocTranslation 처리
        processor = get_paddleocr_processor(
            enable_doc_translation=True,
            enable_layout_analysis=preserve_layout
        )
        
        result = processor.translate_document(
            image=image,
            target_lang=target_lang,
            preserve_layout=preserve_layout,
            translation_service=translation_service
        )
        
        # 에러 체크
        if 'error' in result:
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "target_lang": result['target_lang'],
                "preserve_layout": result['preserve_layout'],
                "translated_text": result.get('translated_text', ''),
                "original_text": result.get('original_text', ''),
                "translated_boxes": result.get('translated_boxes', []),
                "layout": result.get('layout', []),
                "translation_engine": result.get('translation_engine', 'unknown'),
                "translator_used": result.get('translator_used', 'unknown')
            },
            "metadata": {
                "num_boxes": result.get('num_boxes', 0),
                "failed_translations": result.get('failed_translations', 0),
                "num_layout_regions": len(result.get('layout', [])),
                "has_warning": 'warning' in result
            },
            "warning": result.get('warning')
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document translation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    헬스 체크 및 사용 가능한 기능 확인
    
    Returns:
        시스템 상태 및 사용 가능한 기능 목록
        
    Example:
        ```bash
        curl "http://localhost:8000/api/paddleocr-advanced/health"
        ```
    """
    try:
        processor = get_paddleocr_processor()
        stats = processor.get_stats()
        
        return JSONResponse(content={
            "success": True,
            "status": "healthy",
            "features": {
                "pp_chatocr": {
                    "available": stats.get('chatocr_available', False),
                    "version": stats.get('chatocr_version', 'PP-ChatOCRv4'),
                    "status": "✅ Implemented (Phase 1)" if stats.get('chatocr_available') else "❌ Not Available"
                },
                "paddleocr_vl": {
                    "available": stats.get('paddleocr_vl_available', False),
                    "version": "PP-OCRv4",
                    "status": "✅ Implemented (Phase 2)" if stats.get('paddleocr_vl_available') else "❌ Not Available"
                },
                "pp_doc_translation": {
                    "available": stats.get('doc_translator_available', False),
                    "version": "PP-DocTranslation",
                    "status": "✅ Implemented (Phase 3)" if stats.get('doc_translator_available') else "❌ Not Available"
                },
                "pp_structure": {
                    "available": stats.get('table_engine_available', False),
                    "version": stats.get('structure_version', 'PP-StructureV3'),
                    "status": "✅ Implemented"
                },
                "layout_analysis": {
                    "available": stats.get('layout_engine_available', False),
                    "status": "✅ Implemented"
                }
            },
            "stats": stats,
            "endpoints": {
                "chat_with_document": "/api/paddleocr-advanced/chat-with-document (POST) ✅",
                "parse_multimodal": "/api/paddleocr-advanced/parse-multimodal (POST) ✅",
                "translate_document": "/api/paddleocr-advanced/translate-document (POST) ✅",
                "health": "/api/paddleocr-advanced/health (GET) ✅"
            }
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "status": "unhealthy",
                "error": str(e)
            }
        )


@router.get("/")
async def root():
    """
    API 루트 - 사용 가능한 엔드포인트 안내
    """
    return JSONResponse(content={
        "name": "PaddleOCR Advanced API",
        "version": "1.0.0",
        "description": "Advanced document understanding with PaddleOCR",
        "features": {
            "implemented": [
                "PP-ChatOCRv4: Document Q&A (Phase 1)",
                "PaddleOCR-VL: Multimodal Parsing (Phase 2)",
                "PP-DocTranslation: Document Translation (Phase 3)",
                "PP-OCRv5: Text Recognition (98%+)",
                "PP-StructureV3: Table Recognition (98%+)"
            ]
        },
        "endpoints": {
            "chat": "POST /api/paddleocr-advanced/chat-with-document",
            "parse": "POST /api/paddleocr-advanced/parse-multimodal",
            "translate": "POST /api/paddleocr-advanced/translate-document",
            "health": "GET /api/paddleocr-advanced/health"
        },
        "documentation": "http://localhost:8000/docs"
    })
