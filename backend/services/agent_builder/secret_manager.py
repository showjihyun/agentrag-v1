"""Secret Manager for encrypting and decrypting sensitive data."""

import logging
import uuid
import base64
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID
from cryptography.fernet import Fernet

from backend.db.models.agent_builder import Secret, Variable
from backend.config import settings
from backend.core.kms_client import KMSClient, get_default_kms_client

logger = logging.getLogger(__name__)


class SecretManager:
    """Service for managing encrypted secrets with KMS integration."""
    
    def __init__(self, db: Session, kms_client: Optional[KMSClient] = None):
        """
        Initialize Secret Manager.
        
        Args:
            db: Database session
            kms_client: KMS client for key management (optional)
        """
        self.db = db
        self.kms_client = kms_client or get_default_kms_client()
        self._encryption_key_cache = {}
        
        # Validate KMS is properly configured in production
        if getattr(settings, 'IS_PRODUCTION', False):
            if not self.kms_client or isinstance(self.kms_client.__class__.__name__, 'LocalKMSClient'):
                logger.error(
                    "Production environment detected but KMS is not properly configured. "
                    "Please configure AWS KMS or Azure Key Vault."
                )
    
    def _get_encryption_key(self, key_id: str = "default") -> bytes:
        """
        Get encryption key from KMS.
        
        Args:
            key_id: Key identifier
            
        Returns:
            Encryption key bytes
        """
        if key_id in self._encryption_key_cache:
            return self._encryption_key_cache[key_id]
        
        try:
            key = self.kms_client.get_data_key(key_id)
            self._encryption_key_cache[key_id] = key
            return key
        except Exception as e:
            logger.error(f"Failed to get encryption key from KMS: {e}")
            raise SecurityError("Failed to retrieve encryption key")
    
    def _get_deployment_id(self) -> str:
        """Get deployment ID for salt generation."""
        return getattr(settings, 'DEPLOYMENT_ID', 'default')
    
    def encrypt_variable(self, variable_id: str, value: str) -> Secret:
        """
        Encrypt and store variable value as secret.
        
        Args:
            variable_id: Variable ID
            value: Plain text value to encrypt
            
        Returns:
            Created Secret model
            
        Raises:
            ValueError: If variable not found or not marked as secret
        """
        try:
            # Verify variable exists and is marked as secret
            variable = self.db.query(Variable).filter(
                Variable.id == UUID(variable_id),
                Variable.deleted_at.is_(None)
            ).first()
            
            if not variable:
                raise ValueError(f"Variable {variable_id} not found")
            
            if not variable.is_secret:
                raise ValueError(f"Variable {variable_id} is not marked as secret")
            
            # Get encryption key from KMS
            key_id = f"variable-{variable.scope}-{self._get_deployment_id()}"
            encryption_key = self._get_encryption_key(key_id)
            fernet = Fernet(encryption_key)
            encrypted_value = fernet.encrypt(value.encode()).decode()
            
            # Check if secret already exists
            existing_secret = self.db.query(Secret).filter(
                Secret.variable_id == UUID(variable_id)
            ).first()
            
            if existing_secret:
                # Update existing secret
                existing_secret.encrypted_value = encrypted_value
                existing_secret.encryption_key_id = key_id
                existing_secret.updated_at = datetime.utcnow()
                secret = existing_secret
            else:
                # Create new secret
                secret = Secret(
                    id=str(uuid.uuid4()),
                    variable_id=UUID(variable_id),
                    encrypted_value=encrypted_value,
                    encryption_key_id=key_id
                )
                self.db.add(secret)
            
            # Update variable value to masked
            variable.value = "********"
            
            self.db.commit()
            self.db.refresh(secret)
            
            logger.info(f"Encrypted secret for variable: {variable.name}")
            return secret
            
        except ValueError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to encrypt variable: {e}", exc_info=True)
            raise
    
    def decrypt_variable(self, variable_id: str) -> str:
        """
        Decrypt and return variable value.
        
        Args:
            variable_id: Variable ID
            
        Returns:
            Decrypted plain text value
            
        Raises:
            ValueError: If variable or secret not found
        """
        try:
            # Get secret
            secret = self.db.query(Secret).filter(
                Secret.variable_id == UUID(variable_id)
            ).first()
            
            if not secret:
                raise ValueError(f"Secret not found for variable {variable_id}")
            
            # Get encryption key from KMS
            key_id = secret.encryption_key_id or "default"
            encryption_key = self._get_encryption_key(key_id)
            fernet = Fernet(encryption_key)
            
            try:
                decrypted_value = fernet.decrypt(
                    secret.encrypted_value.encode()
                ).decode()
            except Exception as e:
                logger.error(f"Failed to decrypt secret: {e}")
                raise ValueError("Failed to decrypt secret - invalid encryption key or corrupted data")
            
            return decrypted_value
            
        except Exception as e:
            logger.error(f"Failed to decrypt variable: {e}", exc_info=True)
            raise
    
    def rotate_encryption_key(self, new_key_id: str = "rotated") -> int:
        """
        Rotate encryption key for all secrets using KMS.
        
        Args:
            new_key_id: New key identifier in KMS
            
        Returns:
            Number of secrets re-encrypted
            
        Note:
            This is a critical operation that should be performed during maintenance.
            All secrets will be decrypted with old key and re-encrypted with new key.
        """
        try:
            # Get all secrets
            secrets = self.db.query(Secret).all()
            
            if not secrets:
                logger.info("No secrets to rotate")
                return 0
            
            # Get new encryption key from KMS
            new_encryption_key = self._get_encryption_key(new_key_id)
            new_fernet = Fernet(new_encryption_key)
            
            # Decrypt with old key and re-encrypt with new key
            rotated_count = 0
            failed_count = 0
            
            for secret in secrets:
                try:
                    # Decrypt with old key
                    old_key_id = secret.encryption_key_id or "default"
                    old_encryption_key = self._get_encryption_key(old_key_id)
                    old_fernet = Fernet(old_encryption_key)
                    
                    decrypted = old_fernet.decrypt(
                        secret.encrypted_value.encode()
                    ).decode()
                    
                    # Re-encrypt with new key
                    encrypted = new_fernet.encrypt(decrypted.encode()).decode()
                    secret.encrypted_value = encrypted
                    secret.encryption_key_id = new_key_id
                    secret.updated_at = datetime.utcnow()
                    
                    rotated_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to rotate secret {secret.id}: {e}")
                    failed_count += 1
                    continue
            
            # Clear key cache to force refresh
            self._encryption_key_cache.clear()
            
            self.db.commit()
            
            logger.info(
                f"Rotated encryption key for {rotated_count} secrets "
                f"({failed_count} failed)"
            )
            return rotated_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to rotate encryption key: {e}", exc_info=True)
            raise
    
    def delete_secret(self, variable_id: str) -> bool:
        """
        Delete secret for variable.
        
        Args:
            variable_id: Variable ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            secret = self.db.query(Secret).filter(
                Secret.variable_id == UUID(variable_id)
            ).first()
            
            if not secret:
                return False
            
            self.db.delete(secret)
            self.db.commit()
            
            logger.info(f"Deleted secret for variable: {variable_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete secret: {e}", exc_info=True)
            raise
    
    def validate_encryption(self, key_id: str = "default") -> bool:
        """
        Validate that encryption/decryption is working correctly.
        
        Args:
            key_id: Key identifier to test
            
        Returns:
            True if encryption is working, False otherwise
        """
        try:
            test_value = "test-encryption-value"
            
            encryption_key = self._get_encryption_key(key_id)
            fernet = Fernet(encryption_key)
            
            # Encrypt
            encrypted = fernet.encrypt(test_value.encode())
            
            # Decrypt
            decrypted = fernet.decrypt(encrypted).decode()
            
            is_valid = decrypted == test_value
            
            if is_valid:
                logger.info(f"Encryption validation successful for key: {key_id}")
            else:
                logger.error(f"Encryption validation failed for key: {key_id}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Encryption validation failed: {e}", exc_info=True)
            return False


class SecurityError(Exception):
    """Security-related error."""
    pass
