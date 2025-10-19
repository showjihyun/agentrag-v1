"""
Context Optimizer for LLM calls.

Provides utilities to optimize context sent to LLM by:
- Filtering low-relevance documents
- Extracting relevant snippets
- Removing duplicates
- Managing token budgets
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OptimizedContext:
    """Result of context optimization."""

    context: str
    num_documents: int
    estimated_tokens: int
    filtered_count: int
    truncated_count: int
    metadata: Dict[str, Any]


class ContextOptimizer:
    """
    Optimizes context for LLM calls to reduce token usage while maintaining quality.

    Features:
    - Relevance-based filtering
    - Snippet extraction
    - Deduplication
    - Token budget management
    """

    def __init__(
        self,
        min_relevance_score: float = 0.5,
        max_docs: int = 5,
        max_chars_per_doc: int = 1000,
        chars_per_token: float = 4.0,  # Approximate
    ):
        """
        Initialize ContextOptimizer.

        Args:
            min_relevance_score: Minimum score to include document
            max_docs: Maximum number of documents to include
            max_chars_per_doc: Maximum characters per document
            chars_per_token: Approximate characters per token
        """
        self.min_relevance_score = min_relevance_score
        self.max_docs = max_docs
        self.max_chars_per_doc = max_chars_per_doc
        self.chars_per_token = chars_per_token

        logger.info(
            f"ContextOptimizer initialized: "
            f"min_score={min_relevance_score}, "
            f"max_docs={max_docs}, "
            f"max_chars={max_chars_per_doc}"
        )

    def filter_by_relevance(
        self,
        results: List[Any],
        min_score: Optional[float] = None,
        max_docs: Optional[int] = None,
        dynamic_threshold: bool = True
    ) -> List[Any]:
        """
        Filter search results by relevance score with dynamic thresholding.

        Args:
            results: List of search results with 'score' attribute
            min_score: Minimum score threshold (uses default if None)
            max_docs: Maximum documents to return (uses default if None)
            dynamic_threshold: Use dynamic threshold based on score distribution

        Returns:
            Filtered list of results
        """
        if not results:
            return []
        
        min_score = min_score if min_score is not None else self.min_relevance_score
        max_docs = max_docs if max_docs is not None else self.max_docs

        # Dynamic threshold: adjust based on score distribution
        if dynamic_threshold and len(results) > 1:
            scores = [r.score for r in results]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            
            # If top score is significantly higher, use stricter threshold
            if max_score > avg_score * 1.5:
                # Use higher threshold for high-quality results
                dynamic_min = max(min_score, avg_score * 0.8)
                logger.debug(
                    f"Dynamic threshold: {dynamic_min:.3f} "
                    f"(avg={avg_score:.3f}, max={max_score:.3f})"
                )
                min_score = dynamic_min

        # Filter by score
        filtered = [r for r in results if r.score >= min_score]

        # Limit to max_docs
        filtered = filtered[:max_docs]

        logger.debug(
            f"Filtered {len(results)} → {len(filtered)} documents "
            f"(min_score={min_score:.3f}, max_docs={max_docs})"
        )

        return filtered

    def truncate_text(
        self,
        text: str,
        max_length: Optional[int] = None,
        preserve_sentences: bool = True,
    ) -> Tuple[str, bool]:
        """
        Truncate text to maximum length.

        Args:
            text: Text to truncate
            max_length: Maximum length (uses default if None)
            preserve_sentences: Try to preserve complete sentences

        Returns:
            Tuple of (truncated_text, was_truncated)
        """
        max_length = max_length if max_length is not None else self.max_chars_per_doc

        if len(text) <= max_length:
            return text, False

        if preserve_sentences:
            # Try to truncate at sentence boundary
            truncated = text[:max_length]

            # Find last sentence ending
            last_period = truncated.rfind(".")
            last_question = truncated.rfind("?")
            last_exclamation = truncated.rfind("!")

            last_sentence_end = max(last_period, last_question, last_exclamation)

            if last_sentence_end > max_length * 0.7:  # At least 70% of max_length
                truncated = truncated[: last_sentence_end + 1]
            else:
                # No good sentence boundary, just truncate
                truncated = truncated + "..."
        else:
            truncated = text[:max_length] + "..."

        return truncated, True

    def extract_relevant_snippet(
        self,
        text: str,
        query: str,
        max_length: Optional[int] = None,
        context_window: int = 200,
    ) -> str:
        """
        Extract most relevant snippet from text based on query.

        Args:
            text: Full text
            query: Query to find relevant parts
            max_length: Maximum snippet length
            context_window: Characters to include around match

        Returns:
            Relevant snippet
        """
        max_length = max_length if max_length is not None else self.max_chars_per_doc

        # If text is short enough, return as is
        if len(text) <= max_length:
            return text

        # Extract query keywords (simple approach)
        query_lower = query.lower()
        query_words = set(re.findall(r"\w+", query_lower))

        # Find best matching position
        text_lower = text.lower()
        best_pos = 0
        best_score = 0

        # Sliding window to find best match
        window_size = min(max_length, len(text))
        step = window_size // 4  # 25% overlap

        for pos in range(0, len(text) - window_size + 1, step):
            window = text_lower[pos : pos + window_size]

            # Count matching query words
            score = sum(1 for word in query_words if word in window)

            if score > best_score:
                best_score = score
                best_pos = pos

        # Extract snippet
        snippet_start = max(0, best_pos)
        snippet_end = min(len(text), best_pos + max_length)
        snippet = text[snippet_start:snippet_end]

        # Add ellipsis if truncated
        if snippet_start > 0:
            snippet = "..." + snippet
        if snippet_end < len(text):
            snippet = snippet + "..."

        return snippet

    def deduplicate_documents(
        self, results: List[Any], similarity_threshold: float = 0.9
    ) -> List[Any]:
        """
        Remove duplicate or highly similar documents.

        Args:
            results: List of search results
            similarity_threshold: Similarity threshold for deduplication

        Returns:
            Deduplicated list
        """
        if not results:
            return results

        deduplicated = [results[0]]  # Always keep first (highest score)

        for result in results[1:]:
            is_duplicate = False

            for existing in deduplicated:
                # Simple similarity check based on text overlap
                similarity = self._calculate_text_similarity(result.text, existing.text)

                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduplicated.append(result)

        logger.debug(
            f"Deduplicated {len(results)} → {len(deduplicated)} documents "
            f"(threshold={similarity_threshold})"
        )

        return deduplicated

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity (Jaccard similarity of words).

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Extract words
        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))

        if not words1 or not words2:
            return 0.0

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def optimize_context(
        self,
        results: List[Any],
        query: str,
        max_tokens: Optional[int] = None,
        enable_deduplication: bool = True,
        enable_snippet_extraction: bool = False,
    ) -> OptimizedContext:
        """
        Optimize context for LLM by applying all optimization strategies.

        Args:
            results: Search results
            query: User query
            max_tokens: Maximum tokens for context
            enable_deduplication: Whether to remove duplicates
            enable_snippet_extraction: Whether to extract snippets

        Returns:
            OptimizedContext with optimized context string and metadata
        """
        original_count = len(results)

        # Step 1: Filter by relevance
        filtered = self.filter_by_relevance(results)
        filtered_count = original_count - len(filtered)

        # Step 2: Deduplicate
        if enable_deduplication:
            filtered = self.deduplicate_documents(filtered)

        # Step 3: Process each document
        context_parts = []
        truncated_count = 0

        for i, result in enumerate(filtered):
            if enable_snippet_extraction:
                # Extract relevant snippet
                text = self.extract_relevant_snippet(
                    result.text, query, max_length=self.max_chars_per_doc
                )
                was_truncated = len(text) < len(result.text)
            else:
                # Just truncate
                text, was_truncated = self.truncate_text(result.text)

            if was_truncated:
                truncated_count += 1

            # Format without unnecessary metadata
            context_parts.append(text)

        # Combine context
        context = "\n\n".join(context_parts)

        # Estimate tokens
        estimated_tokens = len(context) / self.chars_per_token

        # Create result
        optimized = OptimizedContext(
            context=context,
            num_documents=len(filtered),
            estimated_tokens=int(estimated_tokens),
            filtered_count=filtered_count,
            truncated_count=truncated_count,
            metadata={
                "original_count": original_count,
                "final_count": len(filtered),
                "deduplication_enabled": enable_deduplication,
                "snippet_extraction_enabled": enable_snippet_extraction,
                "avg_chars_per_doc": len(context) // len(filtered) if filtered else 0,
            },
        )

        logger.info(
            f"Context optimized: {original_count} docs → {len(filtered)} docs, "
            f"~{optimized.estimated_tokens} tokens "
            f"(filtered={filtered_count}, truncated={truncated_count})"
        )

        return optimized


# Singleton instance
_context_optimizer: Optional[ContextOptimizer] = None


def get_context_optimizer(
    min_relevance_score: float = 0.5, max_docs: int = 5, max_chars_per_doc: int = 1000
) -> ContextOptimizer:
    """
    Get or create global ContextOptimizer instance.

    Args:
        min_relevance_score: Minimum relevance score
        max_docs: Maximum documents
        max_chars_per_doc: Maximum characters per document

    Returns:
        ContextOptimizer instance
    """
    global _context_optimizer

    if _context_optimizer is None:
        _context_optimizer = ContextOptimizer(
            min_relevance_score=min_relevance_score,
            max_docs=max_docs,
            max_chars_per_doc=max_chars_per_doc,
        )

    return _context_optimizer
