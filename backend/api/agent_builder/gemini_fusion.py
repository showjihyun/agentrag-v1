"""
Gemini Advanced MultiModal Fusion API
고급 멀티모달 융합 처리 API
"""

import base64
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.multimodal.fusion_processor import (
    get_fusion_processor, 
    MultiModalInput, 
    FusionStrategy
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/gemini-fusion", tags=["Gemini Advanced Fusion"])

# ============================================================================
# Request/Response Models
# ============================================================================

class TextInput(BaseModel):
    """텍스트 입력 모델"""
    content: str = Field(..., description="텍스트 내용")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="메타데이터")

class ImageInput(BaseModel):
    """이미지 입력 모델"""
    data: str = Field(..., description="Base64 encoded image data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="메타데이터")

class AudioInput(BaseModel):
    """음성 입력 모델"""
    data: str = Field(..., description="Base64 encoded audio data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="메타데이터")

class MultiModalFusionRequest(BaseModel):
    """멀티모달 융합 요청 모델"""
    fusion_prompt: str = Field(..., description="융합 분석 프롬프트")
    text_inputs: List[TextInput] = Field(default_factory=list, description="텍스트 입력 목록")
    image_inputs: List[ImageInput] = Field(default_factory=list, description="이미지 입력 목록")
    audio_inputs: List[AudioInput] = Field(default_factory=list, description="음성 입력 목록")
    fusion_strategy: str = Field(default=FusionStrategy.UNIFIED, description="융합 전략")
    model: str = Field(default="gemini-1.5-pro", description="사용할 Gemini 모델")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="창의성 수준")
    max_tokens: int = Field(default=4096, ge=1, le=8192, description="최대 토큰 수")

class FusionResponse(BaseModel):
    """융합 분석 응답 모델"""
    success: bool
    fusion_strategy: str
    input_modalities: Dict[str, int]
    fusion_result: Dict[str, Any]
    model_used: str
    processing_time_seconds: float
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# ============================================================================
# Advanced Fusion Endpoints
# ============================================================================

@router.post("/process", response_model=FusionResponse)
async def process_multimodal_fusion(
    request: MultiModalFusionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    고급 멀티모달 융합 처리
    
    여러 종류의 미디어(텍스트, 이미지, 음성)를 동시에 분석하고
    선택한 융합 전략에 따라 통합적인 인사이트를 생성합니다.
    
    융합 전략:
    - unified: 모든 모달리티를 한번에 처리 (가장 정확)
    - parallel: 각 모달리티를 병렬 처리 후 융합 (가장 빠름)
    - sequential: 순차 처리하며 컨텍스트 누적 (가장 상세)
    - hierarchical: 계층적 융합 (가장 체계적)
    """
    try:
        # 입력 검증
        total_inputs = len(request.text_inputs) + len(request.image_inputs) + len(request.audio_inputs)
        if total_inputs < 2:
            raise HTTPException(
                status_code=400, 
                detail="At least 2 inputs are required for multimodal fusion"
            )
        
        modality_count = sum(1 for inputs in [
            request.text_inputs, request.image_inputs, request.audio_inputs
        ] if len(inputs) > 0)
        
        if modality_count < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 different modalities are required for fusion"
            )
        
        # MultiModalInput 객체 생성
        multimodal_input = MultiModalInput()
        
        # 텍스트 입력 추가
        for text_input in request.text_inputs:
            multimodal_input.add_text(text_input.content, text_input.metadata)
        
        # 이미지 입력 추가
        for image_input in request.image_inputs:
            multimodal_input.add_image(image_input.data, image_input.metadata)
        
        # 음성 입력 추가
        for audio_input in request.audio_inputs:
            try:
                audio_bytes = base64.b64decode(audio_input.data)
                multimodal_input.add_audio(audio_bytes, audio_input.metadata)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid audio data: {str(e)}")
        
        # 융합 프로세서 가져오기
        fusion_processor = get_fusion_processor()
        
        # 융합 처리 실행
        result = await fusion_processor.process_multimodal_fusion(
            inputs=multimodal_input,
            fusion_prompt=request.fusion_prompt,
            strategy=request.fusion_strategy,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 사용 로그 기록
        logger.info(
            f"Multimodal fusion completed",
            extra={
                'user_id': current_user.id,
                'fusion_strategy': request.fusion_strategy,
                'input_modalities': multimodal_input.get_modality_count(),
                'processing_time': result.get('processing_time_seconds', 0),
                'success': result.get('success', False)
            }
        )
        
        return FusionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multimodal fusion failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-and-fuse")
async def upload_and_fuse_multimodal(
    fusion_prompt: str = Form(...),
    fusion_strategy: str = Form(default=FusionStrategy.UNIFIED),
    model: str = Form(default="gemini-1.5-pro"),
    temperature: float = Form(default=0.7),
    text_content: Optional[str] = Form(None),
    image_files: List[UploadFile] = File(default=[]),
    audio_files: List[UploadFile] = File(default=[]),
    current_user: User = Depends(get_current_user)
):
    """
    파일 업로드를 통한 멀티모달 융합 처리
    
    편의성을 위한 엔드포인트 - 파일 업로드와 융합 분석을 한 번에 처리
    """
    try:
        # 입력 검증
        total_inputs = (1 if text_content else 0) + len(image_files) + len(audio_files)
        if total_inputs < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 inputs are required for multimodal fusion"
            )
        
        # MultiModalInput 객체 생성
        multimodal_input = MultiModalInput()
        
        # 텍스트 추가
        if text_content:
            multimodal_input.add_text(text_content)
        
        # 이미지 파일 처리
        for i, image_file in enumerate(image_files):
            if not image_file.content_type or not image_file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail=f"Invalid image file: {image_file.filename}")
            
            # 파일 크기 제한 (10MB)
            image_content = await image_file.read()
            if len(image_content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"Image file too large: {image_file.filename}")
            
            multimodal_input.add_image(
                image_content, 
                {"filename": image_file.filename, "content_type": image_file.content_type}
            )
        
        # 음성 파일 처리
        for i, audio_file in enumerate(audio_files):
            if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
                raise HTTPException(status_code=400, detail=f"Invalid audio file: {audio_file.filename}")
            
            # 파일 크기 제한 (25MB)
            audio_content = await audio_file.read()
            if len(audio_content) > 25 * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"Audio file too large: {audio_file.filename}")
            
            multimodal_input.add_audio(
                audio_content,
                {"filename": audio_file.filename, "content_type": audio_file.content_type}
            )
        
        # 융합 프로세서 실행
        fusion_processor = get_fusion_processor()
        result = await fusion_processor.process_multimodal_fusion(
            inputs=multimodal_input,
            fusion_prompt=fusion_prompt,
            strategy=fusion_strategy,
            model=model,
            temperature=temperature
        )
        
        # 파일 정보 추가
        result['file_info'] = {
            'text_provided': bool(text_content),
            'image_files': [f.filename for f in image_files],
            'audio_files': [f.filename for f in audio_files],
            'total_files': len(image_files) + len(audio_files)
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and fuse failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Fusion Strategy Endpoints
# ============================================================================

@router.get("/strategies")
async def get_fusion_strategies(
    current_user: User = Depends(get_current_user)
):
    """
    사용 가능한 융합 전략 목록 조회
    """
    strategies = [
        {
            "name": FusionStrategy.UNIFIED,
            "display_name": "통합 처리",
            "description": "모든 모달리티를 Gemini 3.0으로 한번에 처리",
            "pros": ["가장 정확한 융합", "컨텍스트 보존", "네이티브 멀티모달"],
            "cons": ["상대적으로 느림", "높은 토큰 사용량"],
            "best_for": ["복잡한 분석", "정확성이 중요한 경우"],
            "estimated_time": "5-10초"
        },
        {
            "name": FusionStrategy.PARALLEL,
            "display_name": "병렬 처리",
            "description": "각 모달리티를 병렬로 처리한 후 결과를 융합",
            "pros": ["가장 빠름", "확장성 좋음", "부분 실패 허용"],
            "cons": ["융합 품질 제한", "컨텍스트 손실 가능"],
            "best_for": ["빠른 처리", "대량 데이터", "실시간 응용"],
            "estimated_time": "2-5초"
        },
        {
            "name": FusionStrategy.SEQUENTIAL,
            "display_name": "순차 처리",
            "description": "각 모달리티를 순차적으로 처리하며 컨텍스트 누적",
            "pros": ["상세한 분석", "컨텍스트 누적", "단계별 추적"],
            "cons": ["가장 느림", "높은 비용", "순서 의존성"],
            "best_for": ["상세 분석", "스토리텔링", "단계별 이해"],
            "estimated_time": "8-15초"
        },
        {
            "name": FusionStrategy.HIERARCHICAL,
            "display_name": "계층적 처리",
            "description": "같은 모달리티끼리 먼저 융합 후 모달리티간 융합",
            "pros": ["체계적 융합", "확장성", "모듈화"],
            "cons": ["복잡성", "중간 정도 속도", "구현 복잡"],
            "best_for": ["대규모 데이터", "체계적 분석", "모듈화된 처리"],
            "estimated_time": "6-12초"
        }
    ]
    
    return {
        "strategies": strategies,
        "default_strategy": FusionStrategy.UNIFIED,
        "recommendations": {
            "speed_priority": FusionStrategy.PARALLEL,
            "accuracy_priority": FusionStrategy.UNIFIED,
            "detail_priority": FusionStrategy.SEQUENTIAL,
            "scale_priority": FusionStrategy.HIERARCHICAL
        }
    }

@router.get("/examples")
async def get_fusion_examples(
    current_user: User = Depends(get_current_user)
):
    """
    멀티모달 융합 사용 예시
    """
    examples = [
        {
            "name": "제품 리뷰 종합 분석",
            "description": "제품 이미지 + 리뷰 텍스트 + 언박싱 영상을 종합 분석",
            "inputs": {
                "image": "제품 사진",
                "text": "고객 리뷰 텍스트",
                "audio": "언박싱 영상 음성"
            },
            "fusion_prompt": "이 제품에 대한 종합적인 평가와 개선점을 제시해주세요",
            "expected_output": "제품의 시각적 특징, 고객 만족도, 실제 사용 경험을 종합한 분석",
            "recommended_strategy": FusionStrategy.UNIFIED
        },
        {
            "name": "회의 내용 완전 분석",
            "description": "회의 슬라이드 + 회의록 + 녹음 파일을 통합 분석",
            "inputs": {
                "image": "프레젠테이션 슬라이드",
                "text": "회의록 텍스트",
                "audio": "회의 녹음"
            },
            "fusion_prompt": "회의의 핵심 내용과 결정사항, 액션 아이템을 정리해주세요",
            "expected_output": "시각 자료, 문서, 음성을 종합한 완전한 회의 요약",
            "recommended_strategy": FusionStrategy.SEQUENTIAL
        },
        {
            "name": "교육 콘텐츠 분석",
            "description": "교재 이미지 + 설명 텍스트 + 강의 음성을 분석",
            "inputs": {
                "image": "교재 페이지",
                "text": "교육 자료 텍스트",
                "audio": "강의 음성"
            },
            "fusion_prompt": "학습자를 위한 핵심 요약과 이해도 점검 문제를 만들어주세요",
            "expected_output": "시각, 텍스트, 음성 자료를 통합한 학습 가이드",
            "recommended_strategy": FusionStrategy.HIERARCHICAL
        },
        {
            "name": "뉴스 종합 분석",
            "description": "뉴스 이미지 + 기사 텍스트 + 인터뷰 음성을 종합",
            "inputs": {
                "image": "뉴스 사진",
                "text": "기사 본문",
                "audio": "인터뷰 음성"
            },
            "fusion_prompt": "이 뉴스의 핵심 내용과 다각적 관점을 정리해주세요",
            "expected_output": "시각적 정보, 기사 내용, 인터뷰를 종합한 뉴스 분석",
            "recommended_strategy": FusionStrategy.PARALLEL
        }
    ]
    
    return {
        "examples": examples,
        "total": len(examples),
        "categories": ["business", "education", "media", "research"]
    }

@router.get("/health")
async def health_check():
    """
    멀티모달 융합 서비스 상태 확인
    """
    try:
        fusion_processor = get_fusion_processor()
        
        return {
            "status": "healthy",
            "service": "gemini_multimodal_fusion",
            "available_strategies": [
                FusionStrategy.UNIFIED,
                FusionStrategy.PARALLEL,
                FusionStrategy.SEQUENTIAL,
                FusionStrategy.HIERARCHICAL
            ],
            "supported_modalities": ["text", "image", "audio"],
            "max_inputs": {
                "text": 10,
                "image": 5,
                "audio": 3
            },
            "timestamp": "2024-12-12T10:00:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "gemini_multimodal_fusion"
        }