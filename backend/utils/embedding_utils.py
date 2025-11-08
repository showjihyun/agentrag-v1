"""
Embedding Utilities

Provides utilities for embedding model management.
"""

import logging
from typing import Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Cache for loaded models
_model_cache = {}


def get_embedding_dimension(model_name: str) -> int:
    """
    Get the embedding dimension for a given model.
    
    Args:
        model_name: Name of the embedding model
        
    Returns:
        Embedding dimension
    """
    # Known model dimensions (for quick lookup)
    KNOWN_DIMENSIONS = {
        "jhgan/ko-sroberta-multitask": 768,
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": 768,
        "sentence-transformers/distiluse-base-multilingual-cased-v2": 512,
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "sentence-transformers/all-mpnet-base-v2": 768,
    }
    
    # Check if we know the dimension
    if model_name in KNOWN_DIMENSIONS:
        return KNOWN_DIMENSIONS[model_name]
    
    # Otherwise, load the model and get the dimension
    try:
        logger.info(f"Loading model to determine dimension: {model_name}")
        
        # Check cache first
        if model_name in _model_cache:
            model = _model_cache[model_name]
        else:
            model = SentenceTransformer(model_name)
            _model_cache[model_name] = model
        
        # Get dimension from model
        dimension = model.get_sentence_embedding_dimension()
        logger.info(f"Model {model_name} has dimension: {dimension}")
        
        return dimension
        
    except Exception as e:
        logger.error(f"Failed to get dimension for model {model_name}: {e}")
        # Default to 768 (most common)
        logger.warning(f"Using default dimension 768 for model {model_name}")
        return 768


def get_current_embedding_info() -> dict:
    """
    Get information about the current embedding model.
    
    Returns:
        Dictionary with model name and dimension
    """
    from backend.config import settings
    
    model_name = settings.EMBEDDING_MODEL
    dimension = get_embedding_dimension(model_name)
    
    return {
        "model_name": model_name,
        "dimension": dimension,
    }
