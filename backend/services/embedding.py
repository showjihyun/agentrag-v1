"""
Embedding Service for generating text embeddings using Sentence Transformers.

This service provides methods for generating embeddings for single texts or batches,
with model caching and error handling.
"""

import logging
import asyncio
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using Sentence Transformers.

    Features:
    - Configurable embedding model
    - Single and batch text embedding
    - Model caching for performance
    - Comprehensive error handling
    """

    # Class-level cache for models to avoid reloading
    _model_cache = {}
    # Thread pool for CPU-intensive embedding operations
    _executor = ThreadPoolExecutor(max_workers=4)

    def __init__(
        self,
        model_name: Optional[str] = None,
    ):
        """
        Initialize the EmbeddingService with a specific model.

        Args:
            model_name: Name of the Sentence Transformer model to use.
                       If None, uses the model from config (EMBEDDING_MODEL env var).
                       
                       Recommended Korean models (in order of quality):
                       1. jhgan/ko-sroberta-multitask (768d, BEST for Korean - specialized)
                       2. BM-K/KoSimCSE-roberta (768d, excellent for Korean semantic similarity)
                       3. sentence-transformers/paraphrase-multilingual-mpnet-base-v2 (768d, multilingual)
                       4. sentence-transformers/distiluse-base-multilingual-cased-v2 (512d, faster)
                       
                       English only (NOT recommended for Korean):
                       - sentence-transformers/all-MiniLM-L6-v2 (384d, English only)
                       - sentence-transformers/all-mpnet-base-v2 (768d, English only)

        Raises:
            ValueError: If model_name is empty or invalid
            RuntimeError: If model fails to load
        """
        # Use config model if not specified
        if model_name is None:
            from backend.config import settings
            model_name = settings.EMBEDDING_MODEL
            logger.info(f"Using embedding model from config: {model_name}")
        
        if not model_name or not isinstance(model_name, str):
            raise ValueError("model_name must be a non-empty string")

        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self._dimension: Optional[int] = None

        # Initialize model on creation
        self._load_model()

        logger.info(
            f"EmbeddingService initialized: model={model_name}, dimension={self.dimension}"
        )

    def _load_model(self) -> None:
        """
        Load the embedding model with caching.

        Uses class-level cache to avoid reloading the same model multiple times
        across different instances.

        Raises:
            RuntimeError: If model fails to load
        """
        try:
            # Check if model is already in cache
            if self.model_name in self._model_cache:
                self._model = self._model_cache[self.model_name]
                logger.debug(f"Loaded model from cache: {self.model_name}")
            else:
                # Determine device (GPU if available, else CPU)
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                
                # Load model and add to cache
                logger.info(f"Loading embedding model: {self.model_name} on device: {device}")
                self._model = SentenceTransformer(self.model_name, device=device)
                self._model_cache[self.model_name] = self._model
                logger.info(f"Model loaded successfully: {self.model_name} on {device}")

            # Get embedding dimension
            self._dimension = self._model.get_sentence_embedding_dimension()

        except Exception as e:
            error_msg = f"Failed to load embedding model '{self.model_name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    @property
    def dimension(self) -> int:
        """
        Get the embedding dimension of the current model.

        Returns:
            int: Dimension of the embedding vectors
        """
        if self._dimension is None:
            raise RuntimeError("Model not properly initialized")
        return self._dimension

    @property
    def model(self) -> SentenceTransformer:
        """
        Get the underlying SentenceTransformer model.

        Returns:
            SentenceTransformer: The loaded model instance
        """
        if self._model is None:
            raise RuntimeError("Model not properly initialized")
        return self._model

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text (async).

        Args:
            text: Input text to embed

        Returns:
            List[float]: Embedding vector as a list of floats

        Raises:
            ValueError: If text is empty or invalid
            RuntimeError: If embedding generation fails
        """
        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")

        if not text.strip():
            raise ValueError("text cannot be only whitespace")

        try:
            # Run CPU-intensive embedding in thread pool
            loop = asyncio.get_event_loop()
            embedding_list = await loop.run_in_executor(
                self._executor, self._embed_text_sync, text
            )

            # Use DEBUG for individual embeddings (too verbose for INFO)
            logger.debug(
                f"Generated embedding: text_length={len(text)}, "
                f"dimension={len(embedding_list)}"
            )

            return embedding_list

        except Exception as e:
            error_msg = f"Failed to generate embedding for text: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _embed_text_sync(self, text: str) -> List[float]:
        """
        Synchronous embedding generation (runs in thread pool).

        Args:
            text: Input text to embed

        Returns:
            List[float]: Embedding vector
        """
        # Generate embedding
        embedding = self.model.encode(
            text, convert_to_numpy=True, show_progress_bar=False
        )

        # Convert to list
        return embedding.tolist()

    def _calculate_optimal_batch_size(self, num_texts: int) -> int:
        """
        Calculate optimal batch size based on number of texts.

        Dynamically adjusts batch size for better GPU memory utilization
        and processing efficiency.

        Args:
            num_texts: Total number of texts to process

        Returns:
            Optimal batch size
        """
        if num_texts < 10:
            # Small batches: process all at once
            return num_texts
        elif num_texts < 100:
            # Medium batches: use moderate batch size
            return 32
        elif num_texts < 1000:
            # Large batches: use larger batch size for efficiency
            return 64
        else:
            # Very large batches: use maximum batch size
            return 128

    async def embed_batch(
        self, texts: List[str], batch_size: int = None, show_progress: bool = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch with dynamic optimization (async).

        Batch processing is more efficient than processing texts individually,
        especially for large numbers of texts. Batch size is automatically
        optimized based on the number of texts if not specified.

        Args:
            texts: List of input texts to embed
            batch_size: Number of texts to process in each batch (default: auto)
            show_progress: Whether to show progress bar (default: auto based on size)

        Returns:
            List[List[float]]: List of embedding vectors

        Raises:
            ValueError: If texts is empty or contains invalid entries
            RuntimeError: If embedding generation fails
        """
        if not texts or not isinstance(texts, list):
            raise ValueError("texts must be a non-empty list")

        if not all(isinstance(text, str) and text.strip() for text in texts):
            raise ValueError("All texts must be non-empty strings")

        # Auto-calculate optimal batch size if not provided
        if batch_size is None:
            batch_size = self._calculate_optimal_batch_size(len(texts))
            logger.debug(
                f"Auto-selected batch_size={batch_size} for {len(texts)} texts"
            )
        elif batch_size < 1:
            raise ValueError("batch_size must be at least 1")

        # Auto-determine whether to show progress
        if show_progress is None:
            show_progress = len(texts) > 100

        try:
            # Run CPU-intensive batch embedding in thread pool
            loop = asyncio.get_event_loop()
            embeddings_list = await loop.run_in_executor(
                self._executor, self._embed_batch_sync, texts, batch_size, show_progress
            )

            logger.info(
                f"Generated {len(embeddings_list)} embeddings in batch "
                f"(batch_size={batch_size}, dimension={len(embeddings_list[0])})"
            )

            return embeddings_list

        except Exception as e:
            error_msg = f"Failed to generate batch embeddings: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _embed_batch_sync(
        self, texts: List[str], batch_size: int, show_progress: bool
    ) -> List[List[float]]:
        """
        Synchronous batch embedding generation (runs in thread pool).

        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            show_progress: Whether to show progress bar

        Returns:
            List[List[float]]: List of embedding vectors
        """
        # Generate embeddings in batch
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            show_progress_bar=show_progress,
        )

        # Convert to list of lists
        return embeddings.tolist()

    def get_model_info(self) -> dict:
        """
        Get information about the current model.

        Returns:
            dict: Model information including name, dimension, and max sequence length
        """
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_seq_length": self.model.max_seq_length,
            "cached": self.model_name in self._model_cache,
        }

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear the model cache.

        Useful for freeing memory when models are no longer needed.
        """
        cls._model_cache.clear()
        logger.info("Model cache cleared")
