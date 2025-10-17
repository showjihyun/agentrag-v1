# Advanced Query Analysis Service
import re
import logging
from typing import Dict, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """Query analysis result"""

    complexity_score: float  # 0.0 - 1.0
    query_type: str  # factual, analytical, conversational, multi-step
    requires_reasoning: bool
    requires_multiple_sources: bool
    estimated_tokens: int
    keywords: List[str]
    entities: List[str]
    recommended_mode: str  # fast, balanced, deep


class QueryAnalyzer:
    """
    Analyzes queries to determine complexity and optimal processing strategy.

    Improvements over basic complexity analysis:
    - Detects query intent and type
    - Identifies entities and keywords
    - Estimates token usage
    - Provides mode recommendations with confidence
    """

    def __init__(self):
        # Patterns for different query types
        self.factual_patterns = [
            r"\b(what is|who is|when|where|which|define|explain)\b",
            r"\b(how many|how much|how long)\b",
        ]

        self.analytical_patterns = [
            r"\b(why|how|analyze|compare|evaluate|assess)\b",
            r"\b(difference|similarity|relationship|impact|effect)\b",
            r"\b(pros and cons|advantages|disadvantages)\b",
        ]

        self.multi_step_patterns = [
            r"\b(first|then|next|finally|step by step)\b",
            r"\b(and then|after that|following)\b",
            r"\b(multiple|several|various)\b",
        ]

        # Complexity indicators
        self.complexity_indicators = {
            "high": [
                r"\b(comprehensive|detailed|in-depth|thorough)\b",
                r"\b(all|every|complete|entire)\b",
                r"\b(analyze|synthesize|evaluate|critique)\b",
            ],
            "medium": [
                r"\b(explain|describe|discuss|compare)\b",
                r"\b(some|few|several)\b",
            ],
            "low": [
                r"\b(what|who|when|where|list)\b",
                r"\b(simple|quick|brief)\b",
            ],
        }

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Perform comprehensive query analysis.

        Args:
            query: User query string

        Returns:
            QueryAnalysis with detailed insights
        """
        query_lower = query.lower()

        # Calculate complexity score
        complexity_score = self._calculate_complexity(query_lower)

        # Determine query type
        query_type = self._determine_query_type(query_lower)

        # Check if reasoning is required
        requires_reasoning = self._requires_reasoning(query_lower)

        # Check if multiple sources needed
        requires_multiple_sources = self._requires_multiple_sources(query_lower)

        # Estimate token usage
        estimated_tokens = self._estimate_tokens(query)

        # Extract keywords and entities
        keywords = self._extract_keywords(query)
        entities = self._extract_entities(query)

        # Recommend mode
        recommended_mode = self._recommend_mode(
            complexity_score, query_type, requires_reasoning, requires_multiple_sources
        )

        return QueryAnalysis(
            complexity_score=complexity_score,
            query_type=query_type,
            requires_reasoning=requires_reasoning,
            requires_multiple_sources=requires_multiple_sources,
            estimated_tokens=estimated_tokens,
            keywords=keywords,
            entities=entities,
            recommended_mode=recommended_mode,
        )

    def _calculate_complexity(self, query: str) -> float:
        """Calculate query complexity score (0.0 - 1.0)"""
        score = 0.3  # Base score

        # Length factor
        word_count = len(query.split())
        if word_count > 20:
            score += 0.2
        elif word_count > 10:
            score += 0.1

        # Complexity indicators
        for level, patterns in self.complexity_indicators.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    if level == "high":
                        score += 0.15
                    elif level == "medium":
                        score += 0.08
                    elif level == "low":
                        score -= 0.05

        # Question marks (multiple questions = more complex)
        question_count = query.count("?")
        if question_count > 1:
            score += 0.1 * (question_count - 1)

        # Conjunctions (indicates multi-part query)
        conjunctions = len(re.findall(r"\b(and|or|but|also|additionally)\b", query))
        score += 0.05 * conjunctions

        return min(max(score, 0.0), 1.0)

    def _determine_query_type(self, query: str) -> str:
        """Determine the type of query"""
        # Check for multi-step
        for pattern in self.multi_step_patterns:
            if re.search(pattern, query):
                return "multi-step"

        # Check for analytical
        for pattern in self.analytical_patterns:
            if re.search(pattern, query):
                return "analytical"

        # Check for factual
        for pattern in self.factual_patterns:
            if re.search(pattern, query):
                return "factual"

        # Default to conversational
        return "conversational"

    def _requires_reasoning(self, query: str) -> bool:
        """Check if query requires reasoning"""
        reasoning_keywords = [
            "why",
            "how",
            "explain",
            "reason",
            "cause",
            "analyze",
            "evaluate",
            "compare",
            "contrast",
        ]

        return any(keyword in query for keyword in reasoning_keywords)

    def _requires_multiple_sources(self, query: str) -> bool:
        """Check if query requires multiple sources"""
        multi_source_keywords = [
            "compare",
            "contrast",
            "different",
            "various",
            "multiple",
            "all",
            "comprehensive",
            "complete",
        ]

        return any(keyword in query for keyword in multi_source_keywords)

    def _estimate_tokens(self, query: str) -> int:
        """Estimate token count for query processing"""
        # Rough estimation: 1 token ≈ 0.75 words
        word_count = len(query.split())
        base_tokens = int(word_count / 0.75)

        # Add overhead for system prompts and context
        overhead = 500  # Base overhead

        return base_tokens + overhead

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove common stop words
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
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
        }

        words = re.findall(r"\b\w+\b", query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords[:10]  # Return top 10

    def _extract_entities(self, query: str) -> List[str]:
        """Extract potential entities (capitalized words)"""
        # Simple entity extraction - look for capitalized words
        entities = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", query)

        return list(set(entities))[:5]  # Return top 5 unique

    def _recommend_mode(
        self,
        complexity_score: float,
        query_type: str,
        requires_reasoning: bool,
        requires_multiple_sources: bool,
    ) -> str:
        """Recommend optimal processing mode"""
        # Deep mode conditions
        if complexity_score > 0.7:
            return "deep"

        if query_type == "multi-step":
            return "deep"

        if requires_reasoning and requires_multiple_sources:
            return "deep"

        # Fast mode conditions
        if complexity_score < 0.35:
            return "fast"

        if query_type == "factual" and not requires_reasoning:
            return "fast"

        # Default to balanced
        return "balanced"


# Global analyzer instance
_query_analyzer: QueryAnalyzer = None


def get_query_analyzer() -> QueryAnalyzer:
    """Get global query analyzer instance"""
    global _query_analyzer
    if _query_analyzer is None:
        _query_analyzer = QueryAnalyzer()
    return _query_analyzer
