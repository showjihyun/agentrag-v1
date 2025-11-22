"""
Encryption utilities for sensitive data.
"""
import os
import json
from typing import Dict, Any
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)


class CredentialEncryption:
    """Encrypt and decrypt credentials using Fernet symmetric encryption."""
    
    def __init__(self):
        """Initialize encryption with key from environment."""
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            # Generate a key for development (NOT for production!)
            logger.warning(
                "⚠️  ENCRYPTION_KEY not set! Generating temporary key. "
                "Set ENCRYPTION_KEY in production!"
            )
            encryption_key = Fernet.generate_key().decode()
            logger.info(f"Generated key: {encryption_key}")
        
        try:
            self.cipher = Fernet(encryption_key.encode())
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError(f"Invalid ENCRYPTION_KEY: {e}")
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credentials dictionary to string.
        
        Args:
            credentials: Dictionary of credentials to encrypt
            
        Returns:
            Encrypted string
        """
        try:
            json_str = json.dumps(credentials)
            encrypted = self.cipher.encrypt(json_str.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {e}")
            raise ValueError(f"Encryption failed: {e}")
    
    def decrypt_credentials(self, encrypted: str) -> Dict[str, Any]:
        """
        Decrypt encrypted string to credentials dictionary.
        
        Args:
            encrypted: Encrypted string
            
        Returns:
            Decrypted credentials dictionary
        """
        try:
            decrypted = self.cipher.decrypt(encrypted.encode())
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise ValueError(f"Decryption failed: {e}")
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        return Fernet.generate_key().decode()


# Singleton instance
_encryption_instance = None


def get_encryption() -> CredentialEncryption:
    """Get singleton encryption instance."""
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = CredentialEncryption()
    return _encryption_instance
