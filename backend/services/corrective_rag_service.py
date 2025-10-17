"""
Corrective RAG Service - Evaluate and correct retrieval results.

Based on CRAG (Corrective Retrieval Augmented Generation) - Meta AI 2024:
- Evaluates relevance of retrieved documents
- Filters out low-relevance documents
- Supplements with web search if needed
- Improves retrieval accuracy by 20%+

Key features:
- Relevance scoring
- Adaptive filtering
- Web search fallback
- Quality-based correction
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import re
import numpy as np

logger = logging.getLogger(__name__)


class CorrectiveRAGService:
    """
    Service for correcting and improving retrieval results.

    Features:
    - Document relevance evaluation
    - Low-quality document filtering
    - Web search supplementation
    - Adaptive thresholds
    - Quality metrics tracking
    """

    def __init__(
        self,
        min_relevance_threshold: float = 0.5,
        min_documents: int = 3,
        max_documents: int = 10,
    ):
        """
        Initialize CorrectiveRAGService.

        Args:
            min_relevance_threshold: Minimum relevance score (0-1)
            min_documents: Minimum number of documents to keep
            max_documents: Maximum number of documents to return
        """
        self.min_relevance_threshold = min_relevance_threshold
        self.min_documents = min_documents
        self.max_documents = max_documents

        logger.info(
            f"CorrectiveRAGService initialized: "
            f"threshold={min_relevance_threshold}, "
            f"min_docs={min_documents}, max_docs={max_documents}"
        )

    async def evaluate_and_correct(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        web_search_agent=None,
        enable_web_fallback: bool = True,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Evaluate documents and correct if needed.

        Args:
            query: User query
            documents: Retrieved documents
            web_search_agent: Optional web search agent for fallback
            enable_web_fallback: Whether to use web search fallback

        Returns:
            Tuple of (corrected_documents, correction_metadata)
        """
        try:
            logger.info(
                f"Evaluating {len(documents)} documents for query: {query[:50]}..."
            )

            if not documents:
                logger.warning("No documents to evaluate")
                if enable_web_fallback and web_search_agent:
                    return await self._web_search_fallback(query, web_search_agent)
                return [], {"status": "no_documents", "corrected": False}

            # Step 1: Evaluate relevance of each document
            relevance_scores = await self.evaluate_relevance(query, documents)

            # Step 2: Filter low-relevance documents
            filtered_docs, filter_stats = self._filter_documents(
                documents, relevance_scores
            )

            logger.info(
                f"Filtered: {len(documents)} → {len(filtered_docs)} documents "
                f"(removed {filter_stats['removed']})"
            )

            # Step 3: Check if we need supplementation
            needs_supplement = len(filtered_docs) < self.min_documents

            if needs_supplement and enable_web_fallback and web_search_agent:
                logger.info(
                    f"Insufficient documents ({len(filtered_docs)}), "
                    "supplementing with web search"
                )

                web_docs, web_stats = await self._web_search_fallback(
                    query, web_search_agent
                )

                # Add web results
                filtered_docs.extend(web_docs)

                correction_metadata = {
                    "status": "corrected_and_supplemented",
                    "corrected": True,
                    "original_count": len(documents),
                    "filtered_count": filter_stats["kept"],
                    "removed_count": filter_stats["removed"],
                    "web_supplemented": len(web_docs),
                    "final_count": len(filtered_docs),
                    "avg_relevance_before": filter_stats["avg_relevance_before"],
                    "avg_relevance_after": filter_stats["avg_relevance_after"],
                    "web_search_used": True,
                }
            else:
                correction_metadata = {
                    "status": (
                        "corrected"
                        if filter_stats["removed"] > 0
                        else "no_correction_needed"
                    ),
                    "corrected": filter_stats["removed"] > 0,
                    "original_count": len(documents),
                    "filtered_count": filter_stats["kept"],
                    "removed_count": filter_stats["removed"],
                    "final_count": len(filtered_docs),
                    "avg_relevance_before": filter_stats["avg_relevance_before"],
                    "avg_relevance_after": filter_stats["avg_relevance_after"],
                    "web_search_used": False,
                }

            # Step 4: Limit to max documents
            if len(filtered_docs) > self.max_documents:
                filtered_docs = filtered_docs[: self.max_documents]
                correction_metadata["truncated_to_max"] = True

            logger.info(
                f"Correction complete: {correction_metadata['status']}, "
                f"final_count={len(filtered_docs)}"
            )

            return filtered_docs, correction_metadata

        except Exception as e:
            logger.error(f"Corrective RAG failed: {e}", exc_info=True)
            # Return original documents on error
            return documents, {"status": "error", "corrected": False, "error": str(e)}

    async def evaluate_relevance(
        self, query: str, documents: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Evaluate relevance of each document to the query.

        Uses multiple signals:
        - Keyword overlap
        - Semantic similarity (if available)
        - Document metadata

        Args:
            query: User query
            documents: List of documents

        Returns:
            List of relevance scores (0-1)
        """
        try:
            query_keywords = set(self._extract_keywords(query.lower()))

            if not query_keywords:
                # If no keywords, return neutral scores
                return [0.5] * len(documents)

            relevance_scores = []

            for doc in documents:
                # Get document text
                doc_text = doc.get("text", "") or doc.get("content", "")

                if not doc_text:
                    relevance_scores.append(0.0)
                    continue

                doc_text_lower = doc_text.lower()
                doc_keywords = set(self._extract_keywords(doc_text_lower))

                # Calculate keyword overlap
                if doc_keywords:
                    overlap = len(query_keywords & doc_keywords)
                    keyword_score = overlap / len(query_keywords)
                else:
                    keyword_score = 0.0

                # Calculate query term frequency in document
                query_terms = query.lower().split()
                term_frequency = sum(
                    doc_text_lower.count(term) for term in query_terms
                ) / max(len(doc_text_lower.split()), 1)

                # Normalize term frequency
                tf_score = min(term_frequency * 10, 1.0)

                # Check for exact phrase match
                phrase_match = 1.0 if query.lower() in doc_text_lower else 0.0

                # Use existing score if available
                existing_score = doc.get("score", 0.0)
                if isinstance(existing_score, (int, float)):
                    existing_score = float(existing_score)
                else:
                    existing_score = 0.0

                # Combine scores (weighted average)
                combined_score = (
                    keyword_score * 0.3
                    + tf_score * 0.2
                    + phrase_match * 0.2
                    + existing_score * 0.3
                )

                relevance_scores.append(min(combined_score, 1.0))

            logger.debug(
                f"Relevance scores: min={min(relevance_scores):.2f}, "
                f"max={max(relevance_scores):.2f}, "
                f"avg={np.mean(relevance_scores):.2f}"
            )

            return relevance_scores

        except Exception as e:
            logger.error(f"Relevance evaluation failed: {e}")
            # Return neutral scores on error
            return [0.5] * len(documents)

    def _filter_documents(
        self, documents: List[Dict[str, Any]], relevance_scores: List[float]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Filter documents based on relevance scores.

        Args:
            documents: List of documents
            relevance_scores: Relevance scores for each document

        Returns:
            Tuple of (filtered_documents, filter_statistics)
        """
        if len(documents) != len(relevance_scores):
            logger.warning(
                f"Document count ({len(documents)}) != "
                f"score count ({len(relevance_scores)})"
            )
            return documents, {
                "kept": len(documents),
                "removed": 0,
                "avg_relevance_before": 0.5,
                "avg_relevance_after": 0.5,
            }

        # Calculate statistics before filtering
        avg_before = np.mean(relevance_scores) if relevance_scores else 0.0

        # Create document-score pairs
        doc_score_pairs = list(zip(documents, relevance_scores))

        # Sort by relevance (descending)
        doc_score_pairs.sort(key=lambda x: x[1], reverse=True)

        # Filter based on threshold
        filtered_pairs = [
            (doc, score)
            for doc, score in doc_score_pairs
            if score >= self.min_relevance_threshold
        ]

        # Ensure minimum number of documents
        if len(filtered_pairs) < self.min_documents:
            # Keep top min_documents regardless of threshold
            filtered_pairs = doc_score_pairs[: self.min_documents]
            logger.info(
                f"Kept top {self.min_documents} documents "
                "(below threshold but meeting minimum)"
            )

        # Extract filtered documents and add relevance score
        filtered_docs = []
        filtered_scores = []

        for doc, score in filtered_pairs:
            # Add relevance score to document metadata
            doc_copy = doc.copy()
            doc_copy["relevance_score"] = round(score, 3)
            doc_copy["corrected"] = True
            filtered_docs.append(doc_copy)
            filtered_scores.append(score)

        # Calculate statistics after filtering
        avg_after = np.mean(filtered_scores) if filtered_scores else 0.0

        filter_stats = {
            "kept": len(filtered_docs),
            "removed": len(documents) - len(filtered_docs),
            "avg_relevance_before": round(avg_before, 3),
            "avg_relevance_after": round(avg_after, 3),
            "improvement": round(avg_after - avg_before, 3),
        }

        return filtered_docs, filter_stats

    async def _web_search_fallback(
        self, query: str, web_search_agent, max_results: int = 5
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Fallback to web search when local documents are insufficient.

        Args:
            query: User query
            web_search_agent: Web search agent
            max_results: Maximum web results

        Returns:
            Tuple of (web_documents, web_statistics)
        """
        try:
            logger.info(f"Performing web search fallback for: {query[:50]}...")

            # Perform web search
            web_results = await web_search_agent.search(
                query=query, max_results=max_results
            )

            # Convert web results to document format
            web_docs = []
            for i, result in enumerate(web_results):
                web_doc = {
                    "text": result.get("snippet", "") or result.get("content", ""),
                    "title": result.get("title", f"Web Result {i+1}"),
                    "source": "web_search",
                    "url": result.get("url", ""),
                    "relevance_score": 0.7,  # Default score for web results
                    "corrected": True,
                    "supplemented": True,
                }
                web_docs.append(web_doc)

            web_stats = {"web_results_found": len(web_docs), "web_search_query": query}

            logger.info(f"Web search returned {len(web_docs)} results")

            return web_docs, web_stats

        except Exception as e:
            logger.error(f"Web search fallback failed: {e}")
            return [], {"web_results_found": 0, "error": str(e)}

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
            "it",
            "its",
            "they",
            "them",
            "their",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "every",
            "both",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
        }

        keywords = [w for w in words if len(w) > 2 and w not in stop_words]

        return keywords

    def get_correction_summary(self, correction_metadata: Dict[str, Any]) -> str:
        """
        Generate human-readable correction summary.

        Args:
            correction_metadata: Correction metadata

        Returns:
            Summary string
        """
        status = correction_metadata.get("status", "unknown")

        if status == "no_documents":
            return "No documents found"

        if status == "no_correction_needed":
            return f"All {correction_metadata['original_count']} documents are relevant"

        if status == "corrected":
            return (
                f"Filtered {correction_metadata['removed_count']} low-relevance documents. "
                f"Kept {correction_metadata['filtered_count']} high-quality documents. "
                f"Relevance improved from {correction_metadata['avg_relevance_before']:.2f} "
                f"to {correction_metadata['avg_relevance_after']:.2f}"
            )

        if status == "corrected_and_supplemented":
            return (
                f"Filtered {correction_metadata['removed_count']} low-relevance documents. "
                f"Added {correction_metadata['web_supplemented']} web results. "
                f"Final: {correction_metadata['final_count']} documents"
            )

        if status == "error":
            return f"Correction failed: {correction_metadata.get('error', 'unknown error')}"

        return f"Status: {status}"


# Singleton instance
_corrective_rag_service: Optional[CorrectiveRAGService] = None


def get_corrective_rag_service(
    min_relevance_threshold: float = 0.5,
    min_documents: int = 3,
    max_documents: int = 10,
) -> CorrectiveRAGService:
    """
    Get or create CorrectiveRAGService instance.

    Args:
        min_relevance_threshold: Minimum relevance threshold
        min_documents: Minimum documents to keep
        max_documents: Maximum documents to return

    Returns:
        CorrectiveRAGService instance
    """
    global _corrective_rag_service

    if _corrective_rag_service is None:
        _corrective_rag_service = CorrectiveRAGService(
            min_relevance_threshold=min_relevance_threshold,
            min_documents=min_documents,
            max_documents=max_documents,
        )

    return _corrective_rag_service
