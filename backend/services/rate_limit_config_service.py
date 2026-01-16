"""Rate limit configuration service."""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from backend.db.models.rate_limit_config import (
    RateLimitConfig,
    RateLimitOverride,
    RateLimitUsage,
    RateLimitTier,
    RateLimitScope
)

logger = logging.getLogger(__name__)


class RateLimitConfigService:
    """Service for managing rate limit configurations."""
    
    # Default tier configurations
    TIER_DEFAULTS = {
        RateLimitTier.FREE: {
            "rpm": 30,
            "rph": 500,
            "rpd": 5000,
            "description": "Free tier - Basic usage"
        },
        RateLimitTier.BASIC: {
            "rpm": 60,
            "rph": 1000,
            "rpd": 10000,
            "description": "Basic tier - Standard usage"
        },
        RateLimitTier.PRO: {
            "rpm": 120,
            "rph": 2000,
            "rpd": 20000,
            "description": "Pro tier - Professional usage"
        },
        RateLimitTier.BUSINESS: {
            "rpm": 300,
            "rph": 5000,
            "rpd": 50000,
            "description": "Business tier - High volume"
        },
        RateLimitTier.ENTERPRISE: {
            "rpm": 1000,
            "rph": 20000,
            "rpd": 200000,
            "description": "Enterprise tier - Unlimited usage"
        },
    }
    
    def __init__(self, db: Session):
        """Initialize service."""
        self.db = db
    
    def get_rate_limit_for_identifier(
        self,
        identifier: str,
        endpoint: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Get rate limit configuration for an identifier.
        
        Priority:
        1. Active override
        2. User-specific config
        3. Organization config
        4. API key config
        5. Global default
        
        Args:
            identifier: User ID, IP, or API key
            endpoint: Optional endpoint path
            
        Returns:
            Dict with rpm, rph, rpd
        """
        try:
            # Check for active override
            override = self._get_active_override(identifier)
            if override:
                return {
                    "rpm": override.requests_per_minute or 0,
                    "rph": override.requests_per_hour or 0,
                    "rpd": override.requests_per_day or 0,
                }
            
            # Check for user/org/api_key specific config
            config = self._get_config_for_identifier(identifier)
            
            if config:
                limits = {
                    "rpm": config.requests_per_minute,
                    "rph": config.requests_per_hour,
                    "rpd": config.requests_per_day,
                }
                
                # Apply endpoint-specific overrides if available
                if endpoint and config.endpoint_overrides:
                    endpoint_config = config.endpoint_overrides.get(endpoint, {})
                    if endpoint_config:
                        limits["rpm"] = endpoint_config.get("rpm", limits["rpm"])
                        limits["rph"] = endpoint_config.get("rph", limits["rph"])
                        limits["rpd"] = endpoint_config.get("rpd", limits["rpd"])
                
                return limits
            
            # Return default (Basic tier)
            defaults = self.TIER_DEFAULTS[RateLimitTier.BASIC]
            return {
                "rpm": defaults["rpm"],
                "rph": defaults["rph"],
                "rpd": defaults["rpd"],
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit for {identifier}: {e}")
            # Return safe defaults on error
            return {"rpm": 60, "rph": 1000, "rpd": 10000}
    
    def _get_active_override(self, identifier: str) -> Optional[RateLimitOverride]:
        """Get active override for identifier."""
        now = datetime.utcnow()
        
        return self.db.query(RateLimitOverride).filter(
            and_(
                RateLimitOverride.scope_id == identifier,
                RateLimitOverride.is_active == True,
                RateLimitOverride.starts_at <= now,
                RateLimitOverride.expires_at >= now
            )
        ).first()
    
    def _get_config_for_identifier(self, identifier: str) -> Optional[RateLimitConfig]:
        """Get config for identifier (user, org, or api_key)."""
        return self.db.query(RateLimitConfig).filter(
            and_(
                RateLimitConfig.scope_id == identifier,
                RateLimitConfig.is_active == True
            )
        ).first()
    
    def create_config(
        self,
        scope: RateLimitScope,
        scope_id: Optional[str],
        tier: RateLimitTier,
        created_by: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        custom_limits: Optional[Dict[str, int]] = None,
        endpoint_overrides: Optional[Dict[str, Dict[str, int]]] = None
    ) -> RateLimitConfig:
        """
        Create rate limit configuration.
        
        Args:
            scope: Scope type (global, organization, user, api_key)
            scope_id: ID for the scope (None for global)
            tier: Rate limit tier
            created_by: User ID creating the config
            name: Optional name
            description: Optional description
            custom_limits: Optional custom limits (rpm, rph, rpd)
            endpoint_overrides: Optional per-endpoint overrides
            
        Returns:
            Created config
        """
        # Get tier defaults
        tier_defaults = self.TIER_DEFAULTS.get(tier, self.TIER_DEFAULTS[RateLimitTier.BASIC])
        
        # Use custom limits if provided, otherwise use tier defaults
        if custom_limits:
            rpm = custom_limits.get("rpm", tier_defaults["rpm"])
            rph = custom_limits.get("rph", tier_defaults["rph"])
            rpd = custom_limits.get("rpd", tier_defaults["rpd"])
        else:
            rpm = tier_defaults["rpm"]
            rph = tier_defaults["rph"]
            rpd = tier_defaults["rpd"]
        
        config = RateLimitConfig(
            scope=scope,
            scope_id=scope_id,
            tier=tier,
            requests_per_minute=rpm,
            requests_per_hour=rph,
            requests_per_day=rpd,
            endpoint_overrides=endpoint_overrides,
            name=name,
            description=description or tier_defaults["description"],
            created_by=created_by,
        )
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        logger.info(f"Created rate limit config: {config.id} for {scope}:{scope_id}")
        
        return config
    
    def update_config(
        self,
        config_id: str,
        rpm: Optional[int] = None,
        rph: Optional[int] = None,
        rpd: Optional[int] = None,
        endpoint_overrides: Optional[Dict[str, Dict[str, int]]] = None,
        is_active: Optional[bool] = None
    ) -> RateLimitConfig:
        """Update rate limit configuration."""
        config = self.db.query(RateLimitConfig).filter(
            RateLimitConfig.id == config_id
        ).first()
        
        if not config:
            raise ValueError(f"Config {config_id} not found")
        
        if rpm is not None:
            config.requests_per_minute = rpm
        if rph is not None:
            config.requests_per_hour = rph
        if rpd is not None:
            config.requests_per_day = rpd
        if endpoint_overrides is not None:
            config.endpoint_overrides = endpoint_overrides
        if is_active is not None:
            config.is_active = is_active
        
        config.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(config)
        
        logger.info(f"Updated rate limit config: {config_id}")
        
        return config
    
    def create_override(
        self,
        scope: RateLimitScope,
        scope_id: str,
        starts_at: datetime,
        expires_at: datetime,
        created_by: str,
        rpm: Optional[int] = None,
        rph: Optional[int] = None,
        rpd: Optional[int] = None,
        reason: Optional[str] = None
    ) -> RateLimitOverride:
        """Create temporary rate limit override."""
        override = RateLimitOverride(
            scope=scope,
            scope_id=scope_id,
            requests_per_minute=rpm,
            requests_per_hour=rph,
            requests_per_day=rpd,
            starts_at=starts_at,
            expires_at=expires_at,
            reason=reason,
            created_by=created_by,
        )
        
        self.db.add(override)
        self.db.commit()
        self.db.refresh(override)
        
        logger.info(f"Created rate limit override: {override.id} for {scope}:{scope_id}")
        
        return override
    
    def list_configs(
        self,
        scope: Optional[RateLimitScope] = None,
        is_active: Optional[bool] = None,
        limit: int = 100
    ) -> List[RateLimitConfig]:
        """List rate limit configurations."""
        query = self.db.query(RateLimitConfig)
        
        if scope:
            query = query.filter(RateLimitConfig.scope == scope)
        if is_active is not None:
            query = query.filter(RateLimitConfig.is_active == is_active)
        
        return query.order_by(RateLimitConfig.created_at.desc()).limit(limit).all()
    
    def list_overrides(
        self,
        scope: Optional[RateLimitScope] = None,
        is_active: Optional[bool] = None,
        limit: int = 100
    ) -> List[RateLimitOverride]:
        """List rate limit overrides."""
        query = self.db.query(RateLimitOverride)
        
        if scope:
            query = query.filter(RateLimitOverride.scope == scope)
        if is_active is not None:
            query = query.filter(RateLimitOverride.is_active == is_active)
        
        return query.order_by(RateLimitOverride.created_at.desc()).limit(limit).all()
    
    def delete_config(self, config_id: str) -> bool:
        """Delete rate limit configuration."""
        config = self.db.query(RateLimitConfig).filter(
            RateLimitConfig.id == config_id
        ).first()
        
        if not config:
            return False
        
        self.db.delete(config)
        self.db.commit()
        
        logger.info(f"Deleted rate limit config: {config_id}")
        
        return True
    
    def get_usage_stats(
        self,
        identifier: str,
        window_type: str = "day",
        limit: int = 30
    ) -> List[RateLimitUsage]:
        """Get usage statistics for identifier."""
        return self.db.query(RateLimitUsage).filter(
            and_(
                RateLimitUsage.identifier == identifier,
                RateLimitUsage.window_type == window_type
            )
        ).order_by(RateLimitUsage.window_start.desc()).limit(limit).all()
