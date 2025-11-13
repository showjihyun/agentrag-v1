"""
Test script for newly implemented features
Run this in venv: python test_new_features.py
"""

import asyncio
import sys
from datetime import datetime


def print_section(title):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name, success, message=""):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"     {message}")


async def test_memory_service():
    """Test Memory Service."""
    print_section("Testing Memory Service")
    
    try:
        from services.memory_service import MemoryService
        
        memory = MemoryService("redis://localhost:6380")
        
        # Test 1: Connection
        try:
            is_healthy = await memory.health_check()
            print_result("Memory Service Connection", is_healthy, 
                        "Redis connection successful" if is_healthy else "Redis not available")
            
            if not is_healthy:
                print("     ⚠️  Start Redis: docker run -d --name redis -p 6380:6379 redis:latest")
                return False
        except Exception as e:
            print_result("Memory Service Connection", False, f"Error: {e}")
            return False
        
        # Test 2: Store
        try:
            result = await memory.store(
                namespace="test",
                key="test_key",
                value={"message": "Hello World", "timestamp": datetime.utcnow().isoformat()},
                memory_type="short_term",
                ttl=300,
            )
            print_result("Store Memory", result.get("success", False), 
                        f"Stored key: {result.get('key')}")
        except Exception as e:
            print_result("Store Memory", False, f"Error: {e}")
        
        # Test 3: Retrieve
        try:
            result = await memory.retrieve(
                namespace="test",
                key="test_key",
                memory_type="short_term",
            )
            success = result is not None and result.get("value", {}).get("message") == "Hello World"
            print_result("Retrieve Memory", success, 
                        f"Retrieved: {result.get('value') if result else 'None'}")
        except Exception as e:
            print_result("Retrieve Memory", False, f"Error: {e}")
        
        # Test 4: Update
        try:
            result = await memory.update(
                namespace="test",
                key="test_key",
                value={"message": "Updated!", "count": 42},
                memory_type="short_term",
            )
            print_result("Update Memory", result.get("success", False))
        except Exception as e:
            print_result("Update Memory", False, f"Error: {e}")
        
        # Test 5: List Keys
        try:
            keys = await memory.list_keys(
                namespace="test",
                memory_type="short_term",
            )
            print_result("List Keys", len(keys) > 0, f"Found {len(keys)} keys")
        except Exception as e:
            print_result("List Keys", False, f"Error: {e}")
        
        # Test 6: Delete
        try:
            result = await memory.delete(
                namespace="test",
                key="test_key",
                memory_type="short_term",
            )
            print_result("Delete Memory", result.get("success", False))
        except Exception as e:
            print_result("Delete Memory", False, f"Error: {e}")
        
        await memory.disconnect()
        return True
        
    except ImportError as e:
        print_result("Memory Service Import", False, f"Import error: {e}")
        return False


async def test_slack_service():
    """Test Slack Service."""
    print_section("Testing Slack Service")
    
    try:
        from services.integrations.slack_service import SlackService
        
        # Test 1: Import
        print_result("Slack Service Import", True, "Module imported successfully")
        
        # Test 2: Initialization
        try:
            slack = SlackService(bot_token="xoxb-test-token")
            print_result("Slack Service Init", True, "Service initialized")
        except Exception as e:
            print_result("Slack Service Init", False, f"Error: {e}")
            return False
        
        print("     ℹ️  Actual API calls require valid Slack Bot Token")
        print("     ℹ️  Set up at: https://api.slack.com/apps")
        
        return True
        
    except ImportError as e:
        print_result("Slack Service Import", False, f"Import error: {e}")
        return False


async def test_discord_service():
    """Test Discord Service."""
    print_section("Testing Discord Service")
    
    try:
        from services.integrations.discord_service import DiscordService
        
        # Test 1: Import
        print_result("Discord Service Import", True, "Module imported successfully")
        
        # Test 2: Initialization
        try:
            discord = DiscordService()
            print_result("Discord Service Init", True, "Service initialized")
        except Exception as e:
            print_result("Discord Service Init", False, f"Error: {e}")
            return False
        
        # Test 3: Color conversion
        try:
            color_int = discord.hex_to_int_color("#5865F2")
            expected = 0x5865F2
            success = color_int == expected
            print_result("Color Conversion", success, 
                        f"#5865F2 -> {color_int} (expected {expected})")
        except Exception as e:
            print_result("Color Conversion", False, f"Error: {e}")
        
        print("     ℹ️  Actual webhook calls require valid Discord Webhook URL")
        
        return True
        
    except ImportError as e:
        print_result("Discord Service Import", False, f"Import error: {e}")
        return False


