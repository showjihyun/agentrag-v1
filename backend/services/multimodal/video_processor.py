"""
Gemini Video Processing Service
Gemini 3.0을 활용한 고급 비디오 분석 및 처리
"""

import asyncio
import base64
import json
import tempfile
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from backend.services.multimodal.gemini_service import get_gemini_service
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class VideoAnalysisRequest:
    """비디오 분석 요청 클래스"""
    
    def __init__(self):
        self.video_data: Optional[bytes] = None
        self.video_url: Optional[str] = None
        self.analysis_type: str = "comprehensive"  # comprehensive, summary, transcript, objects, scenes
        self.frame_sampling: str = "auto"  # auto, uniform, keyframes, custom
        self.max_frames: int = 30
        self.include_audio: bool = True
        self.metadata: Dict[str, Any] = {}
    
    def set_video_data(self, video_data: Union[str, bytes]):
        """비디오 데이터 설정"""
        if isinstance(video_data, str):
            # base64 디코딩
            if video_data.startswith('data:video'):
                video_data = video_data.split(',')[1]
            self.video_data = base64.b64decode(video_data)
        else:
            self.video_data = video_data
    
    def set_video_url(self, url: str):
        """비디오 URL 설정"""
        self.video_url = url
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """분석 설정 반환"""
        return {
            "analysis_type": self.analysis_type,
            "frame_sampling": self.frame_sampling,
            "max_frames": self.max_frames,
            "include_audio": self.include_audio,
            "metadata": self.metadata
        }

