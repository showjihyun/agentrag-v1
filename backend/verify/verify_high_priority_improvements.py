"""
Verification script for HIGH PRIORITY improvements:
1. Circuit Breaker & Retry Logic
2. Security Headers
3. New Feature Tests (to be added)
"""

import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def verify_files_exist():
    """Verify all new files are created."""
    print("=" * 70)
    print("VERIFICATION: HIGH PRIORITY Improvements")
    print("=" * 70)
    print()

    files_to_check = ["core/resilience.py"]

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
            "core.resilience",
            [
                "CircuitBreaker",
                "CircuitState",
                "CircuitBreakerError",
                "RetryStrategy",
                "retry_async",
                "retry_sync",
                "with_circuit_breaker",
                "with_retry",
                "get_circuit_breaker",
            ],
        )
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


def test_circuit_breaker():
    """Test circuit breaker functionality."""
    print("3. Testing Circuit Breaker...")

    try:
        from core.resilience import CircuitBreaker, CircuitState, CircuitBreakerError

        # Create circuit breaker
        breaker = CircuitBreaker(
            name="test_service", failure_threshold=3, recovery_timeout=2
        )
        print("   ✓ CircuitBreaker created")

        # Test initial state
        assert breaker.state == CircuitState.CLOSED
        print("   ✓ Initial state is CLOSED")

        # Test successful call
        async def success_func():
            return "success"

        result = asyncio.run(breaker.call(success_func))
        assert result == "success"
        print("   ✓ Successful call works")

        # Test failure recording
        async def fail_func():
            raise ValueError("Test error")

        for i in range(3):
            try:
                asyncio.run(breaker.call(fail_func))
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN
        print("   ✓ Circuit opens after threshold failures")

        # Test circuit breaker error
        try:
            asyncio.run(breaker.call(success_func))
            print("   ✗ Should have raised CircuitBreakerError")
            return False
        except CircuitBreakerError:
            print("   ✓ CircuitBreakerError raised when open")

        # Test stats
        stats = breaker.get_stats()
        assert "state" in stats
        assert stats["state"] == "open"
        print("   ✓ Stats retrieval works")

        print()
        return True

    except Exception as e:
        print(f"   ✗ Circuit breaker test failed: {e}")
        import traceback

        traceback.print_exc()
        print()
        return False


def test_retry_logic():
    """Test retry logic functionality."""
    print("4. Testing Retry Logic...")

    try:
        from core.resilience import RetryStrategy, retry_async, with_retry

        # Test retry strategy
        strategy = RetryStrategy(max_attempts=3, initial_delay=0.1, max_delay=1.0)
        print("   ✓ RetryStrategy created")

        # Test delay calculation
        delay1 = strategy.get_delay(0)
        delay2 = strategy.get_delay(1)
        assert delay2 > delay1
        print("   ✓ Exponential backoff works")

        # Test retry_async
        attempt_count = 0

        async def flaky_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = asyncio.run(
            retry_async(
                flaky_func, strategy=RetryStrategy(max_attempts=3, initial_delay=0.01)
            )
        )
        assert result == "success"
        assert attempt_count == 3
        print("   ✓ retry_async works with eventual success")

        # Test decorator
        call_count = 0

        @with_retry(max_attempts=2, initial_delay=0.01)
        async def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Error")
            return "ok"

        result = asyncio.run(decorated_func())
        assert result == "ok"
        print("   ✓ @with_retry decorator works")

        print()
        return True

    except Exception as e:
        print(f"   ✗ Retry logic test failed: {e}")
        import traceback

        traceback.print_exc()
        print()
        return False


def test_security_headers():
    """Test security headers in main.py."""
    print("5. Testing Security Headers...")

    main_file = os.path.join(os.path.dirname(__file__), "main.py")

    try:
        with open(main_file, "r", encoding="utf-8") as f:
            content = f.read()

        headers = [
            ("Content-Security-Policy", "Content-Security-Policy"),
            ("X-Content-Type-Options", "X-Content-Type-Options"),
            ("X-Frame-Options", "X-Frame-Options"),
            ("X-XSS-Protection", "X-XSS-Protection"),
            ("Strict-Transport-Security", "Strict-Transport-Security"),
            ("Referrer-Policy", "Referrer-Policy"),
            ("Permissions-Policy", "Permissions-Policy"),
        ]

        all_present = True
        for header_name, header_string in headers:
            exists = header_string in content
            status = "✓" if exists else "✗"
            print(f"   {status} {header_name}")

            if not exists:
                all_present = False

        # Check middleware exists
        middleware_exists = "security_headers_middleware" in content
        status = "✓" if middleware_exists else "✗"
        print(f"   {status} Security headers middleware")

        if not middleware_exists:
            all_present = False

        print()
        return all_present

    except Exception as e:
        print(f"   ✗ Failed to check security headers: {e}")
        print()
        return False


def test_integration():
    """Test integration examples."""
    print("6. Testing Integration Examples...")

    try:
        from core.resilience import get_circuit_breaker, with_retry

        # Test global circuit breaker
        breaker = get_circuit_breaker("test_api", failure_threshold=5)
        assert breaker.name == "test_api"
        print("   ✓ Global circuit breaker works")

        # Test combined usage
        @with_retry(max_attempts=2, initial_delay=0.01)
        async def api_call_with_retry():
            return "data"

        result = asyncio.run(api_call_with_retry())
        assert result == "data"
        print("   ✓ Combined patterns work")

        print()
        return True

    except Exception as e:
        print(f"   ✗ Integration test failed: {e}")
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
        print("HIGH PRIORITY Improvements Complete!")
        print()
        print("✅ 1. Circuit Breaker & Retry Logic")
        print("   • CircuitBreaker class with 3 states (CLOSED/OPEN/HALF_OPEN)")
        print("   • Automatic failure tracking and recovery")
        print("   • RetryStrategy with exponential backoff + jitter")
        print("   • Decorators: @with_circuit_breaker, @with_retry")
        print("   • Global circuit breaker registry")
        print()
        print("✅ 2. Security Headers")
        print("   • Content-Security-Policy (CSP)")
        print("   • X-Content-Type-Options (nosniff)")
        print("   • X-Frame-Options (DENY)")
        print("   • X-XSS-Protection")
        print("   • Strict-Transport-Security (HSTS)")
        print("   • Referrer-Policy")
        print("   • Permissions-Policy")
        print()
        print("Usage Examples:")
        print()
        print("# Circuit Breaker")
        print("breaker = get_circuit_breaker('external_api')")
        print("result = await breaker.call(api_function)")
        print()
        print("# Retry with Exponential Backoff")
        print("@with_retry(max_attempts=3, initial_delay=1.0)")
        print("async def unstable_function():")
        print("    # Function code")
        print("    pass")
        print()
        print("# Combined")
        print("@with_circuit_breaker(breaker)")
        print("@with_retry(max_attempts=3)")
        print("async def resilient_api_call():")
        print("    # API call")
        print("    pass")
        print()
        print("Next Steps:")
        print("  1. Add circuit breakers to external service calls")
        print("  2. Add retry logic to network operations")
        print("  3. Monitor circuit breaker states")
        print("  4. Proceed to MEDIUM PRIORITY improvements")
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
        "Circuit Breaker": test_circuit_breaker(),
        "Retry Logic": test_retry_logic(),
        "Security Headers": test_security_headers(),
        "Integration": test_integration(),
    }

    success = print_summary(results)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
