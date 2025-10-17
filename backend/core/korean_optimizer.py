"""
Korean Language Optimizer - Phase 2.2 Optimization

Korean-specific optimizations:
- Korean embedding model (jhgan/ko-sroberta-multitask)
- Korean text preprocessing
- Hybrid search (BM25 + Vector)
- Better Korean understanding

Key features:
- Korean-specific tokenization
- Jamo normalization
- Smart sentence chunking
- Keyword + semantic search
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with score."""

    text: str
    score: float
    source: str  # "vector" or "keyword"
    metadata: Dict[str, Any]


class KoreanTextProcessor:
    """
    Korean text preprocessing and normalization.

    Features:
    - Jamo normalization (incomplete Hangul)
    - Whitespace normalization
    - Special character handling
    - Smart sentence boundary detection
    """

    # Korean Unicode ranges
    HANGUL_START = 0xAC00
    HANGUL_END = 0xD7A3
    JAMO_START = 0x1100
    JAMO_END = 0x11FF

    # Sentence ending markers
    SENTENCE_ENDINGS = ["다", "요", "까", "냐", "지", "네", "군", "야"]

    def __init__(self):
        """Initialize Korean text processor."""
        logger.info("KoreanTextProcessor initialized")

    def preprocess(self, text: str) -> str:
        """
        Preprocess Korean text.

        Args:
            text: Input text

        Returns:
            Preprocessed text
        """
        if not text:
            return ""

        # Remove incomplete Jamo
        text = self._remove_incomplete_jamo(text)

        # Normalize whitespace
        text = self._normalize_whitespace(text)

        # Normalize punctuation
        text = self._normalize_punctuation(text)

        return text.strip()

    def _remove_incomplete_jamo(self, text: str) -> str:
        """Remove incomplete Hangul Jamo characters."""
        # Remove standalone Jamo (not part of complete Hangul)
        return "".join(
            char for char in text if not (self.JAMO_START <= ord(char) <= self.JAMO_END)
        )

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace."""
        # Replace multiple spaces with single space
        text = re.sub(r"\s+", " ", text)

        # Remove spaces before punctuation
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)

        # Add space after punctuation if missing
        text = re.sub(r"([.,!?;:])([^\s\d])", r"\1 \2", text)

        return text

    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation."""
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(""", "'").replace(""", "'")

        # Normalize dashes
        text = text.replace("—", "-").replace("–", "-")

        return text

    def smart_chunk(
        self, text: str, max_length: int = 500, overlap: int = 50
    ) -> List[str]:
        """
        Smart chunking for Korean text.

        Respects sentence boundaries and semantic units.

        Args:
            text: Input text
            max_length: Maximum chunk length
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if not text:
            return []

        # Preprocess
        text = self.preprocess(text)

        # Split into sentences
        sentences = self._split_sentences(text)

        # Build chunks
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # If single sentence exceeds max_length, split it
            if sentence_length > max_length:
                # Add current chunk if not empty
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # Split long sentence
                sub_chunks = self._split_long_sentence(sentence, max_length)
                chunks.extend(sub_chunks)
                continue

            # Check if adding sentence exceeds max_length
            if current_length + sentence_length > max_length and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                if overlap > 0 and current_chunk:
                    # Keep last sentence for overlap
                    current_chunk = [current_chunk[-1]]
                    current_length = len(current_chunk[-1])
                else:
                    current_chunk = []
                    current_length = 0

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length

        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences (Korean-aware).

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Split on sentence endings
        pattern = r"([.!?]+\s+|[.!?]+$)"
        parts = re.split(pattern, text)

        # Recombine sentences
        sentences = []
        current = ""

        for part in parts:
            current += part
            if re.match(pattern, part):
                sentences.append(current.strip())
                current = ""

        if current.strip():
            sentences.append(current.strip())

        return [s for s in sentences if s]

    def _split_long_sentence(self, sentence: str, max_length: int) -> List[str]:
        """Split long sentence into smaller chunks."""
        chunks = []
        words = sentence.split()
        current = []
        current_length = 0

        for word in words:
            word_length = len(word)

            if current_length + word_length > max_length and current:
                chunks.append(" ".join(current))
                current = []
                current_length = 0

            current.append(word)
            current_length += word_length + 1  # +1 for space

        if current:
            chunks.append(" ".join(current))

        return chunks


class HybridKoreanSearch:
    """
    Hybrid search combining vector and keyword search.

    Strategy:
    - Vector search: Semantic similarity (70% weight)
    - BM25 search: Keyword matching (30% weight)
    - Weighted merge: Best of both worlds

    Benefits:
    - Better recall (keyword catches exact matches)
    - Better precision (vector catches semantic matches)
    - Robust to typos and variations
    """

    def __init__(self, vector_weight: float = 0.7, keyword_weight: float = 0.3):
        """
        Initialize hybrid search.

        Args:
            vector_weight: Weight for vector search results
            keyword_weight: Weight for keyword search results
        """
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

        # Normalize weights
        total = vector_weight + keyword_weight
        self.vector_weight /= total
        self.keyword_weight /= total

        logger.info(
            f"HybridKoreanSearch initialized: "
            f"vector_weight={self.vector_weight:.2f}, "
            f"keyword_weight={self.keyword_weight:.2f}"
        )

    async def search(
        self, query: str, vector_search_fn, keyword_search_fn, top_k: int = 10
    ) -> List[SearchResult]:
        """
        Perform hybrid search.

        Args:
            query: Search query
            vector_search_fn: Vector search function
            keyword_search_fn: Keyword search function
            top_k: Number of results

        Returns:
            Merged search results
        """
        # Execute both searches in parallel
        import asyncio

        vector_task = asyncio.create_task(vector_search_fn(query, top_k * 2))
        keyword_task = asyncio.create_task(keyword_search_fn(query, top_k * 2))

        vector_results = await vector_task
        keyword_results = await keyword_task

        # Merge results
        merged = self._merge_results(vector_results, keyword_results, top_k)

        logger.info(
            f"Hybrid search: query={query[:50]}, "
            f"vector={len(vector_results)}, "
            f"keyword={len(keyword_results)}, "
            f"merged={len(merged)}"
        )

        return merged

    def _merge_results(
        self,
        vector_results: List[SearchResult],
        keyword_results: List[SearchResult],
        top_k: int,
    ) -> List[SearchResult]:
        """
        Merge vector and keyword results with weighted scoring.

        Args:
            vector_results: Vector search results
            keyword_results: Keyword search results
            top_k: Number of results to return

        Returns:
            Merged and ranked results
        """
        # Create score map
        scores: Dict[str, Tuple[float, SearchResult]] = {}

        # Add vector results
        for result in vector_results:
            key = self._get_result_key(result)
            weighted_score = result.score * self.vector_weight
            scores[key] = (weighted_score, result)

        # Add keyword results
        for result in keyword_results:
            key = self._get_result_key(result)
            weighted_score = result.score * self.keyword_weight

            if key in scores:
                # Combine scores
                existing_score, existing_result = scores[key]
                combined_score = existing_score + weighted_score

                # Update metadata
                existing_result.metadata["hybrid"] = True
                existing_result.metadata["vector_score"] = (
                    existing_score / self.vector_weight
                )
                existing_result.metadata["keyword_score"] = (
                    weighted_score / self.keyword_weight
                )

                scores[key] = (combined_score, existing_result)
            else:
                scores[key] = (weighted_score, result)

        # Sort by combined score
        sorted_results = sorted(scores.values(), key=lambda x: x[0], reverse=True)

        # Return top_k
        return [result for _, result in sorted_results[:top_k]]

    def _get_result_key(self, result: SearchResult) -> str:
        """Get unique key for result (for deduplication)."""
        # Use text hash as key
        return str(hash(result.text[:100]))


class KoreanQueryAnalyzer:
    """
    Analyze Korean queries for better processing.

    Features:
    - Query type detection (question, command, statement)
    - Intent classification
    - Entity extraction
    - Complexity analysis
    """

    # Question markers
    QUESTION_MARKERS = ["무엇", "누구", "언제", "어디", "왜", "어떻게", "얼마"]
    QUESTION_ENDINGS = ["까", "냐", "니", "가"]

    def __init__(self):
        """Initialize Korean query analyzer."""
        logger.info("KoreanQueryAnalyzer initialized")

    def analyze(self, query: str) -> Dict[str, Any]:
        """
        Analyze Korean query.

        Args:
            query: User query

        Returns:
            Analysis results
        """
        return {
            "query_type": self._detect_query_type(query),
            "is_question": self._is_question(query),
            "complexity": self._analyze_complexity(query),
            "keywords": self._extract_keywords(query),
            "length": len(query),
            "word_count": len(query.split()),
        }

    def _detect_query_type(self, query: str) -> str:
        """Detect query type."""
        if self._is_question(query):
            return "question"
        elif any(word in query for word in ["해줘", "알려줘", "보여줘"]):
            return "command"
        else:
            return "statement"

    def _is_question(self, query: str) -> bool:
        """Check if query is a question."""
        # Check question markers
        if any(marker in query for marker in self.QUESTION_MARKERS):
            return True

        # Check question endings
        if any(query.endswith(ending) for ending in self.QUESTION_ENDINGS):
            return True

        # Check question mark
        if "?" in query:
            return True

        return False

    def _analyze_complexity(self, query: str) -> str:
        """Analyze query complexity."""
        words = query.split()

        if len(words) <= 5:
            return "simple"
        elif len(words) <= 15:
            return "medium"
        else:
            return "complex"

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords (simple version)."""
        # Remove common words
        stopwords = {
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "의",
            "에",
            "에서",
            "로",
            "으로",
        }

        words = query.split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]

        return keywords
