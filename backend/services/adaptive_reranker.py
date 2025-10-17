"""
Adaptive Reranker Service

Dynamically selects the best reranker model based on:
- Query language (Korean vs multilingual)
- Document length (short vs long)
- Content type (pure Korean vs mixed)
- Performance requirements
"""

import logging
import re
from typing import List, Dict, Any, Optional
from functools import lru_cache

from backend.services.cross_encoder_reranker import CrossEncoderReranker

logger = logging.getLogger(__name__)


class AdaptiveReranker:
    """
    Adaptive reranker that selects the best model based on context.
    
    Features:
    - Language detection (Korean, English, Mixed)
    - Document length analysis
    - Dynamic model selection
    - Performance optimization
    """

    def __init__(
        self,
        korean_model: str = "Dongjin-kr/ko-reranker",
        multilingual_model: str = "BAAI/bge-reranker-v2-m3",
        device: str = None,
        enable_caching: bool = True
    ):
        """
        Initialize Adaptive Reranker.
        
        Args:
            korean_model: Model for Korean-only content
            multilingual_model: Model for multilingual content
            device: Device to use (None = auto-detect)
            enable_caching: Enable model caching
        """
        self.korean_model_name = korean_model
        self.multilingual_model_name = multilingual_model
        self.device = device
        self.enable_caching = enable_caching
        
        # Lazy load models
        self._korean_reranker: Optional[CrossEncoderReranker] = None
        self._multilingual_reranker: Optional[CrossEncoderReranker] = None
        
        # Statistics
        self.stats = {
            "korean_model_used": 0,
            "multilingual_model_used": 0,
            "total_queries": 0
        }
        
        logger.info(
            f"AdaptiveReranker initialized: "
            f"korean={korean_model}, multilingual={multilingual_model}"
        )

    def _get_korean_reranker(self) -> CrossEncoderReranker:
        """Get or create Korean reranker with optimizations"""
        if self._korean_reranker is None:
            logger.info(f"Loading Korean reranker: {self.korean_model_name}")
            
            # Try optimized reranker first
            try:
                from backend.services.optimized_reranker import OptimizedReranker
                self._korean_reranker = OptimizedReranker(
                    model_name=self.korean_model_name,
                    device=self.device,
                    use_fp16=True,  # 2x speedup
                    enable_caching=True,
                    dynamic_batching=True
                )
                logger.info("Using optimized Korean reranker")
            except Exception as e:
                logger.warning(f"Optimized reranker failed, using standard: {e}")
                self._korean_reranker = CrossEncoderReranker(
                    model_name=self.korean_model_name,
                    max_length=512,
                    device=self.device
                )
        return self._korean_reranker

    def _get_multilingual_reranker(self) -> CrossEncoderReranker:
        """Get or create multilingual reranker with optimizations"""
        if self._multilingual_reranker is None:
            logger.info(f"Loading multilingual reranker: {self.multilingual_model_name}")
            
            # Try optimized reranker first
            try:
                from backend.services.optimized_reranker import OptimizedReranker
                self._multilingual_reranker = OptimizedReranker(
                    model_name=self.multilingual_model_name,
                    device=self.device,
                    use_fp16=True,  # 2x speedup
                    enable_caching=True,
                    dynamic_batching=True
                )
                logger.info("Using optimized multilingual reranker")
            except Exception as e:
                logger.warning(f"Optimized reranker failed, using standard: {e}")
                self._multilingual_reranker = CrossEncoderReranker(
                    model_name=self.multilingual_model_name,
                    max_length=1024,
                    device=self.device
                )
        return self._multilingual_reranker

    def detect_language(self, text: str) -> Dict[str, float]:
        """
        Detect language composition of text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dict with language percentages: {"korean": 0.8, "english": 0.15, "other": 0.05}
        """
        if not text:
            return {"korean": 0.0, "english": 0.0, "other": 0.0}
        
        # Count characters by type
        korean_chars = len(re.findall(r'[가-힣]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        total_chars = len(re.sub(r'\s', '', text))  # Exclude whitespace
        
        if total_chars == 0:
            return {"korean": 0.0, "english": 0.0, "other": 0.0}
        
        korean_ratio = korean_chars / total_chars
        english_ratio = english_chars / total_chars
        other_ratio = 1.0 - korean_ratio - english_ratio
        
        return {
            "korean": korean_ratio,
            "english": english_ratio,
            "other": max(0.0, other_ratio)
        }

    def analyze_content(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze query and results to determine best model.
        
        Args:
            query: Search query
            results: Search results
        
        Returns:
            Analysis dict with recommendations
        """
        # Analyze query
        query_lang = self.detect_language(query)
        
        # Analyze results (sample first 5)
        sample_results = results[:5]
        result_texts = [
            r.get('text', '') or r.get('content', '')
            for r in sample_results
        ]
        combined_text = ' '.join(result_texts)
        result_lang = self.detect_language(combined_text)
        
        # Calculate average document length
        avg_length = sum(len(text) for text in result_texts) / max(len(result_texts), 1)
        max_length = max((len(text) for text in result_texts), default=0)
        
        # Determine if content is Korean-dominant
        is_korean_dominant = (
            query_lang["korean"] > 0.8 and
            result_lang["korean"] > 0.7
        )
        
        # Determine if documents are short
        is_short_docs = max_length < 2000  # ~512 tokens
        
        # Determine if multilingual
        is_multilingual = (
            query_lang["english"] > 0.2 or
            result_lang["english"] > 0.2 or
            query_lang["other"] > 0.1 or
            result_lang["other"] > 0.1
        )
        
        # Recommendation
        use_korean_model = (
            is_korean_dominant and
            is_short_docs and
            not is_multilingual
        )
        
        return {
            "query_language": query_lang,
            "result_language": result_lang,
            "avg_doc_length": avg_length,
            "max_doc_length": max_length,
            "is_korean_dominant": is_korean_dominant,
            "is_short_docs": is_short_docs,
            "is_multilingual": is_multilingual,
            "recommended_model": "korean" if use_korean_model else "multilingual",
            "confidence": self._calculate_confidence(
                is_korean_dominant,
                is_short_docs,
                is_multilingual
            )
        }

    def _calculate_confidence(
        self,
        is_korean_dominant: bool,
        is_short_docs: bool,
        is_multilingual: bool
    ) -> float:
        """Calculate confidence in model selection"""
        score = 0.0
        
        if is_korean_dominant:
            score += 0.4
        if is_short_docs:
            score += 0.3
        if not is_multilingual:
            score += 0.3
        
        return score

    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        score_threshold: float = 0.0,
        force_model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Adaptively rerank results using the best model.
        
        Args:
            query: Search query
            results: Search results
            top_k: Number of top results to return
            score_threshold: Minimum score threshold
            force_model: Force specific model ("korean" or "multilingual")
        
        Returns:
            Reranked results with metadata
        """
        if not results:
            return []
        
        self.stats["total_queries"] += 1
        
        # Analyze content to determine best model
        analysis = self.analyze_content(query, results)
        
        # Select model
        if force_model:
            use_korean = force_model == "korean"
            logger.info(f"Forced model selection: {force_model}")
        else:
            use_korean = analysis["recommended_model"] == "korean"
            logger.info(
                f"Adaptive model selection: {analysis['recommended_model']} "
                f"(confidence: {analysis['confidence']:.2f})"
            )
        
        # Get appropriate reranker
        if use_korean:
            reranker = self._get_korean_reranker()
            model_used = "korean"
            self.stats["korean_model_used"] += 1
        else:
            reranker = self._get_multilingual_reranker()
            model_used = "multilingual"
            self.stats["multilingual_model_used"] += 1
        
        # Perform reranking
        reranked = await reranker.rerank(
            query=query,
            results=results,
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        # Add metadata
        for result in reranked:
            result['reranker_model'] = model_used
            result['reranker_analysis'] = analysis
        
        logger.info(
            f"Reranked {len(results)} → {len(reranked)} results "
            f"using {model_used} model"
        )
        
        return reranked

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        total = self.stats["total_queries"]
        
        return {
            **self.stats,
            "korean_model_percentage": (
                self.stats["korean_model_used"] / total * 100
                if total > 0 else 0.0
            ),
            "multilingual_model_percentage": (
                self.stats["multilingual_model_used"] / total * 100
                if total > 0 else 0.0
            )
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "korean_model": {
                "name": self.korean_model_name,
                "max_length": 512,
                "loaded": self._korean_reranker is not None
            },
            "multilingual_model": {
                "name": self.multilingual_model_name,
                "max_length": 1024,
                "loaded": self._multilingual_reranker is not None
            },
            "stats": self.get_stats()
        }


# Global instance
_adaptive_reranker: Optional[AdaptiveReranker] = None


def get_adaptive_reranker(
    korean_model: str = "Dongjin-kr/ko-reranker",
    multilingual_model: str = "BAAI/bge-reranker-v2-m3",
    device: str = None
) -> AdaptiveReranker:
    """
    Get global adaptive reranker instance.
    
    Args:
        korean_model: Model for Korean-only content
        multilingual_model: Model for multilingual content
        device: Device to use (None = auto-detect)
    
    Returns:
        AdaptiveReranker instance
    """
    global _adaptive_reranker
    
    if _adaptive_reranker is None:
        _adaptive_reranker = AdaptiveReranker(
            korean_model=korean_model,
            multilingual_model=multilingual_model,
            device=device
        )
    
    return _adaptive_reranker


# Convenience function for backward compatibility
async def adaptive_rerank(
    query: str,
    results: List[Dict[str, Any]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Convenience function for adaptive reranking.
    
    Args:
        query: Search query
        results: Search results
        top_k: Number of results to return
    
    Returns:
        Reranked results
    """
    reranker = get_adaptive_reranker()
    return await reranker.rerank(query, results, top_k=top_k)
