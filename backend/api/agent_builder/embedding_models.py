"""
Embedding Models Management API.

Handles embedding model installation, listing, and management.
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.embedding_model_manager import EmbeddingModelManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/embedding-models",
    tags=["embedding-models"],
)


class ModelInfo(BaseModel):
    """Embedding model information"""
    model_id: str
    name: str
    provider: str
    dimension: int
    max_tokens: int
    installed: bool
    size_mb: float
    description: str


class InstallRequest(BaseModel):
    """Model installation request"""
    model_id: str


class InstallResponse(BaseModel):
    """Model installation response"""
    model_id: str
    success: bool
    message: str
    download_size_mb: float = 0
    install_time_seconds: float = 0


@router.get("/available", response_model=List[ModelInfo])
async def get_available_models(
    current_user: User = Depends(get_current_user),
):
    """
    Get list of available embedding models.
    
    Returns:
        List of available models with installation status
    """
    try:
        manager = EmbeddingModelManager()
        models = await manager.get_available_models()
        return models
    except Exception as e:
        logger.error(f"Failed to get available models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available models"
        )


@router.get("/installed", response_model=List[str])
async def get_installed_models(
    current_user: User = Depends(get_current_user),
):
    """
    Get list of installed embedding models.
    
    Returns:
        List of installed model IDs
    """
    try:
        manager = EmbeddingModelManager()
        models = await manager.get_installed_models()
        return models
    except Exception as e:
        logger.error(f"Failed to get installed models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve installed models"
        )


@router.post("/install", response_model=InstallResponse)
async def install_model(
    request: InstallRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Install an embedding model from Hugging Face.
    
    This will download the model if not already installed.
    
    Args:
        request: Installation request with model_id
        
    Returns:
        Installation result with status and metrics
    """
    try:
        logger.info(f"Installing model: {request.model_id} for user {current_user.id}")
        
        manager = EmbeddingModelManager()
        result = await manager.install_model(request.model_id)
        
        if result['success']:
            logger.info(
                f"Model {request.model_id} installed successfully: "
                f"size={result['download_size_mb']:.1f}MB, "
                f"time={result['install_time_seconds']:.1f}s"
            )
        else:
            logger.warning(f"Model {request.model_id} installation failed: {result['message']}")
        
        return InstallResponse(**result)
        
    except ValueError as e:
        logger.warning(f"Invalid model ID: {request.model_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to install model {request.model_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to install model: {str(e)}"
        )


@router.get("/check/{model_id}")
async def check_model_installed(
    model_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Check if a specific model is installed.
    
    Args:
        model_id: Model identifier
        
    Returns:
        Installation status
    """
    try:
        manager = EmbeddingModelManager()
        installed = await manager.is_model_installed(model_id)
        
        return {
            "model_id": model_id,
            "installed": installed
        }
    except Exception as e:
        logger.error(f"Failed to check model {model_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check model status"
        )


@router.delete("/{model_id}")
async def uninstall_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Uninstall an embedding model.
    
    Args:
        model_id: Model identifier
        
    Returns:
        Uninstallation result
    """
    try:
        logger.info(f"Uninstalling model: {model_id} by user {current_user.id}")
        
        manager = EmbeddingModelManager()
        result = await manager.uninstall_model(model_id)
        
        if result['success']:
            logger.info(f"Model {model_id} uninstalled successfully")
        else:
            logger.warning(f"Model {model_id} uninstallation failed: {result['message']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to uninstall model {model_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to uninstall model: {str(e)}"
        )
