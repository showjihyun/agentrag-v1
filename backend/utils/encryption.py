"""Encryption utilities for sensitive data."""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from backend.config import settings


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        """Initialize encryption service with key from settings."""
        # Use SECRET_KEY from settings as the encryption key base
        self._fernet = self._get_fernet()
    
    def _get_fernet(self) -> Fernet:
        """Get Fernet cipher instance."""
        # Derive a key from the JWT_SECRET_KEY
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'agenticrag_salt',  # Fixed salt for consistency
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(
            kdf.derive(settings.JWT_SECRET_KEY.encode())
        )
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return ""
        
        encrypted_bytes = self._fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            encrypted_text: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted_text:
            return ""
        
        decrypted_bytes = self._fernet.decrypt(encrypted_text.encode())
        return decrypted_bytes.decode()
    
    def mask_api_key(self, api_key: str, visible_chars: int = 4) -> str:
        """
        Mask an API key for display purposes.
        
        Args:
            api_key: API key to mask
            visible_chars: Number of characters to show at the end
            
        Returns:
            Masked API key (e.g., "****XXXX")
        """
        if not api_key or len(api_key) <= visible_chars:
            return "****"
        
        return "*" * (len(api_key) - visible_chars) + api_key[-visible_chars:]


# Global instance
encryption_service = EncryptionService()
