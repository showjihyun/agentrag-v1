"""
Query Complexity Analyzer

Analyzes query complexity to recommend optimal processing mode (FAST/BALANCED/DEEP).
"""

import re
from typing import Dict, Tuple
from enum import Enum
from backend.models.hybrid import QueryMode


class ComplexityLevel(Enum):
    """Query complexity levels"""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class QueryComplexityAnalyzer:
    """
    Analyzes query complexity and recommends appropriate processing mode.

    Uses multiple heuristics:
    - Query length
    - Question type (factual vs analytical)
    - Complexity keywords
    - Sentence structure
    - Korean-specific patterns
    """

    # Complexity indicators
    SIMPLE_PATTERNS = [
        r"\b(what is|who is|when|where|which|define|list)\b",
        r"\b(무엇|누구|언제|어디|어느|정의|나열)\b",  # Korean
    ]

    COMPLEX_PATTERNS = [
        r"\b(compare|contrast|analyze|evaluate|assess|explain why|how does)\b",
        r"\b(비교|대조|분석|평가|설명|이유|어떻게)\b",  # Korean
        r"\b(advantages? and disadvantages?|pros? and cons?)\b",
        r"\b(장단점|장점과 단점)\b",  # Korean
    ]

    DEEP_KEYWORDS = [
        "compare",
        "contrast",
        "analyze",
        "evaluate",
        "assess",
        "critique",
        "synthesize",
        "justify",
        "argue",
        "debate",
        "implications",
        "비교",
        "대조",
        "분석",
        "평가",
        "비판",
        "종합",
        "정당화",
        "논증",
        "토론",
        "시사점",
    ]

    FACTUAL_KEYWORDS = [
        "what",
        "who",
        "when",
        "where",
        "which",
        "define",
        "list",
        "무엇",
        "누구",
        "언제",
        "어디",
        "어느",
        "정의",
        "나열",
    ]

    def __init__(self):
        """Initialize the analyzer"""
        self.simple_regex = re.compile("|".join(self.SIMPLE_PATTERNS), re.IGNORECASE)
        self.complex_regex = re.compile("|".join(self.COMPLEX_PATTERNS), re.IGNORECASE)

    def analyze(self, query: str) -> Tuple[ComplexityLevel, QueryMode, float, Dict]:
        """
        Analyze query complexity and recommend mode.

        Args:
            query: User query string

        Returns:
            Tuple of (complexity_level, recommended_mode, confidence, reasoning)
        """
        # Calculate individual scores
        length_score = self._analyze_length(query)
        keyword_score = self._analyze_keywords(query)
        structure_score = self._analyze_structure(query)
        question_type_score = self._analyze_question_type(query)

        # Weighted average
        weights = {
            "length": 0.2,
            "keywords": 0.4,
            "structure": 0.2,
            "question_type": 0.2,
        }

        complexity_score = (
            weights["length"] * length_score
            + weights["keywords"] * keyword_score
            + weights["structure"] * structure_score
            + weights["question_type"] * question_type_score
        )

        # Determine complexity level and mode
        if complexity_score < 0.35:
            level = ComplexityLevel.SIMPLE
            mode = QueryMode.FAST
            confidence = 0.85
        elif complexity_score < 0.65:
            level = ComplexityLevel.MODERATE
            mode = QueryMode.BALANCED
            confidence = 0.90
        else:
            level = ComplexityLevel.COMPLEX
            mode = QueryMode.DEEP
            confidence = 0.80

        # Build reasoning
        reasoning = {
            "complexity_score": round(complexity_score, 2),
            "length_score": round(length_score, 2),
            "keyword_score": round(keyword_score, 2),
            "structure_score": round(structure_score, 2),
            "question_type_score": round(question_type_score, 2),
            "factors": self._get_reasoning_factors(
                query, length_score, keyword_score, structure_score, question_type_score
            ),
        }

        return level, mode, confidence, reasoning

    def _analyze_length(self, query: str) -> float:
        """
        Analyze query length.

        Short queries (< 10 words) → 0.0 (simple)
        Medium queries (10-25 words) → 0.5 (moderate)
        Long queries (> 25 words) → 1.0 (complex)
        """
        words = query.split()
        word_count = len(words)

        if word_count < 10:
            return 0.0
        elif word_count < 25:
            return 0.5
        else:
            return 1.0

    def _analyze_keywords(self, query: str) -> float:
        """
        Analyze complexity keywords.

        Returns score from 0.0 (simple) to 1.0 (complex)
        """
        query_lower = query.lower()

        # Check for deep analysis keywords
        deep_count = sum(1 for kw in self.DEEP_KEYWORDS if kw in query_lower)
        if deep_count >= 2:
            return 1.0
        elif deep_count == 1:
            return 0.7

        # Check for factual keywords
        factual_count = sum(1 for kw in self.FACTUAL_KEYWORDS if kw in query_lower)
        if factual_count >= 1:
            return 0.2

        # Check patterns
        if self.complex_regex.search(query):
            return 0.8
        elif self.simple_regex.search(query):
            return 0.1

        return 0.5  # Default moderate

    def _analyze_structure(self, query: str) -> float:
        """
        Analyze query structure complexity.

        Multiple sentences → complex
        Multiple questions → complex
        Single simple sentence → simple
        """
        # Count sentences
        sentences = re.split(r"[.!?]+", query)
        sentence_count = len([s for s in sentences if s.strip()])

        # Count question marks
        question_count = query.count("?") + query.count("？")  # English + Korean

        # Count conjunctions (and, or, but)
        conjunction_count = len(
            re.findall(r"\b(and|or|but|그리고|또는|하지만)\b", query, re.IGNORECASE)
        )

        # Calculate structure score
        if sentence_count > 2 or question_count > 1:
            return 1.0
        elif conjunction_count >= 2:
            return 0.7
        elif conjunction_count == 1:
            return 0.4
        else:
            return 0.2

    def _analyze_question_type(self, query: str) -> float:
        """
        Analyze question type.

        Factual (what, who, when, where) → 0.0-0.3
        Explanatory (how, why) → 0.4-0.6
        Analytical (compare, evaluate) → 0.7-1.0
        """
        query_lower = query.lower()

        # Analytical questions
        analytical_patterns = [
            "compare",
            "contrast",
            "analyze",
            "evaluate",
            "assess",
            "비교",
            "대조",
            "분석",
            "평가",
        ]
        if any(pattern in query_lower for pattern in analytical_patterns):
            return 0.9

        # Explanatory questions
        explanatory_patterns = ["how", "why", "어떻게", "왜"]
        if any(pattern in query_lower for pattern in explanatory_patterns):
            return 0.5

        # Factual questions
        factual_patterns = [
            "what",
            "who",
            "when",
            "where",
            "which",
            "무엇",
            "누구",
            "언제",
            "어디",
        ]
        if any(pattern in query_lower for pattern in factual_patterns):
            return 0.2

        return 0.5  # Default moderate

    def _get_reasoning_factors(
        self,
        query: str,
        length_score: float,
        keyword_score: float,
        structure_score: float,
        question_type_score: float,
    ) -> list:
        """Get human-readable reasoning factors"""
        factors = []

        # Length factors
        word_count = len(query.split())
        if word_count < 10:
            factors.append(f"Short query ({word_count} words)")
        elif word_count > 25:
            factors.append(f"Long query ({word_count} words)")

        # Keyword factors
        if keyword_score > 0.7:
            factors.append("Contains analytical keywords (compare, analyze, evaluate)")
        elif keyword_score < 0.3:
            factors.append("Contains factual keywords (what, who, when)")

        # Structure factors
        if structure_score > 0.7:
            factors.append("Complex structure (multiple sentences or questions)")
        elif structure_score < 0.3:
            factors.append("Simple structure (single sentence)")

        # Question type factors
        if question_type_score > 0.7:
            factors.append("Analytical question type")
        elif question_type_score < 0.3:
            factors.append("Factual question type")

        return factors if factors else ["Moderate complexity query"]

    def get_mode_explanation(self, mode: QueryMode, reasoning: Dict) -> str:
        """
        Get human-readable explanation for recommended mode.

        Args:
            mode: Recommended query mode
            reasoning: Reasoning dictionary from analyze()

        Returns:
            Explanation string
        """
        if mode == QueryMode.FAST:
            return (
                f"Recommended FAST mode (~2s): Your query appears to be factual and straightforward. "
                f"Factors: {', '.join(reasoning['factors'])}"
            )
        elif mode == QueryMode.BALANCED:
            return (
                f"Recommended BALANCED mode (~5s): Your query requires moderate analysis. "
                f"You'll get a quick initial answer with progressive refinement. "
                f"Factors: {', '.join(reasoning['factors'])}"
            )
        else:  # DEEP
            return (
                f"Recommended DEEP mode (~10-15s): Your query requires comprehensive analysis. "
                f"The system will perform deep reasoning for the best answer. "
                f"Factors: {', '.join(reasoning['factors'])}"
            )


# Singleton instance
_analyzer = None


def get_analyzer() -> QueryComplexityAnalyzer:
    """Get singleton analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = QueryComplexityAnalyzer()
    return _analyzer
