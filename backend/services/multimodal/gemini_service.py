"""
Gemini 3.0 MultiModal Service
Google의 최신 Gemini 3.0 모델을 활용한 멀티모달 처리 서비스
"""

import os
import base64
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google GenerativeAI not installed. Install with: pip install google-generativeai")

from backend.core.cache_decorators import cached_medium
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class GeminiMultimodalService:
    """Gemini 3.0 기반 멀티모달 AI 서비스"""
    
    def __init__(self):
        if not GEMINI_AVAILABLE:
            raise ImportError("Google GenerativeAI package is required")
            
        # API 키 설정
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")
            
        genai.configure(api_key=api_key)
        
        # 모델 설정
        self.model_configs = {
            'gemini-1.5-pro': {
                'capabilities': ['text', 'image', 'video', 'audio', 'code'],
                'max_tokens': 2000000,  # 2M context window
                'multimodal_fusion': True,
                'reasoning_depth': 'advanced',
                'cost_tier': 'premium'
            },
            'gemini-1.5-flash': {
                'capabilities': ['text', 'image', 'audio'],
                'max_tokens': 1000000,
                'speed_optimized': True,
                'cost_efficient': True,
                'cost_tier': 'standard'
            },
            'gemini-1.5-flash-8b': {
                'capabilities': ['text', 'image'],
                'max_tokens': 1000000,
                'speed_optimized': True,
                'cost_efficient': True,
                'cost_tier': 'budget'
            }
        }
        
        # 안전 설정
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        logger.info("Gemini MultiModal Service initialized")

    async def analyze_image_with_text(
        self, 
        image_data: Union[str, bytes], 
        prompt: str,
        model: str = 'gemini-1.5-flash',
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """
        이미지와 텍스트를 함께 분석하는 핵심 기능
        
        Args:
            image_data: base64 인코딩된 이미지 또는 바이트 데이터
            prompt: 분석 요청 텍스트
            model: 사용할 Gemini 모델
            temperature: 창의성 수준 (0.0-1.0)
            max_tokens: 최대 응답 토큰 수
            
        Returns:
            분석 결과 딕셔너리
        """
        try:
            # 이미지 데이터 처리
            if isinstance(image_data, str):
                # base64 문자열인 경우
                if image_data.startswith('data:image'):
                    # data URL 형식인 경우 헤더 제거
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
            
            # Gemini 모델 초기화
            model_instance = genai.GenerativeModel(
                model_name=model,
                safety_settings=self.safety_settings
            )
            
            # 멀티모달 입력 구성
            contents = [
                prompt,
                {
                    'mime_type': 'image/jpeg',
                    'data': image_bytes
                }
            ]
            
            # 생성 설정
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.8,
                top_k=40
            )
            
            start_time = datetime.now()
            
            # Gemini API 호출
            response = await model_instance.generate_content_async(
                contents,
                generation_config=generation_config
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 응답 처리
            if response.candidates and len(response.candidates) > 0:
                result_text = response.candidates[0].content.parts[0].text
                
                # 사용량 정보
                usage_metadata = getattr(response, 'usage_metadata', None)
                
                result = {
                    'success': True,
                    'result': result_text,
                    'model_used': model,
                    'processing_time_seconds': processing_time,
                    'timestamp': datetime.now().isoformat(),
                    'usage': {
                        'prompt_tokens': usage_metadata.prompt_token_count if usage_metadata else 0,
                        'completion_tokens': usage_metadata.candidates_token_count if usage_metadata else 0,
                        'total_tokens': usage_metadata.total_token_count if usage_metadata else 0
                    },
                    'safety_ratings': [
                        {
                            'category': rating.category.name,
                            'probability': rating.probability.name
                        }
                        for rating in response.candidates[0].safety_ratings
                    ] if response.candidates[0].safety_ratings else []
                }
                
                logger.info(f"Gemini image analysis completed in {processing_time:.2f}s")
                return result
                
            else:
                logger.error("No valid response from Gemini")
                return {
                    'success': False,
                    'error': 'No valid response generated',
                    'model_used': model,
                    'processing_time_seconds': processing_time
                }
                
        except Exception as e:
            logger.error(f"Gemini image analysis failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'model_used': model
            }

    async def process_audio_with_context(
        self,
        audio_data: bytes,
        context: str,
        model: str = 'gemini-1.5-flash',
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        음성 데이터를 컨텍스트와 함께 처리
        
        Args:
            audio_data: 음성 파일 바이트 데이터
            context: 분석 컨텍스트
            model: 사용할 Gemini 모델
            temperature: 창의성 수준
            
        Returns:
            음성 분석 결과
        """
        try:
            model_instance = genai.GenerativeModel(
                model_name=model,
                safety_settings=self.safety_settings
            )
            
            contents = [
                f"다음 컨텍스트를 고려해서 음성을 분석해주세요: {context}",
                {
                    'mime_type': 'audio/wav',
                    'data': audio_data
                }
            ]
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=2048
            )
            
            start_time = datetime.now()
            
            response = await model_instance.generate_content_async(
                contents,
                generation_config=generation_config
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if response.candidates and len(response.candidates) > 0:
                result_text = response.candidates[0].content.parts[0].text
                
                return {
                    'success': True,
                    'transcript': result_text,
                    'analysis': result_text,
                    'model_used': model,
                    'processing_time_seconds': processing_time,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'No valid response generated'
                }
                
        except Exception as e:
            logger.error(f"Gemini audio processing failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

    async def analyze_document_structure(
        self,
        image_data: Union[str, bytes],
        analysis_type: str = 'general'
    ) -> Dict[str, Any]:
        """
        문서 구조 분석 (영수증, 계약서, 양식 등)
        
        Args:
            image_data: 문서 이미지 데이터
            analysis_type: 분석 유형 ('receipt', 'invoice', 'contract', 'form', 'general')
            
        Returns:
            구조화된 문서 분석 결과
        """
        
        analysis_prompts = {
            'receipt': """
            이 영수증 이미지를 분석해서 다음 정보를 JSON 형태로 추출해주세요:
            {
                "store_name": "상점명",
                "date": "날짜 (YYYY-MM-DD)",
                "time": "시간 (HH:MM)",
                "items": [
                    {"name": "상품명", "quantity": 수량, "price": 가격}
                ],
                "subtotal": 소계,
                "tax": 세금,
                "total": 총액,
                "payment_method": "결제방법",
                "receipt_number": "영수증번호"
            }
            """,
            'invoice': """
            이 송장/인보이스를 분석해서 다음 정보를 JSON 형태로 추출해주세요:
            {
                "invoice_number": "송장번호",
                "date": "발행일자",
                "due_date": "지불기한",
                "vendor": "공급업체 정보",
                "customer": "고객 정보",
                "items": [상품 목록],
                "subtotal": 소계,
                "tax": 세금,
                "total": 총액
            }
            """,
            'contract': """
            이 계약서를 분석해서 주요 조항과 정보를 추출해주세요:
            - 계약 당사자
            - 계약 기간
            - 주요 조건
            - 금액 정보
            - 특별 조항
            """,
            'form': """
            이 양식을 분석해서 필드와 입력된 값들을 추출해주세요.
            """,
            'general': """
            이 문서를 분석해서 주요 정보를 구조화해서 추출해주세요.
            """
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts['general'])
        
        result = await self.analyze_image_with_text(
            image_data=image_data,
            prompt=prompt,
            model='gemini-1.5-flash',
            temperature=0.3  # 정확성을 위해 낮은 temperature
        )
        
        if result['success']:
            # JSON 파싱 시도
            try:
                if analysis_type in ['receipt', 'invoice']:
                    # JSON 응답 파싱
                    import re
                    json_match = re.search(r'\{.*\}', result['result'], re.DOTALL)
                    if json_match:
                        parsed_data = json.loads(json_match.group())
                        result['structured_data'] = parsed_data
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from Gemini response")
                
        return result

    @cached_medium
    async def get_model_capabilities(self, model: str) -> Dict[str, Any]:
        """모델 능력 정보 조회 (캐시됨)"""
        return self.model_configs.get(model, {})

    async def health_check(self) -> Dict[str, Any]:
        """Gemini 서비스 상태 확인"""
        try:
            # 간단한 텍스트 생성으로 연결 테스트
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = await model.generate_content_async("Hello, respond with 'OK'")
            
            if response.candidates and len(response.candidates) > 0:
                return {
                    'status': 'healthy',
                    'service': 'gemini_multimodal',
                    'models_available': list(self.model_configs.keys()),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': 'No response from Gemini API'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'service': 'gemini_multimodal'
            }

# 싱글톤 인스턴스
_gemini_service = None

def get_gemini_service() -> GeminiMultimodalService:
    """Gemini 서비스 싱글톤 인스턴스 반환"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiMultimodalService()
    return _gemini_service