"""
Answer Quality Evaluation Service.

Provides comprehensive answer quality assessment including:
- Source relevance evaluation
- Answer grounding (hallucination detection)
- Completeness checking
- User feedback collection
- Quality metrics tracking
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
import re

logger = logging.getLogger(__name__)


class AnswerQualityService:
    """
    Service for evaluating and tracking answer quality.

    Features:
    - Multi-dimensional quality metrics
    - Hallucination detection
    - User feedback integration
    - Quality trend analysis
    - Automatic improvement suggestions
    """

    def __init__(self, llm_manager=None):
        """
        Initialize AnswerQualityService.

        Args:
            llm_manager: Optional LLM manager for advanced evaluation
        """
        self.llm_manager = llm_manager
        logger.info("AnswerQualityService initialized")

    async def evaluate_answer(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]],
        user_feedback: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive answer quality evaluation.

        Args:
            query: User's question
            answer: Generated answer
            sources: List of source documents used
            user_feedback: User rating (1=good, -1=bad, 0=neutral)
            metadata: Additional context (mode, session_id, etc.)

        Returns:
            Dictionary with quality metrics
        """
        try:
            logger.info(f"Evaluating answer quality for query: {query[:50]}...")

            # 1. Source relevance
            source_relevance = self._evaluate_source_relevance(query, sources)

            # 2. Answer grounding
            grounding_score = self._evaluate_grounding(answer, sources)

            # 3. Hallucination detection
            hallucination_risk = self._detect_hallucination(answer, sources)

            # 4. Completeness
            completeness = self._evaluate_completeness(query, answer)

            # 5. Answer length appropriateness
            length_score = self._evaluate_length(answer, query)

            # 6. Citation quality
            citation_score = self._evaluate_citations(answer, sources)

            # Calculate overall score
            overall_score = self._calculate_overall_score(
                source_relevance=source_relevance,
                grounding=grounding_score,
                hallucination_risk=hallucination_risk,
                completeness=completeness,
                length_score=length_score,
                citation_score=citation_score,
                user_feedback=user_feedback,
            )

            quality_metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "query": query,
                "answer_length": len(answer),
                "source_count": len(sources),
                "metrics": {
                    "source_relevance": round(source_relevance, 3),
                    "grounding": round(grounding_score, 3),
                    "hallucination_risk": round(hallucination_risk, 3),
                    "completeness": round(completeness, 3),
                    "length_score": round(length_score, 3),
                    "citation_score": round(citation_score, 3),
                },
                "overall_score": round(overall_score, 3),
                "user_feedback": user_feedback,
                "quality_level": self._get_quality_level(overall_score),
                "suggestions": self._generate_suggestions(
                    source_relevance,
                    grounding_score,
                    hallucination_risk,
                    completeness,
                    length_score,
                    citation_score,
                ),
            }

            if metadata:
                quality_metrics["metadata"] = metadata

            logger.info(
                f"Quality evaluation complete: overall={overall_score:.2f}, "
                f"level={quality_metrics['quality_level']}"
            )

            return quality_metrics

        except Exception as e:
            logger.error(f"Answer quality evaluation failed: {e}", exc_info=True)
            return {"error": str(e), "overall_score": 0.5, "quality_level": "unknown"}

    def _evaluate_source_relevance(
        self, query: str, sources: List[Dict[str, Any]]
    ) -> float:
        """
        Evaluate how relevant sources are to the query.

        Args:
            query: User query
            sources: List of source documents

        Returns:
            Relevance score (0-1)
        """
        if not sources:
            return 0.0

        try:
            # Extract query keywords
            query_keywords = set(self._extract_keywords(query.lower()))

            if not query_keywords:
                return 0.5  # Neutral if no keywords

            relevance_scores = []

            for source in sources:
                source_text = source.get("text", "").lower()
                source_keywords = set(self._extract_keywords(source_text))

                # Calculate keyword overlap
                if source_keywords:
                    overlap = len(query_keywords & source_keywords)
                    relevance = overlap / len(query_keywords)
                    relevance_scores.append(relevance)

            # Average relevance
            if relevance_scores:
                return sum(relevance_scores) / len(relevance_scores)

            return 0.5

        except Exception as e:
            logger.debug(f"Source relevance evaluation failed: {e}")
            return 0.5

    def _evaluate_grounding(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """
        Evaluate how well the answer is grounded in sources.

        Args:
            answer: Generated answer
            sources: Source documents

        Returns:
            Grounding score (0-1)
        """
        if not sources:
            return 0.0

        try:
            # Extract answer keywords
            answer_keywords = set(self._extract_keywords(answer.lower()))

            if not answer_keywords:
                return 0.5

            # Combine all source text
            source_text = " ".join([s.get("text", "") for s in sources]).lower()
            source_keywords = set(self._extract_keywords(source_text))

            # Calculate how many answer keywords are in sources
            if answer_keywords:
                grounded_keywords = len(answer_keywords & source_keywords)
                grounding_score = grounded_keywords / len(answer_keywords)
                return min(grounding_score, 1.0)

            return 0.5

        except Exception as e:
            logger.debug(f"Grounding evaluation failed: {e}")
            return 0.5

    def _detect_hallucination(
        self, answer: str, sources: List[Dict[str, Any]]
    ) -> float:
        """
        Detect potential hallucinations in the answer.

        Hallucination indicators:
        - Specific claims not in sources
        - Exact numbers/dates not in sources
        - Named entities not in sources

        Args:
            answer: Generated answer
            sources: Source documents

        Returns:
            Hallucination risk score (0-1, higher = more risk)
        """
        if not sources:
            return 0.8  # High risk if no sources

        try:
            risk_score = 0.0
            risk_count = 0

            # Combine source text
            source_text = " ".join([s.get("text", "") for s in sources]).lower()
            answer_lower = answer.lower()

            # Check 1: Specific numbers
            answer_numbers = re.findall(r"\b\d+(?:\.\d+)?\b", answer)
            for number in answer_numbers:
                if number not in source_text:
                    risk_score += 0.2
                    risk_count += 1

            # Check 2: Dates
            answer_dates = re.findall(
                r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b",
                answer,
            )
            for date in answer_dates:
                if date not in source_text:
                    risk_score += 0.2
                    risk_count += 1

            # Check 3: Definitive statements without source support
            definitive_phrases = [
                "exactly",
                "precisely",
                "specifically",
                "definitely",
                "certainly",
                "absolutely",
                "always",
                "never",
            ]

            for phrase in definitive_phrases:
                if phrase in answer_lower:
                    risk_score += 0.1
                    risk_count += 1

            # Normalize risk score
            if risk_count > 0:
                normalized_risk = min(risk_score / max(risk_count, 1), 1.0)
                return normalized_risk

            return 0.1  # Low baseline risk

        except Exception as e:
            logger.debug(f"Hallucination detection failed: {e}")
            return 0.3  # Medium risk on error

    def _evaluate_completeness(self, query: str, answer: str) -> float:
        """
        Evaluate if answer addresses all parts of the query.

        Args:
            query: User query
            answer: Generated answer

        Returns:
            Completeness score (0-1)
        """
        try:
            # Check for question words in query
            question_words = {
                "what",
                "when",
                "where",
                "who",
                "why",
                "how",
                "which",
                "whose",
                "whom",
            }

            query_lower = query.lower()
            query_questions = [w for w in question_words if w in query_lower]

            if not query_questions:
                # Not a question, check if answer is substantial
                return 0.8 if len(answer) > 50 else 0.5

            # Check if answer addresses each question type
            answer_lower = answer.lower()
            addressed = 0

            for q_word in query_questions:
                # Simple heuristic: answer should contain related content
                if q_word == "what" and len(answer) > 30:
                    addressed += 1
                elif q_word == "when" and any(
                    word in answer_lower for word in ["date", "time", "year", "day"]
                ):
                    addressed += 1
                elif q_word == "where" and any(
                    word in answer_lower for word in ["location", "place", "at", "in"]
                ):
                    addressed += 1
                elif q_word == "who" and len(answer) > 20:
                    addressed += 1
                elif q_word == "why" and any(
                    word in answer_lower for word in ["because", "reason", "due to"]
                ):
                    addressed += 1
                elif q_word == "how" and len(answer) > 40:
                    addressed += 1

            if query_questions:
                return addressed / len(query_questions)

            return 0.7

        except Exception as e:
            logger.debug(f"Completeness evaluation failed: {e}")
            return 0.6

    def _evaluate_length(self, answer: str, query: str) -> float:
        """
        Evaluate if answer length is appropriate.

        Args:
            answer: Generated answer
            query: User query

        Returns:
            Length appropriateness score (0-1)
        """
        try:
            answer_len = len(answer)
            query_len = len(query)

            # Too short
            if answer_len < 20:
                return 0.3

            # Too long (likely verbose)
            if answer_len > 2000:
                return 0.6

            # Ideal range: 50-500 characters
            if 50 <= answer_len <= 500:
                return 1.0

            # Acceptable range: 20-1000 characters
            if 20 <= answer_len <= 1000:
                return 0.8

            return 0.7

        except Exception as e:
            logger.debug(f"Length evaluation failed: {e}")
            return 0.7

    def _evaluate_citations(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """
        Evaluate quality of citations in answer.

        Args:
            answer: Generated answer
            sources: Source documents

        Returns:
            Citation quality score (0-1)
        """
        if not sources:
            return 0.0

        try:
            # Check for citation markers
            citation_patterns = [
                r"\[\d+\]",  # [1], [2]
                r"\(\d+\)",  # (1), (2)
                r"source \d+",  # source 1
                r"according to",
                r"based on",
                r"as mentioned",
            ]

            has_citations = any(
                re.search(pattern, answer.lower()) for pattern in citation_patterns
            )

            if has_citations:
                return 1.0

            # Check if answer references sources implicitly
            source_keywords = set()
            for source in sources:
                source_keywords.update(self._extract_keywords(source.get("text", "")))

            answer_keywords = set(self._extract_keywords(answer))

            if source_keywords and answer_keywords:
                overlap = len(source_keywords & answer_keywords)
                implicit_citation = overlap / len(answer_keywords)
                return min(implicit_citation, 0.8)

            return 0.5

        except Exception as e:
            logger.debug(f"Citation evaluation failed: {e}")
            return 0.5

    def _calculate_overall_score(
        self,
        source_relevance: float,
        grounding: float,
        hallucination_risk: float,
        completeness: float,
        length_score: float,
        citation_score: float,
        user_feedback: Optional[int] = None,
    ) -> float:
        """
        Calculate weighted overall quality score.

        Args:
            source_relevance: Source relevance score
            grounding: Grounding score
            hallucination_risk: Hallucination risk (inverted for score)
            completeness: Completeness score
            length_score: Length appropriateness score
            citation_score: Citation quality score
            user_feedback: User feedback (1, 0, -1)

        Returns:
            Overall quality score (0-1)
        """
        # Weights for each metric
        weights = {
            "source_relevance": 0.20,
            "grounding": 0.25,
            "hallucination": 0.25,  # Inverted
            "completeness": 0.15,
            "length": 0.05,
            "citation": 0.10,
        }

        # Calculate weighted score
        score = (
            source_relevance * weights["source_relevance"]
            + grounding * weights["grounding"]
            + (1 - hallucination_risk) * weights["hallucination"]
            + completeness * weights["completeness"]
            + length_score * weights["length"]
            + citation_score * weights["citation"]
        )

        # Adjust based on user feedback
        if user_feedback is not None:
            if user_feedback > 0:
                score = min(score * 1.2, 1.0)  # Boost by 20%
            elif user_feedback < 0:
                score = score * 0.7  # Reduce by 30%

        return min(max(score, 0.0), 1.0)

    def _get_quality_level(self, score: float) -> str:
        """
        Convert numeric score to quality level.

        Args:
            score: Quality score (0-1)

        Returns:
            Quality level string
        """
        if score >= 0.9:
            return "excellent"
        elif score >= 0.75:
            return "good"
        elif score >= 0.6:
            return "acceptable"
        elif score >= 0.4:
            return "poor"
        else:
            return "very_poor"

    def _generate_suggestions(
        self,
        source_relevance: float,
        grounding: float,
        hallucination_risk: float,
        completeness: float,
        length_score: float,
        citation_score: float,
    ) -> List[str]:
        """
        Generate improvement suggestions based on metrics.

        Args:
            Various quality metrics

        Returns:
            List of suggestion strings
        """
        suggestions = []

        if source_relevance < 0.6:
            suggestions.append("Consider using more relevant sources for this query")

        if grounding < 0.6:
            suggestions.append(
                "Answer should be better grounded in the provided sources"
            )

        if hallucination_risk > 0.5:
            suggestions.append(
                "High hallucination risk detected - verify all claims against sources"
            )

        if completeness < 0.6:
            suggestions.append("Answer may not fully address all aspects of the query")

        if length_score < 0.6:
            suggestions.append("Answer length may not be appropriate for the query")

        if citation_score < 0.5:
            suggestions.append("Consider adding explicit citations to sources")

        if not suggestions:
            suggestions.append("Quality is good - no major improvements needed")

        return suggestions

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Input text

        Returns:
            List of keywords
        """
        # Remove punctuation and split
        words = re.findall(r"\b\w+\b", text.lower())

        # Filter stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

        keywords = [w for w in words if len(w) > 2 and w not in stop_words]

        return keywords


# Singleton instance
_answer_quality_service: Optional[AnswerQualityService] = None


def get_answer_quality_service(llm_manager=None) -> AnswerQualityService:
    """
    Get or create AnswerQualityService singleton instance.

    Args:
        llm_manager: Optional LLM manager

    Returns:
        AnswerQualityService instance
    """
    global _answer_quality_service

    if _answer_quality_service is None:
        _answer_quality_service = AnswerQualityService(llm_manager=llm_manager)

    return _answer_quality_service
