"""
Semantic Chunking Service for intelligent text segmentation.

Provides multiple chunking strategies:
1. Sentence-based chunking (respects sentence boundaries)
2. Paragraph-based chunking (respects paragraph boundaries)
3. Semantic similarity-based chunking (groups similar sentences)
4. Heading-based chunking (for structured documents)
5. Fixed-size chunking (fallback, with sentence boundaries)
"""

import logging
import re
from typing import List, Optional, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Intelligent text chunking with semantic awareness.

    Features:
    - Multiple chunking strategies
    - Respects sentence and paragraph boundaries
    - Semantic similarity-based grouping
    - Configurable chunk size and overlap
    - Korean and English support
    """

    def __init__(
        self,
        strategy: str = "semantic",
        target_size: int = 500,
        overlap: int = 50,
        min_chunk_size: int = 100,
        max_chunk_size: int = 1000,
    ):
        """
        Initialize SemanticChunker.

        Args:
            strategy: Chunking strategy
                - "semantic": Semantic similarity-based (best quality)
                - "sentence": Sentence boundary-based (good balance)
                - "paragraph": Paragraph boundary-based (fast)
                - "heading": Heading-based (for structured docs)
                - "fixed": Fixed-size with sentence boundaries (fallback)
            target_size: Target chunk size in characters
            overlap: Overlap size in characters
            min_chunk_size: Minimum chunk size
            max_chunk_size: Maximum chunk size
        """
        self.strategy = strategy
        self.target_size = target_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

        # Initialize embedding model for semantic chunking
        self.embedding_model = None
        if strategy == "semantic":
            self._init_embedding_model()

        logger.info(
            f"SemanticChunker initialized: strategy={strategy}, "
            f"target_size={target_size}, overlap={overlap}"
        )

    def _init_embedding_model(self):
        """Initialize embedding model for semantic chunking."""
        try:
            from sentence_transformers import SentenceTransformer
            from backend.config import settings
            import torch

            # Use the same model as configured in settings for consistency
            model_name = settings.EMBEDDING_MODEL
            
            # Auto-detect device (GPU if available)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self.embedding_model = SentenceTransformer(model_name, device=device)
            logger.info(f"Embedding model loaded for semantic chunking: {model_name} on {device}")
        except Exception as e:
            logger.warning(
                f"Failed to load embedding model: {e}. "
                "Falling back to sentence-based chunking."
            )
            self.strategy = "sentence"

    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk text using the configured strategy.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        # Route to appropriate chunking method
        if self.strategy == "semantic":
            return self._semantic_chunking(text)
        elif self.strategy == "sentence":
            return self._sentence_chunking(text)
        elif self.strategy == "paragraph":
            return self._paragraph_chunking(text)
        elif self.strategy == "heading":
            return self._heading_chunking(text)
        else:  # fixed
            return self._fixed_size_chunking(text)

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences with Korean and English support.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Pattern for sentence boundaries
        # Handles: . ! ? (English) and 。！？ (Korean/Chinese)
        pattern = r"(?<=[.!?。！？])\s+(?=[A-Z가-힣])|(?<=[.!?。！？])(?=\n)"

        sentences = re.split(pattern, text)

        # Clean and filter
        sentences = [s.strip() for s in sentences if s.strip()]

        # Handle cases where split didn't work well
        if len(sentences) == 1 and len(text) > self.max_chunk_size:
            # Fallback: split by newlines
            sentences = [s.strip() for s in text.split("\n") if s.strip()]

        return sentences

    def _split_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.

        Args:
            text: Text to split

        Returns:
            List of paragraphs
        """
        # Split by double newlines or multiple newlines
        paragraphs = re.split(r"\n\s*\n", text)

        # Clean and filter
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _semantic_chunking(self, text: str) -> List[str]:
        """
        Chunk based on semantic similarity between sentences.

        Algorithm:
        1. Split into sentences
        2. Embed each sentence
        3. Calculate similarity between consecutive sentences
        4. Find breakpoints where similarity is low
        5. Group sentences into chunks

        Args:
            text: Text to chunk

        Returns:
            List of chunks
        """
        if not self.embedding_model:
            logger.warning(
                "Embedding model not available, falling back to sentence chunking"
            )
            return self._sentence_chunking(text)

        try:
            # Split into sentences
            sentences = self._split_sentences(text)

            if len(sentences) <= 1:
                return [text]

            # Embed sentences
            embeddings = self.embedding_model.encode(sentences, show_progress_bar=False)

            # Calculate similarity between consecutive sentences
            similarities = []
            for i in range(len(embeddings) - 1):
                sim = cosine_similarity(
                    embeddings[i].reshape(1, -1), embeddings[i + 1].reshape(1, -1)
                )[0][0]
                similarities.append(sim)

            # Find breakpoints (low similarity = topic change)
            # Use percentile to find natural breakpoints
            if len(similarities) > 0:
                threshold = np.percentile(similarities, 25)  # Bottom 25%
            else:
                threshold = 0.5

            # Build chunks
            chunks = []
            current_chunk = [sentences[0]]
            current_size = len(sentences[0])

            for i, sentence in enumerate(sentences[1:], 1):
                sentence_len = len(sentence)

                # Check if we should start a new chunk
                should_break = False

                # Reason 1: Low similarity (topic change)
                if i - 1 < len(similarities) and similarities[i - 1] < threshold:
                    should_break = True

                # Reason 2: Current chunk is large enough
                if current_size >= self.target_size:
                    should_break = True

                # Reason 3: Adding this sentence would make chunk too large
                if current_size + sentence_len > self.max_chunk_size:
                    should_break = True

                if should_break and current_size >= self.min_chunk_size:
                    # Save current chunk
                    chunks.append(" ".join(current_chunk))

                    # Start new chunk with overlap
                    overlap_sentences = self._get_overlap_sentences(
                        current_chunk, self.overlap
                    )
                    current_chunk = overlap_sentences + [sentence]
                    current_size = sum(len(s) for s in current_chunk)
                else:
                    # Add to current chunk
                    current_chunk.append(sentence)
                    current_size += sentence_len

            # Add final chunk
            if current_chunk:
                chunks.append(" ".join(current_chunk))

            logger.debug(
                f"Semantic chunking: {len(sentences)} sentences → {len(chunks)} chunks"
            )

            return chunks

        except Exception as e:
            logger.error(
                f"Semantic chunking failed: {e}, falling back to sentence chunking"
            )
            return self._sentence_chunking(text)

    def _sentence_chunking(self, text: str) -> List[str]:
        """
        Chunk based on sentence boundaries.

        Args:
            text: Text to chunk

        Returns:
            List of chunks
        """
        sentences = self._split_sentences(text)

        if not sentences:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            # Check if adding this sentence would exceed max size
            if current_size + sentence_len > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunks.append(" ".join(current_chunk))

                # Start new chunk with overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk, self.overlap
                )
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) for s in current_chunk)
            else:
                # Add to current chunk
                current_chunk.append(sentence)
                current_size += sentence_len

                # Check if we've reached target size
                if current_size >= self.target_size:
                    chunks.append(" ".join(current_chunk))

                    # Start new chunk with overlap
                    overlap_sentences = self._get_overlap_sentences(
                        current_chunk, self.overlap
                    )
                    current_chunk = overlap_sentences
                    current_size = sum(len(s) for s in current_chunk)

        # Add final chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        logger.debug(
            f"Sentence chunking: {len(sentences)} sentences → {len(chunks)} chunks"
        )

        return chunks

    def _paragraph_chunking(self, text: str) -> List[str]:
        """
        Chunk based on paragraph boundaries.

        Args:
            text: Text to chunk

        Returns:
            List of chunks
        """
        paragraphs = self._split_paragraphs(text)

        if not paragraphs:
            return []

        chunks = []
        current_chunk = []
        current_size = 0

        for paragraph in paragraphs:
            para_len = len(paragraph)

            # If single paragraph is too large, split it
            if para_len > self.max_chunk_size:
                # Split large paragraph by sentences
                sub_chunks = self._sentence_chunking(paragraph)
                chunks.extend(sub_chunks)
                current_chunk = []
                current_size = 0
                continue

            # Check if adding this paragraph would exceed max size
            if current_size + para_len > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [paragraph]
                current_size = para_len
            else:
                # Add to current chunk
                current_chunk.append(paragraph)
                current_size += para_len

                # Check if we've reached target size
                if current_size >= self.target_size:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0

        # Add final chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        logger.debug(
            f"Paragraph chunking: {len(paragraphs)} paragraphs → {len(chunks)} chunks"
        )

        return chunks

    def _heading_chunking(self, text: str) -> List[str]:
        """
        Chunk based on heading structure (Markdown-style).

        Args:
            text: Text to chunk

        Returns:
            List of chunks
        """
        # Pattern for Markdown headings (# ## ### etc.)
        heading_pattern = r"^#{1,6}\s+.+$"

        lines = text.split("\n")
        chunks = []
        current_chunk = []

        for line in lines:
            # Check if line is a heading
            if re.match(heading_pattern, line):
                # Save previous chunk if exists
                if current_chunk:
                    chunk_text = "\n".join(current_chunk).strip()
                    if chunk_text:
                        chunks.append(chunk_text)

                # Start new chunk with heading
                current_chunk = [line]
            else:
                current_chunk.append(line)

        # Add final chunk
        if current_chunk:
            chunk_text = "\n".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)

        # If no headings found, fall back to paragraph chunking
        if len(chunks) <= 1:
            logger.debug("No headings found, falling back to paragraph chunking")
            return self._paragraph_chunking(text)

        # Split large chunks
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > self.max_chunk_size:
                sub_chunks = self._sentence_chunking(chunk)
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)

        logger.debug(
            f"Heading chunking: {len(chunks)} sections → {len(final_chunks)} chunks"
        )

        return final_chunks

    def _fixed_size_chunking(self, text: str) -> List[str]:
        """
        Fixed-size chunking with sentence boundary awareness.

        Args:
            text: Text to chunk

        Returns:
            List of chunks
        """
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            # Calculate end position
            end = start + self.target_size

            if end >= text_len:
                # Last chunk
                chunks.append(text[start:].strip())
                break

            # Try to break at sentence boundary
            # Look for sentence endings near the target position
            search_start = max(start, end - 100)
            search_end = min(text_len, end + 100)
            search_text = text[search_start:search_end]

            # Find sentence boundaries
            sentence_ends = [
                m.end() + search_start
                for m in re.finditer(r"[.!?。！？]\s", search_text)
            ]

            if sentence_ends:
                # Find closest sentence end to target
                closest = min(sentence_ends, key=lambda x: abs(x - end))
                end = closest
            else:
                # No sentence boundary found, try word boundary
                if end < text_len and text[end] != " ":
                    space_pos = text.find(" ", end)
                    if space_pos != -1 and space_pos < end + 50:
                        end = space_pos

            # Extract chunk
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position (with overlap)
            start = end - self.overlap

            # Ensure we make progress
            if start <= chunks[-1] if chunks else 0:
                start = end

        logger.debug(f"Fixed-size chunking: {text_len} chars → {len(chunks)} chunks")

        return chunks

    def _get_overlap_sentences(
        self, sentences: List[str], overlap_size: int
    ) -> List[str]:
        """
        Get last few sentences for overlap.

        Args:
            sentences: List of sentences
            overlap_size: Target overlap size in characters

        Returns:
            List of sentences for overlap
        """
        if not sentences:
            return []

        overlap_sentences = []
        current_size = 0

        # Take sentences from the end until we reach overlap size
        for sentence in reversed(sentences):
            if current_size >= overlap_size:
                break
            overlap_sentences.insert(0, sentence)
            current_size += len(sentence)

        return overlap_sentences


# Singleton instance
_semantic_chunker: Optional[SemanticChunker] = None


def get_semantic_chunker(
    strategy: str = "semantic", target_size: int = 500, overlap: int = 50
) -> SemanticChunker:
    """
    Get or create SemanticChunker instance.

    Args:
        strategy: Chunking strategy
        target_size: Target chunk size
        overlap: Overlap size

    Returns:
        SemanticChunker instance
    """
    global _semantic_chunker

    # Create new instance if parameters changed
    if (
        _semantic_chunker is None
        or _semantic_chunker.strategy != strategy
        or _semantic_chunker.target_size != target_size
        or _semantic_chunker.overlap != overlap
    ):
        _semantic_chunker = SemanticChunker(
            strategy=strategy, target_size=target_size, overlap=overlap
        )

    return _semantic_chunker