async def test_email_service():
    """Test Email Service."""
    print_section("Testing Email Service")
    
    try:
        from services.integrations.email_service import EmailService, SMTP_CONFIGS
        
        # Test 1: Import
        print_result("Email Service Import", True, "Module imported successfully")
        
        # Test 2: SMTP Configs
        try:
            configs = list(SMTP_CONFIGS.keys())
            print_result("SMTP Configs", len(configs) > 0, 
                        f"Available: {', '.join(configs)}")
        except Exception as e:
            print_result("SMTP Configs", False, f"Error: {e}")
        
        # Test 3: Initialization
        try:
            email = EmailService(
                smtp_host="smtp.gmail.com",
                smtp_port=587,
                username="test@example.com",
                password="test-password",
            )
            print_result("Email Service Init", True, "Service initialized")
        except Exception as e:
            print_result("Email Service Init", False, f"Error: {e}")
            return False
        
        print("     ℹ️  Actual email sending requires valid SMTP credentials")
        
        return True
        
    except ImportError as e:
        print_result("Email Service Import", False, f"Import error: {e}")
        return False


async def test_google_drive_service():
    """Test Google Drive Service."""
    print_section("Testing Google Drive Service")
    
    try:
        from services.integrations.google_drive_service import GoogleDriveService
        
        # Test 1: Import
        print_result("Google Drive Service Import", True, "Module imported successfully")
        
        print("     ℹ️  Actual operations require Google OAuth2 credentials")
        print("     ℹ️  Set up at: https://console.cloud.google.com")
        
        return True
        
    except ImportError as e:
        print_result("Google Drive Service Import", False, f"Import error: {e}")
        print(f"     ℹ️  Install: pip install google-auth google-api-python-client")
        return False


async def test_approval_model():
    """Test Approval Model."""
    print_section("Testing Approval Model")
    
    try:
        from models.approval import ApprovalRequest
        
        # Test 1: Import
        print_result("Approval Model Import", True, "Model imported successfully")
        
        # Test 2: Create instance
        try:
            approval = ApprovalRequest(
                workflow_id="test_workflow",
                node_id="test_node",
                approvers=["user1@example.com", "user2@example.com"],
                require_all=True,
                message="Test approval request",
            )
            print_result("Create Approval Instance", True, 
                        f"ID: {approval.id}, Status: {approval.status}")
        except Exception as e:
            print_result("Create Approval Instance", False, f"Error: {e}")
            return False
        
        # Test 3: Methods
        try:
            can_approve = approval.can_approve("user1@example.com")
            print_result("Can Approve Check", can_approve, 
                        "user1@example.com can approve")
        except Exception as e:
            print_result("Can Approve Check", False, f"Error: {e}")
        
        # Test 4: Add approval
        try:
            is_complete = approval.add_approval("user1@example.com")
            print_result("Add Approval", not is_complete, 
                        f"Approved by: {approval.approved_by}, Complete: {is_complete}")
        except Exception as e:
            print_result("Add Approval", False, f"Error: {e}")
        
        return True
        
    except ImportError as e:
        print_result("Approval Model Import", False, f"Import error: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "🚀" * 30)
    print("  BACKEND FEATURE TESTS")
    print("  Testing newly implemented features")
    print("🚀" * 30)
    
    results = {}
    
    # Test Memory Service
    results['memory'] = await test_memory_service()
    
    # Test Integration Services
    results['slack'] = await test_slack_service()
    results['discord'] = await test_discord_service()
    results['email'] = await test_email_service()
    results['google_drive'] = await test_google_drive_service()
    
    # Test Approval System
    results['approval'] = await test_approval_model()
    
    # Summary
    print_section("TEST SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/total*100):.1f}%\n")
    
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name.replace('_', ' ').title()}")
    
    print("\n" + "=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
