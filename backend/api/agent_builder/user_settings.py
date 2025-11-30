"""
User Settings API for Agent Builder

Provides endpoints for managing user preferences including:
- Notification settings
- Security settings
- Appearance settings
- LLM configuration
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import logging
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/user-settings", tags=["User Settings"])


# ============================================================================
# Models
# ============================================================================

class EmailDigestFrequency(str, Enum):
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    NEVER = "never"


class TwoFactorMethod(str, Enum):
    APP = "app"
    SMS = "sms"
    EMAIL = "email"


class ThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class NotificationSettings(BaseModel):
    """Notification preferences"""
    email_enabled: bool = True
    email_address: Optional[str] = None
    email_on_workflow_complete: bool = False
    email_on_workflow_error: bool = True
    email_on_agent_alert: bool = True
    email_digest_frequency: EmailDigestFrequency = EmailDigestFrequency.DAILY
    
    in_app_enabled: bool = True
    in_app_on_workflow_complete: bool = True
    in_app_on_workflow_error: bool = True
    in_app_on_agent_alert: bool = True
    in_app_on_system_update: bool = True
    
    slack_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    slack_on_workflow_complete: bool = False
    slack_on_workflow_error: bool = True
    
    browser_enabled: bool = False
    browser_on_workflow_complete: bool = False
    browser_on_workflow_error: bool = True


class SecuritySettings(BaseModel):
    """Security preferences"""
    require_strong_password: bool = True
    password_min_length: int = Field(default=8, ge=6, le=32)
    
    session_timeout: int = Field(default=30, ge=5, le=480)  # minutes
    single_session: bool = False
    
    two_factor_enabled: bool = False
    two_factor_method: TwoFactorMethod = TwoFactorMethod.APP
    
    api_rate_limit_enabled: bool = True
    api_rate_limit_requests: int = Field(default=100, ge=10, le=10000)
    api_rate_limit_window: int = Field(default=60, ge=10, le=3600)  # seconds
    
    audit_logging_enabled: bool = True
    log_api_calls: bool = True
    log_workflow_executions: bool = True
    log_login_attempts: bool = True


class AppearanceSettings(BaseModel):
    """Appearance preferences"""
    theme: ThemeMode = ThemeMode.SYSTEM
    accent_color: str = Field(default="#3b82f6", pattern=r"^#[0-9a-fA-F]{6}$")
    
    font_size: int = Field(default=14, ge=10, le=24)
    font_family: str = "system"
    
    sidebar_collapsed: bool = False
    compact_mode: bool = False
    show_breadcrumbs: bool = True
    
    editor_font_size: int = Field(default=14, ge=10, le=24)
    editor_line_numbers: bool = True
    editor_word_wrap: bool = True
    editor_minimap: bool = True
    
    reduce_motion: bool = False
    high_contrast: bool = False


class LLMSettings(BaseModel):
    """LLM configuration"""
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"
    
    ollama_enabled: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.1"
    
    # API keys are stored separately for security


class AllUserSettings(BaseModel):
    """Combined user settings"""
    notifications: NotificationSettings = NotificationSettings()
    security: SecuritySettings = SecuritySettings()
    appearance: AppearanceSettings = AppearanceSettings()
    llm: LLMSettings = LLMSettings()
    updated_at: Optional[datetime] = None


# In-memory storage (in production, use database)
_user_settings: Dict[int, Dict[str, Any]] = {}


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=AllUserSettings)
async def get_all_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user settings."""
    user_id = current_user.id
    settings = _user_settings.get(user_id, {})
    
    return AllUserSettings(
        notifications=NotificationSettings(**settings.get("notifications", {})),
        security=SecuritySettings(**settings.get("security", {})),
        appearance=AppearanceSettings(**settings.get("appearance", {})),
        llm=LLMSettings(**settings.get("llm", {})),
        updated_at=settings.get("updated_at")
    )


