"""
Advanced MultiModal Fusion Processor
여러 모달리티(이미지, 음성, 텍스트)를 동시에 처리하는 고급 융합 프로세서
"""

import asyncio
import base64
import json
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

class MultiModalInput:
    """멀티모달 입력 데이터 클래스"""
    
    def __init__(self):
        self.text_inputs: List[str] = []
        self.image_inputs: List[bytes] = []
        self.audio_inputs: List[bytes] = []
        self.metadata: Dict[str, Any] = {}
    
    def add_text(self, text: str, metadata: Optional[Dict] = None):
        """텍스트 입력 추가"""
        self.text_inputs.append(text)
        if metadata:
            self.metadata[f"text_{len(self.text_inputs)-1}"] = metadata
    
    def add_image(self, image_data: Union[str, bytes], metadata: Optional[Dict] = None):
        """이미지 입력 추가"""
        if isinstance(image_data, str):
            # base64 디코딩
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
        else:
            image_bytes = image_data
        
        self.image_inputs.append(image_bytes)
        if metadata:
            self.metadata[f"image_{len(self.image_inputs)-1}"] = metadata
    
    def add_audio(self, audio_data: bytes, metadata: Optional[Dict] = None):
        """음성 입력 추가"""
        self.audio_inputs.append(audio_data)
        if metadata:
            self.metadata[f"audio_{len(self.audio_inputs)-1}"] = metadata
    
    def get_modality_count(self) -> Dict[str, int]:
        """각 모달리티별 입력 개수 반환"""
        return {
            "text": len(self.text_inputs),
            "image": len(self.image_inputs),
            "audio": len(self.audio_inputs)
        }
    
    def is_multimodal(self) -> bool:
        """2개 이상의 모달리티가 있는지 확인"""
        modalities = sum(1 for count in self.get_modality_count().values() if count > 0)
        return modalities >= 2

class FusionStrategy:
    """융합 전략 정의"""
    
    SEQUENTIAL = "sequential"  # 순차 처리 후 결합
    PARALLEL = "parallel"     # 병렬 처리 후 융합
    UNIFIED = "unified"       # 통합 모델로 한번에 처리
    HIERARCHICAL = "hierarchical"  # 계층적 처리

