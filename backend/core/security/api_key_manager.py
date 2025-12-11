"""
Secure API Key Management

Provides secure API key generation, rotation, and validation.
"""

import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from backend.core.structured_logging import get_logger
from backend.db.models.user import User

logger = get_logger(__name__)


class APIKeyManager:
    """Manage API keys securely"""
    
    def __init__(self, encryption_key: bytes):
        """
        Initialize API key manager
        
        Args:
            encryption_key: Fernet encryption key (32 url-safe base64-encoded bytes)
        """
        self.cipher = Fernet(encryption_key)
        self.logger = get_logger(__name__)
    
    def generate_key(self) -> str:
        """
        Generate a secure random API key
        
        Returns:
            API key in format: agr_<random_string>
        """
        # Generate 32 bytes of random data
        random_bytes = secrets.token_urlsafe(32)
        
        # Add prefix for identification
        api_key = f"agr_{random_bytes}"
        
        return api_key
    
    def hash_key(self, api_key: str) -> str:
        """
        Hash API key for secure storage
        
        Args:
            api_key: Raw API key
            
        Returns:
            SHA-256 hash of the key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    async def create_key(
        self,
        db: Session,
        user_id: int,
        name: str,
        expires_in_days: int = 90,
        scopes: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Create new API key for user
        
        Args:
            db: Database session
            user_id: User ID
            name: Key name/description
            expires_in_days: Days until expiration
            scopes: List of allowed scopes/permissions
            
        Returns:
            Dictionary with key info (raw key only returned once!)
        """
        from backend.db.models.api_keys import APIKey
        
        # Generate key
        raw_key = self.generate_key()
        key_hash = self.hash_key(raw_key)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create database record
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=raw_key[:12],  # Store prefix for identification
            expires_at=expires_at,
            scopes=scopes or [],
            last_used_at=None,
            usage_count=0,
            is_active=True
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        self.logger.info(
            "api_key_created",
            user_id=user_id,
            key_id=api_key.id,
            name=name,
            expires_at=expires_at.isoformat()
        )
        
        # Return key info (raw key only shown once!)
        return {
            "id": api_key.id,
            "key": raw_key,  # ⚠️ Only returned once!
            "name": name,
            "prefix": api_key.key_prefix,
            "expires_at": expires_at.isoformat(),
            "scopes": scopes or [],
            "created_at": api_key.created_at.isoformat()
        }
    
    async def validate_key(
        self,
        db: Session,
        api_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate API key and return user info
        
        Args:
            db: Database session
            api_key: Raw API key to validate
            
        Returns:
            User info if valid, None if invalid
        """
        from backend.db.models.api_keys import APIKey
        
        # Hash the provided key
        key_hash = self.hash_key(api_key)
        
        # Find key in database
        db_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
        
        if not db_key:
            self.logger.warning("api_key_validation_failed", reason="key_not_found")
            return None
        
        # Check expiration
        if db_key.expires_at and db_key.expires_at < datetime.utcnow():
            self.logger.warning(
                "api_key_validation_failed",
                reason="expired",
                key_id=db_key.id
            )
            return None
        
        # Update usage stats
        db_key.last_used_at = datetime.utcnow()
        db_key.usage_count += 1
        db.commit()
        
        # Get user
        user = db.query(User).filter(User.id == db_key.user_id).first()
        
        if not user:
            self.logger.error(
                "api_key_validation_failed",
                reason="user_not_found",
                key_id=db_key.id
            )
            return None
        
        self.logger.debug(
            "api_key_validated",
            key_id=db_key.id,
            user_id=user.id
        )
        
        return {
            "user_id": user.id,
            "user_email": user.email,
            "key_id": db_key.id,
            "key_name": db_key.name,
            "scopes": db_key.scopes
        }
    
    async def rotate_key(
        self,
        db: Session,
        key_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Rotate existing API key (create new, mark old as rotated)
        
        Args:
            db: Database session
            key_id: ID of key to rotate
            user_id: User ID (for verification)
            
        Returns:
            New key info
        """
        from backend.db.models.api_keys import APIKey
        
        # Get old key
        old_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not old_key:
            raise ValueError("API key not found")
        
        # Create new key with same settings
        new_key_info = await self.create_key(
            db=db,
            user_id=user_id,
            name=f"{old_key.name} (rotated)",
            expires_in_days=90,
            scopes=old_key.scopes
        )
        
        # Mark old key as rotated
        old_key.is_active = False
        old_key.rotated_at = datetime.utcnow()
        old_key.rotated_to_id = new_key_info["id"]
        db.commit()
        
        self.logger.info(
            "api_key_rotated",
            old_key_id=key_id,
            new_key_id=new_key_info["id"],
            user_id=user_id
        )
        
        return new_key_info
    
    async def revoke_key(
        self,
        db: Session,
        key_id: int,
        user_id: int
    ) -> bool:
        """
        Revoke API key
        
        Args:
            db: Database session
            key_id: ID of key to revoke
            user_id: User ID (for verification)
            
        Returns:
            True if revoked successfully
        """
        from backend.db.models.api_keys import APIKey
        
        # Get key
        api_key = db.query(APIKey).filter(
            APIKey.id == key_id,
            APIKey.user_id == user_id
        ).first()
        
        if not api_key:
            return False
        
        # Revoke key
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        db.commit()
        
        self.logger.info(
            "api_key_revoked",
            key_id=key_id,
            user_id=user_id
        )
        
        return True
    
    async def list_keys(
        self,
        db: Session,
        user_id: int,
        include_inactive: bool = False
    ) -> list:
        """
        List all API keys for user
        
        Args:
            db: Database session
            user_id: User ID
            include_inactive: Include revoked/expired keys
            
        Returns:
            List of key info (without raw keys)
        """
        from backend.db.models.api_keys import APIKey
        
        query = db.query(APIKey).filter(APIKey.user_id == user_id)
        
        if not include_inactive:
            query = query.filter(APIKey.is_active == True)
        
        keys = query.order_by(APIKey.created_at.desc()).all()
        
        return [
            {
                "id": key.id,
                "name": key.name,
                "prefix": key.key_prefix,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "usage_count": key.usage_count,
                "is_active": key.is_active,
                "scopes": key.scopes,
                "created_at": key.created_at.isoformat()
            }
            for key in keys
        ]
    
    async def check_expiring_keys(
        self,
        db: Session,
        days_threshold: int = 7
    ) -> list:
        """
        Find keys expiring soon
        
        Args:
            db: Database session
            days_threshold: Days before expiration to alert
            
        Returns:
            List of expiring keys
        """
        from backend.db.models.api_keys import APIKey
        
        threshold_date = datetime.utcnow() + timedelta(days=days_threshold)
        
        expiring_keys = db.query(APIKey).filter(
            APIKey.is_active == True,
            APIKey.expires_at <= threshold_date,
            APIKey.expires_at > datetime.utcnow()
        ).all()
        
        return [
            {
                "id": key.id,
                "user_id": key.user_id,
                "name": key.name,
                "expires_at": key.expires_at.isoformat(),
                "days_until_expiration": (key.expires_at - datetime.utcnow()).days
            }
            for key in expiring_keys
        ]
    
    async def auto_rotate_expiring_keys(
        self,
        db: Session,
        days_threshold: int = 7
    ) -> int:
        """
        Automatically rotate keys expiring soon
        
        Args:
            db: Database session
            days_threshold: Days before expiration to auto-rotate
            
        Returns:
            Number of keys rotated
        """
        expiring_keys = await self.check_expiring_keys(db, days_threshold)
        
        rotated_count = 0
        for key_info in expiring_keys:
            try:
                await self.rotate_key(
                    db=db,
                    key_id=key_info["id"],
                    user_id=key_info["user_id"]
                )
                rotated_count += 1
            except Exception as e:
                self.logger.error(
                    "auto_rotation_failed",
                    key_id=key_info["id"],
                    error=str(e)
                )
        
        self.logger.info(
            "auto_rotation_completed",
            rotated_count=rotated_count
        )
        
        return rotated_count


# Global instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager(encryption_key: Optional[bytes] = None) -> APIKeyManager:
    """
    Get global API key manager instance
    
    Args:
        encryption_key: Encryption key (required on first call)
        
    Returns:
        APIKeyManager instance
    """
    global _api_key_manager
    
    if _api_key_manager is None:
        if encryption_key is None:
            # Generate key from environment or config
            import os
            key_str = os.getenv("API_KEY_ENCRYPTION_KEY")
            if not key_str:
                # Generate new key (should be stored securely!)
                encryption_key = Fernet.generate_key()
                logger.warning(
                    "api_key_encryption_key_generated",
                    message="Store this key securely!"
                )
            else:
                encryption_key = key_str.encode()
        
        _api_key_manager = APIKeyManager(encryption_key)
    
    return _api_key_manager
