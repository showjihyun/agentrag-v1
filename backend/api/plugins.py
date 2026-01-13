"""
Plugin management API endpoints.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.models.plugin import PluginInfo, PluginManifest, PluginStatus, PluginCategory
from backend.services.plugins.manifest_validator import ManifestValidator

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("/health")
async def plugin_system_health():
    """Check plugin system health"""
    return {
        "status": "healthy",
        "message": "Plugin system is operational",
        "version": "1.0.0"
    }


@router.post("/validate-manifest")
async def validate_plugin_manifest(manifest_data: Dict[str, Any]):
    """Validate a plugin manifest"""
    try:
        validator = ManifestValidator()
        result = validator.validate_manifest_data(manifest_data)
        
        return {
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )


@router.get("/categories")
async def get_plugin_categories():
    """Get available plugin categories"""
    return {
        "categories": [category.value for category in PluginCategory]
    }


@router.get("/schema")
async def get_manifest_schema():
    """Get the plugin manifest JSON schema"""
    validator = ManifestValidator()
    return {
        "schema": validator.get_validation_schema(),
        "description": "JSON schema for plugin manifest validation"
    }