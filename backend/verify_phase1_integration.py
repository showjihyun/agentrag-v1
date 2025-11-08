"""
Phase 1 Architecture Integration Verification Script

This script verifies that all Phase 1 components are properly integrated.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))


async def verify_circuit_breaker():
    """Verify Circuit Breaker integration."""
    print("\n[*] Verifying Circuit Breaker...")
    
    try:
        from backend.core.circuit_breaker import CircuitBreaker, get_circuit_breaker_registry
        
        # Test Circuit Breaker creation
        breaker = CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            timeout=5
        )
        
        # Test successful call
        async def success_func():
            return "success"
        
        result = await breaker.call(success_func)
        assert result == "success", "Circuit breaker call failed"
        
        # Test registry
        registry = get_circuit_breaker_registry()
        test_breaker = registry.register("test", failure_threshold=3, timeout=5)
        assert test_breaker is not None, "Registry registration failed"
        
        print("[OK] Circuit Breaker: PASSED")
        return True
        
    except Exception as e:
        print(f"[FAIL] Circuit Breaker: FAILED - {e}")
        return False


async def verify_multi_level_cache():
    """Verify Multi-Level Cache integration."""
    print("\n[*] Verifying Multi-Level Cache...")
    
    try:
        from backend.core.advanced_cache import LRUCache, cache_key
        
        # Test LRU Cache
        cache = LRUCache(max_size=10, ttl=60)
        
        # Test set/get
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        assert value == "test_value", "Cache get/set failed"
        
        # Test cache_key helper
        key = cache_key("agent", "123")
        assert key == "agent:123", "Cache key helper failed"
        
        # Test stats
        stats = cache.get_stats()
        assert "hits" in stats, "Cache stats failed"
        
        print("[OK] Multi-Level Cache: PASSED")
        return True
        
    except Exception as e:
        print(f"[FAIL] Multi-Level Cache: FAILED - {e}")
        return False


async def verify_enhanced_logging():
    """Verify Enhanced Logging integration."""
    print("\n[*] Verifying Enhanced Logging...")
    
    try:
        from backend.core.enhanced_logging import (
            get_logger,
            log_execution_time,
            set_request_context
        )
        
        # Test logger creation
        logger = get_logger(__name__)
        assert logger is not None, "Logger creation failed"
        
        # Test request context
        set_request_context(request_id="test-123", user_id="user-456")
        
        # Test execution time logging
        log_execution_time("test_function", 100.5, test_param="value")
        
        print("[OK] Enhanced Logging: PASSED")
        return True
        
    except Exception as e:
        print(f"[FAIL] Enhanced Logging: FAILED - {e}")
        return False


async def verify_dependencies_integration():
    """Verify ServiceContainer integration."""
    print("\n[*] Verifying ServiceContainer Integration...")
    
    try:
        from backend.core.dependencies import ServiceContainer
        
        # Check if Phase 1 attributes exist
        container = ServiceContainer()
        
        assert hasattr(container, '_multi_level_cache'), "Multi-level cache attribute missing"
        assert hasattr(container, '_circuit_breaker_registry'), "Circuit breaker registry attribute missing"
        
        # Check if getters exist
        assert hasattr(container, 'get_multi_level_cache'), "get_multi_level_cache method missing"
        assert hasattr(container, 'get_circuit_breaker_registry'), "get_circuit_breaker_registry method missing"
        
        print("[OK] ServiceContainer Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"[FAIL] ServiceContainer Integration: FAILED - {e}")
        return False


async def verify_agent_service_integration():
    """Verify Agent Service integration."""
    print("\n[*] Verifying Agent Service Integration...")
    
    try:
        from backend.services.agent_builder.agent_service import AgentService
        import inspect
        
        # Check if AgentService has Phase 1 parameters
        sig = inspect.signature(AgentService.__init__)
        params = list(sig.parameters.keys())
        
        assert 'cache' in params, "cache parameter missing from AgentService"
        assert 'db_breaker' in params, "db_breaker parameter missing from AgentService"
        
        # Check if get_agent is async
        assert asyncio.iscoroutinefunction(AgentService.get_agent), "get_agent should be async"
        
        print("[OK] Agent Service Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"[FAIL] Agent Service Integration: FAILED - {e}")
        return False


async def verify_api_integration():
    """Verify API integration."""
    print("\n[*] Verifying API Integration...")
    
    try:
        # Check if circuit_breaker_status module exists
        from backend.api import circuit_breaker_status
        
        assert hasattr(circuit_breaker_status, 'router'), "Circuit breaker router missing"
        
        print("[OK] API Integration: PASSED")
        return True
        
    except Exception as e:
        print(f"[FAIL] API Integration: FAILED - {e}")
        return False


async def main():
    """Run all verification tests."""
    print("=" * 70)
    print("Phase 1 Architecture Integration Verification")
    print("=" * 70)
    
    results = []
    
    # Run all verifications
    results.append(await verify_circuit_breaker())
    results.append(await verify_multi_level_cache())
    results.append(await verify_enhanced_logging())
    results.append(await verify_dependencies_integration())
    results.append(await verify_agent_service_integration())
    results.append(await verify_api_integration())
    
    # Summary
    print("\n" + "=" * 70)
    print("Verification Summary")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n[OK] Passed: {passed}/{total}")
    print(f"[FAIL] Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All Phase 1 components are properly integrated!")
        return 0
    else:
        print("\n[WARNING] Some components failed verification. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
