"""
Gemini Video Processing API
Gemini 3.0 기반 비디오 분석 및 처리 API 엔드포인트
"""

import base64
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.multimodal.video_processor import (
    get_video_processor, 
    VideoAnalysisRequest
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/gemini-video", tags=["Gemini Video Processing"])

# ============================================================================
# Request/Response Models
# ============================================================================

class VideoAnalysisRequestModel(BaseModel):
    """비디오 분석 요청 모델"""
    video_data: Optional[str] = Field(None, description="Base64 encoded video data")
    video_url: Optional[str] = Field(None, description="Video URL (future feature)")
    analysis_type: str = Field(default="comprehensive", description="분석 유형")
    frame_sampling: str = Field(default="auto", description="프레임 샘플링 방법")
    max_frames: int = Field(default=30, ge=1, le=100, description="최대 프레임 수")
    include_audio: bool = Field(default=True, description="오디오 포함 여부")
    model: str = Field(default="gemini-1.5-pro", description="사용할 Gemini 모델")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="창의성 수준")
    max_tokens: int = Field(default=4096, ge=1, le=8192, description="최대 토큰 수")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="메타데이터")

class VideoAnalysisResponse(BaseModel):
    """비디오 분석 응답 모델"""
    success: bool
    analysis_type: str
    analysis_config: Dict[str, Any]
    video_analysis: Optional[Dict[str, Any]] = None
    model_used: str
    processing_time_seconds: float
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class FrameExtractionRequest(BaseModel):
    """프레임 추출 요청 모델"""
    video_data: str = Field(..., description="Base64 encoded video data")
    frame_count: int = Field(default=10, ge=1, le=50, description="추출할 프레임 수")
    sampling_method: str = Field(default="uniform", description="샘플링 방법")

class VideoMetadataResponse(BaseModel):
    """비디오 메타데이터 응답 모델"""
    success: bool
    metadata: Dict[str, Any]
    processing_time_seconds: float
    error: Optional[str] = None

# ============================================================================
# Video Analysis Endpoints
# ============================================================================

