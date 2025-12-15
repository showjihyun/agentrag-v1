"""
Gemini MultiModal API Endpoints
Gemini 3.0 기반 멀티모달 처리를 위한 REST API
"""

import base64
import io
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.multimodal.gemini_service import get_gemini_service
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/gemini", tags=["Gemini MultiModal"])

# ============================================================================
# Request/Response Models
# ============================================================================

class ImageAnalysisRequest(BaseModel):
    """이미지 분석 요청 모델"""
    image_data: str = Field(..., description="Base64 encoded image data")
    prompt: str = Field(..., description="Analysis prompt")
    model: str = Field(default="gemini-1.5-flash", description="Gemini model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for generation")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Maximum tokens to generate")

class DocumentAnalysisRequest(BaseModel):
    """문서 분석 요청 모델"""
    image_data: str = Field(..., description="Base64 encoded document image")
    analysis_type: str = Field(default="general", description="Type of document analysis")

class AudioAnalysisRequest(BaseModel):
    """음성 분석 요청 모델"""
    audio_data: str = Field(..., description="Base64 encoded audio data")
    context: str = Field(..., description="Context for audio analysis")
    model: str = Field(default="gemini-1.5-flash", description="Gemini model to use")

class MultiModalResponse(BaseModel):
    """멀티모달 분석 응답 모델"""
    success: bool
    result: Optional[str] = None
    structured_data: Optional[dict] = None
    model_used: str
    processing_time_seconds: float
    usage: Optional[dict] = None
    error: Optional[str] = None
    timestamp: str

# ============================================================================
# Image Analysis Endpoints
# ============================================================================

