"""
Response Quality Evaluator for LLM outputs.

Automatically evaluates response quality across multiple dimensions:
- Relevance: Does it answer the query?
- Accuracy: Is information correct based on sources?
- Completeness: Is the answer comprehensive?
- Clarity: Is it easy to understand?
- Source citation: Are sources properly cited?
"""

import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class QualityScore:
    """Quality evaluation score"""
    relevance: float  # 0.0-1.0
    accuracy: float  # 0.0-1.0
    completeness: float  # 0.0-1.0
    clarity: float  # 0.0-1.0
    source_citation: float  # 0.0-1.0
    overall: float  # 0.0-1.0
    issues: List[str]
    timestamp: datetime


class QualityEvaluator:
    """
    Evaluates LLM response quality automatically.
    
    Features:
    - Multi-dimensional scoring
    - Rule-based evaluation
    - Issue detection
    - Quality trends tracking
    """
    
    def __init__(
        self,
        min_acceptable_score: float = 0.7,
        enable_logging: bool = True
    ):
        """
        Initialize QualityEvaluator.
        
        Args:
            min_acceptable_score: Minimum acceptable overall score
            enable_logging: Enable quality logging
        """
        self.min_acceptable_score = min_acceptable_score
        self.enable_logging = enable_logging
        
        # Quality history for trend analysis
        self.quality_history: List[QualityScore] = []
        self.max_history_size = 1000
        
        logger.info(
            f"QualityEvaluator initialized: "
            f"min_score={min_acceptable_score}"
        )
    
    def evaluate(
        self,
        query: str,
        response: str,
        sources: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """
        Evaluate response quality.
        
        Args:
            query: User query
            response: Generated response
            sources: Source documents used
            metadata: Optional metadata
            
        Returns:
            QualityScore with detailed evaluation
        """
        issues = []
        
        # 1. Relevance: Does it answer the query?
        relevance = self._evaluate_relevance(query, response)
        if relevance < 0.5:
            issues.append("Low relevance to query")
        
        # 2. Accuracy: Based on sources
        accuracy = self._evaluate_accuracy(response, sources)
        if accuracy < 0.6:
            issues.append("Potential accuracy issues")
        
        # 3. Completeness: Is answer comprehensive?
        completeness = self._evaluate_completeness(query, response)
        if completeness < 0.5:
            issues.append("Incomplete answer")
        
        # 4. Clarity: Is it easy to understand?
        clarity = self._evaluate_clarity(response)
        if clarity < 0.6:
            issues.append("Clarity issues detected")
        
        # 5. Source citation: Are sources cited?
        source_citation = self._evaluate_source_citation(response, sources)
        if source_citation < 0.5:
            issues.append("Missing or poor source citations")
        
        # Calculate overall score (weighted average)
        overall = (
            relevance * 0.30 +
            accuracy * 0.25 +
            completeness * 0.20 +
            clarity * 0.15 +
            source_citation * 0.10
        )
        
        score = QualityScore(
            relevance=relevance,
            accuracy=accuracy,
            completeness=completeness,
            clarity=clarity,
            source_citation=source_citation,
            overall=overall,
            issues=issues,
            timestamp=datetime.now()
        )
        
        # Log if enabled
        if self.enable_logging:
            self._log_quality(score, query, response)
        
        # Add to history
        self._add_to_history(score)
        
        return score
    
    def _evaluate_relevance(self, query: str, response: str) -> float:
        """
        Evaluate relevance to query.
        
        Args:
            query: User query
            response: Generated response
            
        Returns:
            Relevance score (0.0-1.0)
        """
        if not response or len(response) < 10:
            return 0.0
        
        # Extract keywords from query
        query_words = set(re.findall(r'\w+', query.lower()))
        query_words = {w for w in query_words if len(w) > 3}  # Filter short words
        
        if not query_words:
            return 0.5  # Neutral if no keywords
        
        # Check keyword presence in response
        response_lower = response.lower()
        matched_words = sum(1 for word in query_words if word in response_lower)
        
        # Calculate relevance
        relevance = matched_words / len(query_words)
        
        # Boost if response directly addresses query
        if any(phrase in response_lower for phrase in ["according to", "based on", "the answer is"]):
            relevance = min(1.0, relevance + 0.2)
        
        return relevance
    
    def _evaluate_accuracy(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> float:
        """
        Evaluate accuracy based on sources.
        
        Args:
            response: Generated response
            sources: Source documents
            
        Returns:
            Accuracy score (0.0-1.0)
        """
        if not sources:
            return 0.5  # Neutral if no sources
        
        # Check for hallucination indicators
        hallucination_indicators = [
            "i think", "i believe", "probably", "maybe",
            "i'm not sure", "it seems", "might be"
        ]
        
        response_lower = response.lower()
        has_hallucination = any(
            indicator in response_lower 
            for indicator in hallucination_indicators
        )
        
        if has_hallucination:
            return 0.4  # Low score for uncertain language
        
        # Check for factual statements
        has_factual = any(phrase in response_lower for phrase in [
            "according to", "based on", "the document states",
            "as shown in", "research indicates"
        ])
        
        if has_factual:
            return 0.9  # High score for source-based statements
        
        # Default: moderate accuracy
        return 0.7
    
    def _evaluate_completeness(self, query: str, response: str) -> float:
        """
        Evaluate completeness of answer.
        
        Args:
            query: User query
            response: Generated response
            
        Returns:
            Completeness score (0.0-1.0)
        """
        if not response:
            return 0.0
        
        # Check response length (proxy for completeness)
        word_count = len(response.split())
        
        if word_count < 20:
            return 0.3  # Too short
        elif word_count < 50:
            return 0.6  # Brief
        elif word_count < 150:
            return 0.8  # Good
        else:
            return 0.9  # Comprehensive
    
    def _evaluate_clarity(self, response: str) -> float:
        """
        Evaluate clarity of response.
        
        Args:
            response: Generated response
            
        Returns:
            Clarity score (0.0-1.0)
        """
        if not response:
            return 0.0
        
        clarity_score = 1.0
        
        # Check for overly long sentences
        sentences = re.split(r'[.!?]+', response)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        if avg_sentence_length > 30:
            clarity_score -= 0.2  # Penalize long sentences
        
        # Check for structure (paragraphs, sections)
        has_structure = any(marker in response for marker in [
            "##", "\n\n", "1.", "2.", "-", "•"
        ])
        
        if has_structure:
            clarity_score += 0.1  # Reward structure
        
        # Check for jargon overload
        complex_words = len(re.findall(r'\w{12,}', response))
        total_words = len(response.split())
        
        if total_words > 0 and complex_words / total_words > 0.15:
            clarity_score -= 0.1  # Penalize jargon
        
        return max(0.0, min(1.0, clarity_score))
    
    def _evaluate_source_citation(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> float:
        """
        Evaluate source citation quality.
        
        Args:
            response: Generated response
            sources: Source documents
            
        Returns:
            Citation score (0.0-1.0)
        """
        if not sources:
            return 0.5  # Neutral if no sources
        
        # Check for citation markers
        citation_patterns = [
            r'\[Source:',
            r'\[Web\]',
            r'\[Internal\]',
            r'according to',
            r'based on',
            r'as stated in'
        ]
        
        citations_found = sum(
            1 for pattern in citation_patterns
            if re.search(pattern, response, re.IGNORECASE)
        )
        
        # Calculate score
        if citations_found == 0:
            return 0.2  # No citations
        elif citations_found == 1:
            return 0.6  # Some citations
        else:
            return 0.9  # Good citations
    
    def _log_quality(
        self,
        score: QualityScore,
        query: str,
        response: str
    ) -> None:
        """Log quality evaluation"""
        if score.overall < self.min_acceptable_score:
            logger.warning(
                f"Low quality response detected: "
                f"overall={score.overall:.2f}, "
                f"issues={score.issues}, "
                f"query='{query[:50]}...'"
            )
        else:
            logger.info(
                f"Quality evaluation: overall={score.overall:.2f}, "
                f"relevance={score.relevance:.2f}, "
                f"accuracy={score.accuracy:.2f}"
            )
    
    def _add_to_history(self, score: QualityScore) -> None:
        """Add score to history"""
        self.quality_history.append(score)
        
        # Limit history size
        if len(self.quality_history) > self.max_history_size:
            self.quality_history = self.quality_history[-self.max_history_size:]
    
    def get_quality_trends(
        self,
        last_n: int = 100
    ) -> Dict[str, Any]:
        """
        Get quality trends from recent evaluations.
        
        Args:
            last_n: Number of recent evaluations to analyze
            
        Returns:
            Trend statistics
        """
        if not self.quality_history:
            return {
                "count": 0,
                "average_overall": 0.0,
                "trend": "no_data"
            }
        
        recent = self.quality_history[-last_n:]
        
        avg_overall = sum(s.overall for s in recent) / len(recent)
        avg_relevance = sum(s.relevance for s in recent) / len(recent)
        avg_accuracy = sum(s.accuracy for s in recent) / len(recent)
        avg_completeness = sum(s.completeness for s in recent) / len(recent)
        avg_clarity = sum(s.clarity for s in recent) / len(recent)
        avg_citation = sum(s.source_citation for s in recent) / len(recent)
        
        # Calculate trend (improving/declining/stable)
        if len(recent) >= 10:
            first_half = recent[:len(recent)//2]
            second_half = recent[len(recent)//2:]
            
            first_avg = sum(s.overall for s in first_half) / len(first_half)
            second_avg = sum(s.overall for s in second_half) / len(second_half)
            
            if second_avg > first_avg + 0.05:
                trend = "improving"
            elif second_avg < first_avg - 0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        # Count issues
        all_issues = [issue for score in recent for issue in score.issues]
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        return {
            "count": len(recent),
            "average_overall": avg_overall,
            "average_relevance": avg_relevance,
            "average_accuracy": avg_accuracy,
            "average_completeness": avg_completeness,
            "average_clarity": avg_clarity,
            "average_citation": avg_citation,
            "trend": trend,
            "common_issues": sorted(
                issue_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


# Singleton instance
_quality_evaluator: Optional[QualityEvaluator] = None


def get_quality_evaluator(
    min_acceptable_score: float = 0.7
) -> QualityEvaluator:
    """
    Get or create global QualityEvaluator instance.
    
    Args:
        min_acceptable_score: Minimum acceptable score
        
    Returns:
        QualityEvaluator instance
    """
    global _quality_evaluator
    
    if _quality_evaluator is None:
        _quality_evaluator = QualityEvaluator(
            min_acceptable_score=min_acceptable_score
        )
    
    return _quality_evaluator