@router.post("/analyze", response_model=VideoAnalysisResponse)
async def analyze_video(
    request: VideoAnalysisRequestModel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Gemini 3.0 기반 비디오 분석
    
    다양한 분석 유형을 지원합니다:
    - comprehensive: 종합적인 비디오 분석
    - summary: 간단한 요약
    - transcript: 음성 텍스트 변환
    - objects: 객체 및 인물 분석
    - scenes: 장면 구성 분석
    
    지원 형식: MP4, MOV, AVI, WebM 등
    최대 파일 크기: 100MB
    """
    try:
        # 입력 검증
        if not request.video_data and not request.video_url:
            raise HTTPException(
                status_code=400,
                detail="Either video_data or video_url must be provided"
            )
        
        if request.video_data and request.video_url:
            raise HTTPException(
                status_code=400,
                detail="Provide either video_data or video_url, not both"
            )
        
        # 비디오 프로세서 가져오기
        video_processor = get_video_processor()
        
        # VideoAnalysisRequest 객체 생성
        analysis_request = VideoAnalysisRequest()
        analysis_request.analysis_type = request.analysis_type
        analysis_request.frame_sampling = request.frame_sampling
        analysis_request.max_frames = request.max_frames
        analysis_request.include_audio = request.include_audio
        analysis_request.metadata = request.metadata or {}
        
        # 비디오 데이터 설정
        if request.video_data:
            try:
                analysis_request.set_video_data(request.video_data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid video data: {str(e)}")
        
        if request.video_url:
            analysis_request.set_video_url(request.video_url)
        
        # 비디오 분석 실행
        result = await video_processor.analyze_video(
            request=analysis_request,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 사용 로그 기록
        logger.info(
            f"Video analysis completed",
            extra={
                'user_id': current_user.id,
                'analysis_type': request.analysis_type,
                'model': request.model,
                'processing_time': result.get('processing_time_seconds', 0),
                'success': result.get('success', False)
            }
        )
        
        return VideoAnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-and-analyze")
async def upload_and_analyze_video(
    analysis_type: str = Form(default="comprehensive"),
    frame_sampling: str = Form(default="auto"),
    max_frames: int = Form(default=30),
    include_audio: bool = Form(default=True),
    model: str = Form(default="gemini-1.5-pro"),
    temperature: float = Form(default=0.7),
    video_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    비디오 파일 업로드 및 분석
    
    편의성을 위한 엔드포인트 - 파일 업로드와 분석을 한 번에 처리
    """
    try:
        # 파일 형식 검증
        video_processor = get_video_processor()
        
        if not video_processor.is_supported_format(video_file.content_type or ""):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported video format: {video_file.content_type}"
            )
        
        # 파일 크기 제한 (100MB)
        video_content = await video_file.read()
        if len(video_content) > 100 * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail="Video file too large. Maximum size is 100MB"
            )
        
        # VideoAnalysisRequest 객체 생성
        analysis_request = VideoAnalysisRequest()
        analysis_request.analysis_type = analysis_type
        analysis_request.frame_sampling = frame_sampling
        analysis_request.max_frames = max_frames
        analysis_request.include_audio = include_audio
        analysis_request.metadata = {
            "filename": video_file.filename,
            "content_type": video_file.content_type,
            "size_bytes": len(video_content)
        }
        
        # 비디오 데이터 설정
        analysis_request.set_video_data(video_content)
        
        # 비디오 분석 실행
        result = await video_processor.analyze_video(
            request=analysis_request,
            model=model,
            temperature=temperature
        )
        
        # 파일 정보 추가
        result['file_info'] = {
            'filename': video_file.filename,
            'content_type': video_file.content_type,
            'size_bytes': len(video_content)
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and analyze failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Frame Extraction Endpoints
# ============================================================================

@router.post("/extract-frames")
async def extract_video_frames(
    request: FrameExtractionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    비디오에서 프레임 추출
    
    샘플링 방법:
    - uniform: 균등 간격으로 프레임 추출
    - keyframes: 키프레임만 추출 (향후 구현)
    """
    try:
        video_processor = get_video_processor()
        
        # 비디오 데이터 디코딩
        try:
            video_data = base64.b64decode(request.video_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid video data: {str(e)}")
        
        # 프레임 추출
        frames = await video_processor.extract_frames(
            video_data=video_data,
            frame_count=request.frame_count,
            sampling_method=request.sampling_method
        )
        
        return {
            "success": True,
            "frame_count": len(frames),
            "frames": frames,
            "sampling_method": request.sampling_method
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Frame extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metadata", response_model=VideoMetadataResponse)
async def get_video_metadata(
    video_data: str,
    current_user: User = Depends(get_current_user)
):
    """
    비디오 메타데이터 추출
    
    반환 정보:
    - 파일 크기, 형식, 해상도
    - 재생 시간, FPS
    - 오디오 포함 여부
    - 코덱 정보
    """
    try:
        video_processor = get_video_processor()
        
        # 비디오 데이터 디코딩
        try:
            video_bytes = base64.b64decode(video_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid video data: {str(e)}")
        
        # 메타데이터 추출
        import time
        start_time = time.time()
        
        metadata = await video_processor.get_video_metadata(video_bytes)
        
        processing_time = time.time() - start_time
        
        return VideoMetadataResponse(
            success=True,
            metadata=metadata,
            processing_time_seconds=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata extraction failed: {str(e)}", exc_info=True)
        return VideoMetadataResponse(
            success=False,
            metadata={},
            processing_time_seconds=0,
            error=str(e)
        )

# ============================================================================
# Analysis Types and Configuration
# ============================================================================

@router.get("/analysis-types")
async def get_analysis_types(
    current_user: User = Depends(get_current_user)
):
    """
    사용 가능한 비디오 분석 유형 목록
    """
    analysis_types = [
        {
            "type": "comprehensive",
            "name": "종합 분석",
            "description": "비디오의 모든 측면을 상세히 분석",
            "features": ["전체 요약", "시각적 요소", "오디오 분석", "구조 분석", "품질 평가"],
            "estimated_time": "30-60초",
            "recommended_for": ["상세한 콘텐츠 분석", "품질 검토", "교육 자료"]
        },
        {
            "type": "summary",
            "name": "요약 분석",
            "description": "비디오의 핵심 내용을 간결하게 요약",
            "features": ["주요 내용", "핵심 포인트", "대상 청중", "시청 가치"],
            "estimated_time": "15-30초",
            "recommended_for": ["빠른 검토", "콘텐츠 큐레이션", "미리보기"]
        },
        {
            "type": "transcript",
            "name": "음성 변환",
            "description": "비디오의 음성을 텍스트로 변환",
            "features": ["화자 구분", "시간대별 정리", "키워드 추출", "내용 요약"],
            "estimated_time": "20-40초",
            "recommended_for": ["자막 생성", "회의록 작성", "검색 가능한 텍스트"]
        },
        {
            "type": "objects",
            "name": "객체 분석",
            "description": "비디오에 나타나는 객체와 인물 분석",
            "features": ["객체 목록", "인물 분석", "배경 환경", "브랜드/로고"],
            "estimated_time": "25-45초",
            "recommended_for": ["보안 분석", "마케팅 분석", "인벤토리 관리"]
        },
        {
            "type": "scenes",
            "name": "장면 분석",
            "description": "비디오의 장면 구성과 스토리텔링 분석",
            "features": ["장면 구분", "전환 방식", "시간 구조", "스토리텔링"],
            "estimated_time": "35-55초",
            "recommended_for": ["편집 가이드", "스토리보드", "콘텐츠 구조화"]
        }
    ]
    
    return {
        "analysis_types": analysis_types,
        "default_type": "comprehensive",
        "supported_formats": [
            "video/mp4", "video/mov", "video/avi", "video/webm",
            "video/mpeg", "video/x-flv", "video/mpg", "video/wmv", "video/3gpp"
        ],
        "max_file_size_mb": 100,
        "max_duration_minutes": 30
    }

@router.get("/examples")
async def get_video_analysis_examples(
    current_user: User = Depends(get_current_user)
):
    """
    비디오 분석 사용 예시
    """
    examples = [
        {
            "category": "교육 콘텐츠",
            "icon": "🎓",
            "use_cases": [
                {
                    "name": "온라인 강의 분석",
                    "description": "강의 비디오의 구조와 내용을 자동 분석하여 학습 가이드 생성",
                    "analysis_type": "comprehensive",
                    "expected_output": "강의 구조, 핵심 개념, 실습 부분, 질의응답 정리"
                },
                {
                    "name": "교육 자료 요약",
                    "description": "긴 교육 비디오를 짧은 요약으로 변환",
                    "analysis_type": "summary",
                    "expected_output": "핵심 학습 포인트, 주요 개념, 예상 학습 시간"
                }
            ]
        },
        {
            "category": "비즈니스 & 마케팅",
            "icon": "💼",
            "use_cases": [
                {
                    "name": "제품 데모 분석",
                    "description": "제품 시연 비디오에서 기능과 장점 추출",
                    "analysis_type": "objects",
                    "expected_output": "제품 특징, 사용법, 경쟁 우위, 타겟 고객"
                },
                {
                    "name": "광고 효과 분석",
                    "description": "마케팅 비디오의 메시지와 시각적 요소 분석",
                    "analysis_type": "comprehensive",
                    "expected_output": "브랜드 메시지, 감정적 어필, 시각적 임팩트, 개선 제안"
                }
            ]
        },
        {
            "category": "미디어 & 엔터테인먼트",
            "icon": "🎬",
            "use_cases": [
                {
                    "name": "콘텐츠 큐레이션",
                    "description": "대량의 비디오 콘텐츠를 자동으로 분류하고 태그 생성",
                    "analysis_type": "summary",
                    "expected_output": "장르, 주제, 감정, 적합한 연령대, 추천 태그"
                },
                {
                    "name": "스토리보드 생성",
                    "description": "완성된 비디오에서 장면별 스토리보드 추출",
                    "analysis_type": "scenes",
                    "expected_output": "장면 구분, 주요 액션, 카메라 앵글, 편집 포인트"
                }
            ]
        },
        {
            "category": "보안 & 모니터링",
            "icon": "🔒",
            "use_cases": [
                {
                    "name": "보안 영상 분석",
                    "description": "CCTV 영상에서 이상 행동이나 객체 탐지",
                    "analysis_type": "objects",
                    "expected_output": "인물 수, 행동 패턴, 이상 징후, 시간대별 활동"
                },
                {
                    "name": "품질 관리",
                    "description": "제조 공정 비디오에서 품질 이슈 탐지",
                    "analysis_type": "comprehensive",
                    "expected_output": "공정 단계, 품질 지표, 이상 상황, 개선 포인트"
                }
            ]
        }
    ]
    
    return {
        "examples": examples,
        "total_categories": len(examples),
        "total_use_cases": sum(len(cat["use_cases"]) for cat in examples)
    }

@router.get("/health")
async def health_check():
    """
    비디오 처리 서비스 상태 확인
    """
    try:
        video_processor = get_video_processor()
        health_status = await video_processor.health_check()
        
        return health_status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "gemini_video_processor"
        }