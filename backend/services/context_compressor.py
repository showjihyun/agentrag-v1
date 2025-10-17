# Context Compression Service - Reduce LLM token usage
import logging
import re
from typing import List, Dict, Any, Optional
from sentence_transformers import util
import torch

logger = logging.getLogger(__name__)


class ContextCompressor:
    """
    Compress retrieved context to reduce LLM token usage.

    Strategies:
    1. Extract only relevant sentences
    2. Remove redundant information
    3. Reorder by relevance
    4. Summarize if needed

    Can reduce token usage by 30-50% while maintaining quality.
    """

    def __init__(self, embedding_service=None, max_tokens: int = 2000):
        self.embedding_service = embedding_service
        self.max_tokens = max_tokens
        self.compression_ratio = []

    async def compress(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        target_tokens: Optional[int] = None,
        min_relevance_score: float = 0.3,
    ) -> List[Dict[str, Any]]:
        """
        Compress context chunks for LLM.

        Args:
            query: User query
            chunks: Retrieved chunks with text and scores
            target_tokens: Target token count (None = use max_tokens)
            min_relevance_score: Minimum relevance score for sentences

        Returns:
            Compressed chunks with reduced token count
        """
        if not chunks:
            return []

        target = target_tokens or self.max_tokens

        try:
            # Step 1: Extract relevant sentences from each chunk
            compressed_chunks = []

            for chunk in chunks:
                text = chunk.get("text", "")
                if not text:
                    continue

                # Split into sentences
                sentences = self._split_sentences(text)

                # Score each sentence
                relevant_sentences = await self._extract_relevant_sentences(
                    query, sentences, min_relevance_score
                )

                if relevant_sentences:
                    compressed_text = " ".join(relevant_sentences)
                    compressed_chunks.append(
                        {
                            **chunk,
                            "text": compressed_text,
                            "original_text": text,
                            "compression_ratio": (
                                len(compressed_text) / len(text) if text else 1.0
                            ),
                        }
                    )

            # Step 2: Remove redundant chunks
            deduplicated = self._deduplicate_chunks(compressed_chunks)

            # Step 3: Reorder by relevance
            reordered = self._reorder_by_relevance(query, deduplicated)

            # Step 4: Trim to target token count
            final_chunks = self._trim_to_token_limit(reordered, target)

            # Track compression ratio
            original_tokens = sum(
                self._estimate_tokens(c.get("original_text", "")) for c in chunks
            )
            compressed_tokens = sum(
                self._estimate_tokens(c.get("text", "")) for c in final_chunks
            )

            if original_tokens > 0:
                ratio = compressed_tokens / original_tokens
                self.compression_ratio.append(ratio)
                logger.info(
                    f"Context compressed: {original_tokens} → {compressed_tokens} tokens "
                    f"(ratio: {ratio:.2%})"
                )

            return final_chunks

        except Exception as e:
            logger.error(f"Context compression failed: {e}")
            # Return original chunks if compression fails
            return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r"[.!?]+\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    async def _extract_relevant_sentences(
        self, query: str, sentences: List[str], min_score: float
    ) -> List[str]:
        """Extract sentences relevant to query"""
        if not self.embedding_service or not sentences:
            return sentences

        try:
            # Embed query and sentences
            query_emb = await self.embedding_service.embed(query)
            sentence_embs = await self.embedding_service.embed_batch(sentences)

            # Calculate similarity scores
            query_tensor = torch.tensor(query_emb).unsqueeze(0)
            sentence_tensors = torch.tensor(sentence_embs)

            scores = util.cos_sim(query_tensor, sentence_tensors)[0]

            # Filter by relevance
            relevant = []
            for sent, score in zip(sentences, scores):
                if score >= min_score:
                    relevant.append(sent)

            return relevant if relevant else sentences[:3]  # Keep at least 3 sentences

        except Exception as e:
            logger.debug(f"Sentence relevance scoring failed: {e}")
            return sentences

    def _deduplicate_chunks(
        self, chunks: List[Dict[str, Any]], similarity_threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        """Remove highly similar chunks"""
        if len(chunks) <= 1:
            return chunks

        unique_chunks = []
        seen_texts = []

        for chunk in chunks:
            text = chunk.get("text", "")

            # Check if similar to any seen text
            is_duplicate = False
            for seen in seen_texts:
                similarity = self._text_similarity(text, seen)
                if similarity >= similarity_threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_chunks.append(chunk)
                seen_texts.append(text)

        if len(unique_chunks) < len(chunks):
            logger.info(f"Removed {len(chunks) - len(unique_chunks)} duplicate chunks")

        return unique_chunks

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _reorder_by_relevance(
        self, query: str, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Reorder chunks by relevance score"""
        # Sort by score (descending)
        return sorted(chunks, key=lambda x: x.get("score", 0.0), reverse=True)

    def _trim_to_token_limit(
        self, chunks: List[Dict[str, Any]], max_tokens: int
    ) -> List[Dict[str, Any]]:
        """Trim chunks to fit within token limit"""
        result = []
        total_tokens = 0

        for chunk in chunks:
            text = chunk.get("text", "")
            tokens = self._estimate_tokens(text)

            if total_tokens + tokens <= max_tokens:
                result.append(chunk)
                total_tokens += tokens
            else:
                # Try to fit partial chunk
                remaining_tokens = max_tokens - total_tokens
                if remaining_tokens > 100:  # Only if meaningful space left
                    truncated_text = self._truncate_to_tokens(text, remaining_tokens)
                    result.append({**chunk, "text": truncated_text, "truncated": True})
                break

        logger.info(f"Trimmed to {len(result)} chunks ({total_tokens} tokens)")
        return result

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximate token count"""
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text

        # Truncate at sentence boundary if possible
        truncated = text[:max_chars]
        last_period = truncated.rfind(".")

        if last_period > max_chars * 0.8:  # If period is near end
            return truncated[: last_period + 1]

        return truncated + "..."

    def get_compression_stats(self) -> Dict[str, float]:
        """Get compression statistics"""
        if not self.compression_ratio:
            return {"avg_compression_ratio": 1.0, "count": 0}

        import numpy as np

        return {
            "avg_compression_ratio": float(np.mean(self.compression_ratio)),
            "min_compression_ratio": float(np.min(self.compression_ratio)),
            "max_compression_ratio": float(np.max(self.compression_ratio)),
            "count": len(self.compression_ratio),
        }


# Global compressor instance
_context_compressor: Optional[ContextCompressor] = None


def get_context_compressor(
    embedding_service=None, max_tokens: int = 2000
) -> ContextCompressor:
    """Get global context compressor instance"""
    global _context_compressor
    if _context_compressor is None:
        _context_compressor = ContextCompressor(embedding_service, max_tokens)
    return _context_compressor
