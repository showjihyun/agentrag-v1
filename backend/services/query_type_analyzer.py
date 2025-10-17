# Query Type Analyzer for Smart Search Selection
import re
import logging
from typing import Literal
from dataclasses import dataclass

logger = logging.getLogger(__name__)

QueryType = Literal["keyword", "semantic", "comparison", "technical"]


@dataclass
class QueryTypeAnalysis:
    """Query type analysis result"""

    query_type: QueryType
    confidence: float
    reasoning: str
    use_hybrid: bool


class QueryTypeAnalyzer:
    """
    Analyzes query type to determine optimal search strategy.

    Query Types:
    - keyword: Version numbers, error codes, exact terms
    - semantic: Conceptual questions, explanations
    - comparison: "vs", "compare", "difference"
    - technical: Code, APIs, technical terms
    """

    def __init__(self):
        # Keyword patterns (exact matching important)
        self.keyword_patterns = [
            (r"\d+\.\d+(\.\d+)?", "version_number"),  # 3.11, 1.0.0
            (r"error\s*\d+|exception|traceback", "error_code"),
            (r"[A-Z]{2,}(?:\s+[A-Z]{2,})*", "acronym"),  # API, HTTP, REST
            (r'`[^`]+`|"[^"]+"', "code_snippet"),
            (r"--\w+|-\w+", "cli_flag"),  # --help, -v
        ]

        # Comparison patterns
        self.comparison_patterns = [
            r"\bvs\b|\bversus\b",
            r"\bcompare\b|\bcomparison\b",
            r"\bdifference\b|\bdifferent\b",
            r"\bbetter\b|\bworse\b",
            r"\bor\b.*\bor\b",  # "A or B"
        ]

        # Technical patterns
        self.technical_patterns = [
            r"\bfunction\b|\bmethod\b|\bclass\b",
            r"\bimport\b|\bexport\b",
            r"\bAPI\b|\bSDK\b|\bCLI\b",
            r"\bconfig\b|\bconfiguration\b",
            r"\binstall\b|\bsetup\b",
        ]

        # Semantic patterns (conceptual)
        self.semantic_patterns = [
            r"\bwhat\s+is\b|\bwhat\s+are\b",
            r"\bhow\s+does\b|\bhow\s+do\b",
            r"\bwhy\b|\bexplain\b",
            r"\bunderstand\b|\bconcept\b",
            r"\blearn\b|\bteach\b",
        ]

    def analyze(self, query: str) -> QueryTypeAnalysis:
        """
        Analyze query type and determine if hybrid search should be used.

        Args:
            query: User query string

        Returns:
            QueryTypeAnalysis with type, confidence, and recommendation
        """
        query_lower = query.lower()

        # Score each type
        keyword_score = self._score_keyword(query, query_lower)
        comparison_score = self._score_comparison(query_lower)
        technical_score = self._score_technical(query_lower)
        semantic_score = self._score_semantic(query_lower)

        # Determine primary type
        scores = {
            "keyword": keyword_score,
            "comparison": comparison_score,
            "technical": technical_score,
            "semantic": semantic_score,
        }

        max_score = max(scores.values())
        query_type = max(scores, key=scores.get)
        confidence = max_score

        # Determine if hybrid search should be used
        # Use hybrid for keyword, comparison, and technical queries
        use_hybrid = query_type in ["keyword", "comparison", "technical"]

        # Build reasoning
        reasoning = self._build_reasoning(query_type, scores)

        logger.info(
            f"Query type: {query_type} (confidence: {confidence:.2f}), "
            f"use_hybrid: {use_hybrid}"
        )

        return QueryTypeAnalysis(
            query_type=query_type,
            confidence=confidence,
            reasoning=reasoning,
            use_hybrid=use_hybrid,
        )

    def _score_keyword(self, query: str, query_lower: str) -> float:
        """Score keyword query likelihood"""
        score = 0.0
        matches = []

        for pattern, pattern_type in self.keyword_patterns:
            if re.search(pattern, query):
                score += 0.3
                matches.append(pattern_type)

        # Boost if multiple keyword indicators
        if len(matches) > 1:
            score += 0.2

        return min(score, 1.0)

    def _score_comparison(self, query_lower: str) -> float:
        """Score comparison query likelihood"""
        score = 0.0

        for pattern in self.comparison_patterns:
            if re.search(pattern, query_lower):
                score += 0.4

        return min(score, 1.0)

    def _score_technical(self, query_lower: str) -> float:
        """Score technical query likelihood"""
        score = 0.0

        for pattern in self.technical_patterns:
            if re.search(pattern, query_lower):
                score += 0.25

        return min(score, 1.0)

    def _score_semantic(self, query_lower: str) -> float:
        """Score semantic query likelihood"""
        score = 0.3  # Base score for semantic

        for pattern in self.semantic_patterns:
            if re.search(pattern, query_lower):
                score += 0.2

        return min(score, 1.0)

    def _build_reasoning(self, query_type: str, scores: dict) -> str:
        """Build reasoning explanation"""
        if query_type == "keyword":
            return "Query contains specific terms, versions, or codes requiring exact matching"
        elif query_type == "comparison":
            return "Query asks for comparison between options"
        elif query_type == "technical":
            return "Query involves technical terms or code"
        else:
            return "Query is conceptual and benefits from semantic understanding"


# Global analyzer instance
_analyzer: QueryTypeAnalyzer = None


def get_query_type_analyzer() -> QueryTypeAnalyzer:
    """Get global query type analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = QueryTypeAnalyzer()
    return _analyzer
