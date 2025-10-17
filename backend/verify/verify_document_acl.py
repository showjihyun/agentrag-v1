"""
Verification script for Document ACL (Access Control List) implementation.

Tests:
1. Database models and migrations
2. Permission service functionality
3. Group management
4. Permission checking logic
5. API endpoints
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import settings
from backend.db.database import Base
from backend.db.models.user import User
from backend.db.models.document import Document
from backend.db.models.permission import (
    DocumentPermission,
    Group,
    GroupMember,
    PermissionType,
)
from backend.services.document_acl_service import (
    DocumentACLService,
    DocumentACLServiceError,
)


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message."""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")


async def verify_database_models():
    """Verify database models are properly defined."""
    print_section("1. Database Models Verification")

    try:
        # Check DocumentPermission model
        assert hasattr(DocumentPermission, "id")
        assert hasattr(DocumentPermission, "document_id")
        assert hasattr(DocumentPermission, "user_id")
        assert hasattr(DocumentPermission, "group_id")
        assert hasattr(DocumentPermission, "permission_type")
        assert hasattr(DocumentPermission, "granted_by")
        assert hasattr(DocumentPermission, "granted_at")
        assert hasattr(DocumentPermission, "expires_at")
        print_success("DocumentPermission model has all required fields")

        # Check Group model
        assert hasattr(Group, "id")
        assert hasattr(Group, "name")
        assert hasattr(Group, "description")
        assert hasattr(Group, "created_by")
        assert hasattr(Group, "created_at")
        print_success("Group model has all required fields")

        # Check GroupMember model
        assert hasattr(GroupMember, "id")
        assert hasattr(GroupMember, "group_id")
        assert hasattr(GroupMember, "user_id")
        assert hasattr(GroupMember, "added_by")
        assert hasattr(GroupMember, "added_at")
        print_success("GroupMember model has all required fields")

        # Check PermissionType enum
        assert PermissionType.READ.value == "read"
        assert PermissionType.WRITE.value == "write"
        assert PermissionType.ADMIN.value == "admin"
        print_success("PermissionType enum is correctly defined")

        return True

    except AssertionError as e:
        print_error(f"Model verification failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


async def verify_database_migration():
    """Verify database migration was applied."""
    print_section("2. Database Migration Verification")

    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)

        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('groups', 'group_members', 'document_permissions')
            """
                )
            )

            tables = [row[0] for row in result]

            if "groups" in tables:
                print_success("'groups' table exists")
            else:
                print_error("'groups' table not found")
                return False

            if "group_members" in tables:
                print_success("'group_members' table exists")
            else:
                print_error("'group_members' table not found")
                return False

            if "document_permissions" in tables:
                print_success("'document_permissions' table exists")
            else:
                print_error("'document_permissions' table not found")
                return False

            # Check if permission_type enum exists
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_type
                    WHERE typname = 'permission_type'
                )
            """
                )
            )

            if result.scalar():
                print_success("'permission_type' enum exists")
            else:
                print_error("'permission_type' enum not found")
                return False

        engine.dispose()
        return True

    except Exception as e:
        print_error(f"Migration verification failed: {e}")
        return False