@router.post("/analyze-image", response_model=MultiModalResponse)
async def analyze_image(
    request: ImageAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    이미지와 텍스트 프롬프트를 함께 분석
    
    주요 사용 사례:
    - 영수증/송장 데이터 추출
    - 제품 이미지 설명 생성
    - 차트/그래프 데이터 분석
    - 손글씨 텍스트 인식
    """
    try:
        gemini_service = get_gemini_service()
        
        result = await gemini_service.analyze_image_with_text(
            image_data=request.image_data,
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 사용 로그 기록 (선택적)
        logger.info(
            f"Image analysis completed for user {current_user.id}",
            extra={
                'user_id': current_user.id,
                'model': request.model,
                'processing_time': result.get('processing_time_seconds', 0),
                'success': result.get('success', False)
            }
        )
        
        return MultiModalResponse(**result)
        
    except Exception as e:
        logger.error(f"Image analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-document")
async def analyze_document(
    request: DocumentAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    문서 구조 분석 및 데이터 추출
    
    지원하는 문서 유형:
    - receipt: 영수증
    - invoice: 송장/인보이스  
    - contract: 계약서
    - form: 양식
    - general: 일반 문서
    """
    try:
        gemini_service = get_gemini_service()
        
        result = await gemini_service.analyze_document_structure(
            image_data=request.image_data,
            analysis_type=request.analysis_type
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Document analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-and-analyze")
async def upload_and_analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    model: str = Form(default="gemini-1.5-flash"),
    temperature: float = Form(default=0.7),
    current_user: User = Depends(get_current_user)
):
    """
    이미지 파일 업로드 후 즉시 분석
    
    편의성을 위한 엔드포인트 - 파일 업로드와 분석을 한 번에 처리
    """
    try:
        # 파일 유효성 검사
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # 파일 크기 제한 (10MB)
        max_size = 10 * 1024 * 1024
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Base64 인코딩
        image_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # Gemini 분석
        gemini_service = get_gemini_service()
        result = await gemini_service.analyze_image_with_text(
            image_data=image_base64,
            prompt=prompt,
            model=model,
            temperature=temperature
        )
        
        # 파일 정보 추가
        result['file_info'] = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size_bytes': len(file_content)
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and analyze failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Audio Analysis Endpoints  
# ============================================================================

@router.post("/analyze-audio")
async def analyze_audio(
    request: AudioAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    음성 데이터 분석
    
    주요 사용 사례:
    - 회의 녹음 요약
    - 고객 통화 감정 분석
    - 음성 명령 처리
    """
    try:
        # Base64 디코딩
        audio_bytes = base64.b64decode(request.audio_data)
        
        gemini_service = get_gemini_service()
        result = await gemini_service.process_audio_with_context(
            audio_data=audio_bytes,
            context=request.context,
            model=request.model
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Audio analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-and-analyze-audio")
async def upload_and_analyze_audio(
    file: UploadFile = File(...),
    context: str = Form(...),
    model: str = Form(default="gemini-1.5-flash"),
    current_user: User = Depends(get_current_user)
):
    """
    음성 파일 업로드 후 즉시 분석
    """
    try:
        # 파일 유효성 검사
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file")
        
        # 파일 크기 제한 (25MB)
        max_size = 25 * 1024 * 1024
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(status_code=400, detail="File too large (max 25MB)")
        
        gemini_service = get_gemini_service()
        result = await gemini_service.process_audio_with_context(
            audio_data=file_content,
            context=context,
            model=model
        )
        
        result['file_info'] = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size_bytes': len(file_content)
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and analyze audio failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Utility Endpoints
# ============================================================================

@router.get("/models")
async def get_available_models(
    current_user: User = Depends(get_current_user)
):
    """
    사용 가능한 Gemini 모델 목록 조회
    """
    try:
        gemini_service = get_gemini_service()
        
        models = []
        for model_name, config in gemini_service.model_configs.items():
            models.append({
                'name': model_name,
                'capabilities': config['capabilities'],
                'max_tokens': config['max_tokens'],
                'cost_tier': config.get('cost_tier', 'standard'),
                'optimized_for': 'speed' if config.get('speed_optimized') else 'quality'
            })
        
        return {
            'models': models,
            'default_model': 'gemini-1.5-flash',
            'recommended': {
                'image_analysis': 'gemini-1.5-flash',
                'document_processing': 'gemini-1.5-flash',
                'audio_processing': 'gemini-1.5-flash',
                'complex_reasoning': 'gemini-1.5-pro'
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Gemini 서비스 상태 확인
    """
    try:
        gemini_service = get_gemini_service()
        health_status = await gemini_service.health_check()
        
        if health_status['status'] == 'healthy':
            return health_status
        else:
            return JSONResponse(
                status_code=503,
                content=health_status
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'service': 'gemini_multimodal'
            }
        )

# ============================================================================
# Workflow Integration Endpoints
# ============================================================================

@router.post("/workflow/vision-block")
async def execute_vision_block(
    image_data: str,
    prompt: str,
    block_config: dict = {},
    current_user: User = Depends(get_current_user)
):
    """
    워크플로우에서 사용할 Vision 블록 실행
    
    워크플로우 빌더에서 직접 호출되는 엔드포인트
    """
    try:
        model = block_config.get('model', 'gemini-1.5-flash')
        temperature = block_config.get('temperature', 0.7)
        max_tokens = block_config.get('max_tokens', 2048)
        
        gemini_service = get_gemini_service()
        result = await gemini_service.analyze_image_with_text(
            image_data=image_data,
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 워크플로우 실행 형식으로 응답
        return {
            'block_type': 'gemini_vision',
            'execution_id': f"gemini_{current_user.id}_{int(result.get('timestamp', '0').replace('-', '').replace(':', '').replace('.', '')[:14])}",
            'success': result['success'],
            'output': {
                'text': result.get('result', ''),
                'structured_data': result.get('structured_data'),
                'confidence': 0.9 if result['success'] else 0.0
            },
            'metadata': {
                'model': result.get('model_used'),
                'processing_time': result.get('processing_time_seconds'),
                'tokens_used': result.get('usage', {}).get('total_tokens', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Vision block execution failed: {str(e)}")
        return {
            'block_type': 'gemini_vision',
            'success': False,
            'error': str(e),
            'output': {'text': '', 'confidence': 0.0}
        }