@router.put("", response_model=AllUserSettings)
async def update_all_settings(
    settings_data: AllUserSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update all user settings."""
    user_id = current_user.id
    
    _user_settings[user_id] = {
        "notifications": settings_data.notifications.model_dump(),
        "security": settings_data.security.model_dump(),
        "appearance": settings_data.appearance.model_dump(),
        "llm": settings_data.llm.model_dump(),
        "updated_at": datetime.utcnow()
    }
    
    logger.info(f"User {user_id} updated all settings")
    
    return AllUserSettings(
        **_user_settings[user_id],
        updated_at=_user_settings[user_id]["updated_at"]
    )


@router.get("/notifications", response_model=NotificationSettings)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification settings."""
    user_id = current_user.id
    settings = _user_settings.get(user_id, {}).get("notifications", {})
    return NotificationSettings(**settings)


@router.put("/notifications", response_model=NotificationSettings)
async def update_notification_settings(
    settings_data: NotificationSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification settings."""
    user_id = current_user.id
    
    if user_id not in _user_settings:
        _user_settings[user_id] = {}
    
    _user_settings[user_id]["notifications"] = settings_data.model_dump()
    _user_settings[user_id]["updated_at"] = datetime.utcnow()
    
    logger.info(f"User {user_id} updated notification settings")
    return settings_data


@router.get("/security", response_model=SecuritySettings)
async def get_security_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get security settings."""
    user_id = current_user.id
    settings = _user_settings.get(user_id, {}).get("security", {})
    return SecuritySettings(**settings)


@router.put("/security", response_model=SecuritySettings)
async def update_security_settings(
    settings_data: SecuritySettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update security settings."""
    user_id = current_user.id
    
    if user_id not in _user_settings:
        _user_settings[user_id] = {}
    
    _user_settings[user_id]["security"] = settings_data.model_dump()
    _user_settings[user_id]["updated_at"] = datetime.utcnow()
    
    logger.info(f"User {user_id} updated security settings")
    return settings_data


@router.get("/appearance", response_model=AppearanceSettings)
async def get_appearance_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get appearance settings."""
    user_id = current_user.id
    settings = _user_settings.get(user_id, {}).get("appearance", {})
    return AppearanceSettings(**settings)


@router.put("/appearance", response_model=AppearanceSettings)
async def update_appearance_settings(
    settings_data: AppearanceSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update appearance settings."""
    user_id = current_user.id
    
    if user_id not in _user_settings:
        _user_settings[user_id] = {}
    
    _user_settings[user_id]["appearance"] = settings_data.model_dump()
    _user_settings[user_id]["updated_at"] = datetime.utcnow()
    
    logger.info(f"User {user_id} updated appearance settings")
    return settings_data


@router.get("/llm", response_model=LLMSettings)
async def get_llm_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get LLM configuration settings."""
    user_id = current_user.id
    settings = _user_settings.get(user_id, {}).get("llm", {})
    return LLMSettings(**settings)


@router.put("/llm", response_model=LLMSettings)
async def update_llm_settings(
    settings_data: LLMSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update LLM configuration settings."""
    user_id = current_user.id
    
    if user_id not in _user_settings:
        _user_settings[user_id] = {}
    
    _user_settings[user_id]["llm"] = settings_data.model_dump()
    _user_settings[user_id]["updated_at"] = datetime.utcnow()
    
    logger.info(f"User {user_id} updated LLM settings")
    return settings_data


@router.post("/reset")
async def reset_settings(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset settings to defaults.
    
    Args:
        category: Optional category to reset (notifications, security, appearance, llm).
                  If not provided, resets all settings.
    """
    user_id = current_user.id
    
    if category:
        if category not in ["notifications", "security", "appearance", "llm"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}"
            )
        
        if user_id in _user_settings and category in _user_settings[user_id]:
            del _user_settings[user_id][category]
            logger.info(f"User {user_id} reset {category} settings")
    else:
        if user_id in _user_settings:
            del _user_settings[user_id]
            logger.info(f"User {user_id} reset all settings")
    
    return {"message": f"Settings reset successfully", "category": category or "all"}


@router.post("/export")
async def export_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export all user settings as JSON."""
    user_id = current_user.id
    settings = _user_settings.get(user_id, {})
    
    return {
        "user_id": str(user_id),
        "exported_at": datetime.utcnow().isoformat(),
        "settings": settings
    }


@router.post("/import")
async def import_settings(
    settings_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import user settings from JSON."""
    user_id = current_user.id
    
    try:
        # Validate each category
        if "notifications" in settings_data:
            NotificationSettings(**settings_data["notifications"])
        if "security" in settings_data:
            SecuritySettings(**settings_data["security"])
        if "appearance" in settings_data:
            AppearanceSettings(**settings_data["appearance"])
        if "llm" in settings_data:
            LLMSettings(**settings_data["llm"])
        
        # Import settings
        _user_settings[user_id] = {
            **settings_data,
            "updated_at": datetime.utcnow()
        }
        
        logger.info(f"User {user_id} imported settings")
        
        return {"message": "Settings imported successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid settings format: {str(e)}"
        )
