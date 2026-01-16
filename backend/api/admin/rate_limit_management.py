"""Admin API for rate limit management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.rate_limit_config import RateLimitTier, RateLimitScope
from backend.services.rate_limit_config_service import RateLimitConfigService


router = APIRouter(prefix="/rate-limits", tags=["admin-rate-limits"])


# Pydantic Models
class RateLimitConfigCreate(BaseModel):
    """Create rate limit config request."""
    scope: RateLimitScope
    scope_id: Optional[str] = None
    tier: RateLimitTier
    name: Optional[str] = None
    description: Optional[str] = None
    custom_limits: Optional[dict] = Field(
        None,
        description="Custom limits: {rpm: int, rph: int, rpd: int}"
    )
    endpoint_overrides: Optional[dict] = Field(
        None,
        description="Per-endpoint overrides: {'/api/path': {rpm: int, rph: int, rpd: int}}"
    )


class RateLimitConfigUpdate(BaseModel):
    """Update rate limit config request."""
    rpm: Optional[int] = None
    rph: Optional[int] = None
    rpd: Optional[int] = None
    endpoint_overrides: Optional[dict] = None
    is_active: Optional[bool] = None


class RateLimitOverrideCreate(BaseModel):
    """Create rate limit override request."""
    scope: RateLimitScope
    scope_id: str
    starts_at: datetime
    expires_at: datetime
    rpm: Optional[int] = None
    rph: Optional[int] = None
    rpd: Optional[int] = None
    reason: Optional[str] = None


class RateLimitConfigResponse(BaseModel):
    """Rate limit config response."""
    id: str
    scope: str
    scope_id: Optional[str]
    tier: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    endpoint_overrides: Optional[dict]
    is_active: bool
    name: Optional[str]
    description: Optional[str]
    created_at: str
    updated_at: str


class RateLimitOverrideResponse(BaseModel):
    """Rate limit override response."""
    id: str
    scope: str
    scope_id: str
    requests_per_minute: Optional[int]
    requests_per_hour: Optional[int]
    requests_per_day: Optional[int]
    starts_at: str
    expires_at: str
    is_active: bool
    reason: Optional[str]
    created_at: str


class TierInfo(BaseModel):
    """Tier information."""
    tier: str
    rpm: int
    rph: int
    rpd: int
    description: str


# Dependency: Check admin permission
def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Endpoints
@router.get("/tiers", response_model=List[TierInfo])
async def list_tiers(
    admin: User = Depends(require_admin)
):
    """List available rate limit tiers."""
    tiers = []
    for tier, config in RateLimitConfigService.TIER_DEFAULTS.items():
        tiers.append({
            "tier": tier.value,
            "rpm": config["rpm"],
            "rph": config["rph"],
            "rpd": config["rpd"],
            "description": config["description"]
        })
    return tiers


@router.post("/configs", response_model=RateLimitConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    config_data: RateLimitConfigCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create rate limit configuration."""
    service = RateLimitConfigService(db)
    
    try:
        config = service.create_config(
            scope=config_data.scope,
            scope_id=config_data.scope_id,
            tier=config_data.tier,
            created_by=str(admin.id),
            name=config_data.name,
            description=config_data.description,
            custom_limits=config_data.custom_limits,
            endpoint_overrides=config_data.endpoint_overrides
        )
        
        return {
            "id": str(config.id),
            "scope": config.scope.value,
            "scope_id": config.scope_id,
            "tier": config.tier.value,
            "requests_per_minute": config.requests_per_minute,
            "requests_per_hour": config.requests_per_hour,
            "requests_per_day": config.requests_per_day,
            "endpoint_overrides": config.endpoint_overrides,
            "is_active": config.is_active,
            "name": config.name,
            "description": config.description,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/configs", response_model=List[RateLimitConfigResponse])
async def list_configs(
    scope: Optional[RateLimitScope] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List rate limit configurations."""
    service = RateLimitConfigService(db)
    configs = service.list_configs(scope=scope, is_active=is_active, limit=limit)
    
    return [
        {
            "id": str(config.id),
            "scope": config.scope.value,
            "scope_id": config.scope_id,
            "tier": config.tier.value,
            "requests_per_minute": config.requests_per_minute,
            "requests_per_hour": config.requests_per_hour,
            "requests_per_day": config.requests_per_day,
            "endpoint_overrides": config.endpoint_overrides,
            "is_active": config.is_active,
            "name": config.name,
            "description": config.description,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
        for config in configs
    ]


@router.patch("/configs/{config_id}", response_model=RateLimitConfigResponse)
async def update_config(
    config_id: str,
    config_data: RateLimitConfigUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update rate limit configuration."""
    service = RateLimitConfigService(db)
    
    try:
        config = service.update_config(
            config_id=config_id,
            rpm=config_data.rpm,
            rph=config_data.rph,
            rpd=config_data.rpd,
            endpoint_overrides=config_data.endpoint_overrides,
            is_active=config_data.is_active
        )
        
        return {
            "id": str(config.id),
            "scope": config.scope.value,
            "scope_id": config.scope_id,
            "tier": config.tier.value,
            "requests_per_minute": config.requests_per_minute,
            "requests_per_hour": config.requests_per_hour,
            "requests_per_day": config.requests_per_day,
            "endpoint_overrides": config.endpoint_overrides,
            "is_active": config.is_active,
            "name": config.name,
            "description": config.description,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete rate limit configuration."""
    service = RateLimitConfigService(db)
    
    if not service.delete_config(config_id):
        raise HTTPException(status_code=404, detail="Config not found")


@router.post("/overrides", response_model=RateLimitOverrideResponse, status_code=status.HTTP_201_CREATED)
async def create_override(
    override_data: RateLimitOverrideCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create temporary rate limit override."""
    service = RateLimitConfigService(db)
    
    try:
        override = service.create_override(
            scope=override_data.scope,
            scope_id=override_data.scope_id,
            starts_at=override_data.starts_at,
            expires_at=override_data.expires_at,
            created_by=str(admin.id),
            rpm=override_data.rpm,
            rph=override_data.rph,
            rpd=override_data.rpd,
            reason=override_data.reason
        )
        
        return {
            "id": str(override.id),
            "scope": override.scope.value,
            "scope_id": override.scope_id,
            "requests_per_minute": override.requests_per_minute,
            "requests_per_hour": override.requests_per_hour,
            "requests_per_day": override.requests_per_day,
            "starts_at": override.starts_at.isoformat(),
            "expires_at": override.expires_at.isoformat(),
            "is_active": override.is_active,
            "reason": override.reason,
            "created_at": override.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/overrides", response_model=List[RateLimitOverrideResponse])
async def list_overrides(
    scope: Optional[RateLimitScope] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List rate limit overrides."""
    service = RateLimitConfigService(db)
    overrides = service.list_overrides(scope=scope, is_active=is_active, limit=limit)
    
    return [
        {
            "id": str(override.id),
            "scope": override.scope.value,
            "scope_id": override.scope_id,
            "requests_per_minute": override.requests_per_minute,
            "requests_per_hour": override.requests_per_hour,
            "requests_per_day": override.requests_per_day,
            "starts_at": override.starts_at.isoformat(),
            "expires_at": override.expires_at.isoformat(),
            "is_active": override.is_active,
            "reason": override.reason,
            "created_at": override.created_at.isoformat()
        }
        for override in overrides
    ]


@router.get("/usage/{identifier}")
async def get_usage_stats(
    identifier: str,
    window_type: str = "day",
    limit: int = 30,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get usage statistics for identifier."""
    service = RateLimitConfigService(db)
    usage_stats = service.get_usage_stats(identifier, window_type, limit)
    
    return [
        {
            "identifier": stat.identifier,
            "endpoint": stat.endpoint,
            "requests_count": stat.requests_count,
            "blocked_count": stat.blocked_count,
            "window_start": stat.window_start.isoformat(),
            "window_end": stat.window_end.isoformat(),
            "window_type": stat.window_type,
            "created_at": stat.created_at.isoformat()
        }
        for stat in usage_stats
    ]