class GeminiVideoProcessor:
    """Gemini 3.0 기반 비디오 처리기"""
    
    def __init__(self):
        self.gemini_service = None
        if GEMINI_AVAILABLE:
            try:
                self.gemini_service = get_gemini_service()
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini service: {e}")
        
        # 지원되는 비디오 형식
        self.supported_formats = [
            'video/mp4', 'video/mpeg', 'video/mov', 'video/avi', 
            'video/x-flv', 'video/mpg', 'video/webm', 'video/wmv', 'video/3gpp'
        ]
        
        # 분석 유형별 프롬프트 템플릿
        self.analysis_prompts = {
            "comprehensive": """
이 비디오를 종합적으로 분석해주세요:

1. **전체 요약**: 비디오의 주요 내용과 목적
2. **시각적 요소**: 주요 객체, 인물, 장면, 액션
3. **오디오 분석**: 음성, 음악, 효과음 (있는 경우)
4. **구조 분석**: 장면 전환, 시간 흐름, 구성
5. **핵심 메시지**: 전달하고자 하는 주요 메시지
6. **품질 평가**: 화질, 음질, 편집 품질
7. **개선 제안**: 더 나은 비디오를 위한 제안사항

상세하고 구조화된 분석을 제공해주세요.
            """,
            
            "summary": """
이 비디오의 핵심 내용을 간결하게 요약해주세요:
- 주요 내용 (3-5문장)
- 핵심 포인트 (3-5개 항목)
- 대상 청중
- 예상 시청 시간과 가치
            """,
            
            "transcript": """
이 비디오의 음성 내용을 텍스트로 변환하고 정리해주세요:
- 화자별 대화 구분
- 시간대별 내용 정리
- 주요 키워드 추출
- 내용 요약
            """,
            
            "objects": """
이 비디오에서 보이는 객체들을 분석해주세요:
- 주요 객체 목록
- 인물 분석 (수, 특징, 행동)
- 배경 및 환경
- 브랜드/로고/텍스트
- 특별한 시각적 요소
            """,
            
            "scenes": """
이 비디오의 장면 구성을 분석해주세요:
- 장면별 구분 및 설명
- 장면 전환 방식
- 각 장면의 주요 내용
- 시간 흐름 및 구조
- 스토리텔링 기법
            """
        }
    
    async def analyze_video(
        self,
        request: VideoAnalysisRequest,
        model: str = "gemini-1.5-pro",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        비디오 분석 메인 함수
        
        Args:
            request: 비디오 분석 요청
            model: 사용할 Gemini 모델
            temperature: 창의성 수준
            max_tokens: 최대 토큰 수
            
        Returns:
            비디오 분석 결과
        """
        start_time = datetime.now()
        
        try:
            if not self.gemini_service:
                raise RuntimeError("Gemini service not available")
            
            # 분석 프롬프트 선택
            analysis_prompt = self.analysis_prompts.get(
                request.analysis_type, 
                self.analysis_prompts["comprehensive"]
            )
            
            logger.info(f"Starting video analysis: {request.analysis_type}")
            
            # 비디오 데이터 처리
            if request.video_data:
                result = await self._analyze_video_data(
                    request.video_data, analysis_prompt, model, temperature, max_tokens
                )
            elif request.video_url:
                result = await self._analyze_video_url(
                    request.video_url, analysis_prompt, model, temperature, max_tokens
                )
            else:
                raise ValueError("Either video_data or video_url must be provided")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 결과 포맷팅
            video_result = {
                "success": True,
                "analysis_type": request.analysis_type,
                "analysis_config": request.get_analysis_config(),
                "video_analysis": result,
                "model_used": model,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat(),
                "metadata": request.metadata
            }
            
            logger.info(f"Video analysis completed in {processing_time:.2f}s")
            return video_result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Video analysis failed: {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "analysis_type": request.analysis_type,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_video_data(
        self,
        video_data: bytes,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """비디오 데이터 직접 분석"""
        
        # 임시 파일로 비디오 저장
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_file.write(video_data)
            temp_file_path = temp_file.name
        
        try:
            # Gemini에 비디오 파일 업로드
            video_file = genai.upload_file(temp_file_path)
            
            # 업로드 완료 대기
            while video_file.state.name == "PROCESSING":
                await asyncio.sleep(1)
                video_file = genai.get_file(video_file.name)
            
            if video_file.state.name == "FAILED":
                raise RuntimeError("Video upload failed")
            
            # Gemini 모델 초기화
            model_instance = genai.GenerativeModel(
                model_name=model,
                safety_settings=self.gemini_service.safety_settings
            )
            
            # 생성 설정
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.8,
                top_k=40
            )
            
            # 비디오 분석 실행
            response = await model_instance.generate_content_async(
                [video_file, prompt],
                generation_config=generation_config
            )
            
            if response.candidates and len(response.candidates) > 0:
                analysis_text = response.candidates[0].content.parts[0].text
                
                # 사용량 정보
                usage_metadata = getattr(response, 'usage_metadata', None)
                
                return {
                    "analysis_text": analysis_text,
                    "video_file_info": {
                        "name": video_file.name,
                        "display_name": video_file.display_name,
                        "mime_type": video_file.mime_type,
                        "size_bytes": len(video_data)
                    },
                    "processing_method": "direct_upload",
                    "usage": {
                        "prompt_tokens": usage_metadata.prompt_token_count if usage_metadata else 0,
                        "completion_tokens": usage_metadata.candidates_token_count if usage_metadata else 0,
                        "total_tokens": usage_metadata.total_token_count if usage_metadata else 0
                    },
                    "safety_ratings": [
                        {
                            "category": rating.category.name,
                            "probability": rating.probability.name
                        }
                        for rating in response.candidates[0].safety_ratings
                    ] if response.candidates[0].safety_ratings else []
                }
            else:
                raise RuntimeError("No valid response from Gemini video analysis")
                
        finally:
            # 임시 파일 정리
            try:
                os.unlink(temp_file_path)
            except:
                pass
            
            # Gemini 파일 정리
            try:
                genai.delete_file(video_file.name)
            except:
                pass
    
    async def _analyze_video_url(
        self,
        video_url: str,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """비디오 URL 분석 (향후 구현)"""
        # 현재는 URL 기반 분석을 지원하지 않음
        # 향후 YouTube API 등을 통한 URL 분석 기능 추가 예정
        raise NotImplementedError("Video URL analysis not yet implemented")
    
    async def extract_frames(
        self,
        video_data: bytes,
        frame_count: int = 10,
        sampling_method: str = "uniform"
    ) -> List[Dict[str, Any]]:
        """
        비디오에서 프레임 추출
        
        Args:
            video_data: 비디오 데이터
            frame_count: 추출할 프레임 수
            sampling_method: 샘플링 방법 (uniform, keyframes)
            
        Returns:
            추출된 프레임 정보 리스트
        """
        try:
            # 실제 구현에서는 OpenCV나 FFmpeg를 사용하여 프레임 추출
            # 현재는 기본 구조만 제공
            
            frames = []
            for i in range(frame_count):
                frame_info = {
                    "frame_number": i,
                    "timestamp": i * (30.0 / frame_count),  # 30초 비디오 가정
                    "frame_data": None,  # 실제 프레임 데이터
                    "sampling_method": sampling_method
                }
                frames.append(frame_info)
            
            return frames
            
        except Exception as e:
            logger.error(f"Frame extraction failed: {str(e)}")
            return []
    
    async def get_video_metadata(self, video_data: bytes) -> Dict[str, Any]:
        """비디오 메타데이터 추출"""
        try:
            # 실제 구현에서는 FFprobe 등을 사용하여 메타데이터 추출
            metadata = {
                "size_bytes": len(video_data),
                "format": "unknown",
                "duration_seconds": 0,
                "resolution": {"width": 0, "height": 0},
                "fps": 0,
                "has_audio": False,
                "codec": "unknown"
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            return {}
    
    def is_supported_format(self, mime_type: str) -> bool:
        """지원되는 비디오 형식인지 확인"""
        return mime_type in self.supported_formats
    
    async def health_check(self) -> Dict[str, Any]:
        """비디오 처리 서비스 상태 확인"""
        try:
            if not self.gemini_service:
                return {
                    "status": "unhealthy",
                    "error": "Gemini service not available"
                }
            
            # Gemini 서비스 상태 확인
            gemini_health = await self.gemini_service.health_check()
            
            return {
                "status": "healthy" if gemini_health.get("status") == "healthy" else "degraded",
                "service": "gemini_video_processor",
                "supported_formats": self.supported_formats,
                "analysis_types": list(self.analysis_prompts.keys()),
                "max_file_size_mb": 100,  # 100MB 제한
                "gemini_service_status": gemini_health.get("status", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "gemini_video_processor"
            }

# 싱글톤 인스턴스
_video_processor = None

def get_video_processor() -> GeminiVideoProcessor:
    """비디오 프로세서 싱글톤 인스턴스 반환"""
    global _video_processor
    if _video_processor is None:
        _video_processor = GeminiVideoProcessor()
    return _video_processor