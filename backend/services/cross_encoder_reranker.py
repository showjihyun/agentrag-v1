# Cross-Encoder Reranker Service
"""
Cross-encoder based reranking for improved search accuracy.

Uses sentence-transformers cross-encoder models to rerank search results
based on query-document relevance scores.
"""

import logging
from typing import List, Dict, Any, Optional
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Cross-encoder reranker for search results.
    
    Features:
    - High-accuracy relevance scoring
    - Batch processing for efficiency
    - Caching for repeated queries
    - Multiple model support
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        batch_size: int = 32,
        max_length: int = 1024,
        device: str = None
    ):
        """
        Initialize Cross-Encoder Reranker.
        
        Args:
            model_name: HuggingFace model name
                - "BAAI/bge-reranker-v2-m3": Multilingual, SOTA performance (default) ⭐
                - "BAAI/bge-reranker-v2-gemma": Gemma-based, high quality
                - "BAAI/bge-reranker-v2-minicpm-layerwise": Efficient, layerwise
                - "cross-encoder/ms-marco-MiniLM-L-6-v2": Fast, English only
            batch_size: Batch size for processing
            max_length: Maximum sequence length (1024 for bge-reranker-v2-m3)
            device: Device to use ("cpu" or "cuda", None for auto-detect)
        """
        # Auto-detect device if not specified
        if device is None:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self.device = device
        
        # Lazy load model
        self._model = None
        self._model_loaded = False
        
        logger.info(
            f"CrossEncoderReranker initialized: model={model_name}, "
            f"batch_size={batch_size}, device={device}"
        )

    def _load_model(self):
        """Lazy load cross-encoder model"""
        if self._model_loaded:
            return
        
        try:
            from sentence_transformers import CrossEncoder
            
            logger.info(f"Loading cross-encoder model: {self.model_name}")
            self._model = CrossEncoder(
                self.model_name,
                max_length=self.max_length,
                device=self.device
            )
            self._model_loaded = True
            
            logger.info(f"Cross-encoder model loaded successfully")
            
        except ImportError:
            logger.error(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to load cross-encoder model: {e}")
            raise

    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results using cross-encoder.
        
        Args:
            query: Search query
            results: List of search results with 'text' or 'content' field
            top_k: Number of top results to return (None = all)
            score_threshold: Minimum score threshold (filter out lower scores)
        
        Returns:
            Reranked list of results with updated scores
        """
        if not results:
            return []
        
        # Load model if not loaded
        if not self._model_loaded:
            self._load_model()
        
        try:
            # Prepare query-document pairs
            pairs = []
            for result in results:
                # Get text content
                text = result.get('text') or result.get('content', '')
                
                # Truncate if too long
                if len(text) > self.max_length * 4:  # Rough char estimate
                    text = text[:self.max_length * 4]
                
                pairs.append([query, text])
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                self._model.predict,
                pairs
            )
            
            # Combine results with new scores
            reranked = []
            for result, score in zip(results, scores):
                # Keep original score as backup
                result['original_score'] = result.get('score', 0.0)
                
                # Update with cross-encoder score
                result['score'] = float(score)
                result['reranked'] = True
                
                # Filter by threshold
                if score >= score_threshold:
                    reranked.append(result)
            
            # Sort by new scores
            reranked.sort(key=lambda x: x['score'], reverse=True)
            
            # Apply top_k if specified
            if top_k is not None:
                reranked = reranked[:top_k]
            
            logger.info(
                f"Reranked {len(results)} results to {len(reranked)} "
                f"(threshold={score_threshold}, top_k={top_k})"
            )
            
            return reranked
            
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Return original results on error
            return results

    async def rerank_with_scores(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        """
        Get relevance scores for query-text pairs.
        
        Args:
            query: Search query
            texts: List of text documents
        
        Returns:
            List of relevance scores
        """
        if not texts:
            return []
        
        # Load model if not loaded
        if not self._model_loaded:
            self._load_model()
        
        try:
            # Prepare pairs
            pairs = [[query, text] for text in texts]
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None,
                self._model.predict,
                pairs
            )
            
            return [float(score) for score in scores]
            
        except Exception as e:
            logger.error(f"Scoring failed: {e}")
            return [0.0] * len(texts)

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "batch_size": self.batch_size,
            "max_length": self.max_length,
            "device": self.device,
            "loaded": self._model_loaded
        }


class HybridReranker:
    """
    Hybrid reranker combining multiple reranking strategies.
    
    Combines:
    1. Cross-encoder scores
    2. Original retrieval scores
    3. Diversity (MMR-like)
    """

    def __init__(
        self,
        cross_encoder: CrossEncoderReranker,
        cross_encoder_weight: float = 0.7,
        original_weight: float = 0.3,
        diversity_penalty: float = 0.1
    ):
        """
        Initialize Hybrid Reranker.
        
        Args:
            cross_encoder: CrossEncoderReranker instance
            cross_encoder_weight: Weight for cross-encoder scores
            original_weight: Weight for original retrieval scores
            diversity_penalty: Penalty for similar documents (0.0 = no penalty)
        """
        self.cross_encoder = cross_encoder
        self.cross_encoder_weight = cross_encoder_weight
        self.original_weight = original_weight
        self.diversity_penalty = diversity_penalty
        
        # Normalize weights
        total = cross_encoder_weight + original_weight
        self.cross_encoder_weight /= total
        self.original_weight /= total

    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank using hybrid approach.
        
        Args:
            query: Search query
            results: Search results
            top_k: Number of results to return
        
        Returns:
            Reranked results
        """
        if not results:
            return []
        
        # Get cross-encoder scores
        reranked = await self.cross_encoder.rerank(query, results, top_k=None)
        
        # Normalize scores
        if reranked:
            # Normalize cross-encoder scores
            ce_scores = [r['score'] for r in reranked]
            ce_min, ce_max = min(ce_scores), max(ce_scores)
            ce_range = ce_max - ce_min if ce_max > ce_min else 1.0
            
            # Normalize original scores
            orig_scores = [r.get('original_score', 0.0) for r in reranked]
            orig_min, orig_max = min(orig_scores), max(orig_scores)
            orig_range = orig_max - orig_min if orig_max > orig_min else 1.0
            
            # Combine scores
            for result in reranked:
                ce_norm = (result['score'] - ce_min) / ce_range
                orig_norm = (result.get('original_score', 0.0) - orig_min) / orig_range
                
                # Hybrid score
                result['hybrid_score'] = (
                    self.cross_encoder_weight * ce_norm +
                    self.original_weight * orig_norm
                )
            
            # Sort by hybrid score
            reranked.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            # Apply diversity if enabled
            if self.diversity_penalty > 0:
                reranked = self._apply_diversity(reranked, top_k)
            else:
                reranked = reranked[:top_k]
        
        return reranked

    def _apply_diversity(
        self,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Apply diversity penalty (simple MMR-like approach).
        
        Args:
            results: Sorted results
            top_k: Number of results to select
        
        Returns:
            Diversified results
        """
        if len(results) <= top_k:
            return results
        
        selected = [results[0]]  # Always take top result
        remaining = results[1:]
        
        while len(selected) < top_k and remaining:
            # Find result with highest score and lowest similarity to selected
            best_idx = 0
            best_score = -float('inf')
            
            for idx, candidate in enumerate(remaining):
                # Calculate similarity penalty (simplified)
                max_similarity = 0.0
                candidate_text = candidate.get('text', '')[:200]
                
                for selected_result in selected:
                    selected_text = selected_result.get('text', '')[:200]
                    # Simple word overlap similarity
                    similarity = self._text_similarity(candidate_text, selected_text)
                    max_similarity = max(max_similarity, similarity)
                
                # Penalize score by similarity
                penalized_score = (
                    candidate['hybrid_score'] -
                    self.diversity_penalty * max_similarity
                )
                
                if penalized_score > best_score:
                    best_score = penalized_score
                    best_idx = idx
            
            # Add best candidate
            selected.append(remaining.pop(best_idx))
        
        return selected

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0


# Global reranker instances
_cross_encoder_reranker: Optional[CrossEncoderReranker] = None
_hybrid_reranker: Optional[HybridReranker] = None


def get_cross_encoder_reranker(
    model_name: str = "BAAI/bge-reranker-v2-m3",
    device: str = None
) -> CrossEncoderReranker:
    """
    Get global cross-encoder reranker instance (auto-detects GPU).
    
    Default model: BAAI/bge-reranker-v2-m3
    - Multilingual support (100+ languages including Korean)
    - SOTA performance on BEIR benchmark
    - 1024 token context length
    - Efficient inference
    """
    global _cross_encoder_reranker
    if _cross_encoder_reranker is None:
        _cross_encoder_reranker = CrossEncoderReranker(
            model_name=model_name,
            device=device  # None = auto-detect
        )
    return _cross_encoder_reranker


def get_hybrid_reranker(
    cross_encoder_weight: float = 0.7,
    original_weight: float = 0.3
) -> HybridReranker:
    """Get global hybrid reranker instance"""
    global _hybrid_reranker
    if _hybrid_reranker is None:
        cross_encoder = get_cross_encoder_reranker()
        _hybrid_reranker = HybridReranker(
            cross_encoder=cross_encoder,
            cross_encoder_weight=cross_encoder_weight,
            original_weight=original_weight
        )
    return _hybrid_reranker
