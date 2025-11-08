"""Key Management Service client for secure key management."""

import logging
import os
from typing import Optional
from abc import ABC, abstractmethod
import secrets
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class KMSClient(ABC):
    """Abstract base class for KMS clients."""
    
    @abstractmethod
    def get_data_key(self, key_id: str = "default") -> bytes:
        """Get encryption key from KMS."""
        pass
    
    @abstractmethod
    def get_salt(self, deployment_id: str) -> bytes:
        """Get unique salt for deployment."""
        pass


class LocalKMSClient(KMSClient):
    """Local KMS client for development/testing."""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize local KMS client.
        
        Args:
            master_key: Master encryption key
        """
        self.master_key = master_key or os.environ.get(
            "SECRET_ENCRYPTION_KEY",
            "default-insecure-key-change-in-production"
        )
        self._key_cache = {}
        self._salt_cache = {}
        
        if self.master_key == "default-insecure-key-change-in-production":
            logger.warning(
                "Using default encryption key. "
                "Set SECRET_ENCRYPTION_KEY environment variable for production."
            )
    
    def get_data_key(self, key_id: str = "default") -> bytes:
        """
        Get encryption key.
        
        Args:
            key_id: Key identifier
            
        Returns:
            Encryption key bytes
        """
        if key_id in self._key_cache:
            return self._key_cache[key_id]
        
        # Generate unique salt for this key_id
        salt = self.get_salt(key_id)
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        self._key_cache[key_id] = key
        
        return key
    
    def get_salt(self, deployment_id: str) -> bytes:
        """
        Get unique salt for deployment.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            Salt bytes
        """
        if deployment_id in self._salt_cache:
            return self._salt_cache[deployment_id]
        
        # Generate deterministic salt from deployment_id
        # In production, this should be stored securely
        salt = hashes.Hash(hashes.SHA256(), backend=default_backend())
        salt.update(f"agent-builder-{deployment_id}".encode())
        salt_bytes = salt.finalize()[:16]  # Use first 16 bytes
        
        self._salt_cache[deployment_id] = salt_bytes
        return salt_bytes


class AWSKMSClient(KMSClient):
    """AWS KMS client for production."""
    
    def __init__(self, region: str = "us-east-1"):
        """
        Initialize AWS KMS client.
        
        Args:
            region: AWS region
        """
        try:
            import boto3
            self.kms = boto3.client('kms', region_name=region)
            self._key_cache = {}
            self._salt_cache = {}
            logger.info(f"AWS KMS client initialized for region: {region}")
        except ImportError:
            raise ImportError(
                "boto3 is required for AWS KMS. "
                "Install with: pip install boto3"
            )
    
    def get_data_key(self, key_id: str = "default") -> bytes:
        """
        Get data key from AWS KMS.
        
        Args:
            key_id: KMS key ID or alias
            
        Returns:
            Encryption key bytes
        """
        if key_id in self._key_cache:
            return self._key_cache[key_id]
        
        try:
            response = self.kms.generate_data_key(
                KeyId=key_id,
                KeySpec='AES_256'
            )
            
            # Use plaintext key (will be encrypted in memory)
            key = base64.urlsafe_b64encode(response['Plaintext'])
            self._key_cache[key_id] = key
            
            logger.info(f"Retrieved data key from AWS KMS: {key_id}")
            return key
            
        except Exception as e:
            logger.error(f"Failed to get data key from AWS KMS: {e}")
            raise
    
    def get_salt(self, deployment_id: str) -> bytes:
        """
        Get unique salt for deployment from AWS KMS.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            Salt bytes
        """
        if deployment_id in self._salt_cache:
            return self._salt_cache[deployment_id]
        
        try:
            # Generate random salt using KMS
            response = self.kms.generate_random(NumberOfBytes=16)
            salt = response['Plaintext']
            
            self._salt_cache[deployment_id] = salt
            return salt
            
        except Exception as e:
            logger.error(f"Failed to generate salt from AWS KMS: {e}")
            # Fallback to deterministic salt
            return self._generate_fallback_salt(deployment_id)
    
    def _generate_fallback_salt(self, deployment_id: str) -> bytes:
        """Generate fallback salt if KMS is unavailable."""
        salt = hashes.Hash(hashes.SHA256(), backend=default_backend())
        salt.update(f"agent-builder-{deployment_id}".encode())
        return salt.finalize()[:16]


class AzureKeyVaultClient(KMSClient):
    """Azure Key Vault client for production."""
    
    def __init__(self, vault_url: str):
        """
        Initialize Azure Key Vault client.
        
        Args:
            vault_url: Key Vault URL
        """
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=vault_url, credential=credential)
            self._key_cache = {}
            self._salt_cache = {}
            logger.info(f"Azure Key Vault client initialized: {vault_url}")
        except ImportError:
            raise ImportError(
                "azure-identity and azure-keyvault-secrets are required. "
                "Install with: pip install azure-identity azure-keyvault-secrets"
            )
    
    def get_data_key(self, key_id: str = "default") -> bytes:
        """
        Get data key from Azure Key Vault.
        
        Args:
            key_id: Secret name in Key Vault
            
        Returns:
            Encryption key bytes
        """
        if key_id in self._key_cache:
            return self._key_cache[key_id]
        
        try:
            secret = self.client.get_secret(f"encryption-key-{key_id}")
            key = base64.urlsafe_b64encode(secret.value.encode())
            self._key_cache[key_id] = key
            
            logger.info(f"Retrieved data key from Azure Key Vault: {key_id}")
            return key
            
        except Exception as e:
            logger.error(f"Failed to get data key from Azure Key Vault: {e}")
            raise
    
    def get_salt(self, deployment_id: str) -> bytes:
        """
        Get unique salt for deployment from Azure Key Vault.
        
        Args:
            deployment_id: Deployment identifier
            
        Returns:
            Salt bytes
        """
        if deployment_id in self._salt_cache:
            return self._salt_cache[deployment_id]
        
        try:
            secret = self.client.get_secret(f"salt-{deployment_id}")
            salt = base64.b64decode(secret.value)
            self._salt_cache[deployment_id] = salt
            return salt
            
        except Exception as e:
            logger.warning(f"Salt not found in Key Vault, generating new: {e}")
            # Generate and store new salt
            salt = secrets.token_bytes(16)
            try:
                self.client.set_secret(
                    f"salt-{deployment_id}",
                    base64.b64encode(salt).decode()
                )
            except Exception as store_error:
                logger.error(f"Failed to store salt: {store_error}")
            
            self._salt_cache[deployment_id] = salt
            return salt


def get_kms_client(
    provider: Optional[str] = None,
    **kwargs
) -> KMSClient:
    """
    Get KMS client based on provider.
    
    Args:
        provider: KMS provider (local, aws, azure)
        **kwargs: Provider-specific arguments
        
    Returns:
        KMS client instance
    """
    provider = provider or os.environ.get("KMS_PROVIDER", "local")
    
    if provider == "local":
        return LocalKMSClient(**kwargs)
    elif provider == "aws":
        return AWSKMSClient(**kwargs)
    elif provider == "azure":
        return AzureKeyVaultClient(**kwargs)
    else:
        raise ValueError(f"Unsupported KMS provider: {provider}")


# Global KMS client instance
_kms_client: Optional[KMSClient] = None


def get_default_kms_client() -> KMSClient:
    """Get or create default KMS client."""
    global _kms_client
    
    if _kms_client is None:
        _kms_client = get_kms_client()
    
    return _kms_client


def set_kms_client(client: KMSClient):
    """Set global KMS client."""
    global _kms_client
    _kms_client = client
