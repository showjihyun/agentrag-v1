"""
API Key Manager for Tool Integrations
Manages API keys and credentials for external services.
"""

import os
import logging
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
import json

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API keys and credentials for tool integrations."""
    
    def __init__(self):
        self._encryption_key = self._get_encryption_key()
        self._fernet = Fernet(self._encryption_key) if self._encryption_key else None
        self._api_keys = self._load_api_keys()
    
    def _get_encryption_key(self) -> Optional[bytes]:
        """Get encryption key from environment."""
        key = os.getenv("ENCRYPTION_KEY")
        if key:
            return key.encode()
        return None
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables."""
        api_keys = {}
        
        # AI/LLM Providers
        if os.getenv("OPENAI_API_KEY"):
            api_keys["openai"] = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("ANTHROPIC_API_KEY"):
            api_keys["anthropic"] = os.getenv("ANTHROPIC_API_KEY")
        
        if os.getenv("GOOGLE_API_KEY"):
            api_keys["google"] = os.getenv("GOOGLE_API_KEY")
        
        # Search Providers
        if os.getenv("SERPER_API_KEY"):
            api_keys["serper"] = os.getenv("SERPER_API_KEY")
        
        if os.getenv("TAVILY_API_KEY"):
            api_keys["tavily"] = os.getenv("TAVILY_API_KEY")
        
        if os.getenv("EXA_API_KEY"):
            api_keys["exa"] = os.getenv("EXA_API_KEY")
        
        # Communication
        if os.getenv("SENDGRID_API_KEY"):
            api_keys["sendgrid"] = os.getenv("SENDGRID_API_KEY")
        
        if os.getenv("SLACK_BOT_TOKEN"):
            api_keys["slack"] = os.getenv("SLACK_BOT_TOKEN")
        
        # Productivity
        if os.getenv("NOTION_API_KEY"):
            api_keys["notion"] = os.getenv("NOTION_API_KEY")
        
        if os.getenv("GOOGLE_SHEETS_API_KEY"):
            api_keys["google_sheets"] = os.getenv("GOOGLE_SHEETS_API_KEY")
        
        # Data Services
        if os.getenv("SUPABASE_API_KEY"):
            api_keys["supabase"] = os.getenv("SUPABASE_API_KEY")
        
        if os.getenv("PINECONE_API_KEY"):
            api_keys["pinecone"] = os.getenv("PINECONE_API_KEY")
        
        logger.info(f"Loaded {len(api_keys)} API keys from environment")
        return api_keys
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for a service.
        
        Args:
            service: Service name (e.g., 'openai', 'anthropic')
            
        Returns:
            API key or None if not found
        """
        return self._api_keys.get(service.lower())
    
    def has_api_key(self, service: str) -> bool:
        """
        Check if API key exists for a service.
        
        Args:
            service: Service name
            
        Returns:
            True if API key exists
        """
        return service.lower() in self._api_keys
    
    def get_credentials_for_tool(self, tool_id: str) -> Dict[str, str]:
        """
        Get credentials for a specific tool.
        
        Args:
            tool_id: Tool identifier
            
        Returns:
            Dictionary of credentials
        """
        credentials = {}
        
        # Map tool IDs to service names
        tool_service_map = {
            "openai_chat": "openai",
            "anthropic_claude": "anthropic", 
            "google_gemini": "google",
            "serper_search": "serper",
            "tavily_search": "tavily",
            "exa_search": "exa",
            "sendgrid": "sendgrid",
            "slack": "slack",
            "notion": "notion",
            "google_sheets": "google_sheets",
            "supabase_query": "supabase",
            "pinecone_upsert": "pinecone"
        }
        
        service = tool_service_map.get(tool_id)
        if service and self.has_api_key(service):
            credentials["api_key"] = self.get_api_key(service)
        
        return credentials
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credentials for storage.
        
        Args:
            credentials: Credentials dictionary
            
        Returns:
            Encrypted credentials string
        """
        if not self._fernet:
            # If no encryption key, store as JSON (not recommended for production)
            logger.warning("No encryption key found, storing credentials as plain JSON")
            return json.dumps(credentials)
        
        credentials_json = json.dumps(credentials)
        encrypted = self._fernet.encrypt(credentials_json.encode())
        return encrypted.decode()
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """
        Decrypt stored credentials.
        
        Args:
            encrypted_credentials: Encrypted credentials string
            
        Returns:
            Decrypted credentials dictionary
        """
        if not self._fernet:
            # If no encryption key, assume plain JSON
            try:
                return json.loads(encrypted_credentials)
            except json.JSONDecodeError:
                logger.error("Failed to decode credentials as JSON")
                return {}
        
        try:
            decrypted = self._fernet.decrypt(encrypted_credentials.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            return {}
    
    def get_available_services(self) -> Dict[str, bool]:
        """
        Get list of available services and their status.
        
        Returns:
            Dictionary mapping service names to availability status
        """
        services = {
            # AI/LLM
            "openai": self.has_api_key("openai"),
            "anthropic": self.has_api_key("anthropic"),
            "google": self.has_api_key("google"),
            
            # Search
            "serper": self.has_api_key("serper"),
            "tavily": self.has_api_key("tavily"),
            "exa": self.has_api_key("exa"),
            
            # Communication
            "sendgrid": self.has_api_key("sendgrid"),
            "slack": self.has_api_key("slack"),
            
            # Productivity
            "notion": self.has_api_key("notion"),
            "google_sheets": self.has_api_key("google_sheets"),
            
            # Data
            "supabase": self.has_api_key("supabase"),
            "pinecone": self.has_api_key("pinecone"),
        }
        
        return services
    
    def validate_api_key(self, service: str, api_key: str) -> bool:
        """
        Validate an API key for a service.
        
        Args:
            service: Service name
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation - check if key is not empty and has reasonable length
        if not api_key or len(api_key) < 10:
            return False
        
        # Service-specific validation patterns
        validation_patterns = {
            "openai": lambda key: key.startswith("sk-"),
            "anthropic": lambda key: key.startswith("sk-ant-"),
            "google": lambda key: len(key) >= 30,
            "serper": lambda key: len(key) >= 30,
            "tavily": lambda key: key.startswith("tvly-"),
            "notion": lambda key: key.startswith("secret_"),
        }
        
        validator = validation_patterns.get(service)
        if validator:
            return validator(api_key)
        
        # Default validation - just check length
        return len(api_key) >= 20


# Global instance
api_key_manager = APIKeyManager()