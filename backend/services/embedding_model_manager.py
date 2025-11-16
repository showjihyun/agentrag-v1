"""
Embedding Model Manager Service.

Manages embedding model installation, caching, and lifecycle.
"""

import os
import time
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class EmbeddingModelManager:
    """Manages embedding models from Hugging Face"""
    
    # Available models configuration
    AVAILABLE_MODELS = {
        "text-embedding-3-small": {
            "name": "OpenAI text-embedding-3-small",
            "provider": "OpenAI",
            "dimension": 1536,
            "max_tokens": 8191,
            "size_mb": 0,  # API-based, no download
            "description": "Fast and efficient OpenAI embedding model (API)",
            "requires_api_key": True,
        },
        "text-embedding-3-large": {
            "name": "OpenAI text-embedding-3-large",
            "provider": "OpenAI",
            "dimension": 3072,
            "max_tokens": 8191,
            "size_mb": 0,
            "description": "High-quality OpenAI embedding model (API)",
            "requires_api_key": True,
        },
        "text-embedding-ada-002": {
            "name": "OpenAI text-embedding-ada-002",
            "provider": "OpenAI",
            "dimension": 1536,
            "max_tokens": 8191,
            "size_mb": 0,
            "description": "Legacy OpenAI embedding model (API)",
            "requires_api_key": True,
        },
        "jhgan/ko-sroberta-multitask": {
            "name": "Korean SRoBERTa Multitask",
            "provider": "Hugging Face",
            "dimension": 768,
            "max_tokens": 512,
            "size_mb": 450,
            "description": "🇰🇷 BEST for Korean - Specialized multitask model",
            "requires_api_key": False,
        },
        "BM-K/KoSimCSE-roberta": {
            "name": "KoSimCSE RoBERTa",
            "provider": "Hugging Face",
            "dimension": 768,
            "max_tokens": 512,
            "size_mb": 440,
            "description": "🇰🇷 Excellent Korean semantic similarity model",
            "requires_api_key": False,
        },
        "sentence-transformers/paraphrase-multilingual-mpnet-base-v2": {
            "name": "Paraphrase Multilingual MPNet",
            "provider": "Hugging Face",
            "dimension": 768,
            "max_tokens": 128,
            "size_mb": 1100,
            "description": "🌏 Multilingual (includes Korean) - High quality",
            "requires_api_key": False,
        },
        "sentence-transformers/distiluse-base-multilingual-cased-v2": {
            "name": "DistilUSE Multilingual",
            "provider": "Hugging Face",
            "dimension": 512,
            "max_tokens": 128,
            "size_mb": 500,
            "description": "🌏 Multilingual (includes Korean) - Faster",
            "requires_api_key": False,
        },
        "sentence-transformers/all-MiniLM-L6-v2": {
            "name": "All MiniLM L6 v2",
            "provider": "Hugging Face",
            "dimension": 384,
            "max_tokens": 256,
            "size_mb": 90,
            "description": "Fast and lightweight multilingual model",
            "requires_api_key": False,
        },
        "sentence-transformers/all-mpnet-base-v2": {
            "name": "All MPNet Base v2",
            "provider": "Hugging Face",
            "dimension": 768,
            "max_tokens": 384,
            "size_mb": 420,
            "description": "High-quality multilingual model",
            "requires_api_key": False,
        },
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {
            "name": "Paraphrase Multilingual MiniLM",
            "provider": "Hugging Face",
            "dimension": 384,
            "max_tokens": 128,
            "size_mb": 470,
            "description": "Multilingual paraphrase detection model",
            "requires_api_key": False,
        },
    }
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the model manager.
        
        Args:
            cache_dir: Directory to cache downloaded models
        """
        self.cache_dir = cache_dir or os.path.join(
            os.path.expanduser("~"), ".cache", "agenticrag", "models"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Model cache directory: {self.cache_dir}")
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of all available embedding models.
        
        Returns:
            List of model information dictionaries
        """
        models = []
        
        for model_id, info in self.AVAILABLE_MODELS.items():
            installed = await self.is_model_installed(model_id)
            
            models.append({
                "model_id": model_id,
                "name": info["name"],
                "provider": info["provider"],
                "dimension": info["dimension"],
                "max_tokens": info["max_tokens"],
                "installed": installed,
                "size_mb": info["size_mb"],
                "description": info["description"],
                "requires_api_key": info.get("requires_api_key", False),
            })
        
        return models
    
    async def get_installed_models(self) -> List[str]:
        """
        Get list of installed model IDs.
        
        Returns:
            List of installed model IDs
        """
        installed = []
        
        for model_id in self.AVAILABLE_MODELS.keys():
            if await self.is_model_installed(model_id):
                installed.append(model_id)
        
        return installed
    
    async def is_model_installed(self, model_id: str) -> bool:
        """
        Check if a model is installed.
        
        Args:
            model_id: Model identifier
            
        Returns:
            True if installed, False otherwise
        """
        if model_id not in self.AVAILABLE_MODELS:
            return False
        
        info = self.AVAILABLE_MODELS[model_id]
        
        # API-based models are always "installed" if API key is configured
        if info.get("requires_api_key", False):
            # Check if OpenAI API key is configured
            return os.getenv("OPENAI_API_KEY") is not None
        
        # Check if model is cached locally
        model_path = self._get_model_path(model_id)
        return os.path.exists(model_path)
    
    async def install_model(self, model_id: str) -> Dict[str, Any]:
        """
        Install a model from Hugging Face.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Installation result dictionary
        """
        if model_id not in self.AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_id}")
        
        info = self.AVAILABLE_MODELS[model_id]
        
        # Check if already installed
        if await self.is_model_installed(model_id):
            return {
                "model_id": model_id,
                "success": True,
                "message": "Model already installed",
                "download_size_mb": 0,
                "install_time_seconds": 0,
            }
        
        # API-based models don't need installation
        if info.get("requires_api_key", False):
            if not os.getenv("OPENAI_API_KEY"):
                return {
                    "model_id": model_id,
                    "success": False,
                    "message": "OpenAI API key not configured",
                    "download_size_mb": 0,
                    "install_time_seconds": 0,
                }
            return {
                "model_id": model_id,
                "success": True,
                "message": "API-based model ready",
                "download_size_mb": 0,
                "install_time_seconds": 0,
            }
        
        # Download from Hugging Face
        start_time = time.time()
        
        try:
            logger.info(f"Downloading model {model_id} from Hugging Face...")
            
            # Import here to avoid loading heavy dependencies at startup
            from sentence_transformers import SentenceTransformer
            
            # Download and cache the model
            model = SentenceTransformer(
                model_id,
                cache_folder=self.cache_dir
            )
            
            install_time = time.time() - start_time
            
            logger.info(
                f"Model {model_id} downloaded successfully in {install_time:.1f}s"
            )
            
            return {
                "model_id": model_id,
                "success": True,
                "message": "Model installed successfully",
                "download_size_mb": info["size_mb"],
                "install_time_seconds": install_time,
            }
            
        except Exception as e:
            install_time = time.time() - start_time
            logger.error(f"Failed to install model {model_id}: {e}", exc_info=True)
            
            return {
                "model_id": model_id,
                "success": False,
                "message": f"Installation failed: {str(e)}",
                "download_size_mb": 0,
                "install_time_seconds": install_time,
            }
    
    async def uninstall_model(self, model_id: str) -> Dict[str, Any]:
        """
        Uninstall a model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Uninstallation result dictionary
        """
        if model_id not in self.AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_id}")
        
        info = self.AVAILABLE_MODELS[model_id]
        
        # Can't uninstall API-based models
        if info.get("requires_api_key", False):
            return {
                "model_id": model_id,
                "success": False,
                "message": "Cannot uninstall API-based models",
            }
        
        model_path = self._get_model_path(model_id)
        
        if not os.path.exists(model_path):
            return {
                "model_id": model_id,
                "success": True,
                "message": "Model not installed",
            }
        
        try:
            # Remove model directory
            shutil.rmtree(model_path)
            
            logger.info(f"Model {model_id} uninstalled successfully")
            
            return {
                "model_id": model_id,
                "success": True,
                "message": "Model uninstalled successfully",
            }
            
        except Exception as e:
            logger.error(f"Failed to uninstall model {model_id}: {e}", exc_info=True)
            
            return {
                "model_id": model_id,
                "success": False,
                "message": f"Uninstallation failed: {str(e)}",
            }
    
    def _get_model_path(self, model_id: str) -> str:
        """
        Get the local path for a model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Local path to model
        """
        # Convert model ID to safe directory name
        safe_name = model_id.replace("/", "_")
        return os.path.join(self.cache_dir, safe_name)
