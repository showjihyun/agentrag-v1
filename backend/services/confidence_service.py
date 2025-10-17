"""
Confidence Scoring Service

Integrates ML-based confidence prediction with existing heuristic approach
"""

from typing import Dict, List, Optional
from backend.ml.confidence_predictor import (
    MLConfidencePredictor,
    ConfidenceFeatures,
    get_confidence_predictor,
)
from backend.models.query import QueryResponse


class ConfidenceService:
    """
    Service for calculating confidence scores

    Combines ML predictions with heuristic fallback
    Includes special handling for low-quality queries (no sources)
    """

    # 신뢰도 임계값
    MIN_CONFIDENCE = 0.20  # 최소 20% (15% → 20% 상향)
    MAX_CONFIDENCE = 0.95  # 최대 95% (100%는 비현실적)

    def __init__(self, use_ml: bool = True):
        self.use_ml = use_ml
        self.ml_predictor = get_confidence_predictor() if use_ml else None

    def calculate_confidence(
        self,
        query: str,
        sources: List[Dict],
        response: str,
        mode: str,
        reasoning_steps: int = 0,
        has_memory: bool = False,
        cache_hit: bool = False,
        user_history: Optional[Dict] = None,
    ) -> Dict:
        """
        Calculate confidence score using ML or heuristic approach
        Includes special handling for low-quality queries (no sources)

        Returns:
            Dict with confidence, method, and metadata
        """
        # Extract features
        features = self._extract_features(
            query=query,
            sources=sources,
            response=response,
            mode=mode,
            reasoning_steps=reasoning_steps,
            has_memory=has_memory,
            cache_hit=cache_hit,
            user_history=user_history,
        )

        # Calculate heuristic baseline
        heuristic_score = self._calculate_heuristic_confidence(features)

        # 저품질 쿼리 특별 처리 (소스 없음 또는 매우 적음)
        if features.num_sources == 0:
            # LLM 기반 신뢰도 추가
            llm_confidence = self._calculate_llm_baseline_confidence(features, query)
            heuristic_score = max(heuristic_score, llm_confidence)

            # 응답 품질 기반 보정
            response_quality = self._analyze_response_quality(response)
            quality_boost = response_quality * 0.25  # 최대 25% 증가
            heuristic_score += quality_boost

            # 임계값 적용
            heuristic_score = max(
                self.MIN_CONFIDENCE, min(self.MAX_CONFIDENCE, heuristic_score)
            )

            return {
                "confidence": heuristic_score,
                "method": "llm_knowledge",
                "llm_baseline": llm_confidence,
                "response_quality": response_quality,
                "quality_boost": quality_boost,
                "features": self._features_to_dict(features),
            }

        elif features.num_sources == 1:
            # 소스가 1개일 때도 약간의 보정
            llm_confidence = (
                self._calculate_llm_baseline_confidence(features, query) * 0.5
            )
            heuristic_score = max(heuristic_score, llm_confidence)

        # Use ML if enabled and model is confident
        if self.use_ml and self.ml_predictor:
            ml_score, uncertainty = self.ml_predictor.predict_with_uncertainty(features)

            # Use ML score if uncertainty is low
            if uncertainty < 0.25:
                return {
                    "confidence": ml_score,
                    "method": "ml",
                    "uncertainty": uncertainty,
                    "heuristic_baseline": heuristic_score,
                    "features": self._features_to_dict(features),
                }
            else:
                # High uncertainty - blend with heuristic
                blended_score = 0.6 * ml_score + 0.4 * heuristic_score
                return {
                    "confidence": blended_score,
                    "method": "blended",
                    "uncertainty": uncertainty,
                    "ml_score": ml_score,
                    "heuristic_score": heuristic_score,
                    "features": self._features_to_dict(features),
                }

        # Fallback to heuristic
        return {
            "confidence": heuristic_score,
            "method": "heuristic",
            "features": self._features_to_dict(features),
        }

    def _extract_features(
        self,
        query: str,
        sources: List[Dict],
        response: str,
        mode: str,
        reasoning_steps: int,
        has_memory: bool,
        cache_hit: bool,
        user_history: Optional[Dict],
    ) -> ConfidenceFeatures:
        """Extract features from query context"""

        # Query features
        query_length = len(query.split())
        query_complexity = self._estimate_query_complexity(query)
        has_keywords = self._has_domain_keywords(query)

        # Source features
        num_sources = len(sources)
        similarity_scores = [s.get("score", 0.0) for s in sources]
        avg_similarity = (
            sum(similarity_scores) / len(similarity_scores)
            if similarity_scores
            else 0.0
        )
        max_similarity = max(similarity_scores) if similarity_scores else 0.0
        source_diversity = self._calculate_source_diversity(sources)

        # Response features
        response_length = len(response.split())
        has_citations = any(s.get("cited", False) for s in sources)

        # Historical features
        feedback_history = (
            user_history.get("avg_feedback", 0.7) if user_history else 0.7
        )
        success_rate = user_history.get("success_rate", 0.75) if user_history else 0.75

        return ConfidenceFeatures(
            query_length=query_length,
            query_complexity=query_complexity,
            has_keywords=has_keywords,
            num_sources=num_sources,
            avg_similarity_score=avg_similarity,
            max_similarity_score=max_similarity,
            source_diversity=source_diversity,
            response_length=response_length,
            has_citations=has_citations,
            reasoning_steps=reasoning_steps,
            mode=mode,
            has_memory_context=has_memory,
            cache_hit=cache_hit,
            user_feedback_history=feedback_history,
            similar_query_success_rate=success_rate,
        )

    def _estimate_query_complexity(self, query: str) -> float:
        """Estimate query complexity (0-1 scale)"""
        words = query.split()

        # Factors that increase complexity
        complexity = 0.3  # Base complexity

        # Length factor
        if len(words) > 15:
            complexity += 0.2
        elif len(words) > 8:
            complexity += 0.1

        # Question words
        question_words = ["how", "why", "explain", "compare", "analyze", "describe"]
        if any(word in query.lower() for word in question_words):
            complexity += 0.2

        # Multiple clauses
        if "," in query or " and " in query.lower():
            complexity += 0.15

        # Technical terms
        technical_terms = [
            "algorithm",
            "architecture",
            "implementation",
            "optimization",
        ]
        if any(term in query.lower() for term in technical_terms):
            complexity += 0.15

        return min(complexity, 1.0)

    def _has_domain_keywords(self, query: str) -> bool:
        """Check if query contains domain-specific keywords"""
        keywords = [
            "ai",
            "machine learning",
            "deep learning",
            "neural network",
            "nlp",
            "computer vision",
            "reinforcement learning",
            "algorithm",
            "model",
            "training",
            "inference",
            "embedding",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in keywords)

    def _calculate_source_diversity(self, sources: List[Dict]) -> float:
        """Calculate diversity of sources (0-1 scale)"""
        if not sources:
            return 0.0

        # Check for different document sources
        unique_docs = len(set(s.get("document_id", "") for s in sources))
        diversity = unique_docs / len(sources)

        return diversity

    def _calculate_heuristic_confidence(self, features: ConfidenceFeatures) -> float:
        """
        Calculate confidence using rule-based heuristics (IMPROVED)

        This is the baseline approach being replaced by ML
        Uses more conservative scoring to avoid overconfidence
        """
        # 낮은 기본값으로 시작
        confidence = 0.30

        # Source quality (최대 0.30)
        if features.num_sources >= 5:
            confidence += 0.30
        elif features.num_sources >= 3:
            confidence += 0.20
        elif features.num_sources >= 1:
            confidence += 0.10

        # Similarity score (최대 0.25)
        if features.avg_similarity_score > 0.85:
            confidence += 0.25
        elif features.avg_similarity_score > 0.70:
            confidence += 0.15
        elif features.avg_similarity_score > 0.50:
            confidence += 0.08

        # Response quality (최대 0.20)
        if features.has_citations and features.response_length > 200:
            confidence += 0.20
        elif features.has_citations or features.response_length > 100:
            confidence += 0.10

        # Mode adjustment (최대 0.10)
        mode_bonus = {"fast": 0.0, "balanced": 0.05, "deep": 0.10}
        confidence += mode_bonus.get(features.mode, 0.0)

        # Context (최대 0.10)
        if features.has_memory_context:
            confidence += 0.05

        if features.cache_hit:
            confidence += 0.05

        # Historical performance (최대 0.10)
        confidence += features.user_feedback_history * 0.10

        # 임계값 적용 (15-95%)
        confidence = max(self.MIN_CONFIDENCE, confidence)
        confidence = min(self.MAX_CONFIDENCE, confidence)

        return confidence

    def _calculate_llm_baseline_confidence(
        self, features: ConfidenceFeatures, query: str
    ) -> float:
        """
        LLM 기반 기본 신뢰도 계산

        소스가 없어도 LLM의 일반 지식으로 답변 가능한 경우 신뢰도 부여
        """
        baseline = 0.0

        # 1. 일반 지식 쿼리 감지
        general_knowledge_keywords = [
            "what is",
            "define",
            "explain",
            "how does",
            "why",
            "describe",
            "무엇",
            "정의",
            "설명",
            "어떻게",
            "왜",
            "묘사",
        ]

        query_lower = query.lower()
        is_general_knowledge = any(
            kw in query_lower for kw in general_knowledge_keywords
        )

        if is_general_knowledge:
            baseline += 0.20  # 일반 지식 쿼리는 기본 20%

        # 2. 쿼리 복잡도 기반 조정
        if features.query_complexity < 0.5:  # 간단한 쿼리
            baseline += 0.10

        # 3. LLM 모드 기반 조정
        if features.mode == "deep":
            baseline += 0.10  # Deep 모드는 더 신뢰
        elif features.mode == "balanced":
            baseline += 0.05

        # 4. 응답 품질 기반 조정
        if features.response_length > 100:
            baseline += 0.05  # 충분한 길이의 응답

        if features.reasoning_steps > 0:
            baseline += 0.05  # 추론 과정이 있음

        return min(baseline, 0.40)  # 최대 40%

    def _analyze_response_quality(self, response: str) -> float:
        """
        응답 품질 분석

        Returns:
            품질 점수 (0-1)
        """
        quality_score = 0.0

        # 1. 길이 체크 (너무 짧으면 품질 낮음)
        if len(response) > 200:
            quality_score += 0.25
        elif len(response) > 100:
            quality_score += 0.15
        elif len(response) > 50:
            quality_score += 0.05

        # 2. 구조 체크
        has_structure = any(
            [
                "\n\n" in response,  # 단락 구분
                "1." in response or "2." in response,  # 번호 매기기
                "- " in response or "* " in response,  # 불릿 포인트
            ]
        )
        if has_structure:
            quality_score += 0.15

        # 3. 전문 용어 사용 (도메인 지식)
        technical_terms = [
            "algorithm",
            "system",
            "process",
            "method",
            "approach",
            "model",
            "data",
        ]
        term_count = sum(1 for term in technical_terms if term in response.lower())
        quality_score += min(term_count * 0.05, 0.15)

        # 4. 문장 완성도
        sentences = response.split(".")
        complete_sentences = [s for s in sentences if len(s.strip()) > 10]
        if len(complete_sentences) >= 3:
            quality_score += 0.15

        # 5. 불확실성 표현 체크 (역으로 감점)
        uncertainty_phrases = [
            "i don't know",
            "not sure",
            "maybe",
            "perhaps",
            "possibly",
        ]
        has_uncertainty = any(
            phrase in response.lower() for phrase in uncertainty_phrases
        )
        if has_uncertainty:
            quality_score -= 0.10

        return max(0.0, min(quality_score, 1.0))

    def _features_to_dict(self, features: ConfidenceFeatures) -> Dict:
        """Convert features to dictionary for logging"""
        return {
            "query_length": features.query_length,
            "query_complexity": features.query_complexity,
            "num_sources": features.num_sources,
            "avg_similarity": features.avg_similarity_score,
            "mode": features.mode,
            "cache_hit": features.cache_hit,
        }

    def record_feedback(
        self,
        query: str,
        sources: List[Dict],
        response: str,
        mode: str,
        actual_feedback: float,
        reasoning_steps: int = 0,
        has_memory: bool = False,
        cache_hit: bool = False,
        user_history: Optional[Dict] = None,
    ):
        """
        Record user feedback for model improvement

        Args:
            actual_feedback: User rating (0-1 scale)
        """
        if not self.ml_predictor:
            return

        features = self._extract_features(
            query=query,
            sources=sources,
            response=response,
            mode=mode,
            reasoning_steps=reasoning_steps,
            has_memory=has_memory,
            cache_hit=cache_hit,
            user_history=user_history,
        )

        self.ml_predictor.record_feedback(features, actual_feedback)


# Singleton instance
_confidence_service: Optional[ConfidenceService] = None


def get_confidence_service(use_ml: bool = True) -> ConfidenceService:
    """Get or create singleton confidence service"""
    global _confidence_service
    if _confidence_service is None:
        _confidence_service = ConfidenceService(use_ml=use_ml)
    return _confidence_service