async def verify_acl_service():
    """Verify ACL service functionality."""
    print_section("3. ACL Service Verification")

    try:
        # Create test database session
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # Create test users
        owner = User(
            id=uuid4(),
            username=f"test_owner_{uuid4().hex[:8]}",
            email=f"owner_{uuid4().hex[:8]}@test.com",
            hashed_password="test_hash",
        )

        user1 = User(
            id=uuid4(),
            username=f"test_user1_{uuid4().hex[:8]}",
            email=f"user1_{uuid4().hex[:8]}@test.com",
            hashed_password="test_hash",
        )

        user2 = User(
            id=uuid4(),
            username=f"test_user2_{uuid4().hex[:8]}",
            email=f"user2_{uuid4().hex[:8]}@test.com",
            hashed_password="test_hash",
        )

        db.add_all([owner, user1, user2])
        db.commit()
        print_success("Created test users")

        # Create test document
        document = Document(
            id=uuid4(),
            user_id=owner.id,
            filename="test_acl.pdf",
            original_filename="test_acl.pdf",
            file_path="/test/test_acl.pdf",
            file_size_bytes=1024,
            status="completed",
        )

        db.add(document)
        db.commit()
        print_success("Created test document")

        # Initialize ACL service
        acl_service = DocumentACLService(db)
        print_success("Initialized ACL service")

        # Test 1: Owner has admin permission
        has_admin = await acl_service.check_permission(
            owner.id, document.id, PermissionType.ADMIN
        )
        assert has_admin, "Owner should have admin permission"
        print_success("Owner has admin permission (implicit)")

        # Test 2: Other user has no permission
        has_read = await acl_service.check_permission(
            user1.id, document.id, PermissionType.READ
        )
        assert not has_read, "User1 should not have permission"
        print_success("User without permission correctly denied")

        # Test 3: Grant read permission
        permission = await acl_service.grant_permission(
            document_id=document.id,
            owner_id=owner.id,
            target_user_id=user1.id,
            permission_type=PermissionType.READ,
        )
        assert permission.permission_type == PermissionType.READ
        print_success("Granted read permission to user1")

        # Test 4: User1 now has read permission
        has_read = await acl_service.check_permission(
            user1.id, document.id, PermissionType.READ
        )
        assert has_read, "User1 should have read permission"
        print_success("User1 can read document")

        # Test 5: User1 does not have write permission
        has_write = await acl_service.check_permission(
            user1.id, document.id, PermissionType.WRITE
        )
        assert not has_write, "User1 should not have write permission"
        print_success("User1 correctly denied write permission")

        # Test 6: Create group
        group = await acl_service.create_group(
            name=f"test_group_{uuid4().hex[:8]}",
            description="Test group for ACL",
            creator_id=owner.id,
        )
        assert group.name is not None
        print_success("Created test group")

        # Test 7: Add user2 to group
        member = await acl_service.add_group_member(
            group_id=group.id, user_id=user2.id, added_by=owner.id
        )
        assert member.user_id == user2.id
        print_success("Added user2 to group")

        # Test 8: Grant write permission to group
        group_permission = await acl_service.grant_permission(
            document_id=document.id,
            owner_id=owner.id,
            target_group_id=group.id,
            permission_type=PermissionType.WRITE,
        )
        assert group_permission.permission_type == PermissionType.WRITE
        print_success("Granted write permission to group")

        # Test 9: User2 has write permission via group
        has_write = await acl_service.check_permission(
            user2.id, document.id, PermissionType.WRITE
        )
        assert has_write, "User2 should have write permission via group"
        print_success("User2 has write permission via group membership")

        # Test 10: List permissions
        permissions = await acl_service.list_document_permissions(
            document_id=document.id, owner_id=owner.id
        )
        assert len(permissions) == 2  # user1 + group
        print_success(f"Listed {len(permissions)} permissions")

        # Test 11: Revoke user1 permission
        await acl_service.revoke_permission(
            permission_id=permission.id, owner_id=owner.id
        )
        print_success("Revoked user1 permission")

        # Test 12: User1 no longer has permission
        has_read = await acl_service.check_permission(
            user1.id, document.id, PermissionType.READ
        )
        assert not has_read, "User1 should not have permission after revoke"
        print_success("User1 correctly denied after revoke")

        # Test 13: Expiring permission
        expiring_permission = await acl_service.grant_permission(
            document_id=document.id,
            owner_id=owner.id,
            target_user_id=user1.id,
            permission_type=PermissionType.READ,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Already expired
        )
        print_success("Created expired permission")

        # Test 14: Expired permission is not valid
        has_read = await acl_service.check_permission(
            user1.id, document.id, PermissionType.READ
        )
        assert not has_read, "Expired permission should not grant access"
        print_success("Expired permission correctly denied")

        # Cleanup
        db.delete(document)
        db.delete(owner)
        db.delete(user1)
        db.delete(user2)
        db.delete(group)
        db.commit()
        db.close()
        engine.dispose()

        print_success("All ACL service tests passed")
        return True

    except AssertionError as e:
        print_error(f"ACL service test failed: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def verify_api_endpoints():
    """Verify API endpoints are registered."""
    print_section("4. API Endpoints Verification")

    try:
        from api.permissions import router

        # Check router is defined
        assert router is not None
        print_success("Permissions router is defined")

        # Check routes
        routes = [route.path for route in router.routes]

        expected_routes = [
            "/api/permissions/grant",
            "/api/permissions/revoke/{permission_id}",
            "/api/permissions/document/{document_id}",
            "/api/permissions/check/{document_id}/{permission_type}",
            "/api/permissions/groups",
            "/api/permissions/groups/members",
        ]

        for expected in expected_routes:
            if any(expected in route for route in routes):
                print_success(f"Route exists: {expected}")
            else:
                print_error(f"Route missing: {expected}")
                return False

        return True

    except Exception as e:
        print_error(f"API endpoint verification failed: {e}")
        return False


async def main():
    """Run all verifications."""
    print("\n" + "=" * 80)
    print("  Document ACL (Access Control List) Verification")
    print("=" * 80)

    results = []

    # Run verifications
    results.append(await verify_database_models())
    results.append(await verify_database_migration())
    results.append(await verify_acl_service())
    results.append(await verify_api_endpoints())

    # Summary
    print_section("Verification Summary")

    total = len(results)
    passed = sum(results)

    print(f"Total tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")

    if all(results):
        print("\n" + "=" * 80)
        print("  ✅ ALL VERIFICATIONS PASSED!")
        print("=" * 80 + "\n")
        print_info("Document ACL implementation is complete and working correctly.")
        print_info("Features:")
        print_info("  - User-level permissions (read, write, admin)")
        print_info("  - Group-level permissions")
        print_info("  - Permission inheritance")
        print_info("  - Owner always has admin permission")
        print_info("  - Expiring permissions")
        print_info("  - Permission checking with hierarchy")
        return 0
    else:
        print("\n" + "=" * 80)
        print("  ❌ SOME VERIFICATIONS FAILED")
        print("=" * 80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
