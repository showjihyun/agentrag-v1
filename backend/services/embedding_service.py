"""Embedding service for vector memory operations."""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import asyncio
from functools import lru_cache
import hashlib
import json

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing text embeddings."""
    
    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        self.model_name = model_name
        self._model = None
        self._embedding_cache = {}
        self.max_cache_size = 1000
        
    @property
    def model(self):
        """Lazy load the embedding model."""
        if self._model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                # Fallback to a smaller model
                try:
                    self._model = SentenceTransformer("all-MiniLM-L6-v2")
                    logger.info("Loaded fallback embedding model: all-MiniLM-L6-v2")
                except Exception as fallback_error:
                    logger.error(f"Failed to load fallback model: {fallback_error}")
                    raise RuntimeError("Could not load any embedding model")
        return self._model
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    async def encode_text(self, text: str) -> np.ndarray:
        """Encode single text to embedding vector."""
        cache_key = self._get_cache_key(text)
        
        # Check cache first
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        try:
            # Run encoding in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                lambda: self.model.encode([text], convert_to_numpy=True)[0]
            )
            
            # Cache the result
            if len(self._embedding_cache) < self.max_cache_size:
                self._embedding_cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            # Return zero vector as fallback
            return np.zeros(384)  # Default dimension for most models
    
    async def encode_texts(self, texts: List[str]) -> List[np.ndarray]:
        """Encode multiple texts to embedding vectors."""
        if not texts:
            return []
        
        # Check cache for all texts
        cached_embeddings = {}
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._embedding_cache:
                cached_embeddings[i] = self._embedding_cache[cache_key]
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Encode uncached texts
        new_embeddings = []
        if uncached_texts:
            try:
                loop = asyncio.get_event_loop()
                new_embeddings = await loop.run_in_executor(
                    None,
                    lambda: self.model.encode(uncached_texts, convert_to_numpy=True)
                )
                
                # Cache new embeddings
                for i, embedding in enumerate(new_embeddings):
                    if len(self._embedding_cache) < self.max_cache_size:
                        cache_key = self._get_cache_key(uncached_texts[i])
                        self._embedding_cache[cache_key] = embedding
                        
            except Exception as e:
                logger.error(f"Failed to encode texts: {e}")
                # Return zero vectors as fallback
                new_embeddings = [np.zeros(384) for _ in uncached_texts]
        
        # Combine cached and new embeddings
        result = [None] * len(texts)
        
        # Fill cached embeddings
        for i, embedding in cached_embeddings.items():
            result[i] = embedding
        
        # Fill new embeddings
        for i, embedding in enumerate(new_embeddings):
            result[uncached_indices[i]] = embedding
        
        return result
    
    def calculate_similarity(
        self, 
        embedding1: np.ndarray, 
        embedding2: np.ndarray
    ) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            # Normalize vectors
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5
    ) -> List[tuple[int, float]]:
        """Find most similar embeddings to query."""
        if not candidate_embeddings:
            return []
        
        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            similarity = self.calculate_similarity(query_embedding, candidate)
            similarities.append((i, similarity))
        
        # Sort by similarity (descending) and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get embedding service statistics."""
        return {
            'model_name': self.model_name,
            'cache_size': len(self._embedding_cache),
            'max_cache_size': self.max_cache_size,
            'model_loaded': self._model is not None,
            'embedding_dimension': 384 if self._model is None else self.model.get_sentence_embedding_dimension()
        }
    
    def clear_cache(self):
        """Clear embedding cache."""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")

# Global embedding service instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service