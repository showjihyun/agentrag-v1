"""Service for managing user API keys."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.db.models.agent_builder import UserAPIKey
from backend.models.agent_builder import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
)
from backend.utils.encryption import encryption_service

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing user API keys."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_api_key(
        self,
        user_id: str,
        api_key_data: APIKeyCreate
    ) -> UserAPIKey:
        """
        Create a new API key for a user.
        
        Args:
            user_id: User ID
            api_key_data: API key creation data
            
        Returns:
            Created UserAPIKey instance
        """
        # Encrypt the API key
        encrypted_key = encryption_service.encrypt(api_key_data.api_key)
        
        # Check if key already exists for this service
        existing_key = self.db.query(UserAPIKey).filter(
            and_(
                UserAPIKey.user_id == user_id,
                UserAPIKey.service_name == api_key_data.service_name
            )
        ).first()
        
        if existing_key:
            # Update existing key
            existing_key.encrypted_api_key = encrypted_key
            existing_key.service_display_name = api_key_data.service_display_name
            existing_key.description = api_key_data.description
            existing_key.is_active = True
            existing_key.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_key)
            
            logger.info(f"Updated API key for user {user_id}, service {api_key_data.service_name}")
            return existing_key
        
        # Create new key
        api_key = UserAPIKey(
            user_id=user_id,
            service_name=api_key_data.service_name,
            service_display_name=api_key_data.service_display_name,
            encrypted_api_key=encrypted_key,
            description=api_key_data.description,
            is_active=True,
        )
        
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        
        logger.info(f"Created API key for user {user_id}, service {api_key_data.service_name}")
        return api_key
    
    def get_api_key(
        self,
        user_id: str,
        api_key_id: str
    ) -> Optional[UserAPIKey]:
        """
        Get an API key by ID.
        
        Args:
            user_id: User ID
            api_key_id: API key ID
            
        Returns:
            UserAPIKey instance or None
        """
        return self.db.query(UserAPIKey).filter(
            and_(
                UserAPIKey.id == api_key_id,
                UserAPIKey.user_id == user_id
            )
        ).first()
    
    def get_api_key_by_service(
        self,
        user_id: str,
        service_name: str
    ) -> Optional[UserAPIKey]:
        """
        Get an API key by service name.
        
        Args:
            user_id: User ID
            service_name: Service name
            
        Returns:
            UserAPIKey instance or None
        """
        return self.db.query(UserAPIKey).filter(
            and_(
                UserAPIKey.user_id == user_id,
                UserAPIKey.service_name == service_name,
                UserAPIKey.is_active == True
            )
        ).first()
    
    def list_api_keys(
        self,
        user_id: str,
        include_inactive: bool = False
    ) -> List[UserAPIKey]:
        """
        List all API keys for a user.
        
        Args:
            user_id: User ID
            include_inactive: Whether to include inactive keys
            
        Returns:
            List of UserAPIKey instances
        """
        query = self.db.query(UserAPIKey).filter(
            UserAPIKey.user_id == user_id
        )
        
        if not include_inactive:
            query = query.filter(UserAPIKey.is_active == True)
        
        return query.order_by(UserAPIKey.created_at.desc()).all()
    
    def update_api_key(
        self,
        user_id: str,
        api_key_id: str,
        api_key_data: APIKeyUpdate
    ) -> Optional[UserAPIKey]:
        """
        Update an API key.
        
        Args:
            user_id: User ID
            api_key_id: API key ID
            api_key_data: Update data
            
        Returns:
            Updated UserAPIKey instance or None
        """
        api_key = self.get_api_key(user_id, api_key_id)
        if not api_key:
            return None
        
        if api_key_data.api_key is not None:
            api_key.encrypted_api_key = encryption_service.encrypt(api_key_data.api_key)
        
        if api_key_data.description is not None:
            api_key.description = api_key_data.description
        
        if api_key_data.is_active is not None:
            api_key.is_active = api_key_data.is_active
        
        api_key.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(api_key)
        
        logger.info(f"Updated API key {api_key_id} for user {user_id}")
        return api_key
    
    def delete_api_key(
        self,
        user_id: str,
        api_key_id: str
    ) -> bool:
        """
        Delete an API key.
        
        Args:
            user_id: User ID
            api_key_id: API key ID
            
        Returns:
            True if deleted, False if not found
        """
        api_key = self.get_api_key(user_id, api_key_id)
        if not api_key:
            return False
        
        self.db.delete(api_key)
        self.db.commit()
        
        logger.info(f"Deleted API key {api_key_id} for user {user_id}")
        return True
    
    def get_decrypted_api_key(
        self,
        user_id: str,
        service_name: str
    ) -> Optional[str]:
        """
        Get decrypted API key for a service.
        
        Args:
            user_id: User ID
            service_name: Service name
            
        Returns:
            Decrypted API key or None
        """
        api_key = self.get_api_key_by_service(user_id, service_name)
        if not api_key:
            return None
        
        # Update usage statistics
        api_key.usage_count += 1
        api_key.last_used_at = datetime.utcnow()
        self.db.commit()
        
        # Decrypt and return
        return encryption_service.decrypt(api_key.encrypted_api_key)
    
    def test_api_key(
        self,
        user_id: str,
        service_name: str
    ) -> Dict[str, Any]:
        """
        Test if an API key is valid by making a test API call.
        
        Args:
            user_id: User ID
            service_name: Service name
            
        Returns:
            Test result dictionary
        """
        api_key = self.get_api_key_by_service(user_id, service_name)
        if not api_key:
            return {
                "success": False,
                "message": f"No API key found for service: {service_name}",
                "service_name": service_name,
            }
        
        try:
            # Decrypt the key to verify it's valid
            decrypted_key = encryption_service.decrypt(api_key.encrypted_api_key)
            
            if not decrypted_key:
                return {
                    "success": False,
                    "message": "API key decryption failed",
                    "service_name": service_name,
                }
            
            # Validate API key with actual service
            is_valid, validation_message = self._validate_api_key(service_name, decrypted_key)
            
            return {
                "success": is_valid,
                "message": validation_message,
                "service_name": service_name,
                "details": {
                    "masked_key": encryption_service.mask_api_key(decrypted_key),
                    "last_used": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
                    "usage_count": api_key.usage_count,
                }
            }
            
        except Exception as e:
            logger.error(f"API key test failed: {e}")
            return {
                "success": False,
                "message": f"API key test failed: {str(e)}",
                "service_name": service_name,
            }
    
    def _validate_api_key(self, service_name: str, api_key: str) -> tuple[bool, str]:
        """
        Validate API key by making a test call to the service.
        
        Args:
            service_name: Service name (openai, anthropic, google, etc.)
            api_key: Decrypted API key
            
        Returns:
            Tuple of (is_valid, message)
        """
        import httpx
        
        validators = {
            "openai": self._validate_openai_key,
            "anthropic": self._validate_anthropic_key,
            "google": self._validate_google_key,
            "cohere": self._validate_cohere_key,
        }
        
        validator = validators.get(service_name.lower())
        if validator:
            try:
                return validator(api_key)
            except Exception as e:
                logger.warning(f"API validation failed for {service_name}: {e}")
                return False, f"Validation failed: {str(e)}"
        
        # For unknown services, just check key format
        if len(api_key) < 10:
            return False, "API key appears too short"
        return True, "API key format looks valid (service-specific validation not available)"
    
    def _validate_openai_key(self, api_key: str) -> tuple[bool, str]:
        """Validate OpenAI API key."""
        import httpx
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                if response.status_code == 200:
                    return True, "OpenAI API key is valid"
                elif response.status_code == 401:
                    return False, "Invalid OpenAI API key"
                elif response.status_code == 429:
                    return True, "OpenAI API key is valid (rate limited)"
                else:
                    return False, f"OpenAI API returned status {response.status_code}"
        except httpx.TimeoutException:
            return False, "OpenAI API request timed out"
        except Exception as e:
            return False, f"Failed to validate OpenAI key: {str(e)}"
    
    def _validate_anthropic_key(self, api_key: str) -> tuple[bool, str]:
        """Validate Anthropic API key."""
        import httpx
        
        try:
            with httpx.Client(timeout=10.0) as client:
                # Anthropic doesn't have a simple validation endpoint,
                # so we make a minimal request
                response = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "hi"}]
                    }
                )
                
                if response.status_code == 200:
                    return True, "Anthropic API key is valid"
                elif response.status_code == 401:
                    return False, "Invalid Anthropic API key"
                elif response.status_code == 429:
                    return True, "Anthropic API key is valid (rate limited)"
                elif response.status_code == 400:
                    # Bad request but key is valid
                    return True, "Anthropic API key is valid"
                else:
                    return False, f"Anthropic API returned status {response.status_code}"
        except httpx.TimeoutException:
            return False, "Anthropic API request timed out"
        except Exception as e:
            return False, f"Failed to validate Anthropic key: {str(e)}"
    
    def _validate_google_key(self, api_key: str) -> tuple[bool, str]:
        """Validate Google AI API key."""
        import httpx
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
                )
                
                if response.status_code == 200:
                    return True, "Google AI API key is valid"
                elif response.status_code == 400 or response.status_code == 403:
                    return False, "Invalid Google AI API key"
                else:
                    return False, f"Google AI API returned status {response.status_code}"
        except httpx.TimeoutException:
            return False, "Google AI API request timed out"
        except Exception as e:
            return False, f"Failed to validate Google AI key: {str(e)}"
    
    def _validate_cohere_key(self, api_key: str) -> tuple[bool, str]:
        """Validate Cohere API key."""
        import httpx
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    "https://api.cohere.ai/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                if response.status_code == 200:
                    return True, "Cohere API key is valid"
                elif response.status_code == 401:
                    return False, "Invalid Cohere API key"
                else:
                    return False, f"Cohere API returned status {response.status_code}"
        except httpx.TimeoutException:
            return False, "Cohere API request timed out"
        except Exception as e:
            return False, f"Failed to validate Cohere key: {str(e)}"
