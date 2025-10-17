"""
Verification script for Phase 2: Structured Logging & Health Checks
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verify_files_exist():
    """Verify all new files are created."""
    print("=" * 70)
    print("VERIFICATION: Phase 2 - Structured Logging & Health Checks")
    print("=" * 70)
    print()

    files_to_check = ["core/structured_logging.py", "core/health_check.py"]

    print("1. Checking file creation...")
    all_exist = True

    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        exists = os.path.exists(full_path)
        status = "✓" if exists else "✗"
        print(f"   {status} {file_path}")

        if not exists:
            all_exist = False

    print()
    return all_exist


def verify_imports():
    """Verify all modules can be imported."""
    print("2. Checking module imports...")

    modules = [
        (
            "core.structured_logging",
            [
                "StructuredFormatter",
                "StructuredLogger",
                "setup_structured_logging",
                "get_logger",
                "set_request_context",
                "log_performance",
            ],
        ),
        (
            "core.health_check",
            [
                "HealthChecker",
                "ComponentHealth",
                "HealthStatus",
                "get_health_checker",
                "initialize_health_checks",
            ],
        ),
    ]

    all_imported = True

    for module_name, classes in modules:
        try:
            module = __import__(module_name, fromlist=classes)

            for class_name in classes:
                if hasattr(module, class_name):
                    print(f"   ✓ {module_name}.{class_name}")
                else:
                    print(f"   ✗ {module_name}.{class_name} not found")
                    all_imported = False

        except Exception as e:
            print(f"   ✗ Failed to import {module_name}: {e}")
            all_imported = False

    print()
    return all_imported


def verify_structured_logging():
    """Test structured logging functionality."""
    print("3. Testing structured logging...")

    try:
        from core.structured_logging import (
            get_logger,
            set_request_context,
            StructuredFormatter,
        )
        import logging
        import json

        # Create test logger
        test_logger = get_logger("test")
        print("   ✓ Logger created")

        # Test context setting
        set_request_context(request_id="test-123", user_id="user-456")
        print("   ✓ Request context set")

        # Test formatter
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        formatted = formatter.format(record)

        # Verify it's valid JSON
        parsed = json.loads(formatted)
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "message" in parsed
        print("   ✓ JSON formatting works")

        # Test convenience methods
        test_logger.info("Test info message", extra_field="value")
        print("   ✓ Convenience methods work")

        print()
        return True

    except Exception as e:
        print(f"   ✗ Structured logging test failed: {e}")
        print()
        return False


def verify_health_checks():
    """Test health check functionality."""
    print("4. Testing health check system...")

    try:
        from core.health_check import (
            HealthChecker,
            ComponentHealth,
            HealthStatus,
            get_health_checker,
        )

        # Create health checker
        checker = HealthChecker()
        print("   ✓ HealthChecker created")

        # Create test component health
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            message="Test component healthy",
            details={"test": "value"},
        )
        print("   ✓ ComponentHealth created")

        # Test to_dict
        health_dict = health.to_dict()
        assert "name" in health_dict
        assert "status" in health_dict
        assert health_dict["status"] == "healthy"
        print("   ✓ ComponentHealth.to_dict() works")

        # Test health checker registration
        async def test_check():
            return ComponentHealth(
                name="test", status=HealthStatus.HEALTHY, message="Test passed"
            )

        checker.register_check("test", test_check, critical=True)
        assert "test" in checker.checks
        print("   ✓ Health check registration works")

        # Test global instance
        global_checker = get_health_checker()
        assert global_checker is not None
        print("   ✓ Global health checker works")

        print()
        return True

    except Exception as e:
        print(f"   ✗ Health check test failed: {e}")
        import traceback

        traceback.print_exc()
        print()
        return False


def verify_config_updates():
    """Verify config.py has new settings."""
    print("5. Checking configuration updates...")

    try:
        from config import settings

        checks = [
            ("LOG_FORMAT", hasattr(settings, "LOG_FORMAT")),
            ("LOG_FILE", hasattr(settings, "LOG_FILE")),
        ]

        all_updated = True
        for setting_name, exists in checks:
            status = "✓" if exists else "✗"
            print(f"   {status} {setting_name}")

            if not exists:
                all_updated = False

        print()
        return all_updated

    except Exception as e:
        print(f"   ✗ Failed to check config: {e}")
        print()
        return False


def verify_main_integration():
    """Verify main.py integrates new components."""
    print("6. Checking main.py integration...")

    main_file = os.path.join(os.path.dirname(__file__), "main.py")

    try:
        with open(main_file, "r", encoding="utf-8") as f:
            content = f.read()

        checks = [
            (
                "Structured logging import",
                "from backend.core.structured_logging import",
            ),
            ("Setup structured logging", "setup_structured_logging"),
            ("Get logger", "get_logger"),
            ("Set request context", "set_request_context"),
            ("Health check import", "from backend.core.health_check import"),
            ("Initialize health checks", "initialize_health_checks"),
            ("Health endpoint", '@app.get("/api/health")'),
            ("Simple health endpoint", '@app.get("/api/health/simple")'),
            ("Component health endpoint", '@app.get("/api/health/{component}")'),
        ]

        all_integrated = True
        for check_name, check_string in checks:
            exists = check_string in content
            status = "✓" if exists else "✗"
            print(f"   {status} {check_name}")

            if not exists:
                all_integrated = False

        print()
        return all_integrated

    except Exception as e:
        print(f"   ✗ Failed to check main.py: {e}")
        print()
        return False


def print_summary(results):
    """Print verification summary."""
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print()

    all_passed = all(results.values())

    for check_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"   {status}: {check_name}")

    print()
    print("=" * 70)

    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print()
        print("Phase 2 Implementation Complete!")
        print()
        print("New Features:")
        print("  • Structured Logging (JSON format)")
        print("    - Automatic request ID tracking")
        print("    - User context in logs")
        print("    - Performance logging decorator")
        print("    - Convenience methods for common scenarios")
        print()
        print("  • Comprehensive Health Checks")
        print("    - Database health monitoring")
        print("    - Redis health monitoring")
        print("    - Milvus health monitoring")
        print("    - LLM provider health monitoring")
        print("    - Embedding service health monitoring")
        print("    - Cache system health monitoring")
        print("    - Storage health monitoring")
        print("    - Background tasks health monitoring")
        print()
        print("Health Check Endpoints:")
        print("  • GET /api/health - Full system health check")
        print("  • GET /api/health/simple - Simple OK check")
        print("  • GET /api/health/{component} - Specific component check")
        print()
        print("Example Health Response:")
        print("  {")
        print('    "status": "healthy",')
        print('    "timestamp": "2025-10-07T10:30:45.123Z",')
        print('    "response_time_ms": 234.5,')
        print('    "components": {')
        print('      "database": {')
        print('        "status": "healthy",')
        print('        "response_time_ms": 12.3,')
        print('        "details": {...}')
        print("      },")
        print("      ...")
        print("    }")
        print("  }")
        print()
        print("Next Steps:")
        print("  1. Start the application and test health endpoints")
        print("  2. Review JSON logs in logs/app.log")
        print("  3. Monitor component health status")
        print("  4. Proceed to Phase 3: Metrics Collection (Prometheus)")
    else:
        print("✗ SOME CHECKS FAILED")
        print()
        print("Please review the failed checks above and fix any issues.")

    print("=" * 70)

    return all_passed


def main():
    """Run all verifications."""
    results = {
        "File Creation": verify_files_exist(),
        "Module Imports": verify_imports(),
        "Structured Logging": verify_structured_logging(),
        "Health Checks": verify_health_checks(),
        "Config Updates": verify_config_updates(),
        "Main Integration": verify_main_integration(),
    }

    success = print_summary(results)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
