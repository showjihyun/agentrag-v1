"""API endpoints for LLM model management."""

import logging
import httpx
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status

from backend.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/ollama/list")
async def list_ollama_models() -> Dict[str, Any]:
    """
    Get list of locally installed Ollama models.

    Returns:
        Dictionary with:
        - models: List of model information
        - current: Currently configured model
        - provider: LLM provider (ollama)
    """
    try:
        # Get Ollama base URL from settings
        ollama_base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

        # Call Ollama API to get model list
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ollama_base_url}/api/tags")

            if response.status_code != 200:
                logger.error(f"Failed to fetch Ollama models: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ollama service is not available. Please ensure Ollama is running.",
                )

            data = response.json()
            models = data.get("models", [])

            # Format model information
            formatted_models = []
            for model in models:
                formatted_models.append(
                    {
                        "name": model.get("name"),
                        "model": model.get("model"),
                        "size": model.get("size"),
                        "modified_at": model.get("modified_at"),
                        "digest": model.get("digest"),
                        "details": model.get("details", {}),
                    }
                )

            # Get current model from settings
            current_model = settings.LLM_MODEL

            logger.info(f"Found {len(formatted_models)} Ollama models")

            return {
                "models": formatted_models,
                "current": current_model,
                "provider": settings.LLM_PROVIDER,
                "ollama_url": ollama_base_url,
            }

    except httpx.ConnectError:
        logger.error("Cannot connect to Ollama service")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot connect to Ollama. Please ensure Ollama is running on your system.",
        )
    except Exception as e:
        logger.error(f"Error fetching Ollama models: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch Ollama models: {str(e)}",
        )


@router.get("/current")
async def get_current_model() -> Dict[str, str]:
    """
    Get currently configured LLM model.

    Returns:
        Dictionary with provider and model information
    """
    return {"provider": settings.LLM_PROVIDER, "model": settings.LLM_MODEL}
