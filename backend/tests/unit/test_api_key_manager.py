"""
Tests for API Key Manager
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from backend.core.security.api_key_manager import APIKeyManager
from backend.db.models.api_keys import APIKey
from backend.db.models.user import User


@pytest.fixture
def encryption_key():
    """Generate test encryption key"""
    return Fernet.generate_key()


@pytest.fixture
def api_key_manager(encryption_key):
    """Create API key manager instance"""
    return APIKeyManager(encryption_key)


@pytest.fixture
def test_user(db: Session):
    """Create test user"""
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestAPIKeyGeneration:
    """Test API key generation"""
    
    def test_generate_key_format(self, api_key_manager):
        """Test generated key has correct format"""
        key = api_key_manager.generate_key()
        
        assert key.startswith("agr_")
        assert len(key) > 40  # Prefix + random data
    
    def test_generate_key_uniqueness(self, api_key_manager):
        """Test generated keys are unique"""
        keys = [api_key_manager.generate_key() for _ in range(100)]
        
        assert len(set(keys)) == 100  # All unique
    
    def test_hash_key_consistency(self, api_key_manager):
        """Test key hashing is consistent"""
        key = "agr_test123"
        
        hash1 = api_key_manager.hash_key(key)
        hash2 = api_key_manager.hash_key(key)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex digest


class TestAPIKeyCreation:
    """Test API key creation"""
    
    @pytest.mark.asyncio
    async def test_create_key_success(self, api_key_manager, test_user, db):
        """Test successful key creation"""
        key_info = await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Test Key",
            expires_in_days=90,
            scopes=["workflows:read"]
        )
        
        assert "id" in key_info
        assert "key" in key_info
        assert key_info["key"].startswith("agr_")
        assert key_info["name"] == "Test Key"
        assert key_info["scopes"] == ["workflows:read"]
        
        # Verify in database
        db_key = db.query(APIKey).filter(APIKey.id == key_info["id"]).first()
        assert db_key is not None
        assert db_key.user_id == test_user.id
        assert db_key.is_active is True
    
    @pytest.mark.asyncio
    async def test_create_key_with_expiration(self, api_key_manager, test_user, db):
        """Test key creation with expiration"""
        key_info = await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Expiring Key",
            expires_in_days=30
        )
        
        # Check expiration date
        db_key = db.query(APIKey).filter(APIKey.id == key_info["id"]).first()
        expected_expiry = datetime.utcnow() + timedelta(days=30)
        
        assert db_key.expires_at is not None
        assert abs((db_key.expires_at - expected_expiry).total_seconds()) < 60
    
    @pytest.mark.asyncio
    async def test_create_key_stores_hash_not_raw(self, api_key_manager, test_user, db):
        """Test that raw key is not stored in database"""
        key_info = await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Secure Key"
        )
        
        raw_key = key_info["key"]
        
        # Verify raw key is not in database
        db_key = db.query(APIKey).filter(APIKey.id == key_info["id"]).first()
        assert raw_key not in str(db_key.key_hash)
        assert db_key.key_hash == api_key_manager.hash_key(raw_key)


class TestAPIKeyValidation:
    """Test API key validation"""
    
    @pytest.mark.asyncio
    async def test_validate_key_success(self, api_key_manager, test_user, db):
        """Test successful key validation"""
        # Create key
        key_info = await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Valid Key"
        )
        
        # Validate key
        user_info = await api_key_manager.validate_key(db, key_info["key"])
        
        assert user_info is not None
        assert user_info["user_id"] == test_user.id
        assert user_info["user_email"] == test_user.email
        assert user_info["key_name"] == "Valid Key"
    
    @pytest.mark.asyncio
    async def test_validate_key_invalid(self, api_key_manager, db):
        """Test validation of invalid key"""
        user_info = await api_key_manager.validate_key(db, "agr_invalid_key")
        
        assert user_info is None
    
    @pytest.mark.asyncio
    async def test_validate_key_expired(self, api_key_manager, test_user, db):
        """Test validation of expired key"""
        # Create key with past expiration
        key_info = await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Expired Key",
            expires_in_days=1
        )
        
        # Manually set expiration to past
        db_key = db.query(APIKey).filter(APIKey.id == key_info["id"]).first()
        db_key.expires_at = datetime.utcnow() - timedelta(days=1)
        db.commit()
        
        # Validate key
        user_info = await api_key_manager.validate_key(db, key_info["key"])
        
        assert user_info is None
    
    @pytest.mark.asyncio
    async def test_validate_key_updates_usage(self, api_key_manager, test_user, db):
        """Test that validation updates usage stats"""
        # Create key
        key_info = await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Usage Key"
        )
        
        # Validate multiple times
        for _ in range(3):
            await api_key_manager.validate_key(db, key_info["key"])
        
        # Check usage stats
        db_key = db.query(APIKey).filter(APIKey.id == key_info["id"]).first()
        assert db_key.usage_count == 3
        assert db_key.last_used_at is not None


class TestAPIKeyRotation:
    """Test API key rotation"""
    
    @pytest.mark.asyncio
    async def test_rotate_key_success(self, api_key_manager, test_user, db):
        """Test successful key rotation"""
        # Create original key
        old_key_info = await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Original Key",
            scopes=["workflows:read"]
        )
        
        # Rotate key
        new_key_info = await api_key_manager.rotate_key(
            db=db,
            key_id=old_key_info["id"],
            user_id=test_user.id
        )
        
        # Verify new key
        assert new_key_info["key"] != old_key_info["key"]
        assert new_key_info["scopes"] == old_key_info["scopes"]
        
        # Verify old key is inactive
        old_db_key = db.query(APIKey).filter(APIKey.id == old_key_info["id"]).first()
        assert old_db_key.is_active is False
        assert old_db_key.rotated_at is not None
        assert old_db_key.rotated_to_id == new_key_info["id"]
    
    @pytest.mark.asyncio
    async def test_rotate_key_not_found(self, api_key_manager, test_user, db):
        """Test rotation of non-existent key"""
        with pytest.raises(ValueError):
            await api_key_manager.rotate_key(
                db=db,
                key_id="non_existent_id",
                user_id=test_user.id
            )


class TestAPIKeyRevocation:
    """Test API key revocation"""
    
    @pytest.mark.asyncio
    async def test_revoke_key_success(self, api_key_manager, test_user, db):
        """Test successful key revocation"""
        # Create key
        key_info = await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Revoke Key"
        )
        
        # Revoke key
        success = await api_key_manager.revoke_key(
            db=db,
            key_id=key_info["id"],
            user_id=test_user.id
        )
        
        assert success is True
        
        # Verify key is inactive
        db_key = db.query(APIKey).filter(APIKey.id == key_info["id"]).first()
        assert db_key.is_active is False
        assert db_key.revoked_at is not None
    
    @pytest.mark.asyncio
    async def test_revoke_key_not_found(self, api_key_manager, test_user, db):
        """Test revocation of non-existent key"""
        success = await api_key_manager.revoke_key(
            db=db,
            key_id="non_existent_id",
            user_id=test_user.id
        )
        
        assert success is False


class TestAPIKeyListing:
    """Test API key listing"""
    
    @pytest.mark.asyncio
    async def test_list_keys_active_only(self, api_key_manager, test_user, db):
        """Test listing active keys only"""
        # Create multiple keys
        await api_key_manager.create_key(db, test_user.id, "Key 1")
        await api_key_manager.create_key(db, test_user.id, "Key 2")
        key3 = await api_key_manager.create_key(db, test_user.id, "Key 3")
        
        # Revoke one key
        await api_key_manager.revoke_key(db, key3["id"], test_user.id)
        
        # List active keys
        keys = await api_key_manager.list_keys(db, test_user.id, include_inactive=False)
        
        assert len(keys) == 2
        assert all(key["is_active"] for key in keys)
    
    @pytest.mark.asyncio
    async def test_list_keys_include_inactive(self, api_key_manager, test_user, db):
        """Test listing all keys including inactive"""
        # Create and revoke key
        key_info = await api_key_manager.create_key(db, test_user.id, "Key")
        await api_key_manager.revoke_key(db, key_info["id"], test_user.id)
        
        # List all keys
        keys = await api_key_manager.list_keys(db, test_user.id, include_inactive=True)
        
        assert len(keys) == 1
        assert keys[0]["is_active"] is False


class TestExpiringKeys:
    """Test expiring key detection"""
    
    @pytest.mark.asyncio
    async def test_check_expiring_keys(self, api_key_manager, test_user, db):
        """Test detection of expiring keys"""
        # Create key expiring in 5 days
        key_info = await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Expiring Soon",
            expires_in_days=5
        )
        
        # Check expiring keys (7 day threshold)
        expiring = await api_key_manager.check_expiring_keys(db, days_threshold=7)
        
        assert len(expiring) == 1
        assert expiring[0]["id"] == key_info["id"]
        assert expiring[0]["days_until_expiration"] <= 7
    
    @pytest.mark.asyncio
    async def test_auto_rotate_expiring_keys(self, api_key_manager, test_user, db):
        """Test automatic rotation of expiring keys"""
        # Create key expiring in 5 days
        await api_key_manager.create_key(
            db=db,
            user_id=test_user.id,
            name="Auto Rotate",
            expires_in_days=5
        )
        
        # Auto-rotate expiring keys
        rotated_count = await api_key_manager.auto_rotate_expiring_keys(
            db=db,
            days_threshold=7
        )
        
        assert rotated_count == 1
        
        # Verify new key exists
        keys = await api_key_manager.list_keys(db, test_user.id)
        assert len(keys) == 1
        assert keys[0]["name"] == "Auto Rotate (rotated)"