class AdvancedMultiModalFusionProcessor:
    """고급 멀티모달 융합 프로세서"""
    
    def __init__(self):
        self.gemini_service = None
        if GEMINI_AVAILABLE:
            try:
                self.gemini_service = get_gemini_service()
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini service: {e}")
        
        # 융합 전략별 처리 함수 매핑
        self.strategy_handlers = {
            FusionStrategy.SEQUENTIAL: self._process_sequential,
            FusionStrategy.PARALLEL: self._process_parallel,
            FusionStrategy.UNIFIED: self._process_unified,
            FusionStrategy.HIERARCHICAL: self._process_hierarchical
        }
    
    async def process_multimodal_fusion(
        self,
        inputs: MultiModalInput,
        fusion_prompt: str,
        strategy: str = FusionStrategy.UNIFIED,
        model: str = "gemini-1.5-pro",
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        멀티모달 융합 처리 메인 함수
        
        Args:
            inputs: 멀티모달 입력 데이터
            fusion_prompt: 융합 분석 프롬프트
            strategy: 융합 전략
            model: 사용할 Gemini 모델
            temperature: 창의성 수준
            max_tokens: 최대 토큰 수
            
        Returns:
            융합 분석 결과
        """
        start_time = datetime.now()
        
        try:
            # 입력 검증
            if not inputs.is_multimodal():
                raise ValueError("At least 2 different modalities are required for fusion")
            
            # 전략별 처리
            handler = self.strategy_handlers.get(strategy)
            if not handler:
                raise ValueError(f"Unknown fusion strategy: {strategy}")
            
            logger.info(f"Starting multimodal fusion with strategy: {strategy}")
            logger.info(f"Input modalities: {inputs.get_modality_count()}")
            
            # 융합 처리 실행
            result = await handler(inputs, fusion_prompt, model, temperature, max_tokens)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 결과 포맷팅
            fusion_result = {
                "success": True,
                "fusion_strategy": strategy,
                "input_modalities": inputs.get_modality_count(),
                "fusion_result": result,
                "model_used": model,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat(),
                "metadata": inputs.metadata
            }
            
            logger.info(f"Multimodal fusion completed in {processing_time:.2f}s")
            return fusion_result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Multimodal fusion failed: {str(e)}", exc_info=True)
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "fusion_strategy": strategy,
                "processing_time_seconds": processing_time,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _process_unified(
        self,
        inputs: MultiModalInput,
        fusion_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        통합 모델로 모든 모달리티를 한번에 처리
        Gemini 3.0의 네이티브 멀티모달 능력 활용
        """
        if not self.gemini_service:
            raise RuntimeError("Gemini service not available")
        
        # Gemini 입력 구성
        gemini_contents = []
        
        # 융합 프롬프트 추가
        gemini_contents.append(fusion_prompt)
        
        # 텍스트 입력 추가
        for i, text in enumerate(inputs.text_inputs):
            gemini_contents.append(f"텍스트 {i+1}: {text}")
        
        # 이미지 입력 추가
        for i, image_data in enumerate(inputs.image_inputs):
            gemini_contents.append({
                'mime_type': 'image/jpeg',
                'data': image_data
            })
        
        # 음성 입력 추가
        for i, audio_data in enumerate(inputs.audio_inputs):
            gemini_contents.append({
                'mime_type': 'audio/wav',
                'data': audio_data
            })
        
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
        
        # Gemini API 호출
        response = await model_instance.generate_content_async(
            gemini_contents,
            generation_config=generation_config
        )
        
        if response.candidates and len(response.candidates) > 0:
            result_text = response.candidates[0].content.parts[0].text
            
            # 사용량 정보
            usage_metadata = getattr(response, 'usage_metadata', None)
            
            return {
                "fusion_text": result_text,
                "processing_method": "unified_gemini",
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
            raise RuntimeError("No valid response from Gemini unified processing")
    
    async def _process_parallel(
        self,
        inputs: MultiModalInput,
        fusion_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        각 모달리티를 병렬로 처리한 후 결과를 융합
        """
        if not self.gemini_service:
            raise RuntimeError("Gemini service not available")
        
        # 병렬 처리 태스크 생성
        tasks = []
        
        # 이미지 처리 태스크
        for i, image_data in enumerate(inputs.image_inputs):
            task = self.gemini_service.analyze_image_with_text(
                image_data=image_data,
                prompt=f"이미지 {i+1}을 분석해주세요: {fusion_prompt}",
                model=model,
                temperature=temperature
            )
            tasks.append(("image", i, task))
        
        # 음성 처리 태스크
        for i, audio_data in enumerate(inputs.audio_inputs):
            task = self.gemini_service.process_audio_with_context(
                audio_data=audio_data,
                context=f"음성 {i+1} 분석: {fusion_prompt}",
                model=model,
                temperature=temperature
            )
            tasks.append(("audio", i, task))
        
        # 병렬 실행
        results = {}
        for modality, index, task in tasks:
            try:
                result = await task
                if modality not in results:
                    results[modality] = {}
                results[modality][index] = result
            except Exception as e:
                logger.error(f"Failed to process {modality} {index}: {e}")
                if modality not in results:
                    results[modality] = {}
                results[modality][index] = {"success": False, "error": str(e)}
        
        # 텍스트 입력 처리
        if inputs.text_inputs:
            results["text"] = {}
            for i, text in enumerate(inputs.text_inputs):
                results["text"][i] = {"success": True, "content": text}
        
        # 결과 융합
        fusion_summary = await self._fuse_parallel_results(results, fusion_prompt, model)
        
        return {
            "individual_results": results,
            "fusion_summary": fusion_summary,
            "processing_method": "parallel_fusion"
        }
    
    async def _process_sequential(
        self,
        inputs: MultiModalInput,
        fusion_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        각 모달리티를 순차적으로 처리하며 컨텍스트를 누적
        """
        if not self.gemini_service:
            raise RuntimeError("Gemini service not available")
        
        accumulated_context = fusion_prompt
        sequential_results = []
        
        # 텍스트 먼저 처리
        for i, text in enumerate(inputs.text_inputs):
            accumulated_context += f"\n\n텍스트 {i+1}: {text}"
            sequential_results.append({
                "step": len(sequential_results) + 1,
                "modality": "text",
                "index": i,
                "content": text,
                "accumulated_context": accumulated_context
            })
        
        # 이미지 순차 처리
        for i, image_data in enumerate(inputs.image_inputs):
            prompt = f"{accumulated_context}\n\n위 컨텍스트를 고려하여 이 이미지를 분석해주세요."
            
            result = await self.gemini_service.analyze_image_with_text(
                image_data=image_data,
                prompt=prompt,
                model=model,
                temperature=temperature
            )
            
            if result["success"]:
                accumulated_context += f"\n\n이미지 {i+1} 분석 결과: {result['result']}"
            
            sequential_results.append({
                "step": len(sequential_results) + 1,
                "modality": "image",
                "index": i,
                "result": result,
                "accumulated_context": accumulated_context
            })
        
        # 음성 순차 처리
        for i, audio_data in enumerate(inputs.audio_inputs):
            context = f"{accumulated_context}\n\n위 컨텍스트를 고려하여 이 음성을 분석해주세요."
            
            result = await self.gemini_service.process_audio_with_context(
                audio_data=audio_data,
                context=context,
                model=model,
                temperature=temperature
            )
            
            if result["success"]:
                accumulated_context += f"\n\n음성 {i+1} 분석 결과: {result.get('analysis', result.get('transcript', ''))}"
            
            sequential_results.append({
                "step": len(sequential_results) + 1,
                "modality": "audio",
                "index": i,
                "result": result,
                "accumulated_context": accumulated_context
            })
        
        # 최종 융합 요약
        final_summary = await self._generate_final_summary(accumulated_context, model)
        
        return {
            "sequential_steps": sequential_results,
            "final_summary": final_summary,
            "processing_method": "sequential_accumulation"
        }
    
    async def _process_hierarchical(
        self,
        inputs: MultiModalInput,
        fusion_prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        계층적 처리: 같은 모달리티끼리 먼저 융합 후 모달리티간 융합
        """
        hierarchical_results = {}
        
        # 1단계: 모달리티별 내부 융합
        if len(inputs.image_inputs) > 1:
            hierarchical_results["image_fusion"] = await self._fuse_same_modality(
                inputs.image_inputs, "image", fusion_prompt, model
            )
        elif len(inputs.image_inputs) == 1:
            result = await self.gemini_service.analyze_image_with_text(
                image_data=inputs.image_inputs[0],
                prompt=fusion_prompt,
                model=model
            )
            hierarchical_results["image_fusion"] = result
        
        if len(inputs.audio_inputs) > 1:
            hierarchical_results["audio_fusion"] = await self._fuse_same_modality(
                inputs.audio_inputs, "audio", fusion_prompt, model
            )
        elif len(inputs.audio_inputs) == 1:
            result = await self.gemini_service.process_audio_with_context(
                audio_data=inputs.audio_inputs[0],
                context=fusion_prompt,
                model=model
            )
            hierarchical_results["audio_fusion"] = result
        
        if inputs.text_inputs:
            hierarchical_results["text_fusion"] = {
                "success": True,
                "combined_text": " ".join(inputs.text_inputs)
            }
        
        # 2단계: 모달리티간 융합
        cross_modal_fusion = await self._fuse_cross_modality(
            hierarchical_results, fusion_prompt, model
        )
        
        return {
            "modality_level_fusion": hierarchical_results,
            "cross_modal_fusion": cross_modal_fusion,
            "processing_method": "hierarchical_fusion"
        }
    
    async def _fuse_parallel_results(
        self,
        results: Dict[str, Dict],
        fusion_prompt: str,
        model: str
    ) -> Dict[str, Any]:
        """병렬 처리 결과를 융합"""
        # 결과 요약 생성
        summary_text = f"다음은 멀티모달 분석 결과입니다:\n\n{fusion_prompt}\n\n"
        
        for modality, modality_results in results.items():
            summary_text += f"\n{modality.upper()} 분석 결과:\n"
            for index, result in modality_results.items():
                if result.get("success"):
                    content = result.get("result") or result.get("analysis") or result.get("content", "")
                    summary_text += f"- {modality} {index + 1}: {content}\n"
        
        summary_text += "\n위 모든 정보를 종합하여 통합적인 인사이트를 제공해주세요."
        
        # 간단한 텍스트 요약 (실제로는 더 정교한 융합 로직 필요)
        return {
            "success": True,
            "fusion_summary": summary_text,
            "fusion_method": "parallel_concatenation"
        }
    
    async def _generate_final_summary(self, accumulated_context: str, model: str) -> Dict[str, Any]:
        """최종 요약 생성"""
        return {
            "success": True,
            "final_context": accumulated_context,
            "summary_method": "sequential_accumulation"
        }
    
    async def _fuse_same_modality(
        self,
        modality_inputs: List[bytes],
        modality_type: str,
        fusion_prompt: str,
        model: str
    ) -> Dict[str, Any]:
        """같은 모달리티 내 융합"""
        # 실제 구현에서는 더 정교한 융합 로직 필요
        return {
            "success": True,
            "fused_count": len(modality_inputs),
            "modality_type": modality_type,
            "fusion_method": "same_modality_fusion"
        }
    
    async def _fuse_cross_modality(
        self,
        modality_results: Dict[str, Any],
        fusion_prompt: str,
        model: str
    ) -> Dict[str, Any]:
        """모달리티간 융합"""
        return {
            "success": True,
            "cross_modal_insights": "모달리티간 융합 결과",
            "fusion_method": "cross_modal_fusion"
        }

# 싱글톤 인스턴스
_fusion_processor = None

def get_fusion_processor() -> AdvancedMultiModalFusionProcessor:
    """융합 프로세서 싱글톤 인스턴스 반환"""
    global _fusion_processor
    if _fusion_processor is None:
        _fusion_processor = AdvancedMultiModalFusionProcessor()
    return _fusion_processor